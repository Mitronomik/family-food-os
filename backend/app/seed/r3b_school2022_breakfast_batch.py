"""R3-B School2022 ten-recipe BREAKFAST prepared-output publication batch."""

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
from app.seed.r3a_school2022_main_batch import seed_r3b_school2022_breakfast_batch
from app.services.food_ingredients import TrustedFoodIngredientIdentitySeed
from app.services.food_recipes import (
    TrustedRecipeIngredientSeed,
    TrustedRecipeSeed,
    TrustedRecipeSeedDisposition,
    TrustedRecipeVersionSeed,
)
from app.services.planner import PlannerService
from app.services.prepared_recipe_activation import activate_prepared_recipe_batch
from app.services.recipe_nutrition_v2 import (
    PreparedPublicationDisposition,
    RecipeNutritionV2ConflictError,
    ReviewedPreparedRecipeNutritionSpec,
)

PACKAGE = REPOSITORY_ROOT / "data/curation/r3b-school2022-breakfast-batch"
SELECTION_PATH = PACKAGE / "candidate-selection.json"
IDENTITY_REVIEW_PATH = PACKAGE / "food-identity-review.json"
APPLICABILITY_PATH = PACKAGE / "household-applicability-review.json"
PROCESS_BINDING_PATH = PACKAGE / "process-binding-review.json"
PUBLICATION_SPECS_PATH = PACKAGE / "publication-specs.json"
SOURCE_VERIFICATION_PATH = PACKAGE / "source-verification.json"
SUMMARY_PATH = PACKAGE / "summary.json"

SELECTION_GIT_BLOB_SHA = "5e2d5fe06315857395e541e5c28ae1e862682cb3"
IDENTITY_REVIEW_GIT_BLOB_SHA = "5985436867a0acf7fb26a67871998709821755d4"
APPLICABILITY_GIT_BLOB_SHA = "c5cd486515ee3aecf459178e63efb4fa9c557246"
PROCESS_BINDING_GIT_BLOB_SHA = "70e92e3c710c941bd719b5bf570feb9cb4e8d86a"
PUBLICATION_SPECS_GIT_BLOB_SHA = "96d134265a8c256e34ad985670feed8ca56c295d"
SOURCE_VERIFICATION_GIT_BLOB_SHA = "55582e3aa9b4f985eee5f41d95d6de20e607fab3"
SUMMARY_GIT_BLOB_SHA = "48c8790f4f17176d06bc27462edae00a36d09e5e"

R3B_RUNTIME_ACCEPTED_BASE = "dcc5f37f57a83283e4dee0d3c2957ed0704e9a46"
R3B_GATE_ACCEPTED_BASE = "69c68f4153b25ac4e51cbe9ff54fb080201f08bd"
SOURCE_PDF_SHA256 = "c9264cf521ae699fb30a964d5668caec8f31ff1efc1f13a3dd055df40ebafb5d"
SOURCE_ARCHIVE_SHA256 = (
    "c0d90020798b2998e841328b9081f06f8197efda084b852aa8457fd41a5ce8ea"
)

RECIPE_CODES = (
    "SCHOOL2022_54_2O_GREEN_PEA_OMELET",
    "SCHOOL2022_54_3O_CARROT_OMELET",
    "SCHOOL2022_54_4O_SEMI_HARD_CHEESE_OMELET",
    "SCHOOL2022_54_2T_COTTAGE_CHEESE_CARROT_CASSEROLE",
    "SCHOOL2022_54_1K_LIQUID_CORN_MILK_PORRIDGE",
    "SCHOOL2022_54_2K_VISCOUS_CORN_MILK_PORRIDGE",
    "SCHOOL2022_54_6K_MILLET_MILK_PORRIDGE",
    "SCHOOL2022_54_16K_DRUZHBA_PORRIDGE",
    "SCHOOL2022_54_23K_LIQUID_WHEAT_MILK_PORRIDGE",
    "SCHOOL2022_54_24K_LIQUID_MILLET_MILK_PORRIDGE",
)
SOURCE_RECIPE_IDS = (
    "ru-school2022:recipe:54-2о",
    "ru-school2022:recipe:54-3о",
    "ru-school2022:recipe:54-4о",
    "ru-school2022:recipe:54-2т",
    "ru-school2022:recipe:54-1к",
    "ru-school2022:recipe:54-2к",
    "ru-school2022:recipe:54-6к",
    "ru-school2022:recipe:54-16к",
    "ru-school2022:recipe:54-23к",
    "ru-school2022:recipe:54-24к",
)
IDENTITY_ONLY_FOOD_CODES = (
    "CHEESE_SEMI_HARD_UNSPECIFIED",
    "CORN_GROATS",
    "MILLET_GROATS",
)
EXCLUDED_SOURCE_RECIPE_IDS = (
    "ru-school2022:recipe:54-3т",
    "ru-school2022:recipe:54-21к",
    "ru-school2022:recipe:54-22к",
    "ru-school2022:recipe:54-7т",
)
MILK_FOOD_CODE = "MILK_2_5"
MILK_UNAFFECTED_BREAKFAST_CODES = (
    "HARD_BOILED_EGG",
    "SCHOOL2022_54_1T_COTTAGE_CHEESE_CASSEROLE",
    "SAD28_SANDWICH_CHEESE_20_10",
)
OMELET_CODES = (
    "SCHOOL2022_54_2O_GREEN_PEA_OMELET",
    "SCHOOL2022_54_3O_CARROT_OMELET",
    "SCHOOL2022_54_4O_SEMI_HARD_CHEESE_OMELET",
)
OMELET_SELECTED_BRANCH = "OVEN_BAKE_180_200C_8_10_MIN"
OMELET_NON_SELECTED_BRANCH = "STEAM_25_30_MIN"

