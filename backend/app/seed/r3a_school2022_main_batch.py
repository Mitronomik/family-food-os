"""R3-A School2022 ten-recipe MAIN prepared-output publication batch."""

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
from app.seed.r2f_cheese_sandwich import seed_r2f_cheese_sandwich
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

PACKAGE = REPOSITORY_ROOT / "data/curation/r3a-school2022-main-batch"
SELECTION_PATH = PACKAGE / "candidate-selection.json"
IDENTITY_REVIEW_PATH = PACKAGE / "food-identity-review.json"
APPLICABILITY_PATH = PACKAGE / "household-applicability-review.json"
PROCESS_BINDING_PATH = PACKAGE / "process-binding-review.json"
PUBLICATION_SPECS_PATH = PACKAGE / "publication-specs.json"
SOURCE_VERIFICATION_PATH = PACKAGE / "source-verification.json"
SUMMARY_PATH = PACKAGE / "summary.json"

SELECTION_GIT_BLOB_SHA = "512968ee02a195bcf9e6f2e83c408419bc0b9a67"
IDENTITY_REVIEW_GIT_BLOB_SHA = "2def51f5b95a04d1263d132e201ef71ec1f2df7e"
APPLICABILITY_GIT_BLOB_SHA = "805417a908aee61dc5f128840868c2d0e8740aa2"
PROCESS_BINDING_GIT_BLOB_SHA = "579a56ca7acd8a8e84d35563af00e2993ad3a665"
PUBLICATION_SPECS_GIT_BLOB_SHA = "ab40c2b8c6a646a60d72922faea451225e875697"
SOURCE_VERIFICATION_GIT_BLOB_SHA = "5fc8a6b70bc685b1e6c0996fcb819c63b4df29a3"
SUMMARY_GIT_BLOB_SHA = "e4f8678f2ce3eadce5aa5f4767e2409992603b96"

R3A_RUNTIME_ACCEPTED_BASE = "e152b357528bb000cf5cf16e792a0d31b983f117"
R3A_GATE_ACCEPTED_BASE = "da6d1e05fd44ecc2733e1a6f472eae3e54b60604"
SOURCE_PDF_SHA256 = "c9264cf521ae699fb30a964d5668caec8f31ff1efc1f13a3dd055df40ebafb5d"
SOURCE_ARCHIVE_SHA256 = (
    "c0d90020798b2998e841328b9081f06f8197efda084b852aa8457fd41a5ce8ea"
)

RECIPE_CODES = (
    "SCHOOL2022_54_1R_COD_CUTLET",
    "SCHOOL2022_54_2R_PINK_SALMON_CUTLET",
    "SCHOOL2022_54_3R_POLLOCK_CUTLET",
    "SCHOOL2022_54_10R_PINK_SALMON_TOMATO_VEGETABLES",
    "SCHOOL2022_54_8M_STEAMED_BEEF_MEATBALLS",
    "SCHOOL2022_54_11M_BEEF_PILAF",
    "SCHOOL2022_54_4M_BEEF_CUTLET",
    "SCHOOL2022_54_11R_POLLOCK_TOMATO_VEGETABLES",
    "SCHOOL2022_54_6M_BEEF_BITOCHEK",
    "SCHOOL2022_54_7M_BEEF_SCHNITZEL",
)
SOURCE_RECIPE_IDS = (
    "ru-school2022:recipe:54-1р",
    "ru-school2022:recipe:54-2р",
    "ru-school2022:recipe:54-3р",
    "ru-school2022:recipe:54-10р",
    "ru-school2022:recipe:54-8м",
    "ru-school2022:recipe:54-11м",
    "ru-school2022:recipe:54-4м",
    "ru-school2022:recipe:54-11р",
    "ru-school2022:recipe:54-6м",
    "ru-school2022:recipe:54-7м",
)
IDENTITY_ONLY_FOOD_CODES = (
    "COD_FILLET_RAW",
    "PARSLEY_ROOT_RAW",
    "WHEAT_BREAD_STALE_UNSPECIFIED_GRADE",
)
EXCLUDED_SOURCE_RECIPE_IDS = (
    "ru-school2022:recipe:54-5м",
    "ru-school2022:recipe:54-9р",
    "ru-school2022:recipe:54-12м",
    "ru-school2022:recipe:54-15м",
    "ru-school2022:recipe:54-18м",
)


