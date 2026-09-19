"""Focused production-data tests for the bounded Russian Gate1 corpus."""

from collections import Counter
from decimal import Decimal
import json
import shutil

import pytest

from app.db.config import DatabaseConfig
from app.domain.nutrition import NutritionStatus
from app.domain.nutrition_evidence import AssessmentStatus, ConversionDecision
from app.domain.units import UnitCode
from app.persistence.sqlalchemy_core.b2b2 import B2B2UnitOfWork
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
from app.persistence.sqlalchemy_core.food_recipe_composition import (
    create_food_recipe_catalogue_service,
)
from app.persistence.sqlalchemy_core.nutrition_composition import (
    create_nutrition_service,
)
from app.seed.gate1_ru_corpus import (
    EXPECTED_PROFILE_CODES,
    EXPECTED_RECIPE_IDS,
    PACKAGE_DIR,
    Gate1RuCorpusError,
    load_gate1_ru_package,
    seed_gate1_ru_corpus,
)
from scripts.audit_gate1a_readiness import seed_current


RU_CODES = {
    "RU82_467_OMELET_NATURAL",
    "RU82_492_SYRNIKI",
    "RU82_1081_BLINI",
    "RU82_208_RASSOLNIK_LENINGRAD",
    "RU82_263_MILK_SOUP_POTATO_DUMPLINGS",
    "RU82_462_FRIED_EGGS_POTATO",
    "RU82_697_BOILED_CHICKEN",
    "RU82_720_CHICKEN_KIEV",
}


def test_gate1_ru_package_is_bounded_and_hash_pinned() -> None:
    package = load_gate1_ru_package()

    assert {row["canonical_code"] for row in package["profiles"]} == (
        EXPECTED_PROFILE_CODES
    )
    assert {row["source_recipe_id"] for row in package["recipes"]} == (
        EXPECTED_RECIPE_IDS
    )
    assert {row["canonical_code"] for row in package["recipes"]} == RU_CODES
    assert sum(len(row["ingredients"]) for row in package["recipes"]) == 40
    assert Counter(row["meal_type_code"] for row in package["recipes"]) == {
        "breakfast": 3,
        "main": 5,
    }
    assert all(
        row["source_document_sha256"] == package["source_snapshot"]["sha256"]
        for row in package["recipes"]
    )


def test_gate1_ru_package_rejects_changed_selected_snapshot(tmp_path) -> None:
    folder = tmp_path / "gate1-ru-package"
    shutil.copytree(PACKAGE_DIR, folder)
    snapshot = folder / "source-snapshot.json"
    payload = json.loads(snapshot.read_text(encoding="utf-8"))
    payload["recipes"][0]["output_g"] = "999"
    snapshot.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(Gate1RuCorpusError, match="snapshot hash"):
        load_gate1_ru_package(folder / "package.json", snapshot)


def test_gate1_ru_seed_is_idempotent_and_nutrition_ready(tmp_path) -> None:
    config = DatabaseConfig(path=tmp_path / "gate1-ru.sqlite")
    seed_current(config)

    first = seed_gate1_ru_corpus(config)
    assert first == {
        "food_ingredients_inserted": 10,
        "recipes_inserted": 8,
        "recipe_versions_inserted": 8,
        "assessments_inserted": 40,
    }
    second = seed_gate1_ru_corpus(config)
    assert second == {
        "food_ingredients_inserted": 0,
        "recipes_inserted": 0,
        "recipe_versions_inserted": 0,
        "assessments_inserted": 0,
    }

    engine = create_sqlite_engine(config)
    try:
        recipes = create_food_recipe_catalogue_service(engine)
        nutrition = create_nutrition_service(engine)
        active = recipes.list_active(limit=100)
        assert len(active) == 38

        results = {}
        for code in sorted(RU_CODES):
            recipe = recipes.get_by_code(code)
            detail = recipes.get_current_verified(recipe.id)
            result = nutrition.recipe_version(detail.version.id)
            results[code] = result

            assert detail.version.source_recipe_id in EXPECTED_RECIPE_IDS
            assert result.status in {
                NutritionStatus.COMPLETE,
                NutritionStatus.COMPLETE_WITH_WARNINGS,
            }
            assert result.per_base_serving.kcal is not None
            assert result.per_base_serving.kcal > Decimal("0")
            assert all(
                contribution.nutrition.mass_g is not None
                and contribution.row.unit is UnitCode.GRAM
                for contribution in result.required_contributions
            )
            assert not result.optional_contributions

        assert Counter(
            result.version.meal_type_code.value for result in results.values()
        ) == {"breakfast": 3, "main": 5}

        with B2B2UnitOfWork(engine) as scope:
            for code in EXPECTED_PROFILE_CODES:
                food = scope.ingredients.get_by_code(code)
                assert food is not None and food.is_active
                profile = scope.nutrition_profiles.get_current(food.id)
                assert profile is not None
                vector = scope.nutrient_vectors.get(profile.id)
                assert vector.amount("ENERGY_KCAL") is not None
                assert vector.amount("CARBOHYDRATE_AVAILABLE") is None
                composition = scope.compositions.find_version(food.id, 1)
                assert composition is not None
                assert composition.profile_id == profile.id
                assert composition.provenance.source == "GATE1-A-RU"

            for code in RU_CODES:
                recipe = scope.recipes.get_by_code(code)
                detail = scope.versions.get_current_verified(recipe.id)
                assert detail is not None
                for row in detail.ingredients:
                    assessment = scope.evidence.get_current_assessment(row.id)
                    assert assessment is not None
                    assert (
                        assessment.status_code
                        is AssessmentStatus.APPROVED_NO_CONVERSION
                    )
                    assert (
                        assessment.conversion_decision_code
                        is ConversionDecision.DIRECT_RECIPE_MASS
                    )
                    assert assessment.measure_evidence_id is None
                    assert assessment.source_audit_operation == "GATE1-A-RU"

        old_statuses = []
        for recipe in active:
            if recipe.canonical_code in RU_CODES:
                continue
            detail = recipes.get_current_verified(recipe.id)
            old_statuses.append(nutrition.recipe_version(detail.version.id).status)
        assert Counter(old_statuses) == {
            NutritionStatus.INCOMPLETE: 29,
            NutritionStatus.CONDITIONAL: 1,
        }
    finally:
        engine.dispose()