@dataclass(frozen=True)
class R3BPublicationResult:
    identity_food_inserted: int
    identity_food_existing: int
    recipe_version_ids: tuple[tuple[str, UUID], ...]
    authority_dispositions: tuple[tuple[str, str], ...]
    exact_energy_kcal: tuple[tuple[str, Decimal], ...]


@dataclass(frozen=True)
class R3BBreakfastBatchResult:
    publication: R3BPublicationResult
    activation_changed: bool
    active_recipe_codes: tuple[str, ...]


def _git_blob_sha(raw: bytes) -> str:
    header = f"blob {len(raw)}\0".encode()
    return hashlib.sha1(header + raw).hexdigest()


def _checked_json(path: Path, expected_git_blob_sha: str) -> dict[str, Any]:
    raw = path.read_bytes()
    if _git_blob_sha(raw) != expected_git_blob_sha:
        raise ValueError(f"R3-B frozen artifact changed: {path.name}.")
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise TypeError(f"R3-B artifact must be a JSON object: {path.name}.")
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
) -> tuple[
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
]:
    selection = _checked_json(package / SELECTION_PATH.name, SELECTION_GIT_BLOB_SHA)
    identities = _checked_json(
        package / IDENTITY_REVIEW_PATH.name,
        IDENTITY_REVIEW_GIT_BLOB_SHA,
    )
    applicability = _checked_json(
        package / APPLICABILITY_PATH.name,
        APPLICABILITY_GIT_BLOB_SHA,
    )
    process = _checked_json(
        package / PROCESS_BINDING_PATH.name,
        PROCESS_BINDING_GIT_BLOB_SHA,
    )
    specs = _checked_json(
        package / PUBLICATION_SPECS_PATH.name,
        PUBLICATION_SPECS_GIT_BLOB_SHA,
    )
    source = _checked_json(
        package / SOURCE_VERIFICATION_PATH.name,
        SOURCE_VERIFICATION_GIT_BLOB_SHA,
    )
    summary = _checked_json(package / SUMMARY_PATH.name, SUMMARY_GIT_BLOB_SHA)

    expected_operations = {
        "selection": "R3B_SCHOOL2022_BREAKFAST_BATCH_CANDIDATE_SELECTION",
        "identities": "R3B_SCHOOL2022_BREAKFAST_BATCH_FOOD_IDENTITY_REVIEW",
        "applicability": "R3B_SCHOOL2022_BREAKFAST_BATCH_HOUSEHOLD_APPLICABILITY",
        "process": "R3B_SCHOOL2022_BREAKFAST_BATCH_PROCESS_BINDING_REVIEW",
        "specs": "R3B_SCHOOL2022_BREAKFAST_BATCH_PUBLICATION_SPECS",
        "source": "R3B_SCHOOL2022_BREAKFAST_BATCH_SOURCE_VERIFICATION",
        "summary": "R3B_SCHOOL2022_BREAKFAST_BATCH_GATE_SUMMARY",
    }
    payloads = {
        "selection": selection,
        "identities": identities,
        "applicability": applicability,
        "process": process,
        "specs": specs,
        "source": source,
        "summary": summary,
    }
    for name, payload in payloads.items():
        if (
            payload.get("schema_version") != 1
            or payload.get("operation") != expected_operations[name]
            or payload.get("accepted_base") != R3B_GATE_ACCEPTED_BASE
            or payload.get("issue") != 149
        ):
            raise ValueError(f"R3-B {name} contract identity changed.")

    selected = selection.get("selected")
    recipes = specs.get("recipes")
    applicability_rows = applicability.get("candidates")
    process_rows = process.get("selected")
    source_pages = source.get("selected_pages")
    if (
        not isinstance(selected, list)
        or not isinstance(recipes, dict)
        or not isinstance(applicability_rows, list)
        or not isinstance(process_rows, list)
        or not isinstance(source_pages, list)
    ):
        raise TypeError("R3-B contract collections changed.")

    selected_codes = tuple(row.get("canonical_code") for row in selected)
    selected_source_ids = tuple(row.get("source_recipe_id") for row in selected)
    selected_by_code = {row.get("canonical_code"): row for row in selected}
    recipe_source_ids = tuple(
        recipes[code].get("source_receipt", {}).get("source_recipe_id")
        for code in RECIPE_CODES
    )
    if (
        selected_codes != RECIPE_CODES
        or selected_source_ids != SOURCE_RECIPE_IDS
        or tuple(recipes) != RECIPE_CODES
        or recipe_source_ids != SOURCE_RECIPE_IDS
        or tuple(row.get("source_recipe_id") for row in applicability_rows)
        != SOURCE_RECIPE_IDS
        or tuple(row.get("source_recipe_id") for row in process_rows)
        != SOURCE_RECIPE_IDS
        or tuple(row.get("source_recipe_id") for row in source_pages)
        != SOURCE_RECIPE_IDS
        or summary.get("selected_count") != 10
        or tuple(summary.get("selected_recipe_codes", ())) != RECIPE_CODES
    ):
        raise ValueError("R3-B selected Recipe set/order drifted.")

    if any(
        source_id in selected_source_ids for source_id in EXCLUDED_SOURCE_RECIPE_IDS
    ):
        raise ValueError("R3-B excluded source card entered selected batch.")

    identity_rows = identities.get("new_identity_only_foods")
    spec_identity_rows = specs.get("new_identity_only_foods")
    if (
        not isinstance(identity_rows, list)
        or not isinstance(spec_identity_rows, list)
        or tuple(row.get("canonical_code") for row in identity_rows)
        != IDENTITY_ONLY_FOOD_CODES
        or tuple(row.get("canonical_code") for row in spec_identity_rows)
        != IDENTITY_ONLY_FOOD_CODES
        or tuple(summary.get("new_identity_only_foods", ()))
        != IDENTITY_ONLY_FOOD_CODES
        or any(
            row.get("nutrition_profile") is not None
            or row.get("composition") is not None
            for row in spec_identity_rows
        )
    ):
        raise ValueError("R3-B identity-only FoodIngredient contract changed.")

    expected_unknown = tuple(code for code in NUTRIENT_CODES if code != "ENERGY_KCAL")
    nutrient_partition = specs.get("nutrient_partition")
    if (
        specs.get("authority_kind") != "PREPARED_OUTPUT_V1"
        or specs.get("recipe_calculation_version")
        != "RECIPE_PREPARED_OUTPUT_NUTRITION_V1"
        or not isinstance(nutrient_partition, dict)
        or nutrient_partition.get("frozen_code_count") != len(NUTRIENT_CODES)
        or nutrient_partition.get("available_codes") != ["ENERGY_KCAL"]
        or tuple(nutrient_partition.get("unknown_codes", ())) != expected_unknown
    ):
        raise ValueError("R3-B prepared Nutrition contract changed.")

    spec_source = specs.get("source")
    durable_source = source.get("durable_source")
    if (
        not isinstance(spec_source, dict)
        or not isinstance(durable_source, dict)
        or spec_source.get("source_document_sha256") != SOURCE_PDF_SHA256
        or spec_source.get("source_archive_sha256") != SOURCE_ARCHIVE_SHA256
        or durable_source.get("source_pdf_sha256") != SOURCE_PDF_SHA256
        or durable_source.get("archive_sha256") != SOURCE_ARCHIVE_SHA256
        or summary.get("source_pdf_sha256") != SOURCE_PDF_SHA256
        or summary.get("source_archive_sha256") != SOURCE_ARCHIVE_SHA256
    ):
        raise ValueError("R3-B durable source receipt changed.")

    forbidden_consumer_terms = (
        "authority",
        "retained-water",
        "yield inference",
        "quantified RecipeIngredient",
        "exact WATER",
    )
    for code, source_id in zip(RECIPE_CODES, SOURCE_RECIPE_IDS, strict=True):
        recipe = recipes[code]
        trusted = recipe.get("trusted_recipe_seed")
        version = trusted.get("version") if isinstance(trusted, dict) else None
        prepared = recipe.get("prepared_spec")
        steps = tuple(version.get("steps", ())) if isinstance(version, dict) else ()
        ingredients = (
            tuple(version.get("ingredients", ())) if isinstance(version, dict) else ()
        )
        if (
            recipe.get("canonical_code") != code
            or recipe.get("initial_is_active") is not False
            or not isinstance(trusted, dict)
            or trusted.get("canonical_code") != code
            or trusted.get("initial_is_active") is not False
            or not isinstance(version, dict)
            or version.get("source_recipe_id") != source_id
            or version.get("meal_type_code") != "breakfast"
            or version.get("source_document_sha256") != SOURCE_PDF_SHA256
            or any(term in step for step in steps for term in forbidden_consumer_terms)
            or not isinstance(prepared, dict)
            or prepared.get("recipe_code") != code
            or prepared.get("source_recipe_id") != source_id
            or prepared.get("source_document_sha256") != SOURCE_PDF_SHA256
            or prepared.get("expected_available_amounts")
            != [["ENERGY_KCAL", selected_by_code[code]["prepared_energy_kcal"]]]
            or tuple(prepared.get("expected_unknown_codes", ())) != expected_unknown
            or prepared.get("require_recipe_inactive") is not True
            or not any(
                row.get("food_ingredient_code") == MILK_FOOD_CODE
                for row in ingredients
            )
        ):
            raise ValueError(f"R3-B frozen Recipe/prepared spec changed: {code}.")

    if tuple(row.get("decision") for row in applicability_rows) != (
        "REVIEWED_PASS",
    ) * len(RECIPE_CODES):
        raise ValueError("R3-B household-applicability decisions changed.")

    applicability_by_code = {
        row.get("canonical_code"): row for row in applicability_rows
    }
    process_by_code = {row.get("canonical_code"): row for row in process_rows}
    for code in OMELET_CODES:
        recipe = recipes[code]
        published_branch = recipe.get("source_branch_selection")
        receipt_branch = recipe.get("process_binding_receipt", {}).get(
            "source_branch_selection"
        )
        household_branch = applicability_by_code[code].get(
            "selected_process_branch"
        )
        process_branch = process_by_code[code]
        if (
            not isinstance(published_branch, dict)
            or published_branch.get("selected_process_branch")
            != OMELET_SELECTED_BRANCH
            or published_branch.get("non_selected_source_branches", [{}])[0].get(
                "code"
            )
            != OMELET_NON_SELECTED_BRANCH
            or not isinstance(receipt_branch, dict)
            or receipt_branch.get("selected_process_branch")
            != OMELET_SELECTED_BRANCH
            or not isinstance(household_branch, dict)
            or household_branch.get("code") != OMELET_SELECTED_BRANCH
            or process_branch.get("selected_process_branch")
            != OMELET_SELECTED_BRANCH
            or process_branch.get("non_selected_source_branch", {}).get("code")
            != OMELET_NON_SELECTED_BRANCH
        ):
            raise ValueError(f"R3-B omelet source branch drifted: {code}.")

    runtime_rules = specs.get("runtime_rules")
    activation = specs.get("batch_transaction_semantics", {}).get("activation")
    publication = specs.get("batch_transaction_semantics", {}).get("publication")
    if (
        not isinstance(runtime_rules, dict)
        or runtime_rules.get("migration_0043_allowed") is not False
        or runtime_rules.get("planner_change_allowed") is not False
        or runtime_rules.get("new_nutrition_authority_allowed") is not False
        or runtime_rules.get("partial_inactive_batch_publication_allowed") is not True
        or runtime_rules.get("batch_activation_atomic") is not True
        or runtime_rules.get("reuse_merged_r3a_batch_activation_seam") is not True
        or runtime_rules.get("hard_milk_exclusion_acceptance_required") is not True
        or runtime_rules.get("hard_milk_exclusion_food_code") != MILK_FOOD_CODE
        or not isinstance(publication, dict)
        or publication.get("mode") != "PER_RECIPE_ATOMIC_UOW"
        or publication.get("activation_during_publication") is not False
        or not isinstance(activation, dict)
        or activation.get("mode") != "SEPARATE_EXPLICIT_BATCH_COMMAND_ONE_UOW"
        or activation.get("new_activation_architecture_allowed") is not False
    ):
        raise ValueError("R3-B option-B transaction contract changed.")

    acceptance = summary.get("future_runtime_acceptance")
    projected = selection.get("projected_effect")
    if (
        not isinstance(acceptance, dict)
        or acceptance.get("hard_milk_exclusion_food_code") != MILK_FOOD_CODE
        or acceptance.get("r3b_candidate_count_rejected") != len(RECIPE_CODES)
        or tuple(acceptance.get("unaffected_breakfast_compatible_codes", ()))
        != MILK_UNAFFECTED_BREAKFAST_CODES
        or acceptance.get("unaffected_candidate_count") != 3
        or acceptance.get("max_recipe_repetitions") != 3
        or acceptance.get("unaffected_capacity_per_week") != 9
        or acceptance.get("seven_breakfast_authoritative_generation_must_succeed")
        is not True
        or acceptance.get("no_r3b_recipe_may_enter_excluded_plan") is not True
        or not isinstance(projected, dict)
        or projected.get("milk_2_5_dependency_count") != len(RECIPE_CODES)
        or projected.get("hard_milk_exclusion_new_candidates_rejected")
        != len(RECIPE_CODES)
        or tuple(projected.get("milk_2_5_unaffected_breakfast_compatible_codes", ()))
        != MILK_UNAFFECTED_BREAKFAST_CODES
        or projected.get("milk_2_5_unaffected_capacity_per_week") != 9
    ):
        raise ValueError("R3-B hard MILK_2_5 acceptance contract changed.")

    return (
        selection,
        identities,
        applicability,
        process,
        specs,
        source,
        summary,
    )


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