@dataclass(frozen=True)
class R3APublicationResult:
    identity_food_inserted: int
    identity_food_existing: int
    recipe_version_ids: tuple[tuple[str, UUID], ...]
    authority_dispositions: tuple[tuple[str, str], ...]
    exact_energy_kcal: tuple[tuple[str, Decimal], ...]


@dataclass(frozen=True)
class R3AMainBatchResult:
    publication: R3APublicationResult
    activation_changed: bool
    active_recipe_codes: tuple[str, ...]


def _git_blob_sha(raw: bytes) -> str:
    header = f"blob {len(raw)}\0".encode()
    return hashlib.sha1(header + raw).hexdigest()


def _checked_json(path: Path, expected_git_blob_sha: str) -> dict[str, Any]:
    raw = path.read_bytes()
    if _git_blob_sha(raw) != expected_git_blob_sha:
        raise ValueError(f"R3-A frozen artifact changed: {path.name}.")
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise TypeError(f"R3-A artifact must be a JSON object: {path.name}.")
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
        "selection": "R3A_SCHOOL2022_MAIN_BATCH_CANDIDATE_SELECTION",
        "identities": "R3A_SCHOOL2022_MAIN_BATCH_FOOD_IDENTITY_REVIEW",
        "applicability": "R3A_SCHOOL2022_MAIN_BATCH_HOUSEHOLD_APPLICABILITY",
        "process": "R3A_SCHOOL2022_PROCESS_BINDING_REVIEW",
        "specs": "R3A_SCHOOL2022_MAIN_BATCH_PUBLICATION_SPECS",
        "source": "R3A_SCHOOL2022_SOURCE_VERIFICATION",
        "summary": "R3A_SCHOOL2022_MAIN_BATCH_GATE_SUMMARY",
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
            or payload.get("accepted_base") != R3A_GATE_ACCEPTED_BASE
            or payload.get("issue") != 144
        ):
            raise ValueError(f"R3-A {name} contract identity changed.")

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
        raise ValueError("R3-A contract collections changed.")

    selected_codes = tuple(row.get("canonical_code") for row in selected)
    selected_source_ids = tuple(row.get("source_recipe_id") for row in selected)
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
        raise ValueError("R3-A selected Recipe set/order drifted.")

    if any(source_id in selected_source_ids for source_id in EXCLUDED_SOURCE_RECIPE_IDS):
        raise ValueError("R3-A excluded source card entered selected batch.")

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
        raise ValueError("R3-A identity-only FoodIngredient contract changed.")

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
        raise ValueError("R3-A prepared Nutrition contract changed.")

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
        raise ValueError("R3-A durable source receipt changed.")

    for code, source_id in zip(RECIPE_CODES, SOURCE_RECIPE_IDS, strict=True):
        recipe = recipes[code]
        trusted = recipe.get("trusted_recipe_seed")
        version = trusted.get("version") if isinstance(trusted, dict) else None
        prepared = recipe.get("prepared_spec")
        if (
            recipe.get("canonical_code") != code
            or recipe.get("initial_is_active") is not False
            or not isinstance(trusted, dict)
            or trusted.get("canonical_code") != code
            or trusted.get("initial_is_active") is not False
            or not isinstance(version, dict)
            or version.get("source_recipe_id") != source_id
            or version.get("meal_type_code") != "main"
            or version.get("source_document_sha256") != SOURCE_PDF_SHA256
            or not isinstance(prepared, dict)
            or prepared.get("recipe_code") != code
            or prepared.get("source_recipe_id") != source_id
            or prepared.get("source_document_sha256") != SOURCE_PDF_SHA256
            or prepared.get("expected_available_amounts", ())[:1]
            != [["ENERGY_KCAL", selection[RECIPE_CODES.index(code)]["prepared_energy_kcal"]]]
            or tuple(prepared.get("expected_unknown_codes", ())) != expected_unknown
            or prepared.get("require_recipe_inactive") is not True
        ):
            raise ValueError(f"R3-A frozen Recipe/prepared spec changed: {code}.")

    app_decisions = tuple(row.get("decision") for row in applicability_rows)
    if app_decisions != ("REVIEWED_PASS",) * len(RECIPE_CODES):
        raise ValueError("R3-A household-applicability decisions changed.")

    r8 = recipes["SCHOOL2022_54_8M_STEAMED_BEEF_MEATBALLS"]
    r8_steps = tuple(r8["trusted_recipe_seed"]["version"]["steps"])
    if (
        any("замоченным в воде" in step for step in r8_steps)
        or not any("не указывает жидкость" in step for step in r8_steps)
        or r8.get("process_binding_receipt", {}).get("water_binding")
        != "PARTIAL_SOURCE_PLACEMENT"
    ):
        raise ValueError("R3-A 54-8м source-process correction drifted.")

    r11 = recipes["SCHOOL2022_54_11M_BEEF_PILAF"]
    r11_steps = tuple(r11["trusted_recipe_seed"]["version"]["steps"])
    if (
        any("частью воды" in step for step in r11_steps)
        or not any("5–10 минут" in step for step in r11_steps)
        or not any("160 °C 30–40 минут" in step for step in r11_steps)
        or r11.get("process_binding_receipt", {}).get("water_binding")
        != "SOURCE_PLACED_TOTAL_UNSPLIT"
    ):
        raise ValueError("R3-A 54-11м source-process correction drifted.")

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
        or runtime_rules.get("batch_activation_requires_transaction_neutral_in_scope_seam")
        is not True
        or not isinstance(publication, dict)
        or publication.get("mode") != "PER_RECIPE_ATOMIC_UOW"
        or publication.get("activation_during_publication") is not False
        or not isinstance(activation, dict)
        or activation.get("mode") != "SEPARATE_EXPLICIT_BATCH_COMMAND_ONE_UOW"
        or activation.get("existing_single_recipe_commit_owning_guard_loop_allowed")
        is not False
        or activation.get("inner_commit_allowed") is not False
    ):
        raise ValueError("R3-A option-B transaction contract changed.")

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
            f"Partial persisted R3-A state for {seed.canonical_code}."
        )
    replay = nutrition.publish_prepared(spec)
    if replay.disposition is not PreparedPublicationDisposition.EXACT_REPLAY:
        raise RecipeNutritionV2ConflictError(
            f"Expected exact R3-A prepared replay for {seed.canonical_code}."
        )


