"""Guarded activation boundary for source-backed prepared Recipe Nutrition."""

from collections.abc import Iterable
from dataclasses import dataclass
from uuid import UUID

from app.domain.food_recipes import Recipe
from app.domain.recipe_nutrition_v2 import RecipeNutritionAuthorityKind
from app.services.food_recipes import FoodRecipeCatalogueService
from app.services.planner import PlannerAdmissionBlocker, PlannerService
from app.services.recipe_nutrition_v2 import (
    PreparedPublicationDisposition,
    RecipeNutritionV2Service,
    RecipeNutritionV2UnavailableError,
    ReviewedPreparedRecipeNutritionSpec,
)


class PreparedRecipeActivationError(ValueError):
    """Prepared Recipe cannot be activated under the reviewed authority contract."""


def _same_source_lineage_contains(
    catalogue: FoodRecipeCatalogueService,
    recipe_id: UUID,
    *,
    descendant_version_id: UUID,
    ancestor_version_id: UUID,
) -> bool:
    versions = {version.id: version for version in catalogue.list_versions(recipe_id)}
    descendant = versions.get(descendant_version_id)
    ancestor = versions.get(ancestor_version_id)
    if descendant is None or ancestor is None:
        return False
    source_identity = (
        ancestor.source_name,
        ancestor.source_recipe_id,
        ancestor.source_version,
        ancestor.source_document_sha256,
    )
    current = descendant
    while True:
        if (
            current.source_name,
            current.source_recipe_id,
            current.source_version,
            current.source_document_sha256,
        ) != source_identity:
            return False
        if current.id == ancestor.id:
            return True
        if current.created_from_version_id is None:
            return False
        parent = versions.get(current.created_from_version_id)
        if parent is None:
            return False
        current = parent


@dataclass(frozen=True)
class PreparedRecipeActivationResult:
    recipe: Recipe
    recipe_version_id: UUID
    activated: bool


def activate_prepared_recipe(
    *,
    catalogue: FoodRecipeCatalogueService,
    nutrition: RecipeNutritionV2Service,
    planner: PlannerService,
    spec: ReviewedPreparedRecipeNutritionSpec,
) -> PreparedRecipeActivationResult:
    recipe = catalogue.get_by_code(spec.recipe_code)
    detail = catalogue.get_latest_verified(recipe.id)

    try:
        canonical = nutrition.prepared_canonical_nutrition(detail.version.id)
    except RecipeNutritionV2UnavailableError as exc:
        raise PreparedRecipeActivationError(
            "Prepared Recipe Nutrition authority is unavailable for activation."
        ) from exc

    replay = nutrition.publish_prepared(spec)
    if replay.disposition is not PreparedPublicationDisposition.EXACT_REPLAY:
        raise PreparedRecipeActivationError(
            "Prepared authority is not an exact reviewed replay."
        )
    if replay.authority.recipe_version_id != detail.version.id:
        if not recipe.is_active:
            raise PreparedRecipeActivationError(
                "Inactive Recipe requires the reviewed spec to target the exact "
                "RecipeVersion being activated."
            )
        if not _same_source_lineage_contains(
            catalogue,
            recipe.id,
            descendant_version_id=detail.version.id,
            ancestor_version_id=replay.authority.recipe_version_id,
        ):
            raise PreparedRecipeActivationError(
                "Active Recipe current version is not an authorized same-source "
                "descendant of the reviewed prepared authority."
            )

    projection = nutrition.neutral_consumption_projection(detail.version.id)
    if (
        projection.authority_kind is not RecipeNutritionAuthorityKind.PREPARED_OUTPUT_V1
        or not projection.exact_energy_ready
        or canonical.per_serving_amount("ENERGY_KCAL") is None
    ):
        raise PreparedRecipeActivationError(
            "Prepared Recipe does not have exact positive prepared energy."
        )

    admission = next(
        (
            row
            for row in planner.compose_candidate_admission()
            if row.recipe_id == recipe.id
        ),
        None,
    )
    if admission is None or admission.recipe_version_id != detail.version.id:
        raise PreparedRecipeActivationError(
            "Planner admission does not resolve the exact reviewed RecipeVersion."
        )

    if recipe.is_active:
        if (
            admission.blockers
            or not admission.eligible
            or not admission.exact_energy_ready
            or not admission.is_active
        ):
            raise PreparedRecipeActivationError(
                "Active prepared Recipe no longer satisfies Planner admission."
            )
        return PreparedRecipeActivationResult(recipe, detail.version.id, False)

    if (
        admission.blockers != (PlannerAdmissionBlocker.INACTIVE,)
        or admission.eligible
        or not admission.exact_energy_ready
    ):
        raise PreparedRecipeActivationError(
            "Planner admission has blockers beyond the reversible INACTIVE flag."
        )

    activated = catalogue._activate_after_policy_check(recipe.id)
    post = next(
        (
            row
            for row in planner.compose_candidate_admission()
            if row.recipe_id == recipe.id
        ),
        None,
    )
    if (
        post is None
        or post.recipe_version_id != detail.version.id
        or not post.is_active
        or not post.eligible
        or not post.exact_energy_ready
        or post.blockers
    ):
        catalogue.deactivate(recipe.id)
        raise PreparedRecipeActivationError(
            "Prepared Recipe failed post-activation Planner verification."
        )
    return PreparedRecipeActivationResult(activated, detail.version.id, True)


