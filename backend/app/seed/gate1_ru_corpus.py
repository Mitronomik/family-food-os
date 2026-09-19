"""Bounded Russian normative Gate1 publication; no schema or Planner changes."""

from dataclasses import asdict
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path
from uuid import uuid4

from app.db.config import DatabaseConfig, REPOSITORY_ROOT
from app.domain.food_ingredients import IngredientAlias, normalize_unicode_search_key
from app.domain.nutrition_evidence import (
    AssessmentStatus,
    ConversionDecision,
    RecipeIngredientNutritionAssessment,
    SemanticCompatibility,
)
from app.domain.nutrient_vector_backfill_v1 import canonical_json, value_set_digest
from app.domain.units import UnitCode
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
from app.persistence.sqlalchemy_core.food_recipe_composition import (
    create_food_recipe_catalogue_service,
)
from app.persistence.sqlalchemy_core.nutrition_evidence_uow import (
    SqlAlchemyNutritionEvidenceUnitOfWork,
)
from app.persistence.sqlalchemy_core.ru_food_data import SqlAlchemyRuFoodUnitOfWork
from app.services.food_recipes import (
    TrustedRecipeIngredientSeed,
    TrustedRecipeSeed,
    TrustedRecipeVersionSeed,
)
from app.services.ru_food_data import reconcile_ru_food_data

OPERATION = "GATE1-A-RU"
BASE = "9a76a97790b676f36c4c982af825721c3ef2c67e"
CHECKPOINT = "e720944aeb66e25fd666884576b10904d00f848fa655fae03f718a163108a1fe"
PACKAGE = REPOSITORY_ROOT / "data/seed/gate1_ru_corpus/package.json"
SOURCE_SNAPSHOT = REPOSITORY_ROOT / "data/seed/gate1_ru_corpus/source-snapshot.json"
REVIEWED_AT = datetime(2026, 9, 19, 7, 30, tzinfo=timezone.utc)
NUTRIENTS = (
    ("kcal", "ENERGY_KCAL", "Калорийность", "kcal", "METHOD_SPECIFIC"),
    ("protein_g", "PROTEIN", "Белки", "g", "METHOD_SPECIFIC"),
    ("fat_g", "FAT_TOTAL", "Жиры", "g", "METHOD_SPECIFIC"),
    (
        "carbohydrates_g",
        "CARBOHYDRATE_AVAILABLE",
        "Углеводы",
        "g",
        "METHOD_SPECIFIC",
    ),
    ("calcium_mg", "CALCIUM", "Кальций", "mg", "EXACT"),
    ("magnesium_mg", "MAGNESIUM", "Магний", "mg", "EXACT"),
    ("phosphorus_mg", "PHOSPHORUS", "Фосфор", "mg", "EXACT"),
    ("iron_mg", "IRON", "Железо", "mg", "EXACT"),
    ("thiamin_mg", "THIAMIN", "Витамин B1", "mg", "EXACT"),
    ("riboflavin_mg", "RIBOFLAVIN", "Витамин B2", "mg", "EXACT"),
    ("vitamin_c_mg", "VITAMIN_C", "Витамин C", "mg", "EXACT"),
)


class Gate1RuCorpusError(ValueError):
    """Stable bounded-data error for the Gate1 Russian corpus operation."""


def require(ok: bool, message: str) -> None:
    if not ok:
        raise Gate1RuCorpusError(message)


def dec(value: str) -> Decimal:
    result = Decimal(value)
    require(
        result.is_finite() and result >= 0,
        "Некорректное числовое значение Gate1 RU.",
    )
    return result


