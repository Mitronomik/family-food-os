"""R1-F prepared-output Nutrition publication and activation pilot."""

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path
from uuid import UUID

from app.db.config import DatabaseConfig, REPOSITORY_ROOT
from app.db.migrations import apply_migrations
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
from app.services.food_ingredients import TrustedFoodIngredientIdentitySeed
from app.services.food_recipes import (
    TrustedRecipeIngredientSeed,
    TrustedRecipeSeed,
    TrustedRecipeSeedDisposition,
    TrustedRecipeVersionSeed,
)
from app.services.planner import PlannerAdmissionBlocker, PlannerService
from app.services.recipe_nutrition_v2 import (
    PreparedPublicationDisposition,
    RecipeNutritionV2ConflictError,
    ReviewedPreparedRecipeNutritionSpec,
)

PACKAGE = REPOSITORY_ROOT / "data/curation/r1f-cooked-nutrition-authority-gate"
EVIDENCE_PATH = PACKAGE / "evidence.json"
CHICKEN_OCR_PATH = PACKAGE / "dietetic-recipes-1988-recipe-303-factual-excerpt.txt"
MR_BUNDLE_PATH = (
    REPOSITORY_ROOT
    / "data/seed/ru_normative_recipe_corpus/mr_2_4_0162_19.bundle.json"
)

EGG_RECIPE_CODE = "HARD_BOILED_EGG"
CHICKEN_RECIPE_CODE = "BOILED_CHICKEN_MAIN_PRODUCT"
CHICKEN_FOOD_CODE = "CHICKEN_CATEGORY_2_RAW"


@dataclass(frozen=True)
class R1FPreparedPilotResult:
    chicken_food_inserted: int
    chicken_food_existing: int
    recipe_version_ids: tuple[tuple[str, UUID], ...]
    authority_dispositions: tuple[tuple[str, str], ...]
    active_recipe_codes: tuple[str, ...]
    exact_energy_kcal: tuple[tuple[str, Decimal], ...]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_evidence() -> dict:
    evidence = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))
    if (
        evidence.get("schema_version") != 2
        or evidence.get("operation") != "R1F_COOKED_NUTRITION_AUTHORITY_GATE"
    ):
        raise ValueError("R1-F evidence identity changed.")

    egg = evidence["source_receipts"]["hard_boiled_egg"]
    bundle = json.loads(MR_BUNDLE_PATH.read_text(encoding="utf-8"))
    if MR_BUNDLE_PATH.stat().st_size != egg["durable_artifact_size_bytes"]:
        raise ValueError("R1-F MR bundle size changed.")
    document = bundle["document"]
    if (
        document["raw_bytes_sha256"] != egg["source_document_raw_bytes_sha256"]
        or document["raw_text_sha256"] != egg["source_document_raw_text_sha256"]
        or document["publication_policy"] != "NORMATIVE_BASE_RECIPE_APPROVED"
    ):
        raise ValueError("R1-F MR document receipt changed.")
    cards = [
        row
        for row in bundle["cards"]
        if row["source_section_code"] == egg["source_section_code"]
        and row["source_card_code"] == egg["source_card_code"]
    ]
    if len(cards) != 1:
        raise ValueError("R1-F hard-boiled egg card identity is not exact.")
    raw = cards[0]["raw_card_text"].encode("utf-8")
    if hashlib.sha256(raw).hexdigest() != egg["raw_card_sha256"]:
        raise ValueError("R1-F hard-boiled egg card hash changed.")

    chicken = evidence["source_receipts"]["boiled_chicken_75g"]
    if (
        CHICKEN_OCR_PATH.stat().st_size != chicken["durable_artifact_size_bytes"]
        or _sha256(CHICKEN_OCR_PATH) != chicken["durable_artifact_sha256"]
        or chicken["artifact_kind"] != "EXACT_SOURCE_PAGE_OCR_CAPTURE"
        or chicken["rights_review_status"] != "BOUNDED_FACTUAL_USE_REVIEWED"
    ):
        raise ValueError("R1-F chicken OCR receipt changed.")
    text = CHICKEN_OCR_PATH.read_text(encoding="utf-8")
    for expected in (
        "303. Курица отварная",
        "Курица 260 179 208 143 155 107",
        "Выход: 125 100 75",
        "Вариант III: Б—12,6, Ж—12,8, У—0,5; калорийность—167,7 ккал.",
        "Кур отваривают целиком.",
    ):
        if expected not in text:
            raise ValueError("R1-F chicken OCR source text changed.")
    return evidence


