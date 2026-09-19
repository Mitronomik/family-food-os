"""Bounded Russian normative recipe publication for the Gate 1 planning fixture."""

from dataclasses import replace
from datetime import datetime
from decimal import Decimal
import hashlib
import json
from pathlib import Path
from uuid import UUID, uuid4

from app.db.config import DatabaseConfig, REPOSITORY_ROOT
from app.domain.food_composition import (
    CompositionKind,
    CompositionProvenance,
    FoodCompositionVersion,
    MassState,
)
from app.domain.food_ingredients import (
    FoodIngredient,
    FoodNutritionProfile,
    IngredientAlias,
    normalize_unicode_search_key,
)
from app.domain.food_recipes import (
    MealTypeCode,
    Recipe,
    RecipeIngredient,
    RecipeStep,
    RecipeVersion,
    RecipeVersionDetail,
    RightsReviewStatus,
    VerificationStatus,
)
from app.domain.nutrition_evidence import (
    AssessmentStatus,
    ConversionDecision,
    RecipeIngredientNutritionAssessment,
    SemanticCompatibility,
)
from app.domain.nutrient_vector_backfill_v1 import canonical_json
from app.domain.units import UnitCode
from app.persistence.sqlalchemy_core.b2b2 import B2B2UnitOfWork
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
from app.services.food_composition import CompositionCalculator
from app.services.food_recipes import (
    TrustedRecipeIngredientSeed,
    TrustedRecipeSeed,
    TrustedRecipeVersionSeed,
    _seed_matches,
)

OPERATION = "GATE1-A-RU"
STARTING_MAIN = "9a76a97790b676f36c4c982af825721c3ef2c67e"
PACKAGE_DIR = REPOSITORY_ROOT / "data/seed/gate1_ru_corpus"
PACKAGE_PATH = PACKAGE_DIR / "package.json"
SNAPSHOT_PATH = PACKAGE_DIR / "source-snapshot.json"
EXPECTED_PROFILE_CODES = {
    "BREAD_WHEAT_HIGH_GRADE",
    "CHICKEN_CATEGORY_I",
    "COOKING_FAT",
    "COTTAGE_CHEESE_9",
    "CUCUMBER_PICKLED_SALTED",
    "MARGARINE_MILK",
    "MILK_PASTEURIZED_3_2",
    "RICE_GROATS_POLISHED",
    "SOUR_CREAM_30",
    "YEAST_COMPRESSED",
}
EXPECTED_RECIPE_IDS = {
    "USSR82-208",
    "USSR82-263",
    "USSR82-462",
    "USSR82-467",
    "USSR82-492",
    "USSR82-697",
    "USSR82-720",
    "USSR82-1081",
}
EXPECTED_RECIPE_COUNT = 8
EXPECTED_PROFILE_COUNT = 10
EXPECTED_INGREDIENT_ROWS = 40
EXPECTED_EXISTING_MAPPINGS = {
    "ING-0006": "WATER",
    "ING-0019": "POTATO",
    "ING-0028": "ONION_YELLOW",
    "ING-0032": "BUTTER_UNSALTED",
    "ING-0035": "CARROT",
    "ING-0036": "FLOUR_WHEAT",
    "ING-0042": "SUGAR",
    "ING-0050": "SALT",
    "ING-0071": "EGG",
}
_NUTRIENTS = (
    ("kcal", "ENERGY_KCAL", "kcal", "Энергетическая ценность", "METHOD_SPECIFIC"),
    ("protein_g", "PROTEIN", "g", "Белки", "METHOD_SPECIFIC"),
    ("fat_g", "FAT_TOTAL", "g", "Жиры", "METHOD_SPECIFIC"),
    ("calcium_mg", "CALCIUM", "mg", "Кальций", "EXACT"),
    ("magnesium_mg", "MAGNESIUM", "mg", "Магний", "EXACT"),
    ("phosphorus_mg", "PHOSPHORUS", "mg", "Фосфор", "EXACT"),
    ("iron_mg", "IRON", "mg", "Железо", "EXACT"),
    ("thiamin_mg", "THIAMIN", "mg", "Витамин B1", "EXACT"),
    ("riboflavin_mg", "RIBOFLAVIN", "mg", "Витамин B2", "EXACT"),
    ("vitamin_c_mg", "VITAMIN_C", "mg", "Витамин C", "EXACT"),
)