def load_package(path: Path = PACKAGE) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    require(
        data.get("schema_version") == 1 and data.get("operation") == OPERATION,
        "Неверный пакет Gate1 RU.",
    )
    require(data.get("starting_main") == BASE, "Изменена стартовая база Gate1 RU.")
    require(
        data.get("checkpoint", {}).get("sha256") == CHECKPOINT,
        "Изменён исходный checkpoint Gate1 RU.",
    )
    require(
        len(data.get("profiles", [])) == 10 and len(data.get("recipes", [])) == 8,
        "Gate1 RU остаётся bounded 10 foods / 8 recipes.",
    )

    snapshot = data.get("source_snapshot", {})
    expected_snapshot = snapshot.get("sha256")
    require(
        isinstance(expected_snapshot, str) and len(expected_snapshot) == 64,
        "Нет hash selected-source snapshot.",
    )
    actual_snapshot = hashlib.sha256(SOURCE_SNAPSHOT.read_bytes()).hexdigest()
    require(
        actual_snapshot == expected_snapshot,
        "Изменён selected-source snapshot Gate1 RU.",
    )
    require(
        all(
            row.get("source_document_sha256") == expected_snapshot
            and row.get("source_version") == f"sha256:{expected_snapshot}"
            for row in data["recipes"]
        ),
        "Recipe provenance не закреплена selected-source snapshot.",
    )
    require(
        sum(row["meal_type_code"] == "breakfast" for row in data["recipes"]) == 3,
        "Gate1 RU требует три завтрака.",
    )
    require(
        sum(row["meal_type_code"] == "main" for row in data["recipes"]) == 5,
        "Gate1 RU требует пять основных блюд.",
    )
    return data


def vector_payload(row: dict) -> tuple[list[dict], str]:
    values: list[dict] = []
    observations: list[dict] = []
    for field, code, label, unit, status in NUTRIENTS:
        amount = dec(row[field])
        observation = {
            "audit_identity": f"{OPERATION}:{row['external_id']}:{field}",
            "profile_source_name": row["source_name"],
            "profile_source_id": row["source_id"],
            "profile_source_version": row["source_version"],
            "profile_source_data_type": row["source_data_type"],
            "source_nutrient_id": field,
            "source_nutrient_name": label,
            "source_unit": unit,
            "source_value": row[field],
            "source_food_nutrient_id": f"{row['external_id']}:{field}",
            "source_derivation_id": None,
            "source_observation": {
                "checkpoint_sha256": CHECKPOINT,
                "profile_quality": row["profile_quality"],
                "exactness_tier": row["exactness_tier"],
                "source_url": row["source_url"],
                "secondary_evidence_url": row.get("secondary_evidence_url"),
            },
            "source_review_reference": (
                f"data/seed/gate1_ru_corpus/package.json#{row['external_id']}"
            ),
            "source_archive_id": "russian_normative_recipes_v22_5_checkpoint.zip",
            "uncertainty": (
                "Проверенная транскрипция пользовательского checkpoint; "
                "отсутствующие значения остаются unknown, нули не уплотняют "
                "sparse vector."
            ),
        }
        observations.append(
            {
                "origin": (
                    "SOURCE_REPORTED_ZERO_HELD"
                    if amount == 0
                    else "SOURCE_COMPONENT_CONFIRMED"
                ),
                "observation": observation,
            }
        )
        if amount == 0:
            continue
        mapping = {
            "canonical_code": code,
            "source_name": row["source_name"],
            "source_release": row["source_version"],
            "source_data_type": row["source_data_type"],
            "source_nutrient_id": field,
            "source_nutrient_name": label,
            "source_nutrient_nbr": field,
            "source_unit": unit,
            "mapping_status": status,
            "unit_conversion_required": False,
        }
        values.append(
            {
                "nutrient_code": code,
                "amount": amount,
                "provenance_json": canonical_json(
                    {"observation": observation, "mapping": mapping}
                ),
            }
        )
    return (
        sorted(values, key=lambda item: item["nutrient_code"]),
        canonical_json(observations),
    )


