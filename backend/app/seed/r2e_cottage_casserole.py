"""R2-E School2022 cottage-cheese casserole prepared-output publication batch."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any
from uuid import UUID

from app.db.config import REPOSITORY_ROOT, DatabaseConfig
from app.db.migrations import apply_migrations
from app.domain.recipe_nutrition_v2 import NUTRIENT_CODES
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
from app.persistence.sqlalchemy_core.food_ingredient_composition import (
    create_food_catalogue_service,
)
from app.persistence.sqlalchemy_core.food_recipe_composition import (
    create_food_recipe_catalogue_service,
)
from app.persistence.sqlalchemy_core.recipe_nutrition_v2 import (
    SqlAlchemyRecipeNutritionV2ReadScope,
    SqlAlchemyRecipeNutritionV2UnitOfWork,
    create_recipe_nutrition_v2_service,
)
from app.seed.r2c_breakfast_grain_diversity import (
    seed_r2c_breakfast_grain_diversity,
)
from app.services.food_ingredients import TrustedFoodIngredientIdentitySeed
from app.services.food_recipes import (
    TrustedRecipeIngredientSeed,
    TrustedRecipeSeed,
    TrustedRecipeSeedDisposition,
    TrustedRecipeVersionSeed,
)
from app.services.planner import PlannerAdmissionBlocker, PlannerService
from app.services.prepared_recipe_activation import activate_prepared_recipe
from app.services.recipe_nutrition_v2 import (
    PreparedPublicationDisposition,
    RecipeNutritionV2ConflictError,
    ReviewedPreparedRecipeNutritionSpec,
)

PACKAGE = REPOSITORY_ROOT / "data/curation/r2e-cottage-casserole"
SELECTION_PATH = PACKAGE / "candidate-selection.json"
IDENTITY_REVIEW_PATH = PACKAGE / "food-identity-review.json"
APPLICABILITY_PATH = PACKAGE / "household-applicability-review.json"
PUBLICATION_SPECS_PATH = PACKAGE / "publication-specs.json"

SELECTION_GIT_BLOB_SHA = "62baaf64daea24ed52c32f8c0ce80f743c9033f3"
IDENTITY_REVIEW_GIT_BLOB_SHA = "7582a3c5821718c0e97dadd5eeae6b4bc597fc85"
APPLICABILITY_GIT_BLOB_SHA = "dbcefdac0528cddbcbe01871e22a84ea2206c238"
PUBLICATION_SPECS_GIT_BLOB_SHA = "52f966d60226aec852d06790fe912e36f168cbdc"

R2E_CONTRACT_ACCEPTED_BASE = "99a579e35b0a0fa6d09947b80ffecb222a45bf96"
SOURCE_PDF_SHA256 = "c9264cf521ae699fb30a964d5668caec8f31ff1efc1f13a3dd055df40ebafb5d"
SOURCE_ARCHIVE_SHA256 = (
    "c0d90020798b2998e841328b9081f06f8197efda084b852aa8457fd41a5ce8ea"
)

CASSEROLE_RECIPE_CODE = "SCHOOL2022_54_1T_COTTAGE_CHEESE_CASSEROLE"
SOURCE_RECIPE_ID = "ru-school2022:recipe:54-1т"

TVOROG_5_FOOD_CODE = "TVOROG_5"
SEMOLINA_GROATS_FOOD_CODE = "SEMOLINA_GROATS"
SOUR_CREAM_15_FOOD_CODE = "SOUR_CREAM_15"
VANILLIN_FOOD_CODE = "VANILLIN"
IDENTITY_ONLY_FOOD_CODES = (
    TVOROG_5_FOOD_CODE,
    SEMOLINA_GROATS_FOOD_CODE,
    SOUR_CREAM_15_FOOD_CODE,
    VANILLIN_FOOD_CODE,
)
REUSED_FOOD_CODES = (
    "SUGAR",
    "BREADCRUMBS",
    "EGG",
    "BUTTER_PEASANT_72_5_UNSALTED",
    "SALT_IODIZED",
    "WATER",
)


@dataclass(frozen=True)
class R2ECottageCasseroleResult:
    identity_food_inserted: int
    identity_food_existing: int
    recipe_version_id: UUID
    authority_disposition: str
    active: bool
    exact_energy_kcal: Decimal


def _git_blob_sha(raw: bytes) -> str:
    header = f"blob {len(raw)}\0".encode()
    return hashlib.sha1(header + raw).hexdigest()


def _checked_json(path: Path, expected_git_blob_sha: str) -> dict[str, Any]:
    raw = path.read_bytes()
    if _git_blob_sha(raw) != expected_git_blob_sha:
        raise ValueError(f"R2-E frozen artifact changed: {path.name}.")
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise TypeError(f"R2-E artifact must be a JSON object: {path.name}.")
    return payload


def _decimal(value: object, *, field: str) -> Decimal:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field} must be a canonical Decimal string.")
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field} is not Decimal.") from exc
    if not parsed.is_finite() or parsed < 0 or format(parsed, "f") != value:
        raise ValueError(f"{field} must be a canonical non-negative Decimal.")
    return parsed


def _load_contract(
    package: Path = PACKAGE,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    selection = _checked_json(package / SELECTION_PATH.name, SELECTION_GIT_BLOB_SHA)
    identity_review = _checked_json(
        package / IDENTITY_REVIEW_PATH.name,
        IDENTITY_REVIEW_GIT_BLOB_SHA,
    )
    applicability = _checked_json(
        package / APPLICABILITY_PATH.name,
        APPLICABILITY_GIT_BLOB_SHA,
    )
    specs = _checked_json(
        package / PUBLICATION_SPECS_PATH.name,
        PUBLICATION_SPECS_GIT_BLOB_SHA,
    )

    selected = selection.get("selected")
    projected = selection.get("projected_after_future_runtime")
    if (
        selection.get("schema_version") != 1
        or selection.get("operation") != "R2E_COTTAGE_CASSEROLE_CANDIDATE_SELECTION"
        or selection.get("accepted_base") != R2E_CONTRACT_ACCEPTED_BASE
        or not isinstance(selected, dict)
        or selected.get("canonical_code") != CASSEROLE_RECIPE_CODE
        or selected.get("source_recipe_id") != SOURCE_RECIPE_ID
        or selected.get("source_output_g") != "150"
        or selected.get("prepared_energy_kcal") != "301.2"
        or not isinstance(projected, dict)
        or projected.get("capacity_per_week") != 6
        or projected.get("closes_seven_breakfast_gap") is not False
    ):
        raise ValueError("R2-E candidate-selection contract identity changed.")

    decisions = identity_review.get("decisions")
    new_identities = identity_review.get("new_identity_only_foods")
    if (
        identity_review.get("schema_version") != 1
        or identity_review.get("operation")
        != "R2E_COTTAGE_CASSEROLE_FOOD_IDENTITY_REVIEW"
        or identity_review.get("accepted_base") != R2E_CONTRACT_ACCEPTED_BASE
        or identity_review.get("source", {}).get("archive_sha256")
        != SOURCE_ARCHIVE_SHA256
        or identity_review.get("source", {}).get("source_pdf_sha256")
        != SOURCE_PDF_SHA256
        or identity_review.get("source_recipe_id") != SOURCE_RECIPE_ID
        or not isinstance(decisions, list)
        or not isinstance(new_identities, list)
    ):
        raise ValueError("R2-E FoodIngredient review identity changed.")

    created = tuple(
        row.get("canonical_code")
        for row in decisions
        if row.get("decision") == "CREATE_IDENTITY_ONLY"
    )
    reused = tuple(
        row.get("canonical_code")
        for row in decisions
        if row.get("decision") == "REUSE_EXISTING"
    )
    if (
        created != IDENTITY_ONLY_FOOD_CODES
        or reused != REUSED_FOOD_CODES
        or tuple(row.get("canonical_code") for row in new_identities)
        != IDENTITY_ONLY_FOOD_CODES
        or any(
            row.get("nutrition_profile") is not None
            or row.get("composition") is not None
            for row in new_identities
        )
    ):
        raise ValueError("R2-E FoodIngredient mapping decisions changed.")

    candidate = applicability.get("candidate")
    if (
        applicability.get("schema_version") != 1
        or applicability.get("operation")
        != "R2E_COTTAGE_CASSEROLE_HOUSEHOLD_APPLICABILITY"
        or applicability.get("accepted_base") != R2E_CONTRACT_ACCEPTED_BASE
        or applicability.get("source", {}).get("archive_sha256")
        != SOURCE_ARCHIVE_SHA256
        or applicability.get("source", {}).get("source_pdf_sha256")
        != SOURCE_PDF_SHA256
        or not isinstance(candidate, dict)
        or candidate.get("source_recipe_id") != SOURCE_RECIPE_ID
        or candidate.get("decision") != "HOUSEHOLD_APPLICABLE"
        or candidate.get("specialized_medical_scope") is not False
        or candidate.get("planner_role_review") != "breakfast"
        or candidate.get("source_output_g") != "150"
        or candidate.get("source_energy_kcal") != "301.2"
    ):
        raise ValueError("R2-E household-applicability contract identity changed.")

    if (
        specs.get("schema_version") != 1
        or specs.get("operation")
        != "R2E_COTTAGE_CASSEROLE_PREPARED_PUBLICATION_SPECS"
        or specs.get("accepted_base") != R2E_CONTRACT_ACCEPTED_BASE
        or specs.get("authority_kind") != "PREPARED_OUTPUT_V1"
        or specs.get("recipe_calculation_version")
        != "RECIPE_PREPARED_OUTPUT_NUTRITION_V1"
        or specs.get("source", {}).get("archive_sha256") != SOURCE_ARCHIVE_SHA256
        or specs.get("source", {}).get("source_document_sha256")
        != SOURCE_PDF_SHA256
    ):
        raise ValueError("R2-E prepared publication contract identity changed.")

    lineage = specs.get("exact_lineage")
    if (
        not isinstance(lineage, dict)
        or lineage.get("source_recipe_id") != SOURCE_RECIPE_ID
        or lineage.get("prepared_energy_authority_basis") != "READY_SAME_CARD_EXACT"
    ):
        raise ValueError("R2-E exact source lineage changed.")

    nutrient_partition = specs.get("nutrient_partition")
    expected_unknown = tuple(code for code in NUTRIENT_CODES if code != "ENERGY_KCAL")
    if (
        not isinstance(nutrient_partition, dict)
        or nutrient_partition.get("frozen_code_count") != len(NUTRIENT_CODES)
        or nutrient_partition.get("available_codes") != ["ENERGY_KCAL"]
        or tuple(nutrient_partition.get("unknown_codes", ())) != expected_unknown
    ):
        raise ValueError("R2-E frozen nutrient partition changed.")

    identities = specs.get("new_identity_only_foods")
    if (
        not isinstance(identities, list)
        or tuple(row.get("canonical_code") for row in identities)
        != IDENTITY_ONLY_FOOD_CODES
        or any(
            row.get("nutrition_profile") is not None
            or row.get("composition") is not None
            for row in identities
        )
    ):
        raise ValueError("R2-E identity-only publication contract changed.")

    recipe = specs.get("recipe")
    prepared = recipe.get("prepared_spec") if isinstance(recipe, dict) else None
    if (
        not isinstance(recipe, dict)
        or recipe.get("canonical_code") != CASSEROLE_RECIPE_CODE
        or recipe.get("initial_is_active") is not False
        or recipe.get("version", {}).get("source_recipe_id") != SOURCE_RECIPE_ID
        or recipe.get("version", {}).get("meal_type_code") != "breakfast"
        or recipe.get("version", {}).get("source_output_g") != "150"
        or recipe.get("version", {}).get("cook_time_minutes") is not None
        or not isinstance(prepared, dict)
        or prepared.get("recipe_code") != CASSEROLE_RECIPE_CODE
        or prepared.get("source_recipe_id") != SOURCE_RECIPE_ID
        or prepared.get("output_mass_g") != "150"
        or prepared.get("expected_available_amounts")
        != [["ENERGY_KCAL", "301.2"]]
        or tuple(prepared.get("expected_unknown_codes", ())) != expected_unknown
        or prepared.get("require_recipe_inactive") is not True
    ):
        raise ValueError("R2-E frozen Recipe/prepared spec changed.")

    runtime_rules = specs.get("runtime_rules")
    if (
        not isinstance(runtime_rules, dict)
        or runtime_rules.get("migration_0043_allowed") is not False
        or runtime_rules.get("planner_change_allowed") is not False
        or runtime_rules.get("source_scaling_allowed") is not False
        or runtime_rules.get("menu_energy_override_allowed") is not False
        or runtime_rules.get("implicit_retention_allowed") is not False
    ):
        raise ValueError("R2-E runtime preservation rules changed.")

    return selection, identity_review, applicability, specs


def _identity_seeds(
    specs: dict[str, Any],
) -> tuple[TrustedFoodIngredientIdentitySeed, ...]:
    return tuple(
        TrustedFoodIngredientIdentitySeed(
            canonical_code=row["canonical_code"],
            canonical_name=row["canonical_name"],
            category_code=row["category_code"],
            default_unit=row["default_unit"],
        )
        for row in specs["new_identity_only_foods"]
    )


def _recipe_seed(specs: dict[str, Any]) -> TrustedRecipeSeed:
    seed = specs["recipe"]
    version = seed["version"]
    retrieved = version["source_retrieved_at"]
    return TrustedRecipeSeed(
        canonical_code=seed["canonical_code"],
        canonical_name=seed["canonical_name"],
        initial_is_active=seed["initial_is_active"],
        version=TrustedRecipeVersionSeed(
            base_servings=_decimal(version["base_servings"], field="base_servings"),
            meal_type_code=version["meal_type_code"],
            prep_time_minutes=version["prep_time_minutes"],
            cook_time_minutes=version["cook_time_minutes"],
            total_time_minutes=version["total_time_minutes"],
            difficulty_code=version["difficulty_code"],
            batch_friendly=version["batch_friendly"],
            freezable=version["freezable"],
            storage_days_fridge=version["storage_days_fridge"],
            storage_days_freezer=version["storage_days_freezer"],
            verification_status=version["verification_status"],
            verified_at=datetime.fromisoformat(
                version["verified_at"].replace("Z", "+00:00")
            ),
            source_name=version["source_name"],
            source_recipe_id=version["source_recipe_id"],
            source_url=version["source_url"],
            source_version=version["source_version"],
            source_retrieved_at=(
                None
                if retrieved is None
                else datetime.fromisoformat(retrieved.replace("Z", "+00:00"))
            ),
            source_document_sha256=version["source_document_sha256"],
            source_original_servings=_decimal(
                version["source_original_servings"],
                field="source_original_servings",
            ),
            rights_review_status=version["rights_review_status"],
            rights_basis=version["rights_basis"],
            change_note=version["change_note"],
            ingredients=tuple(
                TrustedRecipeIngredientSeed(
                    food_ingredient_code=row["food_ingredient_code"],
                    quantity=_decimal(row["quantity"], field="ingredient.quantity"),
                    unit=row["unit"],
                    source_amount_text=row["source_amount_text"],
                    normalization_note=row["normalization_note"],
                    prep_note=row["prep_note"],
                    optional=row["optional"],
                )
                for row in version["ingredients"]
            ),
            steps=tuple(version["steps"]),
            equipment_codes=tuple(version["equipment_codes"]),
            source_output_g=_decimal(
                version["source_output_g"], field="source_output_g"
            ),
            source_output_text=version["source_output_text"],
        ),
    )


def _prepared_spec(
    specs: dict[str, Any],
    seed: TrustedRecipeSeed,
) -> ReviewedPreparedRecipeNutritionSpec:
    spec = specs["recipe"]["prepared_spec"]
    return ReviewedPreparedRecipeNutritionSpec(
        trusted_recipe_seed=seed,
        recipe_code=spec["recipe_code"],
        source_name=spec["source_name"],
        source_recipe_id=spec["source_recipe_id"],
        source_version=spec["source_version"],
        source_document_sha256=spec["source_document_sha256"],
        output_mass_g=_decimal(spec["output_mass_g"], field="output_mass_g"),
        source_locator=spec["source_locator"],
        source_data_type=spec["source_data_type"],
        rights_review_status=spec["rights_review_status"],
        rights_basis=spec["rights_basis"],
        review_reference=spec["review_reference"],
        expected_available_amounts=tuple(
            (code, _decimal(amount, field=f"nutrient.{code}"))
            for code, amount in spec["expected_available_amounts"]
        ),
        expected_unknown_codes=tuple(spec["expected_unknown_codes"]),
        require_recipe_inactive=spec["require_recipe_inactive"],
    )


def _recipe_seed_and_spec(
    specs: dict[str, Any],
) -> tuple[TrustedRecipeSeed, ReviewedPreparedRecipeNutritionSpec]:
    seed = _recipe_seed(specs)
    return seed, _prepared_spec(specs, seed)


def _assert_replay_not_partial(engine, catalogue, nutrition, seed, spec) -> None:
    disposition = catalogue.preflight_trusted_seed(seed)
    if disposition is TrustedRecipeSeedDisposition.FRESH:
        return
    recipe = catalogue.get_by_code(seed.canonical_code)
    detail = catalogue.get_latest_verified(recipe.id)
    with SqlAlchemyRecipeNutritionV2ReadScope(engine) as scope:
        authority = scope.prepared.get_authority(detail.version.id)
        values = scope.prepared.list_values(detail.version.id)
    if authority is None or not values:
        raise RecipeNutritionV2ConflictError("Partial persisted R2-E state.")
    replay = nutrition.publish_prepared(spec)
    if replay.disposition is not PreparedPublicationDisposition.EXACT_REPLAY:
        raise RecipeNutritionV2ConflictError(
            "Expected exact R2-E prepared authority replay."
        )


def seed_r2e_cottage_casserole(
    config: DatabaseConfig | None = None,
    *,
    package: Path = PACKAGE,
) -> R2ECottageCasseroleResult:
    _, _, _, specs_payload = _load_contract(package)

    apply_migrations(config)
    seed_r2c_breakfast_grain_diversity(config)

    engine = create_sqlite_engine(config)
    try:
        food = create_food_catalogue_service(engine)
        identity_summary = food.reconcile_identity_seed(_identity_seeds(specs_payload))
        catalogue = create_food_recipe_catalogue_service(engine)
        nutrition = create_recipe_nutrition_v2_service(engine)
        seed, spec = _recipe_seed_and_spec(specs_payload)

        _assert_replay_not_partial(engine, catalogue, nutrition, seed, spec)

        fresh = (
            catalogue.preflight_trusted_seed(seed) is TrustedRecipeSeedDisposition.FRESH
        )
        if fresh:
            with SqlAlchemyRecipeNutritionV2UnitOfWork(engine) as uow:
                catalogue.reconcile_seed_in_scope(uow, (seed,))
                published = nutrition.publish_prepared_in_scope(uow, spec)
                if published.disposition is not PreparedPublicationDisposition.FRESH:
                    raise RecipeNutritionV2ConflictError(
                        "Fresh R2-E Recipe did not publish fresh prepared authority."
                    )
                projection = nutrition.prepared_consumption_projection_in_scope(
                    uow, published.authority.recipe_version_id
                )
                if (
                    not projection.exact_energy_ready
                    or projection.per_base_serving.kcal is None
                ):
                    raise RecipeNutritionV2ConflictError(
                        "R2-E in-scope exact energy unavailable."
                    )
                uow.commit()
        else:
            published = nutrition.publish_prepared(spec)

        recipe = catalogue.get_by_code(seed.canonical_code)
        detail = catalogue.get_latest_verified(recipe.id)
        projection = nutrition.neutral_consumption_projection(detail.version.id)
        if (
            not projection.exact_energy_ready
            or projection.per_base_serving.kcal is None
        ):
            raise RecipeNutritionV2ConflictError("R2-E exact energy unavailable.")

        planner = PlannerService(
            None,
            None,
            catalogue,
            None,
            None,
            recipe_nutrition=nutrition,  # type: ignore[arg-type]
        )
        admission = next(
            row
            for row in planner.compose_candidate_admission()
            if row.canonical_code == seed.canonical_code
        )
        if fresh:
            activate_prepared_recipe(
                catalogue=catalogue,
                nutrition=nutrition,
                planner=planner,
                spec=spec,
            )
            admission = next(
                row
                for row in planner.compose_candidate_admission()
                if row.canonical_code == seed.canonical_code
            )

        if admission.is_active:
            if not admission.eligible or not admission.exact_energy_ready:
                raise RecipeNutritionV2ConflictError(
                    "R2-E active Planner admission failed."
                )
        elif admission.blockers != (PlannerAdmissionBlocker.INACTIVE,):
            raise RecipeNutritionV2ConflictError(
                "R2-E replay admission has unexpected blockers."
            )

        return R2ECottageCasseroleResult(
            identity_food_inserted=identity_summary.ingredients_inserted,
            identity_food_existing=identity_summary.ingredients_existing,
            recipe_version_id=detail.version.id,
            authority_disposition=published.disposition.value,
            active=admission.is_active,
            exact_energy_kcal=projection.per_base_serving.kcal,
        )
    finally:
        engine.dispose()


if __name__ == "__main__":
    result = seed_r2e_cottage_casserole()
    print(
        json.dumps(
            {
                "identity_food_inserted": result.identity_food_inserted,
                "identity_food_existing": result.identity_food_existing,
                "recipe_version_id": str(result.recipe_version_id),
                "authority_disposition": result.authority_disposition,
                "active": result.active,
                "exact_energy_kcal": format(result.exact_energy_kcal, "f"),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