def _recipe_seed(payload: dict[str, Any]) -> TrustedRecipeSeed:
    seed = payload["trusted_recipe_seed"]
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
                version["source_output_g"],
                field="source_output_g",
            ),
            source_output_text=version["source_output_text"],
        ),
    )


def _prepared_spec(
    payload: dict[str, Any],
    seed: TrustedRecipeSeed,
) -> ReviewedPreparedRecipeNutritionSpec:
    spec = payload["prepared_spec"]
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


def _recipe_seeds_and_specs(
    specs: dict[str, Any],
) -> tuple[
    tuple[TrustedRecipeSeed, ...],
    tuple[ReviewedPreparedRecipeNutritionSpec, ...],
]:
    seeds = tuple(_recipe_seed(specs["recipes"][code]) for code in RECIPE_CODES)
    reviewed = tuple(
        _prepared_spec(specs["recipes"][code], seed)
        for code, seed in zip(RECIPE_CODES, seeds, strict=True)
    )
    return seeds, reviewed


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
        raise RecipeNutritionV2ConflictError(
            f"Partial persisted R3-B state for {seed.canonical_code}."
        )
    replay = nutrition.publish_prepared(spec)
    if replay.disposition is not PreparedPublicationDisposition.EXACT_REPLAY:
        raise RecipeNutritionV2ConflictError(
            f"Expected exact R3-B prepared replay for {seed.canonical_code}."
        )


