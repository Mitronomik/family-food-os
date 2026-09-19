"""Focused production-data tests for the bounded Russian Gate1 corpus."""

from decimal import Decimal

from app.db.config import DatabaseConfig
from app.domain.nutrition import NutritionStatus
from app.domain.nutrition_evidence import AssessmentStatus
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
from app.persistence.sqlalchemy_core.food_recipe_composition import (
    create_food_recipe_catalogue_service,
)
from app.persistence.sqlalchemy_core.nutrition_composition import (
    create_nutrition_service,
)
from app.seed.b2b2 import upgrade_b2b2
from app.seed.food_recipes import seed_food_recipes
from app.seed.gate1_ru_corpus import load_package, seed_gate1_ru_corpus
from app.seed.nutrition_measure_evidence import seed_nutrition_measure_evidence
from app.seed.recipe_corrections import (
    seed_correction_assessments,
    seed_recipe_corrections,
)
from app.seed.ru_food_data import seed_ru_food_data


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


def seed_current_baseline(config: DatabaseConfig) -> None:
    seed_food_recipes(config)
    seed_nutrition_measure_evidence(config)
    seed_recipe_corrections(config)
    seed_correction_assessments(config)
    seed_ru_food_data(config)
    upgrade_b2b2(config)


def test_gate1_ru_package_is_bounded_and_hash_pinned() -> None:
    package = load_package()
    assert len(package["profiles"]) == 10
    assert len(package["recipes"]) == 8
    assert {row["canonical_code"] for row in package["recipes"]} == RU_CODES
    assert sum(row["meal_type_code"] == "breakfast" for row in package["recipes"]) == 3
    assert sum(row["meal_type_code"] == "main" for row in package["recipes"]) == 5
    assert all(
        row["source_document_sha256"] == package["source_snapshot"]["sha256"]
        for row in package["recipes"]
    )
    assert all(
        row["source_version"] == f"sha256:{package['source_snapshot']['sha256']}"
        for row in package["recipes"]
    )


def test_gate1_ru_seed_is_idempotent_and_nutrition_ready(tmp_path) -> None:
    config = DatabaseConfig(path=tmp_path / "gate1-ru.sqlite")
    seed_current_baseline(config)

    first = seed_gate1_ru_corpus(config)
    assert first["foods"]["ingredients"] == 10
    assert first["foods"]["profiles"] == 10
    assert first["foods"]["vector_seals"] == 10
    assert first["foods"]["atomic_compositions"] == 10
    assert first["recipes"]["recipes_inserted"] == 8
    assert first["recipes"]["versions_inserted"] == 8
    assert first["recipes"]["ingredients_inserted"] == 40
    assert first["assessments"] == {
        "assessments_inserted": 40,
        "assessments_existing": 0,
    }

    second = seed_gate1_ru_corpus(config)
    assert second["foods"]["ingredients"] == 0
    assert second["foods"]["profiles"] == 0
    assert second["foods"]["vector_seals"] == 0
    assert second["foods"]["atomic_compositions"] == 0
    assert second["recipes"]["recipes_existing"] == 8
    assert second["recipes"]["versions_existing"] == 8
    assert second["recipes"]["ingredients_existing"] == 40
    assert second["assessments"] == {
        "assessments_inserted": 0,
        "assessments_existing": 40,
    }

    engine = create_sqlite_engine(config)
    try:
        recipes = create_food_recipe_catalogue_service(engine)
        nutrition = create_nutrition_service(engine)
        active = recipes.list_active(limit=200)
        assert len(active) == 38

        results = {}
        for code in RU_CODES:
            recipe = recipes.get_by_code(code)
            detail = recipes.get_current_verified(recipe.id)
            result = nutrition.recipe_version(detail.version.id)
            results[code] = result
            assert result.status is not NutritionStatus.INCOMPLETE
            assert result.per_base_serving.kcal is not None
            assert result.per_base_serving.kcal > Decimal("0")
            assert all(
                contribution.nutrition.mass_g is not None
                and contribution.assessment is not None
                and contribution.assessment.status_code
                is AssessmentStatus.APPROVED_NO_CONVERSION
                for contribution in result.required_contributions
            )
            assert not result.optional_contributions

        assert set(results) == RU_CODES
    finally:
        engine.dispose()