def _recipe_seeds(evidence: dict) -> tuple[TrustedRecipeSeed, TrustedRecipeSeed]:
    egg_receipt = evidence["source_receipts"]["hard_boiled_egg"]
    chicken_receipt = evidence["source_receipts"]["boiled_chicken_75g"]
    verified_at = datetime(2026, 9, 30, tzinfo=timezone.utc)

    egg = TrustedRecipeSeed(
        canonical_code=EGG_RECIPE_CODE,
        canonical_name="Яйцо куриное вкрутую",
        initial_is_active=False,
        version=TrustedRecipeVersionSeed(
            base_servings=Decimal("1"),
            meal_type_code="breakfast",
            prep_time_minutes=None,
            cook_time_minutes=10,
            total_time_minutes=10,
            difficulty_code=None,
            batch_friendly=False,
            freezable=False,
            storage_days_fridge=None,
            storage_days_freezer=None,
            verification_status="SOURCE_VERIFIED",
            verified_at=verified_at,
            source_name="RU_MR_2_4_0162_19",
            source_recipe_id="APPENDIX_5_CARD_4_1",
            source_url=egg_receipt["source_locator"],
            source_version=f"sha256:{egg_receipt['source_document_raw_bytes_sha256']}",
            source_retrieved_at=datetime.fromisoformat(egg_receipt["retrieved_at"]),
            source_document_sha256=egg_receipt["source_document_raw_bytes_sha256"],
            source_original_servings=Decimal("1"),
            rights_review_status="REVIEWED",
            rights_basis=egg_receipt["rights_basis"],
            change_note="R1-F exact hard-boiled branch from MR 2.4.0162-19 card 4.1.",
            ingredients=(
                TrustedRecipeIngredientSeed(
                    food_ingredient_code="EGG",
                    quantity=Decimal("40"),
                    unit="g",
                    source_amount_text="Яйцо куриное 40 г",
                    normalization_note="exact source net amount",
                    prep_note=None,
                    optional=False,
                ),
            ),
            steps=(
                "Погрузить яйцо в кипящую воду и варить вкрутую 8–10 минут.",
                "Охладить в холодной воде и очистить от скорлупы.",
            ),
            source_output_g=Decimal("40"),
            source_output_text="выход 1 шт.; нормативная масса порции 40 г",
        ),
    )

    chicken = TrustedRecipeSeed(
        canonical_code=CHICKEN_RECIPE_CODE,
        canonical_name="Курица отварная без гарнира",
        initial_is_active=False,
        version=TrustedRecipeVersionSeed(
            base_servings=Decimal("1"),
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
            verified_at=verified_at,
            source_name="DIETETIC_RECIPES_1988",
            source_recipe_id="303_VARIANT_III",
            source_url=chicken_receipt["source_locator"],
            source_version=f"sha256:{chicken_receipt['durable_artifact_sha256']}",
            source_retrieved_at=None,
            source_document_sha256=chicken_receipt["durable_artifact_sha256"],
            source_original_servings=Decimal("1"),
            rights_review_status="REVIEWED",
            rights_basis=chicken_receipt["rights_basis"],
            change_note="R1-F exact recipe 303 Variant III main-product publication.",
            ingredients=(
                TrustedRecipeIngredientSeed(
                    food_ingredient_code=CHICKEN_FOOD_CODE,
                    quantity=Decimal("107"),
                    unit="g",
                    source_amount_text="Курица 155 г брутто / 107 г нетто",
                    normalization_note="exact source Variant III net amount; category II",
                    prep_note=None,
                    optional=False,
                ),
            ),
            steps=("Курицу отварить целиком.",),
            source_output_g=Decimal("75"),
            source_output_text="выход 75 г; основной продукт без гарнира/соуса",
        ),
    )
    return egg, chicken


def _prepared_specs(
    evidence: dict,
    seeds: tuple[TrustedRecipeSeed, TrustedRecipeSeed],
) -> tuple[ReviewedPreparedRecipeNutritionSpec, ...]:
    egg, chicken = seeds
    egg_receipt = evidence["source_receipts"]["hard_boiled_egg"]
    chicken_receipt = evidence["source_receipts"]["boiled_chicken_75g"]
    return (
        ReviewedPreparedRecipeNutritionSpec(
            recipe_code=egg.canonical_code,
            source_name=egg.version.source_name,
            source_recipe_id=egg.version.source_recipe_id,
            source_version=egg.version.source_version,
            source_document_sha256=egg.version.source_document_sha256,
            output_mass_g=Decimal(egg_receipt["authority_values"]["output_g"]),
            source_locator=egg_receipt["source_locator"],
            source_data_type="NORMATIVE_TECH_CARD_OCR",
            rights_review_status=egg_receipt["rights_review_status"],
            rights_basis=egg.version.rights_basis or "",
            review_reference=(
                "data/curation/r1f-cooked-nutrition-authority-gate/"
                "evidence.json#source_receipts.hard_boiled_egg"
            ),
            expected_available_amounts=(
                ("ENERGY_KCAL", Decimal(egg_receipt["authority_values"]["energy_kcal"])),
            ),
        ),
        ReviewedPreparedRecipeNutritionSpec(
            recipe_code=chicken.canonical_code,
            source_name=chicken.version.source_name,
            source_recipe_id=chicken.version.source_recipe_id,
            source_version=chicken.version.source_version,
            source_document_sha256=chicken.version.source_document_sha256,
            output_mass_g=Decimal(chicken_receipt["authority_values"]["output_g"]),
            source_locator=chicken_receipt["source_locator"],
            source_data_type="NORMATIVE_RECIPE_SOURCE_PAGE_OCR",
            rights_review_status=chicken_receipt["rights_review_status"],
            rights_basis=chicken.version.rights_basis or "",
            review_reference=(
                "data/curation/r1f-cooked-nutrition-authority-gate/"
                "evidence.json#source_receipts.boiled_chicken_75g"
            ),
            expected_available_amounts=(
                (
                    "ENERGY_KCAL",
                    Decimal(chicken_receipt["authority_values"]["energy_kcal"]),
                ),
            ),
        ),
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
            f"Partial persisted R1-F state for {seed.canonical_code}."
        )
    replay = nutrition.publish_prepared(spec)
    if replay.disposition is not PreparedPublicationDisposition.EXACT_REPLAY:
        raise RecipeNutritionV2ConflictError(
            f"Expected exact prepared replay for {seed.canonical_code}."
        )


