"""Production Step 10-A binding publication for the accepted School2022 butter row."""

from decimal import Decimal
import shutil
import sqlite3

import pytest

from app.db.config import DatabaseConfig
from app.domain.nutrition import NutritionStatus
from app.domain.recipe_nutrition_v2 import RecipeNutritionV2Status
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
from app.persistence.sqlalchemy_core.recipe_nutrition_v2 import (
    create_recipe_nutrition_v2_service,
)
from app.seed.food_recipes import seed_food_recipes
from app.seed.ru_nut_db_step8_butter import seed_ru_nut_db_step8_butter
from app.seed.ru_school2022_step9_recipe import (
    EXPECTED_RECIPE_AMOUNTS,
    FOOD_CODE,
    RECIPE_CODE,
    seed_ru_school2022_step9_recipe,
)
from app.seed.ru_school2022_step10a_binding import (
    STEP10A_BINDING_SPEC,
    seed_ru_school2022_step10a_binding,
)
from app.services.recipe_nutrition_v2 import BindingDisposition

TABLE = "recipe_ingredient_composition_bindings"


@pytest.fixture(scope="module")
def baseline(tmp_path_factory):
    config = DatabaseConfig(path=tmp_path_factory.mktemp("step10a-pub") / "base.sqlite")
    seed_food_recipes(config)
    seed_ru_nut_db_step8_butter(config)
    seed_ru_school2022_step9_recipe(config)
    return config


@pytest.fixture
def database(baseline, tmp_path):
    config = DatabaseConfig(path=tmp_path / "step10a.sqlite")
    shutil.copyfile(baseline.path, config.path)
    return config


def db_dump(config):
    with sqlite3.connect(config.path) as db:
        return "\n".join(db.iterdump())


def test_production_entrypoint_fresh_replay_and_exact_truth(database):
    with sqlite3.connect(database.path) as db:
        assert db.execute(f"SELECT COUNT(*) FROM {TABLE}").fetchone()[0] == 0
        assert db.execute(
            "SELECT is_active FROM food_recipes WHERE canonical_code=?", (RECIPE_CODE,)
        ).fetchone()[0] == 0

    first = seed_ru_school2022_step10a_binding(database)
    assert first.disposition is BindingDisposition.FRESH

    engine = create_sqlite_engine(database)
    try:
        service = create_recipe_nutrition_v2_service(engine)
        canonical = service.calculate(first.recipe_version_id)
        assert canonical.status is RecipeNutritionV2Status.PARTIAL
        known = {
            item.code: item.amount
            for item in canonical.required_total
            if item.amount is not None
        }
        assert known == EXPECTED_RECIPE_AMOUNTS
        assert len(canonical.required_total) == 54
        assert canonical.total_amount("WATER") is None
        assert canonical.total_amount("CARBOHYDRATE_AVAILABLE") is None
        assert canonical.total_amount("CARBOHYDRATE_BY_DIFFERENCE") is None

        projection = service.consumption_projection(first.recipe_version_id)
        assert projection.legacy_status is NutritionStatus.INCOMPLETE
        assert projection.required_total == projection.per_base_serving
        assert projection.required_total.kcal == Decimal("66.090000")
        assert projection.required_total.carbohydrates_g is None
        assert projection.exact_energy_ready is True
    finally:
        engine.dispose()

    with sqlite3.connect(database.path) as db:
        row = db.execute(
            f"""
            SELECT registry_version, nutrient_set_version,
                   composition_calculation_version, recipe_calculation_version
            FROM {TABLE}
            """
        ).fetchone()
        assert row == (
            "RU_NUTRIENT_REGISTRY_V2",
            "RECIPE_V2_NUTRIENT_SET_V1",
            "FOOD_COMPOSITION_APPLICABILITY_V2",
            "RECIPE_COMPOSITION_NUTRITION_V1",
        )
        assert db.execute(
            "SELECT is_active FROM food_recipes WHERE canonical_code=?", (RECIPE_CODE,)
        ).fetchone()[0] == 0
        assert db.execute("PRAGMA foreign_key_check").fetchall() == []

    before = db_dump(database)
    second = seed_ru_school2022_step10a_binding(database)
    assert second.disposition is BindingDisposition.EXACT_REPLAY
    assert second.binding == first.binding
    assert db_dump(database) == before