def food_entries(data: dict) -> tuple[dict, ...]:
    entries: list[dict] = []
    for row in data["profiles"]:
        values, observations = vector_payload(row)
        profile = {
            key: dec(row[key]) if row[key] is not None else None
            for key in (
                "basis_grams",
                "kcal",
                "protein_g",
                "fat_g",
                "carbohydrates_g",
                "fiber_g",
            )
        }
        profile.update(
            source_name=row["source_name"],
            source_id=row["source_id"],
            source_version=row["source_version"],
            source_data_type=row["source_data_type"],
            verified_at=datetime.fromisoformat(row["verified_at"]),
            estimated=bool(row["estimated"]),
        )
        decision = {
            "food_code": row["canonical_code"],
            "canonical_name_ru": row["canonical_name_ru"],
            "decision": "PROMOTE",
            "mass_state": "INPUT",
            "vector_reference": {
                "value_count": len(values),
                "value_sha256": value_set_digest(values),
            },
            "review_reference": f"{OPERATION}:{row['external_id']}",
        }
        entries.append(
            {
                "row": decision,
                "profile": profile,
                "values": values,
                "observations": observations,
                "category_code": row["category_code"],
            }
        )
    return tuple(entries)


def seed_foods(config: DatabaseConfig | None, data: dict) -> dict[str, int]:
    engine = create_sqlite_engine(config)
    try:
        result = reconcile_ru_food_data(
            lambda: SqlAlchemyRuFoodUnitOfWork(engine),
            food_entries(data),
        )
        with SqlAlchemyRuFoodUnitOfWork(engine) as uow:
            for row in data["profiles"]:
                food = uow.ingredients.get_by_code(row["canonical_code"])
                require(
                    food is not None,
                    f"Нет FoodIngredient {row['canonical_code']}.",
                )
                for alias in row["aliases_ru"]:
                    normalized = normalize_unicode_search_key(alias)
                    existing = uow.aliases.get_by_key(normalized)
                    if existing is None:
                        require(
                            uow.ingredients.get_by_name_key(normalized) is None,
                            f"Alias занят: {alias}",
                        )
                        uow.aliases.add(
                            IngredientAlias(
                                uuid4(),
                                food.id,
                                alias,
                                normalized,
                                "ru",
                                REVIEWED_AT,
                            )
                        )
                    else:
                        require(
                            existing.food_ingredient_id == food.id,
                            f"Alias ведёт на другой продукт: {alias}",
                        )
            uow.commit()
        return result
    finally:
        engine.dispose()


def recipe_seed(row: dict) -> TrustedRecipeSeed:
    ingredients = tuple(
        TrustedRecipeIngredientSeed(
            food_ingredient_code=item["food_ingredient_code"],
            quantity=dec(item["quantity_g"]),
            unit=UnitCode.GRAM,
            source_amount_text=item["source_amount_text"],
            normalization_note=(
                "Прямая нормативная масса нетто; без преобразования объёма/штук "
                "в граммы."
            ),
            prep_note=None,
            optional=False,
        )
        for item in row["ingredients"]
    )
    return TrustedRecipeSeed(
        canonical_code=row["canonical_code"],
        canonical_name=row["canonical_name_ru"],
        version=TrustedRecipeVersionSeed(
            base_servings=dec(row["base_servings"]),
            meal_type_code=row["meal_type_code"],
            prep_time_minutes=None,
            cook_time_minutes=None,
            total_time_minutes=None,
            difficulty_code=None,
            batch_friendly=None,
            freezable=None,
            storage_days_fridge=None,
            storage_days_freezer=None,
            verification_status="SOURCE_VERIFIED",
            verified_at=REVIEWED_AT,
            source_name=row["source_name"],
            source_recipe_id=row["source_recipe_id"],
            source_url=row["source_url"],
            source_version=row["source_version"],
            source_retrieved_at=datetime.fromisoformat(row["source_retrieved_at"]),
            source_document_sha256=row["source_document_sha256"],
            source_original_servings=dec(row["source_original_servings"]),
            rights_review_status=row["rights_review_status"],
            rights_basis=row["rights_basis"],
            change_note=row["change_note"],
            ingredients=ingredients,
            steps=tuple(row["steps_ru"]),
            equipment_codes=(),
        ),
    )