def seed_r1f_prepared_output(
    config: DatabaseConfig | None = None,
) -> R1FPreparedPilotResult:
    apply_migrations(config)
    evidence = _load_evidence()
    engine = create_sqlite_engine(config)
    try:
        food = create_food_catalogue_service(engine)
        food_summary = food.reconcile_identity_seed(
            (
                TrustedFoodIngredientIdentitySeed(
                    canonical_code=CHICKEN_FOOD_CODE,
                    canonical_name="Курица II категории, сырая",
                    category_code="poultry",
                    default_unit="g",
                ),
            )
        )
        catalogue = create_food_recipe_catalogue_service(engine)
        nutrition = create_recipe_nutrition_v2_service(engine)
        seeds = _recipe_seeds(evidence)
        specs = _prepared_specs(evidence, seeds)

        for seed, spec in zip(seeds, specs, strict=True):
            _assert_replay_not_partial(engine, catalogue, nutrition, seed, spec)

        dispositions = []
        version_ids = []
        energies = []
        for seed, spec in zip(seeds, specs, strict=True):
            if catalogue.preflight_trusted_seed(seed) is TrustedRecipeSeedDisposition.FRESH:
                with SqlAlchemyRecipeNutritionV2UnitOfWork(engine) as uow:
                    catalogue.reconcile_seed_in_scope(uow, (seed,))
                    published = nutrition.publish_prepared_in_scope(uow, spec)
                    projection = nutrition.neutral_consumption_projection
                    if published.disposition is not PreparedPublicationDisposition.FRESH:
                        raise RecipeNutritionV2ConflictError(
                            f"Fresh R1-F publication did not produce FRESH: {seed.canonical_code}."
                        )
                    uow.commit()
            else:
                published = nutrition.publish_prepared(spec)

            recipe = catalogue.get_by_code(seed.canonical_code)
            detail = catalogue.get_latest_verified(recipe.id)
            projected = nutrition.neutral_consumption_projection(detail.version.id)
            if not projected.exact_energy_ready or projected.per_base_serving.kcal is None:
                raise RecipeNutritionV2ConflictError(
                    f"R1-F exact energy unavailable: {seed.canonical_code}."
                )
            dispositions.append((seed.canonical_code, published.disposition.value))
            version_ids.append((seed.canonical_code, detail.version.id))
            energies.append((seed.canonical_code, projected.per_base_serving.kcal))

        planner = PlannerService(
            None, None, catalogue, None, None, recipe_nutrition=nutrition  # type: ignore[arg-type]
        )
        for seed in seeds:
            admission = next(
                row
                for row in planner.compose_candidate_admission()
                if row.canonical_code == seed.canonical_code
            )
            if admission.blockers != (PlannerAdmissionBlocker.INACTIVE,):
                raise RecipeNutritionV2ConflictError(
                    f"R1-F pre-activation admission blocked: {seed.canonical_code} {admission.blockers}."
                )
            catalogue.activate(admission.recipe_id)
            active = next(
                row
                for row in planner.compose_candidate_admission()
                if row.canonical_code == seed.canonical_code
            )
            if not active.eligible or not active.exact_energy_ready:
                raise RecipeNutritionV2ConflictError(
                    f"R1-F post-activation admission failed: {seed.canonical_code}."
                )

        return R1FPreparedPilotResult(
            chicken_food_inserted=food_summary.ingredients_inserted,
            chicken_food_existing=food_summary.ingredients_existing,
            recipe_version_ids=tuple(version_ids),
            authority_dispositions=tuple(dispositions),
            active_recipe_codes=tuple(seed.canonical_code for seed in seeds),
            exact_energy_kcal=tuple(energies),
        )
    finally:
        engine.dispose()


if __name__ == "__main__":
    result = seed_r1f_prepared_output()
    print(
        json.dumps(
            {
                "chicken_food_inserted": result.chicken_food_inserted,
                "chicken_food_existing": result.chicken_food_existing,
                "recipe_version_ids": [
                    [code, str(version_id)]
                    for code, version_id in result.recipe_version_ids
                ],
                "authority_dispositions": list(result.authority_dispositions),
                "active_recipe_codes": list(result.active_recipe_codes),
                "exact_energy_kcal": [
                    [code, format(value, "f")]
                    for code, value in result.exact_energy_kcal
                ],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