def test_binding_sql_history_is_immutable_including_replace(database):
    seed_ru_school2022_step10a_binding(database)
    with sqlite3.connect(database.path) as db:
        row = db.execute(
            f"""
            SELECT recipe_ingredient_id, composition_version_id, registry_version,
                   nutrient_set_version, composition_calculation_version,
                   recipe_calculation_version, created_at
            FROM {TABLE}
            """
        ).fetchone()
        assert row is not None

        with pytest.raises(sqlite3.IntegrityError, match="неизменяем"):
            db.execute(
                f"UPDATE {TABLE} SET nutrient_set_version=nutrient_set_version"
            )
        db.rollback()

        with pytest.raises(sqlite3.IntegrityError, match="неизменяем"):
            db.execute(f"DELETE FROM {TABLE}")
        db.rollback()

        with pytest.raises(sqlite3.IntegrityError, match="неизменяем"):
            db.execute(
                f"""
                INSERT OR REPLACE INTO {TABLE} (
                    recipe_ingredient_id, composition_version_id, registry_version,
                    nutrient_set_version, composition_calculation_version,
                    recipe_calculation_version, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                row,
            )
        db.rollback()

        assert db.execute(f"SELECT COUNT(*) FROM {TABLE}").fetchone()[0] == 1


def test_binding_rejects_wrong_food_composition_relation(database):
    with sqlite3.connect(database.path) as db:
        recipe_row = db.execute(
            """
            SELECT ri.id, ri.food_ingredient_id
            FROM food_recipe_ingredients ri
            JOIN food_recipe_versions rv ON rv.id = ri.recipe_version_id
            JOIN food_recipes r ON r.id = rv.recipe_id
            WHERE r.canonical_code=?
            """,
            (RECIPE_CODE,),
        ).fetchone()
        assert recipe_row is not None
        wrong = db.execute(
            """
            SELECT id FROM food_composition_versions
            WHERE food_ingredient_id != ?
            LIMIT 1
            """,
            (recipe_row[1],),
        ).fetchone()
        assert wrong is not None

        with pytest.raises(sqlite3.IntegrityError, match="разным FoodIngredient"):
            db.execute(
                f"""
                INSERT INTO {TABLE} (
                    recipe_ingredient_id, composition_version_id, registry_version,
                    nutrient_set_version, composition_calculation_version,
                    recipe_calculation_version, created_at
                ) VALUES (?, ?, 'RU_NUTRIENT_REGISTRY_V2',
                          'RECIPE_V2_NUTRIENT_SET_V1',
                          'FOOD_COMPOSITION_APPLICABILITY_V2',
                          'RECIPE_COMPOSITION_NUTRITION_V1',
                          '2026-09-26 00:00:00.000000')
                """,
                (recipe_row[0], wrong[0]),
            )
        db.rollback()


def test_binding_rejects_wrong_authority_version(database):
    with sqlite3.connect(database.path) as db:
        recipe_row = db.execute(
            """
            SELECT ri.id, ri.food_ingredient_id
            FROM food_recipe_ingredients ri
            JOIN food_recipe_versions rv ON rv.id = ri.recipe_version_id
            JOIN food_recipes r ON r.id = rv.recipe_id
            WHERE r.canonical_code=?
            """,
            (RECIPE_CODE,),
        ).fetchone()
        composition = db.execute(
            """
            SELECT id FROM food_composition_versions
            WHERE food_ingredient_id=? AND version=1
            """,
            (recipe_row[1],),
        ).fetchone()
        with pytest.raises(sqlite3.IntegrityError):
            db.execute(
                f"""
                INSERT INTO {TABLE} (
                    recipe_ingredient_id, composition_version_id, registry_version,
                    nutrient_set_version, composition_calculation_version,
                    recipe_calculation_version, created_at
                ) VALUES (?, ?, 'RU_NUTRIENT_REGISTRY_V2',
                          'WRONG_SET',
                          'FOOD_COMPOSITION_APPLICABILITY_V2',
                          'RECIPE_COMPOSITION_NUTRITION_V1',
                          '2026-09-26 00:00:00.000000')
                """,
                (recipe_row[0], composition[0]),
            )
        db.rollback()