def publish_r3b_school2022_breakfast_batch(
    config: DatabaseConfig | None = None,
    *,
    package: Path = PACKAGE,
) -> R3BPublicationResult:
    _, _, _, _, specs_payload, _, _ = _load_contract(package)

    apply_migrations(config)
    seed_r3a_school2022_main_batch(config)

    engine = create_sqlite_engine(config)
    try:
        food = create_food_catalogue_service(engine)
        identity_summary = food.reconcile_identity_seed(_identity_seeds(specs_payload))
        catalogue = create_food_recipe_catalogue_service(engine)
        nutrition = create_recipe_nutrition_v2_service(engine)
        seeds, specs = _recipe_seeds_and_specs(specs_payload)

        for seed, spec in zip(seeds, specs, strict=True):
            _assert_replay_not_partial(engine, catalogue, nutrition, seed, spec)

        dispositions: list[tuple[str, str]] = []
        version_ids: list[tuple[str, UUID]] = []
        energies: list[tuple[str, Decimal]] = []

        for seed, spec in zip(seeds, specs, strict=True):
            fresh = (
                catalogue.preflight_trusted_seed(seed)
                is TrustedRecipeSeedDisposition.FRESH
            )
            if fresh:
                with SqlAlchemyRecipeNutritionV2UnitOfWork(engine) as uow:
                    catalogue.reconcile_seed_in_scope(uow, (seed,))
                    published = nutrition.publish_prepared_in_scope(uow, spec)
                    if (
                        published.disposition
                        is not PreparedPublicationDisposition.FRESH
                    ):
                        raise RecipeNutritionV2ConflictError(
                            f"Fresh R3-B authority was not fresh: {seed.canonical_code}."
                        )
                    projection = nutrition.prepared_consumption_projection_in_scope(
                        uow,
                        published.authority.recipe_version_id,
                    )
                    if (
                        not projection.exact_energy_ready
                        or projection.per_base_serving.kcal is None
                    ):
                        raise RecipeNutritionV2ConflictError(
                            f"R3-B in-scope exact energy unavailable: {seed.canonical_code}."
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
                raise RecipeNutritionV2ConflictError(
                    f"R3-B exact energy unavailable: {seed.canonical_code}."
                )
            dispositions.append((seed.canonical_code, published.disposition.value))
            version_ids.append((seed.canonical_code, detail.version.id))
            energies.append((seed.canonical_code, projection.per_base_serving.kcal))

        return R3BPublicationResult(
            identity_food_inserted=identity_summary.ingredients_inserted,
            identity_food_existing=identity_summary.ingredients_existing,
            recipe_version_ids=tuple(version_ids),
            authority_dispositions=tuple(dispositions),
            exact_energy_kcal=tuple(energies),
        )
    finally:
        engine.dispose()


def activate_r3b_school2022_breakfast_batch(
    config: DatabaseConfig | None = None,
    *,
    package: Path = PACKAGE,
) -> bool:
    _, _, _, _, specs_payload, _, _ = _load_contract(package)

    apply_migrations(config)
    seed_r3a_school2022_main_batch(config)

    engine = create_sqlite_engine(config)
    try:
        catalogue = create_food_recipe_catalogue_service(engine)
        nutrition = create_recipe_nutrition_v2_service(engine)
        seeds, specs = _recipe_seeds_and_specs(specs_payload)

        planner = PlannerService(
            None,
            None,
            catalogue,
            None,
            None,
            recipe_nutrition=nutrition,  # type: ignore[arg-type]
        )
        result = activate_prepared_recipe_batch(
            catalogue=catalogue,
            nutrition=nutrition,
            planner=planner,
            specs=specs,
        )
        if result.recipe_version_ids != tuple(
            catalogue.get_latest_verified(
                catalogue.get_by_code(seed.canonical_code).id
            ).version.id
            for seed in seeds
        ):
            raise AssertionError("R3-B activation version ordering drifted.")
        return result.activated
    finally:
        engine.dispose()


def seed_r3b_school2022_breakfast_batch(
    config: DatabaseConfig | None = None,
    *,
    package: Path = PACKAGE,
) -> R3BBreakfastBatchResult:
    publication = publish_r3b_school2022_breakfast_batch(config, package=package)
    activation_changed = activate_r3b_school2022_breakfast_batch(config, package=package)

    engine = create_sqlite_engine(config)
    try:
        catalogue = create_food_recipe_catalogue_service(engine)
        active_recipe_codes = tuple(
            code for code in RECIPE_CODES if catalogue.get_by_code(code).is_active
        )
        if active_recipe_codes != RECIPE_CODES:
            raise AssertionError("R3-B final active batch does not match frozen set.")
    finally:
        engine.dispose()

    return R3BBreakfastBatchResult(
        publication=publication,
        activation_changed=activation_changed,
        active_recipe_codes=active_recipe_codes,
    )


if __name__ == "__main__":
    result = seed_r3b_school2022_breakfast_batch()
    print(
        json.dumps(
            {
                "identity_food_inserted": result.publication.identity_food_inserted,
                "identity_food_existing": result.publication.identity_food_existing,
                "recipe_version_ids": [
                    [code, str(version_id)]
                    for code, version_id in result.publication.recipe_version_ids
                ],
                "authority_dispositions": list(
                    result.publication.authority_dispositions
                ),
                "active_recipe_codes": list(result.active_recipe_codes),
                "activation_changed": result.activation_changed,
                "exact_energy_kcal": [
                    [code, format(value, "f")]
                    for code, value in result.publication.exact_energy_kcal
                ],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