class Gate1RuCorpusError(ValueError):
    """Stable fail-closed error for the bounded Gate1 Russian data operation."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise Gate1RuCorpusError(message)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _instant(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    _require(parsed.utcoffset() is not None, "Gate1 RU instant must be timezone-aware.")
    return parsed


def _decimal(value: str) -> Decimal:
    parsed = Decimal(value)
    _require(parsed.is_finite() and parsed >= 0, "Gate1 RU numeric value is invalid.")
    return parsed


def load_gate1_ru_package(
    package_path: Path = PACKAGE_PATH,
    snapshot_path: Path = SNAPSHOT_PATH,
) -> dict:
    package = _read_json(package_path)
    snapshot = _read_json(snapshot_path)
    _require(package.get("schema_version") == 1, "Invalid Gate1 RU package schema.")
    _require(package.get("operation") == OPERATION, "Invalid Gate1 RU operation.")
    _require(
        package.get("starting_main") == STARTING_MAIN,
        "Gate1 RU starting main differs from the authorized base.",
    )
    source_snapshot = package.get("source_snapshot") or {}
    _require(
        source_snapshot.get("path")
        == "data/seed/gate1_ru_corpus/source-snapshot.json",
        "Gate1 RU source snapshot path differs.",
    )
    _require(
        source_snapshot.get("sha256") == _sha256(snapshot_path),
        "Gate1 RU source snapshot hash differs.",
    )
    _require(
        snapshot.get("source_checkpoint_sha256")
        == package.get("checkpoint", {}).get("sha256"),
        "Gate1 RU checkpoint lineage differs.",
    )
    profiles = package.get("profiles")
    recipes = package.get("recipes")
    mappings = package.get("existing_mappings")
    _require(
        isinstance(profiles, list)
        and len(profiles) == EXPECTED_PROFILE_COUNT
        and {row["canonical_code"] for row in profiles} == EXPECTED_PROFILE_CODES,
        "Gate1 RU profile scope differs.",
    )
    _require(
        isinstance(recipes, list)
        and len(recipes) == EXPECTED_RECIPE_COUNT
        and {row["source_recipe_id"] for row in recipes} == EXPECTED_RECIPE_IDS,
        "Gate1 RU recipe scope differs.",
    )
    _require(
        sum(len(row["ingredients"]) for row in recipes) == EXPECTED_INGREDIENT_ROWS,
        "Gate1 RU ingredient-row count differs.",
    )
    _require(
        isinstance(mappings, list)
        and {row["external_id"]: row["canonical_code"] for row in mappings}
        == EXPECTED_EXISTING_MAPPINGS,
        "Gate1 RU accepted v22.13 mappings differ.",
    )
    snapshot_by_id = {row["source_recipe_id"]: row for row in snapshot["recipes"]}
    _require(
        set(snapshot_by_id) == EXPECTED_RECIPE_IDS,
        "Gate1 RU snapshot scope differs.",
    )
    for recipe in recipes:
        _require(
            recipe["source_document_sha256"] == source_snapshot["sha256"]
            and recipe["source_version"] == f"sha256:{source_snapshot['sha256']}",
            "RecipeVersion provenance is not pinned to the selected snapshot.",
        )
        source = snapshot_by_id[recipe["source_recipe_id"]]
        _require(
            source.get("published_ingredients") == recipe["ingredients"]
            and source.get("steps_ru") == recipe["steps_ru"],
            f"Selected source snapshot differs for {recipe['source_recipe_id']}.",
        )
    profile_by_external = {row["external_id"]: row for row in profiles}
    _require(
        len(profile_by_external) == len(profiles),
        "Gate1 RU external profile identity is duplicated.",
    )
    for recipe in recipes:
        for ingredient in recipe["ingredients"]:
            external_id = ingredient.get("external_id")
            code = ingredient["food_ingredient_code"]
            if external_id is None:
                _require(
                    code == "WATER",
                    "Only the explicit water branch may lack v22 ID.",
                )
            elif external_id in profile_by_external:
                _require(
                    profile_by_external[external_id]["canonical_code"] == code,
                    "Gate1 RU new-form binding differs from the reviewed profile.",
                )
            else:
                _require(
                    EXPECTED_EXISTING_MAPPINGS.get(external_id) == code,
                    "Gate1 RU existing FoodIngredient binding differs from v22.13.",
                )
            quantity = _decimal(ingredient["quantity_g"])
            _require(quantity > 0, "Gate1 RU recipe input mass must be positive.")
    return package


def _vector_payload(row: dict) -> tuple[list[dict], str]:
    values: list[dict] = []
    observations: list[dict] = []
    for field, canonical_code, unit, label, mapping_status in _NUTRIENTS:
        raw = row.get(field)
        if raw is None:
            continue
        amount = _decimal(raw)
        observation = {
            "audit_identity": f"{OPERATION}:{row['external_id']}:{field}",
            "profile_source_name": row["source_name"],
            "profile_source_id": row["source_id"],
            "profile_source_version": row["source_version"],
            "profile_source_data_type": row["source_data_type"],
            "source_nutrient_id": field,
            "source_nutrient_name": label,
            "source_unit": unit,
            "source_value": raw,
            "source_food_nutrient_id": f"{row['external_id']}:{field}",
            "source_derivation_id": None,
            "source_observation": {
                "checkpoint_sha256": row["checkpoint_sha256"],
                "exactness_tier": row["exactness_tier"],
                "profile_quality": row["profile_quality"],
                "source_url": row["source_url"],
                "secondary_evidence_url": row.get("secondary_evidence_url"),
            },
            "source_review_reference": (
                f"data/seed/gate1_ru_corpus/package.json#{row['external_id']}"
            ),
            "source_archive_id": row["checkpoint_sha256"],
            "uncertainty": (
                "User-supplied reference transcription; exact food/form binding "
                "reviewed for the bounded Gate1 subset. Retention is not inferred."
            ),
        }
        mapping = {
            "source_name": row["source_name"],
            "source_release": row["source_version"],
            "source_data_type": row["source_data_type"],
            "source_nutrient_id": field,
            "canonical_code": canonical_code,
            "source_nutrient_name": label,
            "source_nutrient_nbr": field,
            "source_unit": unit,
            "canonical_unit": unit,
            "mapping_status": mapping_status,
            "unit_conversion_required": False,
        }
        if amount == 0:
            observations.append(
                {"origin": "SOURCE_REPORTED_ZERO_HELD", "observation": observation}
            )
            continue
        observations.append(
            {"origin": "SOURCE_COMPONENT_CONFIRMED", "observation": observation}
        )
        values.append(
            {
                "nutrient_code": canonical_code,
                "amount": amount,
                "provenance_json": canonical_json(
                    {"observation": observation, "mapping": mapping}
                ),
            }
        )
    observations.append(
        {
            "origin": "METHOD_AMBIGUOUS_HELD",
            "field": "carbohydrates_g",
            "source_value": row["carbohydrates_g"],
            "reason": (
                "The checkpoint does not establish whether the reported carbohydrate "
                "field is CHOAVL, CHOCDF or another analytical convention. The value "
                "remains in the legacy Nutrition v1 snapshot for deterministic Planner "
                "compatibility but is not normalized into the sparse NutrientVector."
            ),
        }
    )
    if row.get("fiber_g") is None:
        observations.append(
            {
                "origin": "VALUE_ABSENT",
                "field": "fiber_g",
                "reason": "The selected reference profile provides no exact fibre value.",
            }
        )
    return sorted(values, key=lambda item: item["nutrient_code"]), canonical_json(
        observations
    )


def _profile(row: dict, ingredient_id: UUID) -> FoodNutritionProfile:
    return FoodNutritionProfile(
        id=uuid4(),
        food_ingredient_id=ingredient_id,
        basis_grams=_decimal(row["basis_grams"]),
        kcal=_decimal(row["kcal"]),
        protein_g=_decimal(row["protein_g"]),
        fat_g=_decimal(row["fat_g"]),
        carbohydrates_g=_decimal(row["carbohydrates_g"]),
        fiber_g=None if row.get("fiber_g") is None else _decimal(row["fiber_g"]),
        source_name=row["source_name"],
        source_id=row["source_id"],
        source_version=row["source_version"],
        source_data_type=row["source_data_type"],
        verified_at=_instant(row["verified_at"]),
        estimated=row["estimated"],
        is_current=True,
        created_at=_instant(row["verified_at"]),
    )


def _recipe_seed(row: dict) -> TrustedRecipeSeed:
    instant = _instant(row["source_retrieved_at"])
    return TrustedRecipeSeed(
        canonical_code=row["canonical_code"],
        canonical_name=row["canonical_name_ru"],
        version=TrustedRecipeVersionSeed(
            base_servings=Decimal(row["base_servings"]),
            meal_type_code=MealTypeCode(row["meal_type_code"]),
            prep_time_minutes=None,
            cook_time_minutes=None,
            total_time_minutes=None,
            difficulty_code=None,
            batch_friendly=None,
            freezable=None,
            storage_days_fridge=None,
            storage_days_freezer=None,
            verification_status=VerificationStatus.SOURCE_VERIFIED,
            verified_at=instant,
            source_name=row["source_name"],
            source_recipe_id=row["source_recipe_id"],
            source_url=row["source_url"],
            source_version=row["source_version"],
            source_retrieved_at=instant,
            source_document_sha256=row["source_document_sha256"],
            source_original_servings=Decimal(row["source_original_servings"]),
            rights_review_status=RightsReviewStatus.REVIEWED,
            rights_basis=row["rights_basis"],
            change_note=row["change_note"],
            ingredients=tuple(
                TrustedRecipeIngredientSeed(
                    food_ingredient_code=item["food_ingredient_code"],
                    quantity=Decimal(item["quantity_g"]),
                    unit=UnitCode.GRAM,
                    source_amount_text=item["source_amount_text"],
                    normalization_note=(
                        "Exact net gram input preserved from the sealed "
                        "GATE1-A-RU source snapshot."
                    ),
                    prep_note=None,
                    optional=False,
                )
                for item in row["ingredients"]
            ),
            steps=tuple(row["steps_ru"]),
            equipment_codes=(),
        ),
    )


def _new_recipe_detail(
    uow: B2B2UnitOfWork, seed: TrustedRecipeSeed
) -> RecipeVersionDetail:
    now = seed.version.verified_at
    assert now is not None
    recipe = Recipe(
        id=uuid4(),
        canonical_code=seed.canonical_code,
        canonical_name=seed.canonical_name,
        canonical_name_key=normalize_unicode_search_key(
            seed.canonical_name, field="canonical_name"
        ),
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    version_id = uuid4()
    version = RecipeVersion(
        id=version_id,
        recipe_id=recipe.id,
        version_number=1,
        base_servings=seed.version.base_servings,
        meal_type_code=MealTypeCode(seed.version.meal_type_code),
        prep_time_minutes=None,
        cook_time_minutes=None,
        total_time_minutes=None,
        difficulty_code=None,
        batch_friendly=None,
        freezable=None,
        storage_days_fridge=None,
        storage_days_freezer=None,
        verification_status=VerificationStatus.SOURCE_VERIFIED,
        verified_at=now,
        source_name=seed.version.source_name,
        source_recipe_id=seed.version.source_recipe_id,
        source_url=seed.version.source_url,
        source_version=seed.version.source_version,
        source_retrieved_at=seed.version.source_retrieved_at,
        source_document_sha256=seed.version.source_document_sha256,
        source_original_servings=seed.version.source_original_servings,
        rights_review_status=RightsReviewStatus.REVIEWED,
        rights_basis=seed.version.rights_basis,
        created_from_version_id=None,
        change_note=seed.version.change_note,
        created_at=now,
    )
    ingredients = []
    for position, item in enumerate(seed.version.ingredients, 1):
        food = uow.ingredients.get_by_code(item.food_ingredient_code)
        _require(
            food is not None and food.is_active,
            f"Missing food {item.food_ingredient_code}.",
        )
        ingredients.append(
            RecipeIngredient(
                id=uuid4(),
                recipe_version_id=version_id,
                food_ingredient_id=food.id,
                position=position,
                quantity=item.quantity,
                unit=UnitCode.GRAM,
                source_amount_text=item.source_amount_text,
                normalization_note=item.normalization_note,
                prep_note=None,
                optional=False,
                created_at=now,
            )
        )
    steps = tuple(
        RecipeStep(
            id=uuid4(),
            recipe_version_id=version_id,
            position=position,
            instruction=instruction,
            stage_code=None,
            created_at=now,
        )
        for position, instruction in enumerate(seed.version.steps, 1)
    )
    return RecipeVersionDetail(
        recipe=recipe,
        version=version,
        ingredients=tuple(ingredients),
        steps=steps,
        equipment=(),
    )


def _ensure_food(
    uow: B2B2UnitOfWork, row: dict
) -> tuple[FoodIngredient, FoodNutritionProfile, bool]:
    now = _instant(row["verified_at"])
    code = row["canonical_code"]
    ingredient = uow.ingredients.get_by_code(code)
    inserted = ingredient is None
    if ingredient is None:
        key = normalize_unicode_search_key(row["canonical_name_ru"])
        _require(
            uow.ingredients.get_by_name_key(key) is None
            and uow.aliases.get_by_key(key) is None,
            f"FoodIngredient name collision for {code}.",
        )
        ingredient = FoodIngredient(
            id=uuid4(),
            canonical_code=code,
            canonical_name=row["canonical_name_ru"],
            canonical_name_key=key,
            category_code=row["category_code"],
            default_unit=UnitCode.GRAM,
            density_g_per_ml=None,
            edible_fraction=None,
            allergens_reviewed=False,
            allergen_codes=(),
            storage_profile_code=None,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        uow.ingredients.add(ingredient)
    else:
        _require(
            ingredient.is_active
            and ingredient.canonical_name == row["canonical_name_ru"]
            and ingredient.category_code == row["category_code"]
            and ingredient.default_unit is UnitCode.GRAM,
            f"Persisted FoodIngredient differs for {code}.",
        )
    for alias_text in row["aliases_ru"]:
        key = normalize_unicode_search_key(alias_text, field="alias")
        existing_alias = uow.aliases.get_by_key(key)
        canonical = uow.ingredients.get_by_name_key(key)
        _require(
            canonical is None or canonical.id == ingredient.id,
            f"Alias collision for {code}.",
        )
        if existing_alias is None:
            uow.aliases.add(
                IngredientAlias(uuid4(), ingredient.id, alias_text, key, "ru", now)
            )
        else:
            _require(
                existing_alias.food_ingredient_id == ingredient.id,
                f"Alias owner differs for {code}.",
            )
    expected = _profile(row, ingredient.id)
    profile = uow.nutrition_profiles.get_by_provenance(
        ingredient.id,
        expected.source_name,
        expected.source_id,
        expected.source_version,
    )
    if profile is None:
        _require(
            uow.nutrition_profiles.get_current(ingredient.id) is None,
            f"Unexpected current profile for new Gate1 RU food {code}.",
        )
        profile = expected
        uow.nutrition_profiles.add(profile)
        values, observations = _vector_payload(row)
        uow.publish_vector(profile, values, observations)
    else:
        _require(
            profile.snapshot_values() == expected.snapshot_values(),
            f"Profile differs for {code}.",
        )
    vector = uow.nutrient_vectors.get(profile.id)
    _require(
        vector.amount("ENERGY_KCAL") is not None
        and vector.amount("ENERGY_KCAL") > 0,
        f"Energy vector missing for {code}.",
    )
    provenance = CompositionProvenance(
        OPERATION,
        "1",
        f"data/seed/gate1_ru_corpus/package.json#{code}",
        f"Issue #64 / v22.13 mapping / {row['external_id']}",
    )
    expected_composition = FoodCompositionVersion(
        id=uuid4(),
        food_ingredient_id=ingredient.id,
        version=1,
        kind=CompositionKind.ATOMIC,
        input_state=MassState(row["mass_state"]),
        provenance=provenance,
        profile_id=profile.id,
    )
    composition = uow.compositions.find_version(ingredient.id, 1)
    if composition is None:
        composition = expected_composition
        uow.compositions.add_versions((composition,))
    else:
        _require(
            composition == replace(expected_composition, id=composition.id),
            f"Composition differs for {code}.",
        )
    result = CompositionCalculator(
        uow.compositions, uow.nutrient_vectors
    ).calculate(composition.id, nutrient_codes=("ENERGY_KCAL",))
    _require(
        result.nutrients[0].amount is not None,
        f"Composition energy missing for {code}.",
    )
    return ingredient, profile, inserted


def _ensure_recipe(
    uow: B2B2UnitOfWork, row: dict
) -> tuple[RecipeVersionDetail, bool]:
    seed = _recipe_seed(row)
    recipe = uow.recipes.get_by_code(seed.canonical_code)
    if recipe is None:
        key = normalize_unicode_search_key(
            seed.canonical_name, field="canonical_name"
        )
        _require(
            uow.recipes.get_by_name_key(key) is None,
            f"Recipe name collision for {seed.canonical_code}.",
        )
        detail = _new_recipe_detail(uow, seed)
        uow.recipes.add(detail.recipe)
        uow.versions.add_detail(detail)
        return detail, True
    _require(
        recipe.is_active and recipe.canonical_name == seed.canonical_name,
        f"Persisted Recipe differs for {seed.canonical_code}.",
    )
    matches = uow.versions.list_by_provenance(
        recipe.id,
        seed.version.source_name,
        seed.version.source_recipe_id,
        seed.version.source_version,
    )
    _require(
        len(matches) <= 1,
        f"Duplicate Gate1 RU provenance for {seed.canonical_code}.",
    )
    if matches:
        detail = matches[0]
        _require(
            _seed_matches(uow, detail, seed.version),
            f"RecipeVersion differs for {seed.canonical_code}.",
        )
        return detail, False
    _require(
        not uow.versions.list_for_recipe(recipe.id),
        f"Unexpected prior RecipeVersion history for {seed.canonical_code}.",
    )
    raise Gate1RuCorpusError(
        f"Recipe {seed.canonical_code} exists without the reviewed immutable version."
    )


def _ensure_assessments(
    uow: B2B2UnitOfWork, detail: RecipeVersionDetail
) -> int:
    inserted = 0
    reviewed_at = detail.version.verified_at
    assert reviewed_at is not None
    for row in detail.ingredients:
        profile = uow.nutrition_profiles.get_current(row.food_ingredient_id)
        _require(profile is not None, "Recipe row lacks current nutrition profile.")
        expected = RecipeIngredientNutritionAssessment(
            id=uuid4(),
            recipe_ingredient_id=row.id,
            nutrition_profile_id=profile.id,
            assessment_version=1,
            is_current=True,
            status_code=AssessmentStatus.APPROVED_NO_CONVERSION,
            semantic_compatibility_code=SemanticCompatibility.MATCH,
            conversion_decision_code=ConversionDecision.DIRECT_RECIPE_MASS,
            measure_evidence_id=None,
            source_audit_operation=OPERATION,
            source_audit_key=(
                f"{detail.recipe.canonical_code}:"
                f"v{detail.version.version_number}:{row.position}"
            ),
            review_note=(
                "Direct source net gram input from the sealed Russian normative "
                "Gate1 snapshot; no household measure conversion, yield inference "
                "or retention assumption is used."
            ),
            reviewed_at=reviewed_at,
            created_at=reviewed_at,
            issues=(),
        )
        current = uow.evidence.get_current_assessment(row.id)
        if current is None:
            uow.evidence.add_assessment(expected)
            inserted += 1
        else:
            _require(
                current == replace(expected, id=current.id),
                (
                    "Nutrition assessment differs for "
                    f"{detail.recipe.canonical_code}:{row.position}."
                ),
            )
    return inserted


def seed_gate1_ru_corpus(
    config: DatabaseConfig | None = None,
    *,
    package_path: Path = PACKAGE_PATH,
    snapshot_path: Path = SNAPSHOT_PATH,
) -> dict[str, int]:
    """Publish the selected Gate1 Russian corpus after the accepted baseline seed chain.

    This operation deliberately does not run migrations or historical seeds. The
    caller must establish the accepted current baseline first. All Gate1-RU writes
    share one project transaction.
    """
    package = load_gate1_ru_package(package_path, snapshot_path)
    engine = create_sqlite_engine(config)
    counters = {
        "food_ingredients_inserted": 0,
        "recipes_inserted": 0,
        "recipe_versions_inserted": 0,
        "assessments_inserted": 0,
    }
    try:
        with B2B2UnitOfWork(engine) as uow:
            for row in package["profiles"]:
                _, _, inserted = _ensure_food(uow, row)
                counters["food_ingredients_inserted"] += int(inserted)
            for row in package["recipes"]:
                detail, inserted = _ensure_recipe(uow, row)
                counters["recipes_inserted"] += int(inserted)
                counters["recipe_versions_inserted"] += int(inserted)
                counters["assessments_inserted"] += _ensure_assessments(uow, detail)
            uow.commit()
        return counters
    finally:
        engine.dispose()


if __name__ == "__main__":
    print(json.dumps(seed_gate1_ru_corpus(), ensure_ascii=False, sort_keys=True))
