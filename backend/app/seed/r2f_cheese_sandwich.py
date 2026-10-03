"""R2-F cheese-sandwich prepared-output publication batch."""

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
from app.seed.r2e_cottage_casserole import seed_r2e_cottage_casserole
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

PACKAGE = REPOSITORY_ROOT / "data/curation/r2f-sandwich-resilience"
SELECTION_PATH = PACKAGE / "candidate-selection.json"
IDENTITY_REVIEW_PATH = PACKAGE / "food-identity-review.json"
APPLICABILITY_PATH = PACKAGE / "household-applicability-review.json"
PUBLICATION_SPECS_PATH = PACKAGE / "publication-specs.json"
RAW_CARD_PATH = PACKAGE / "raw-cheese-card.txt"

SELECTION_GIT_BLOB_SHA = "421405fffae9d428e9ce5ced5c326e0d870c26cb"
IDENTITY_REVIEW_GIT_BLOB_SHA = "7963c55ce7b81115d9cc9fb74978f4abd60d63a8"
APPLICABILITY_GIT_BLOB_SHA = "c4c4b2aaf60684a6cded5e37edc0c8eb89141f67"
PUBLICATION_SPECS_GIT_BLOB_SHA = "b6c6b7a0650527e25a7b1ad23a7ab1b67bbb6ac1"
RAW_CARD_GIT_BLOB_SHA = "422103f5c4beacb99cf60fa750695f41ebbddbe8"

R2F_CONTRACT_ACCEPTED_BASE = "561c13aad6ce978de399dfd807071232af06b71c"
RAW_CARD_SHA256 = "77bc74917305adb0d4fee7a54910c9675068b1ec093a051f7c58bd34cc7dd27c"
RAW_CARD_SIZE_BYTES = 1783

CHEESE_SANDWICH_RECIPE_CODE = "SAD28_SANDWICH_CHEESE_20_10"
SOURCE_RECIPE_ID = "sad28-hosted:techcard:3:cheese-sandwich:20-10"
DISCOVERY_SOURCE_RECIPE_ID = "sad28-luppolovo:techcard:cheese-sandwich:20-10"

WHEAT_BREAD_PLAIN_FOOD_CODE = "WHEAT_BREAD_PLAIN"
CHEESE_UNSPECIFIED_FOOD_CODE = "CHEESE_UNSPECIFIED"
IDENTITY_ONLY_FOOD_CODES = (
    WHEAT_BREAD_PLAIN_FOOD_CODE,
    CHEESE_UNSPECIFIED_FOOD_CODE,
)
EXPECTED_MILK_UNAFFECTED_CODES = (
    "HARD_BOILED_EGG",
    "SCHOOL2022_54_1T_COTTAGE_CHEESE_CASSEROLE",
    CHEESE_SANDWICH_RECIPE_CODE,
)


@dataclass(frozen=True)
class R2FCheeseSandwichResult:
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
        raise ValueError(f"R2-F frozen artifact changed: {path.name}.")
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise TypeError(f"R2-F artifact must be a JSON object: {path.name}.")
    return payload