def publish_r3a_school2022_main_batch(
    config: DatabaseConfig | None = None,
    *,
    package: Path = PACKAGE,
) -> R3APublicationResult:
    _, _, _, _, specs_payload, _, _ = _load_contract(package)

    apply_migrations(config)
    seed_r2f_cheese_sandwich(config)

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
                            f"Fresh R3-A authority was not fresh: {seed.canonical_code}."
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
                            f"R3-A in-scope exact energy unavailable: {seed.canonical_code}."
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
                    f"R3-A exact energy unavailable: {seed.canonical_code}."
                )
            dispositions.append((seed.canonical_code, published.disposition.value))
            version_ids.append((seed.canonical_code, detail.version.id))
            energies.append((seed.canonical_code, projection.per_base_serving.kcal))

        return R3APublicationResult(
            identity_food_inserted=identity_summary.ingredients_inserted,
            identity_food_existing=identity_summary.ingredients_existing,
            recipe_version_ids=tuple(version_ids),
            authority_dispositions=tuple(dispositions),
            exact_energy_kcal=tuple(energies),
        )
    finally:
        engine.dispose()


def activate_r3a_school2022_main_batch(
    config: DatabaseConfig | None = None,
    *,
    package: Path = PACKAGE,
) -> bool:
    _, _, _, _, specs_payload, _, _ = _load_contract(package)

    apply_migrations(config)
    seed_r2f_cheese_sandwich(config)

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
            raise AssertionError("R3-A activation version ordering drifted.")
        return result.activated
    finally:
        engine.dispose()


def seed_r3a_school2022_main_batch(
    config: DatabaseConfig | None = None,
    *,
    package: Path = PACKAGE,
) -> R3AMainBatchResult:
    publication = publish_r3a_school2022_main_batch(config, package=package)
    activation_changed = activate_r3a_school2022_main_batch(config, package=package)

    engine = create_sqlite_engine(config)
    try:
        catalogue = create_food_recipe_catalogue_service(engine)
        active_recipe_codes = tuple(
            code for code in RECIPE_CODES if catalogue.get_by_code(code).is_active
        )
        if active_recipe_codes != RECIPE_CODES:
            raise AssertionError("R3-A final active batch does not match frozen set.")
    finally:
        engine.dispose()

    return R3AMainBatchResult(
        publication=publication,
        activation_changed=activation_changed,
        active_recipe_codes=active_recipe_codes,
    )


if __name__ == "__main__":
    result = seed_r3a_school2022_main_batch()
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