def seed_recipes(config: DatabaseConfig | None, data: dict) -> dict:
    engine = create_sqlite_engine(config)
    try:
        service = create_food_recipe_catalogue_service(engine)
        return asdict(
            service.reconcile_seed(tuple(recipe_seed(row) for row in data["recipes"]))
        )
    finally:
        engine.dispose()


def seed_assessments(config: DatabaseConfig | None, data: dict) -> dict[str, int]:
    engine = create_sqlite_engine(config)
    inserted = 0
    existing_count = 0
    try:
        with SqlAlchemyNutritionEvidenceUnitOfWork(engine) as uow:
            for recipe_row in data["recipes"]:
                recipe = uow.recipes.get_by_code(recipe_row["canonical_code"])
                require(
                    recipe is not None and recipe.is_active,
                    "Нет опубликованного Gate1 RU Recipe.",
                )
                detail = uow.versions.get_current_verified(recipe.id)
                require(
                    detail is not None
                    and detail.version.source_recipe_id
                    == recipe_row["source_recipe_id"],
                    "Изменена provenance Gate1 RU RecipeVersion.",
                )
                for item in detail.ingredients:
                    food = uow.ingredients.get(item.food_ingredient_id)
                    profile = (
                        None
                        if food is None
                        else uow.nutrition_profiles.get_current(food.id)
                    )
                    require(
                        food is not None and profile is not None,
                        "Gate1 RU строка потеряла FoodIngredient/profile.",
                    )
                    key = (
                        f"{recipe_row['source_recipe_id']}:"
                        f"v{detail.version.version_number}:{item.position}"
                    )
                    current = uow.evidence.get_current_assessment(item.id)
                    if current is not None:
                        require(
                            current.nutrition_profile_id == profile.id
                            and current.status_code
                            is AssessmentStatus.APPROVED_NO_CONVERSION
                            and current.semantic_compatibility_code
                            is SemanticCompatibility.MATCH
                            and current.conversion_decision_code
                            is ConversionDecision.DIRECT_RECIPE_MASS
                            and current.measure_evidence_id is None
                            and current.source_audit_operation == OPERATION
                            and current.source_audit_key == key
                            and not current.issues,
                            f"Конфликт assessment {key}",
                        )
                        existing_count += 1
                        continue
                    uow.evidence.add_assessment(
                        RecipeIngredientNutritionAssessment(
                            id=uuid4(),
                            recipe_ingredient_id=item.id,
                            nutrition_profile_id=profile.id,
                            assessment_version=1,
                            is_current=True,
                            status_code=AssessmentStatus.APPROVED_NO_CONVERSION,
                            semantic_compatibility_code=SemanticCompatibility.MATCH,
                            conversion_decision_code=(
                                ConversionDecision.DIRECT_RECIPE_MASS
                            ),
                            measure_evidence_id=None,
                            source_audit_operation=OPERATION,
                            source_audit_key=key,
                            review_note=(
                                "Нормативная масса нетто выражена в граммах; "
                                "binding проверен по v22.13 mapping и bounded "
                                "Gate1-A-RU package."
                            ),
                            reviewed_at=REVIEWED_AT,
                            created_at=REVIEWED_AT,
                            issues=(),
                        )
                    )
                    inserted += 1
            uow.commit()
        return {
            "assessments_inserted": inserted,
            "assessments_existing": existing_count,
        }
    finally:
        engine.dispose()


def seed_gate1_ru_corpus(
    config: DatabaseConfig | None = None,
) -> dict[str, dict]:
    data = load_package()
    return {
        "foods": seed_foods(config, data),
        "recipes": seed_recipes(config, data),
        "assessments": seed_assessments(config, data),
    }


if __name__ == "__main__":
    print(
        json.dumps(
            seed_gate1_ru_corpus(),
            ensure_ascii=False,
            sort_keys=True,
        )
    )