def _checked_raw_card(path: Path) -> bytes:
    raw = path.read_bytes()
    if _git_blob_sha(raw) != RAW_CARD_GIT_BLOB_SHA:
        raise ValueError("R2-F frozen artifact changed: raw-cheese-card.txt.")
    if len(raw) != RAW_CARD_SIZE_BYTES:
        raise ValueError("R2-F retained raw-card byte size changed.")
    if hashlib.sha256(raw).hexdigest() != RAW_CARD_SHA256:
        raise ValueError("R2-F retained raw-card SHA-256 changed.")
    return raw


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
    _checked_raw_card(package / RAW_CARD_PATH.name)

    selected = selection.get("selected")
    projected = selection.get("projected_after_future_runtime")
    if (
        selection.get("schema_version") != 1
        or selection.get("operation") != "R2F_SANDWICH_RESILIENCE_CANDIDATE_SELECTION"
        or selection.get("accepted_base") != R2F_CONTRACT_ACCEPTED_BASE
        or not isinstance(selected, list)
        or len(selected) != 1
        or selected[0].get("canonical_code") != CHEESE_SANDWICH_RECIPE_CODE
        or selected[0].get("source_recipe_id") != SOURCE_RECIPE_ID
        or selected[0].get("source_discovery_recipe_id") != DISCOVERY_SOURCE_RECIPE_ID
        or selected[0].get("meal_type_code") != "sandwich"
        or selected[0].get("source_output_g") != "30"
        or selected[0].get("prepared_energy_kcal") != "83"
        or not isinstance(projected, dict)
        or tuple(projected.get("milk_2_5_unaffected_breakfast_compatible_codes", ()))
        != EXPECTED_MILK_UNAFFECTED_CODES
        or projected.get("milk_2_5_unaffected_candidate_count") != 3
        or projected.get("max_recipe_repetitions") != 3
        or projected.get("milk_2_5_unaffected_capacity_per_week") != 9
        or projected.get("required_breakfast_opportunities") != 7
        or projected.get("closes_seven_breakfast_gap") is not True
        or projected.get("lunch_compatible_candidates_added") != 1
        or projected.get("snack_compatible_candidates_added") != 1
    ):
        raise ValueError("R2-F candidate-selection contract identity changed.")

    decisions = identity_review.get("decisions")
    new_identities = identity_review.get("new_identity_only_foods")
    rejected_identity = identity_review.get("rejected_identity_demand")
    if (
        identity_review.get("schema_version") != 1
        or identity_review.get("operation") != "R2F_SANDWICH_FOOD_IDENTITY_REVIEW"
        or identity_review.get("accepted_base") != R2F_CONTRACT_ACCEPTED_BASE
        or not isinstance(decisions, list)
        or not isinstance(new_identities, list)
        or not isinstance(rejected_identity, list)
    ):
        raise ValueError("R2-F FoodIngredient review identity changed.")

    created = tuple(
        row.get("canonical_code")
        for row in decisions
        if row.get("decision") == "CREATE_IDENTITY_ONLY"
    )
    if (
        created != IDENTITY_ONLY_FOOD_CODES
        or tuple(row.get("canonical_code") for row in new_identities)
        != IDENTITY_ONLY_FOOD_CODES
        or any(
            row.get("nutrition_profile") is not None
            or row.get("composition") is not None
            for row in new_identities
        )
        or tuple(
            row.get("canonical_code_that_would_have_been_created")
            for row in rejected_identity
        )
        != ("BUTTER_CREAM_UNSPECIFIED",)
    ):
        raise ValueError("R2-F FoodIngredient mapping decisions changed.")

    candidates = applicability.get("candidates")
    if (
        applicability.get("schema_version") != 1
        or applicability.get("operation") != "R2F_SANDWICH_HOUSEHOLD_APPLICABILITY"
        or applicability.get("accepted_base") != R2F_CONTRACT_ACCEPTED_BASE
        or not isinstance(candidates, list)
        or len(candidates) != 1
        or candidates[0].get("source_recipe_id") != SOURCE_RECIPE_ID
        or candidates[0].get("decision") != "HOUSEHOLD_APPLICABLE"
        or candidates[0].get("specialized_medical_scope") is not False
        or candidates[0].get("planner_classification") != "sandwich"
    ):
        raise ValueError("R2-F household-applicability contract identity changed.")

    source = specs.get("source")
    if (
        specs.get("schema_version") != 1
        or specs.get("operation")
        != "R2F_CHEESE_SANDWICH_RESILIENCE_PREPARED_PUBLICATION_SPECS"
        or specs.get("accepted_base") != R2F_CONTRACT_ACCEPTED_BASE
        or specs.get("authority_kind") != "PREPARED_OUTPUT_V1"
        or specs.get("recipe_calculation_version")
        != "RECIPE_PREPARED_OUTPUT_NUTRITION_V1"
        or not isinstance(source, dict)
        or source.get("publication_source_recipe_id") != SOURCE_RECIPE_ID
        or source.get("discovery_source_recipe_id") != DISCOVERY_SOURCE_RECIPE_ID
        or source.get("source_data_type") != "RETAINED_RAW_CARD_TEXT_SNAPSHOT"
        or source.get("retained_source_path")
        != "data/curation/r2f-sandwich-resilience/raw-cheese-card.txt"
        or source.get("retained_source_sha256") != RAW_CARD_SHA256
        or source.get("retained_source_size_bytes") != RAW_CARD_SIZE_BYTES
        or source.get("document_card_issuer", {}).get("status")
        != "NOT_ESTABLISHED_FROM_RETAINED_CARD"
        or source.get("raw_pdf_is_source_document") is not False
    ):
        raise ValueError("R2-F source authority contract identity changed.")

    nutrient_partition = specs.get("nutrient_partition")
    expected_unknown = tuple(code for code in NUTRIENT_CODES if code != "ENERGY_KCAL")
    if (
        not isinstance(nutrient_partition, dict)
        or nutrient_partition.get("frozen_code_count") != len(NUTRIENT_CODES)
        or nutrient_partition.get("available_codes") != ["ENERGY_KCAL"]
        or tuple(nutrient_partition.get("unknown_codes", ())) != expected_unknown
    ):
        raise ValueError("R2-F frozen nutrient partition changed.")

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
        raise ValueError("R2-F identity-only publication contract changed.")

    recipes = specs.get("recipes")
    if not isinstance(recipes, dict) or tuple(recipes) != (
        CHEESE_SANDWICH_RECIPE_CODE,
    ):
        raise ValueError("R2-F Recipe set changed.")

    recipe = recipes[CHEESE_SANDWICH_RECIPE_CODE]
    receipt = recipe.get("source_receipt")
    trusted_seed = recipe.get("trusted_recipe_seed")
    version = trusted_seed.get("version") if isinstance(trusted_seed, dict) else None
    prepared = recipe.get("prepared_spec")
    if (
        not isinstance(receipt, dict)
        or receipt.get("source_recipe_id") != SOURCE_RECIPE_ID
        or receipt.get("source_discovery_recipe_id") != DISCOVERY_SOURCE_RECIPE_ID
        or receipt.get("source_document_sha256") != RAW_CARD_SHA256
        or receipt.get("source_data_type") != "RETAINED_RAW_CARD_TEXT_SNAPSHOT"
        or not isinstance(trusted_seed, dict)
        or trusted_seed.get("canonical_code") != CHEESE_SANDWICH_RECIPE_CODE
        or trusted_seed.get("initial_is_active") is not False
        or not isinstance(version, dict)
        or version.get("source_recipe_id") != SOURCE_RECIPE_ID
        or version.get("meal_type_code") != "sandwich"
        or version.get("source_document_sha256") != RAW_CARD_SHA256
        or version.get("source_output_g") != "30"
        or tuple(
            (row.get("food_ingredient_code"), row.get("quantity"))
            for row in version.get("ingredients", ())
        )
        != (
            (WHEAT_BREAD_PLAIN_FOOD_CODE, "20"),
            (CHEESE_UNSPECIFIED_FOOD_CODE, "10"),
        )
        or not isinstance(prepared, dict)
        or prepared.get("recipe_code") != CHEESE_SANDWICH_RECIPE_CODE
        or prepared.get("source_recipe_id") != SOURCE_RECIPE_ID
        or prepared.get("source_document_sha256") != RAW_CARD_SHA256
        or prepared.get("output_mass_g") != "30"
        or prepared.get("expected_available_amounts") != [["ENERGY_KCAL", "83"]]
        or tuple(prepared.get("expected_unknown_codes", ())) != expected_unknown
        or prepared.get("require_recipe_inactive") is not True
    ):
        raise ValueError("R2-F frozen Recipe/prepared spec changed.")

    runtime_rules = specs.get("runtime_rules")
    if (
        not isinstance(runtime_rules, dict)
        or runtime_rules.get("migration_0043_allowed") is not False
        or runtime_rules.get("planner_change_allowed") is not False
        or runtime_rules.get("source_scaling_allowed") is not False
        or runtime_rules.get("new_nutrition_authority_allowed") is not False
        or runtime_rules.get("live_web_runtime_dependency_allowed") is not False
        or runtime_rules.get("implicit_food_identity_narrowing_allowed") is not False
        or runtime_rules.get("raw_pdf_is_runtime_source_document") is not False
        or runtime_rules.get("retained_runtime_source_sha256") != RAW_CARD_SHA256
    ):
        raise ValueError("R2-F runtime preservation rules changed.")

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
    payload = specs["recipes"][CHEESE_SANDWICH_RECIPE_CODE]["trusted_recipe_seed"]
    version = payload["version"]
    retrieved = version["source_retrieved_at"]
    return TrustedRecipeSeed(
        canonical_code=payload["canonical_code"],
        canonical_name=payload["canonical_name"],
        initial_is_active=payload["initial_is_active"],
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
    spec = specs["recipes"][CHEESE_SANDWICH_RECIPE_CODE]["prepared_spec"]
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
        raise RecipeNutritionV2ConflictError("Partial persisted R2-F state.")
    replay = nutrition.publish_prepared(spec)
    if replay.disposition is not PreparedPublicationDisposition.EXACT_REPLAY:
        raise RecipeNutritionV2ConflictError(
            "Expected exact R2-F prepared authority replay."
        )


def seed_r2f_cheese_sandwich(
    config: DatabaseConfig | None = None,
    *,
    package: Path = PACKAGE,
) -> R2FCheeseSandwichResult:
    _, _, _, specs_payload = _load_contract(package)

    apply_migrations(config)
    seed_r2e_cottage_casserole(config)

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
                        "Fresh R2-F Recipe did not publish fresh prepared authority."
                    )
                projection = nutrition.prepared_consumption_projection_in_scope(
                    uow, published.authority.recipe_version_id
                )
                if (
                    not projection.exact_energy_ready
                    or projection.per_base_serving.kcal is None
                ):
                    raise RecipeNutritionV2ConflictError(
                        "R2-F in-scope exact energy unavailable."
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
            raise RecipeNutritionV2ConflictError("R2-F exact energy unavailable.")

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
                    "R2-F active Planner admission failed."
                )
        elif admission.blockers != (PlannerAdmissionBlocker.INACTIVE,):
            raise RecipeNutritionV2ConflictError(
                "R2-F replay admission has unexpected blockers."
            )

        return R2FCheeseSandwichResult(
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
    result = seed_r2f_cheese_sandwich()
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
