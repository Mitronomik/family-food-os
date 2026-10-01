"""Guarded activation boundary for source-backed prepared Recipe Nutrition."""

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
    if (
        replay.disposition is not PreparedPublicationDisposition.EXACT_REPLAY
        or replay.authority.recipe_version_id != detail.version.id
    ):
        raise PreparedRecipeActivationError(
            "Prepared authority is not the exact reviewed RecipeVersion authority."
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
