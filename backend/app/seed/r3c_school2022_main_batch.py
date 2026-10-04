"""R3-C frozen eight-recipe MAIN prepared-output publication batch."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
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
from app.seed.r3a_school2022_main_batch import (
    RECIPE_CODES as R3A_RECIPE_CODES,
)
from app.seed.r3a_school2022_main_batch import seed_r3a_school2022_main_batch
from app.seed.r3b_school2022_breakfast_batch import (
    RECIPE_CODES as R3B_RECIPE_CODES,
)
from app.seed.r3b_school2022_breakfast_batch import seed_r3b_school2022_breakfast_batch
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

PACKAGE = REPOSITORY_ROOT / "data/curation/r3c-post-r3b-catalogue-gate"
FROZEN_BATCH_PATH = PACKAGE / "frozen-batch.json"
SUMMARY_PATH = PACKAGE / "summary.json"

FROZEN_BATCH_GIT_BLOB_SHA = "c11fd55695c655fee5add14a3416a27527771e75"
SUMMARY_GIT_BLOB_SHA = "0564579c6c8ffeba18e19814e08d6e44918d9f86"

R3C_RUNTIME_ACCEPTED_BASE = "3c5740b319e453715c5a58f5b65e6d216b7c4fdb"
R3C_GATE_ACCEPTED_BASE = "90c4f0ebab693b01ec5b4cf7b93b67feeaf0ddb4"
SOURCE_PDF_SHA256 = "c9264cf521ae699fb30a964d5668caec8f31ff1efc1f13a3dd055df40ebafb5d"
SOURCE_ARCHIVE_SHA256 = (
    "c0d90020798b2998e841328b9081f06f8197efda084b852aa8457fd41a5ce8ea"
)

RECIPE_CODES = (
    "SCHOOL2022_54_21M_BOILED_CHICKEN",
    "SCHOOL2022_54_3M_LAZY_CABBAGE_ROLLS",
    "SCHOOL2022_54_26M_POTATO_BEEF_CASSEROLE",
    "SCHOOL2022_54_1M_BOILED_BEEF_STROGANOFF",
    "SCHOOL2022_54_30M_BEEF_RICE_QUENELLES",
    "SCHOOL2022_54_20M_BOILED_BEEF",
    "SCHOOL2022_54_15R_SALMON_IN_MILK",
    "SCHOOL2022_54_17R_SALMON_TOMATO_VEGETABLES",
)
SOURCE_RECIPE_IDS = (
    "ru-school2022:recipe:54-21м",
    "ru-school2022:recipe:54-3м",
    "ru-school2022:recipe:54-26м",
    "ru-school2022:recipe:54-1м",
    "ru-school2022:recipe:54-30м",
    "ru-school2022:recipe:54-20м",
    "ru-school2022:recipe:54-15р",
    "ru-school2022:recipe:54-17р",
)
IDENTITY_ONLY_FOOD_CODES = ("ATLANTIC_SALMON_FILLET_RAW",)
STEAM_ONLY_RECIPE_CODE = "SCHOOL2022_54_30M_BEEF_RICE_QUENELLES"
MILK_FOOD_CODE = "MILK_2_5"
BEEF_FOOD_CODE = "BEEF_CATEGORY_1_RAW"
MILK_UNAFFECTED_BREAKFAST_CODES = (
    "HARD_BOILED_EGG",
    "SCHOOL2022_54_1T_COTTAGE_CHEESE_CASSEROLE",
    "SAD28_SANDWICH_CHEESE_20_10",
)

_ASCII_WORD_RE = re.compile(r"[A-Za-z]{2,}")


@dataclass(frozen=True)
class R3CPublicationResult:
    identity_food_inserted: int
    identity_food_existing: int
    recipe_version_ids: tuple[tuple[str, UUID], ...]
    authority_dispositions: tuple[tuple[str, str], ...]
    exact_energy_kcal: tuple[tuple[str, Decimal], ...]


@dataclass(frozen=True)
class R3CMainBatchResult:
    publication: R3CPublicationResult
    activation_changed: bool
    active_recipe_codes: tuple[str, ...]


def _git_blob_sha(raw: bytes) -> str:
    header = f"blob {len(raw)}\0".encode()
    return hashlib.sha1(header + raw).hexdigest()


def _checked_json(path: Path, expected_git_blob_sha: str) -> dict[str, Any]:
    raw = path.read_bytes()
    if _git_blob_sha(raw) != expected_git_blob_sha:
        raise ValueError(f"R3-C frozen artifact changed: {path.name}.")
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise TypeError(f"R3-C artifact must be a JSON object: {path.name}.")
    return payload


def _decimal(value: object, *, field: str) -> Decimal:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field} must be a canonical Decimal string.")
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field} is not Decimal.") from exc
    if not parsed.is_finite() or parsed <= 0 or format(parsed, "f") != value:
        raise ValueError(f"{field} must be a canonical positive Decimal.")
    return parsed


def _load_contract(
    package: Path = PACKAGE,
) -> tuple[dict[str, Any], dict[str, Any]]:
    frozen = _checked_json(
        package / FROZEN_BATCH_PATH.name,
        FROZEN_BATCH_GIT_BLOB_SHA,
    )
    summary = _checked_json(package / SUMMARY_PATH.name, SUMMARY_GIT_BLOB_SHA)

    if (
        frozen.get("schema_version") != 1
        or frozen.get("operation") != "R3C_POST_R3B_FROZEN_BATCH_CONTRACT"
        or frozen.get("accepted_base") != R3C_GATE_ACCEPTED_BASE
        or frozen.get("issue") != 153
        or frozen.get("status") != "FROZEN_FOR_GATE_REVIEW"
        or summary.get("schema_version") != 1
        or summary.get("operation") != "R3C_POST_R3B_CATALOGUE_GATE_SUMMARY"
        or summary.get("accepted_base") != R3C_GATE_ACCEPTED_BASE
        or summary.get("issue") != 153
    ):
        raise ValueError("R3-C contract identity changed.")

    source = frozen.get("source")
    selected = frozen.get("selected")
    identities = frozen.get("new_identity_only_foods")
    deferred = frozen.get("deferred_or_rejected")
    if (
        not isinstance(source, dict)
        or not isinstance(selected, list)
        or not isinstance(identities, list)
        or not isinstance(deferred, list)
    ):
        raise TypeError("R3-C contract collections changed.")

    selected_codes = tuple(row.get("canonical_code") for row in selected)
    selected_source_ids = tuple(row.get("source_recipe_id") for row in selected)
    if (
        selected_codes != RECIPE_CODES
        or selected_source_ids != SOURCE_RECIPE_IDS
        or len(set(selected_codes)) != len(RECIPE_CODES)
        or len(set(selected_source_ids)) != len(SOURCE_RECIPE_IDS)
        or summary.get("r3c", {}).get("selected_count") != len(RECIPE_CODES)
        or tuple(summary.get("r3c", {}).get("selected_recipe_codes", ()))
        != RECIPE_CODES
    ):
        raise ValueError("R3-C selected Recipe set/order drifted.")

    deferred_ids = {row.get("source_recipe_id") for row in deferred}
    if deferred_ids & set(SOURCE_RECIPE_IDS):
        raise ValueError("R3-C selected/deferred source sets overlap.")

    if (
        len(identities) != 1
        or identities[0].get("canonical_code") != IDENTITY_ONLY_FOOD_CODES[0]
        or identities[0].get("nutrition_profile") is not None
        or identities[0].get("composition_authority") is not None
        or summary.get("r3c", {}).get("new_identity_only_foods")
        != list(IDENTITY_ONLY_FOOD_CODES)
    ):
        raise ValueError("R3-C identity-only FoodIngredient contract changed.")

    if (
        source.get("source_name") != "ru-school2022"
        or source.get("source_pdf_sha256") != SOURCE_PDF_SHA256
        or source.get("source_archive_sha256") != SOURCE_ARCHIVE_SHA256
        or source.get("rights_review_status") != "REVIEWED"
        or not isinstance(source.get("rights_basis"), str)
        or not source.get("rights_basis")
        or not isinstance(source.get("source_pdf_locator"), str)
        or not source.get("source_pdf_locator")
    ):
        raise ValueError("R3-C source/provenance contract changed.")

    expected_unknown = tuple(code for code in NUTRIENT_CODES if code != "ENERGY_KCAL")
    for row, code, source_id in zip(
        selected,
        RECIPE_CODES,
        SOURCE_RECIPE_IDS,
        strict=True,
    ):
        prepared = row.get("prepared_authority")
        ingredients = row.get("ingredients")
        steps = row.get("consumer_steps_ru")
        process = row.get("process_binding")
        if (
            row.get("canonical_code") != code
            or row.get("source_recipe_id") != source_id
            or row.get("meal_type_code") != "main"
            or row.get("household_applicability") != "REVIEWED_PASS"
            or not isinstance(process, dict)
            or not str(process.get("status", "")).startswith("PASS_")
            or not isinstance(ingredients, list)
            or not ingredients
            or not isinstance(steps, list)
            or not steps
            or any(
                not isinstance(step, str)
                or not step.strip()
                or _ASCII_WORD_RE.search(step) is not None
                for step in steps
            )
            or not isinstance(prepared, dict)
            or prepared.get("authority_kind") != "PREPARED_OUTPUT_V1"
            or prepared.get("calculation_version")
            != "RECIPE_PREPARED_OUTPUT_NUTRITION_V1"
            or prepared.get("available") != {"ENERGY_KCAL": row.get("energy_kcal")}
            or prepared.get("unknown_policy")
            != "all other frozen nutrient codes UNKNOWN"
        ):
            raise ValueError(f"R3-C frozen Recipe contract changed: {code}.")

        _decimal(row.get("source_output_g"), field=f"{code}.source_output_g")
        _decimal(row.get("energy_kcal"), field=f"{code}.energy_kcal")
        for ingredient in ingredients:
            if (
                not isinstance(ingredient, dict)
                or not isinstance(ingredient.get("source_label"), str)
                or not ingredient.get("source_label")
                or not isinstance(ingredient.get("food_code"), str)
                or not ingredient.get("food_code")
            ):
                raise ValueError(f"R3-C ingredient mapping changed: {code}.")
            _decimal(ingredient.get("gross_g"), field=f"{code}.ingredient.gross_g")
            _decimal(ingredient.get("net_g"), field=f"{code}.ingredient.net_g")

        if tuple(prepared) != (
            "authority_kind",
            "calculation_version",
            "available",
            "unknown_policy",
        ):
            raise ValueError(f"R3-C prepared authority shape changed: {code}.")

        if tuple(expected_unknown) != tuple(
            code for code in NUTRIENT_CODES if code != "ENERGY_KCAL"
        ):
            raise AssertionError("R3-C nutrient registry changed during validation.")

    steam = next(
        row for row in selected if row.get("canonical_code") == STEAM_ONLY_RECIPE_CODE
    )
    steam_steps = tuple(steam["consumer_steps_ru"])
    if (
        not any("на пару 15–20 минут" in step for step in steam_steps)
        or any("10–12" in step and "вод" in step.casefold() for step in steam_steps)
        or "SELECTED_STEAM_BRANCH" not in steam["process_binding"]["status"]
    ):
        raise ValueError("R3-C 54-30м selected steam branch changed.")

    current = summary.get("current_repository_truth")
    projected = summary.get("projected_after_future_runtime")
    milk = summary.get("hard_exclusion_resilience", {}).get("MILK_2_5")
    beef = summary.get("hard_exclusion_resilience", {}).get(
        "main_dependency_analysis"
    )
    if (
        not isinstance(current, dict)
        or current.get("dc3_active_exact_energy_count") != 33
        or current.get("active_exact_energy_by_meal_type")
        != {"breakfast": 17, "main": 15, "sandwich": 1}
        or current.get("breakfast_compatible_count") != 18
        or not isinstance(milk, dict)
        or tuple(milk.get("unaffected_breakfast_compatible_codes", ()))
        != MILK_UNAFFECTED_BREAKFAST_CODES
        or milk.get("unaffected_count") != 3
        or milk.get("capacity") != 9
        or not isinstance(beef, dict)
        or beef.get("BEEF_CATEGORY_1_RAW_current_count") != 7
        or beef.get("unaffected_after_exact_beef_exclusion") != 8
        or beef.get("capacity_after_exact_beef_exclusion") != 24
        or not isinstance(projected, dict)
        or projected.get("active_exact_energy_count") != 41
        or projected.get("active_exact_energy_by_meal_type")
        != {"breakfast": 17, "main": 23, "sandwich": 1}
        or projected.get("gap_to_50_usable") != 9
        or projected.get("dc4_ready_after") is not False
    ):
        raise ValueError("R3-C catalogue projection/exclusion contract changed.")

    transaction = frozen.get("transaction_contract")
    if (
        not isinstance(transaction, dict)
        or transaction.get("architecture")
        != "reuse merged R3-A/R3-B option B; no new activation architecture"
        or transaction.get("publication")
        != [
            "per-recipe atomic inactive RecipeVersion + prepared authority",
            "exact existing rows are zero-write",
            "partial exact inactive subset is resumable",
            "conflicting or partial persisted truth fails closed",
            "publication never activates",
        ]
        or transaction.get("activation")
        != [
            "starts only after all eight exact publications reconcile",
            "all-inactive batch activates in one caller-owned UoW / one commit",
            "all-active replay is zero-write",
            "mixed active/inactive fails closed",
            "injected activation failure rolls back all staged activation writes",
        ]
    ):
        raise ValueError("R3-C option-B transaction contract changed.")

    return frozen, summary


def _identity_seeds(
    frozen: dict[str, Any],
) -> tuple[TrustedFoodIngredientIdentitySeed, ...]:
    return tuple(
        TrustedFoodIngredientIdentitySeed(
            canonical_code=row["canonical_code"],
            canonical_name=row["canonical_name"],
            category_code=row["category_code"],
            default_unit=row["default_unit"],
        )
        for row in frozen["new_identity_only_foods"]
    )


def _source_amount_text(row: dict[str, Any]) -> str:
    return (
        f"{row['source_label']}: брутто {row['gross_g']} г; "
        f"нетто {row['net_g']} г"
    )


def _recipe_seed(
    row: dict[str, Any],
    source: dict[str, Any],
) -> TrustedRecipeSeed:
    source_id = row["source_recipe_id"]
    return TrustedRecipeSeed(
        canonical_code=row["canonical_code"],
        canonical_name=row["canonical_name"],
        initial_is_active=False,
        version=TrustedRecipeVersionSeed(
            base_servings=Decimal(1),
            meal_type_code="main",
            prep_time_minutes=None,
            cook_time_minutes=None,
            total_time_minutes=None,
            difficulty_code=None,
            batch_friendly=None,
            freezable=None,
            storage_days_fridge=None,
            storage_days_freezer=None,
            verification_status="SOURCE_VERIFIED",
            verified_at=datetime(2026, 10, 4, tzinfo=timezone.utc),
            source_name=source["source_name"],
            source_recipe_id=source_id,
            source_url=source["source_pdf_locator"],
            source_version=f"sha256:{source['source_pdf_sha256']}",
            source_retrieved_at=None,
            source_document_sha256=source["source_pdf_sha256"],
            source_original_servings=Decimal(1),
            rights_review_status=source["rights_review_status"],
            rights_basis=source["rights_basis"],
            change_note=(
                "R3-C frozen School2022 MAIN card from merged Contract Gate #154."
            ),
            ingredients=tuple(
                TrustedRecipeIngredientSeed(
                    food_ingredient_code=ingredient["food_code"],
                    quantity=_decimal(
                        ingredient["net_g"],
                        field=f"{row['canonical_code']}.ingredient.net_g",
                    ),
                    unit="g",
                    source_amount_text=_source_amount_text(ingredient),
                    normalization_note=(
                        "R3-C frozen gate mapping; exact source gross/net evidence "
                        "retained without form inference."
                    ),
                    prep_note=None,
                    optional=False,
                )
                for ingredient in row["ingredients"]
            ),
            steps=tuple(row["consumer_steps_ru"]),
            equipment_codes=(),
            source_output_g=_decimal(
                row["source_output_g"],
                field=f"{row['canonical_code']}.source_output_g",
            ),
            source_output_text=(
                f"выход {row['source_output_g']} г; точный source-card output "
                f"для {source_id}"
            ),
        ),
    )


def _prepared_spec(
    row: dict[str, Any],
    source: dict[str, Any],
    seed: TrustedRecipeSeed,
) -> ReviewedPreparedRecipeNutritionSpec:
    return ReviewedPreparedRecipeNutritionSpec(
        trusted_recipe_seed=seed,
        recipe_code=seed.canonical_code,
        source_name=source["source_name"],
        source_recipe_id=row["source_recipe_id"],
        source_version=f"sha256:{source['source_pdf_sha256']}",
        source_document_sha256=source["source_pdf_sha256"],
        output_mass_g=_decimal(
            row["source_output_g"],
            field=f"{seed.canonical_code}.output_mass_g",
        ),
        source_locator=source["source_pdf_locator"],
        source_data_type="NORMATIVE_RECIPE_CARD_PDF",
        rights_review_status=source["rights_review_status"],
        rights_basis=source["rights_basis"],
        review_reference=(
            "data/curation/r3c-post-r3b-catalogue-gate/"
            f"frozen-batch.json#selected.{seed.canonical_code}"
        ),
        expected_available_amounts=(
            (
                "ENERGY_KCAL",
                _decimal(
                    row["energy_kcal"],
                    field=f"{seed.canonical_code}.ENERGY_KCAL",
                ),
            ),
        ),
        expected_unknown_codes=tuple(
            code for code in NUTRIENT_CODES if code != "ENERGY_KCAL"
        ),
        require_recipe_inactive=True,
    )


def _recipe_seeds_and_specs(
    frozen: dict[str, Any],
) -> tuple[
    tuple[TrustedRecipeSeed, ...],
    tuple[ReviewedPreparedRecipeNutritionSpec, ...],
]:
    source = frozen["source"]
    rows = frozen["selected"]
    seeds = tuple(_recipe_seed(row, source) for row in rows)
    specs = tuple(
        _prepared_spec(row, source, seed)
        for row, seed in zip(rows, seeds, strict=True)
    )
    return seeds, specs


def _ensure_prerequisite_batch(
    config: DatabaseConfig | None,
    *,
    codes: tuple[str, ...],
    seed,
    label: str,
) -> None:
    engine = create_sqlite_engine(config)
    try:
        catalogue = create_food_recipe_catalogue_service(engine)
        existing_codes = {recipe.canonical_code for recipe in catalogue.list_all()}
    finally:
        engine.dispose()

    present = set(codes) & existing_codes
    if not present:
        seed(config)
        return
    if present != set(codes):
        raise RecipeNutritionV2ConflictError(
            f"Partial persisted prerequisite {label} Recipe batch."
        )


def _ensure_prerequisites(config: DatabaseConfig | None) -> None:
    apply_migrations(config)
    _ensure_prerequisite_batch(
        config,
        codes=R3A_RECIPE_CODES,
        seed=seed_r3a_school2022_main_batch,
        label="R3-A",
    )
    _ensure_prerequisite_batch(
        config,
        codes=R3B_RECIPE_CODES,
        seed=seed_r3b_school2022_breakfast_batch,
        label="R3-B",
    )


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
            f"Partial persisted R3-C state for {seed.canonical_code}."
        )
    replay = nutrition.publish_prepared(spec)
    if replay.disposition is not PreparedPublicationDisposition.EXACT_REPLAY:
        raise RecipeNutritionV2ConflictError(
            f"Expected exact R3-C prepared replay for {seed.canonical_code}."
        )


def publish_r3c_school2022_main_batch(
    config: DatabaseConfig | None = None,
    *,
    package: Path = PACKAGE,
) -> R3CPublicationResult:
    frozen, _ = _load_contract(package)

    _ensure_prerequisites(config)

    engine = create_sqlite_engine(config)
    try:
        food = create_food_catalogue_service(engine)
        identity_summary = food.reconcile_identity_seed(_identity_seeds(frozen))
        catalogue = create_food_recipe_catalogue_service(engine)
        nutrition = create_recipe_nutrition_v2_service(engine)
        seeds, specs = _recipe_seeds_and_specs(frozen)

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
                            f"Fresh R3-C authority was not fresh: "
                            f"{seed.canonical_code}."
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
                            f"R3-C in-scope exact energy unavailable: "
                            f"{seed.canonical_code}."
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
                    f"R3-C exact energy unavailable: {seed.canonical_code}."
                )
            dispositions.append((seed.canonical_code, published.disposition.value))
            version_ids.append((seed.canonical_code, detail.version.id))
            energies.append((seed.canonical_code, projection.per_base_serving.kcal))

        return R3CPublicationResult(
            identity_food_inserted=identity_summary.ingredients_inserted,
            identity_food_existing=identity_summary.ingredients_existing,
            recipe_version_ids=tuple(version_ids),
            authority_dispositions=tuple(dispositions),
            exact_energy_kcal=tuple(energies),
        )
    finally:
        engine.dispose()


def activate_r3c_school2022_main_batch(
    config: DatabaseConfig | None = None,
    *,
    package: Path = PACKAGE,
) -> bool:
    frozen, _ = _load_contract(package)

    _ensure_prerequisites(config)

    engine = create_sqlite_engine(config)
    try:
        catalogue = create_food_recipe_catalogue_service(engine)
        nutrition = create_recipe_nutrition_v2_service(engine)
        seeds, specs = _recipe_seeds_and_specs(frozen)
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
            raise AssertionError("R3-C activation version ordering drifted.")
        return result.activated
    finally:
        engine.dispose()


def seed_r3c_school2022_main_batch(
    config: DatabaseConfig | None = None,
    *,
    package: Path = PACKAGE,
) -> R3CMainBatchResult:
    publication = publish_r3c_school2022_main_batch(config, package=package)
    activation_changed = activate_r3c_school2022_main_batch(config, package=package)

    engine = create_sqlite_engine(config)
    try:
        catalogue = create_food_recipe_catalogue_service(engine)
        active_recipe_codes = tuple(
            code for code in RECIPE_CODES if catalogue.get_by_code(code).is_active
        )
        if active_recipe_codes != RECIPE_CODES:
            raise AssertionError("R3-C final active batch does not match frozen set.")
    finally:
        engine.dispose()

    return R3CMainBatchResult(
        publication=publication,
        activation_changed=activation_changed,
        active_recipe_codes=active_recipe_codes,
    )


if __name__ == "__main__":
    result = seed_r3c_school2022_main_batch()
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