@dataclass(frozen=True)
class PreparedRecipeBatchActivationResult:
    recipe_version_ids: tuple[UUID, ...]
    activated: bool


def activate_prepared_recipe_batch(
    *,
    catalogue: FoodRecipeCatalogueService,
    nutrition: RecipeNutritionV2Service,
    planner: PlannerService,
    specs: Iterable[ReviewedPreparedRecipeNutritionSpec],
) -> PreparedRecipeBatchActivationResult:
    """Activate an exact prepared batch atomically after a zero-write preflight."""

    reviewed = tuple(specs)
    if not reviewed:
        raise PreparedRecipeActivationError("Prepared batch is empty.")
    recipe_codes = tuple(spec.recipe_code for spec in reviewed)
    if len(set(recipe_codes)) != len(recipe_codes):
        raise PreparedRecipeActivationError(
            "Prepared batch contains duplicate Recipe codes."
        )

    recipes: list[Recipe] = []
    version_ids: list[UUID] = []
    admissions = []

    admission_rows = tuple(planner.compose_candidate_admission())
    admission_by_recipe = {row.recipe_id: row for row in admission_rows}

    for spec in reviewed:
        recipe = catalogue.get_by_code(spec.recipe_code)
        detail = catalogue.get_latest_verified(recipe.id)

        try:
            canonical = nutrition.prepared_canonical_nutrition(detail.version.id)
        except RecipeNutritionV2UnavailableError as exc:
            raise PreparedRecipeActivationError(
                f"Prepared Recipe Nutrition authority is unavailable: {spec.recipe_code}."
            ) from exc

        replay = nutrition.publish_prepared(spec)
        if replay.disposition is not PreparedPublicationDisposition.EXACT_REPLAY:
            raise PreparedRecipeActivationError(
                f"Prepared authority is not exact: {spec.recipe_code}."
            )
        if replay.authority.recipe_version_id != detail.version.id:
            if not recipe.is_active:
                raise PreparedRecipeActivationError(
                    "Inactive prepared Recipe requires the reviewed spec to target "
                    f"the exact current RecipeVersion: {spec.recipe_code}."
                )
            if not _same_source_lineage_contains(
                catalogue,
                recipe.id,
                descendant_version_id=detail.version.id,
                ancestor_version_id=replay.authority.recipe_version_id,
            ):
                raise PreparedRecipeActivationError(
                    "Active prepared Recipe current version is not an authorized "
                    f"same-source descendant: {spec.recipe_code}."
                )

        projection = nutrition.neutral_consumption_projection(detail.version.id)
        if (
            projection.authority_kind
            is not RecipeNutritionAuthorityKind.PREPARED_OUTPUT_V1
            or not projection.exact_energy_ready
            or canonical.per_serving_amount("ENERGY_KCAL") is None
        ):
            raise PreparedRecipeActivationError(
                f"Prepared Recipe lacks exact positive energy: {spec.recipe_code}."
            )

        admission = admission_by_recipe.get(recipe.id)
        if admission is None or admission.recipe_version_id != detail.version.id:
            raise PreparedRecipeActivationError(
                f"Planner admission does not resolve reviewed RecipeVersion: {spec.recipe_code}."
            )

        recipes.append(recipe)
        version_ids.append(detail.version.id)
        admissions.append(admission)

    active_states = {recipe.is_active for recipe in recipes}
    if len(active_states) != 1:
        raise PreparedRecipeActivationError(
            "Prepared batch has mixed active/inactive state."
        )

    if True in active_states:
        for spec, admission in zip(reviewed, admissions, strict=True):
            if (
                admission.blockers
                or not admission.eligible
                or not admission.exact_energy_ready
                or not admission.is_active
            ):
                raise PreparedRecipeActivationError(
                    f"Active prepared Recipe no longer satisfies Planner admission: {spec.recipe_code}."
                )
        return PreparedRecipeBatchActivationResult(tuple(version_ids), False)

    for spec, admission in zip(reviewed, admissions, strict=True):
        if (
            admission.blockers != (PlannerAdmissionBlocker.INACTIVE,)
            or admission.eligible
            or not admission.exact_energy_ready
            or admission.is_active
        ):
            raise PreparedRecipeActivationError(
                f"Prepared Recipe has blockers beyond INACTIVE: {spec.recipe_code}."
            )

    catalogue._activate_batch_after_policy_check(tuple(recipe.id for recipe in recipes))

    post_rows = tuple(planner.compose_candidate_admission())
    post_by_recipe = {row.recipe_id: row for row in post_rows}
    for spec, recipe, version_id in zip(
        reviewed,
        recipes,
        version_ids,
        strict=True,
    ):
        post = post_by_recipe.get(recipe.id)
        if (
            post is None
            or post.recipe_version_id != version_id
            or not post.is_active
            or not post.eligible
            or not post.exact_energy_ready
            or post.blockers
        ):
            raise AssertionError(
                f"Prepared batch post-commit invariant failed: {spec.recipe_code}."
            )

    return PreparedRecipeBatchActivationResult(tuple(version_ids), True)
