import sqlite3

import pytest

from app.db.config import DatabaseConfig
from app.db.connection import session
from app.db.migration_lineage import REQUIRED_TABLES_BY_MIGRATION
from app.db.migrations import (
    MIGRATION_MODULES,
    apply_migrations,
    expected_migration_ids,
)
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
from app.persistence.sqlalchemy_core.household_composition import (
    create_household_service,
)
from app.seed.food_recipes import seed_food_recipes


@pytest.mark.parametrize("upgrade", [False, True])
def test_0025_fresh_and_upgrade_preserve_previous_schema(tmp_path, upgrade):
    config = DatabaseConfig(path=tmp_path / "pantry.sqlite")
    before = {}
    previous_rows = {}
    previous_history = []
    if upgrade:
        original = list(MIGRATION_MODULES)
        try:
            MIGRATION_MODULES[:] = original[:24]
            assert apply_migrations(config)[-1] == "0024_food_recipe_catalogue"
            seed_food_recipes(config)
            seed_engine = create_sqlite_engine(config)
            try:
                create_household_service(seed_engine).create_household(
                    name="Migration fixture household",
                    timezone_name="Europe/Moscow",
                    default_weekly_budget="12345.67",
                )
            finally:
                seed_engine.dispose()
        finally:
            MIGRATION_MODULES[:] = original
        with sqlite3.connect(config.path) as connection:
            before = {
                row[0]: row[1:]
                for row in connection.execute(
                    "SELECT name, type, tbl_name, sql FROM sqlite_master"
                )
            }
            previous_tables = [
                row[0]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name != 'schema_migrations'"
                )
            ]
            previous_rows = {
                table: sorted(
                    connection.execute(f'SELECT * FROM "{table}"').fetchall(), key=repr
                )
                for table in previous_tables
            }
            previous_history = connection.execute(
                "SELECT * FROM schema_migrations ORDER BY rowid"
            ).fetchall()
            assert len(previous_rows["households"]) == 1
            assert len(previous_rows["food_recipes"]) == 30
            assert len(previous_rows["food_recipe_versions"]) == 30
            assert len(previous_rows["food_recipe_ingredients"]) == 189
            assert previous_rows["food_ingredients"]
            assert previous_rows["food_nutrition_profiles"]
    applied = apply_migrations(config)
    assert applied == (["0025_pantry"] if upgrade else expected_migration_ids())
    assert apply_migrations(config) == []
    with sqlite3.connect(config.path) as connection:
        after = {
            row[0]: row[1:]
            for row in connection.execute(
                "SELECT name, type, tbl_name, sql FROM sqlite_master"
            )
        }
        for name, definition in before.items():
            assert after[name] == definition
        for table, rows in previous_rows.items():
            assert (
                sorted(
                    connection.execute(f'SELECT * FROM "{table}"').fetchall(), key=repr
                )
                == rows
            )
        if upgrade:
            history = connection.execute(
                "SELECT * FROM schema_migrations ORDER BY rowid"
            ).fetchall()
            assert history[:-1] == previous_history
            assert history[-1][0] == "0025_pantry"
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        assert {"pantry_items", "pantry_movements"} <= tables
        assert not {"pantry_lots", "meal_plans", "servings", "retail_skus"} & tables
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        assert (
            len(
                connection.execute(
                    "SELECT name FROM sqlite_master WHERE type='trigger' AND tbl_name='pantry_movements'"
                ).fetchall()
            )
            == 2
        )
        targets = {
            row[2]
            for row in connection.execute("PRAGMA foreign_key_list(pantry_items)")
        }
        assert targets == {"households", "food_ingredients"}
        movement_fks = connection.execute(
            "PRAGMA foreign_key_list(pantry_movements)"
        ).fetchall()
        assert {row[3] for row in movement_fks if row[2] == "pantry_items"} == {
            "pantry_item_id",
            "household_id",
            "unit",
        }
    with session(config) as connection:
        assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1
    engine = create_sqlite_engine(config)
    try:
        with engine.connect() as connection:
            assert connection.exec_driver_sql("PRAGMA foreign_keys").scalar_one() == 1
    finally:
        engine.dispose()


def test_0025_registration_and_restore_required_tables():
    assert expected_migration_ids()[-2:] == [
        "0024_food_recipe_catalogue",
        "0025_pantry",
    ]
    assert expected_migration_ids().count("0025_pantry") == 1
    assert REQUIRED_TABLES_BY_MIGRATION["0025_pantry"] == frozenset(
        {"pantry_items", "pantry_movements"}
    )


@pytest.fixture(autouse=True)
def pantry_migration_boundary():
    """Retain this historical 0024→0025 test; B1 separately verifies 0025→0026."""
    original = MIGRATION_MODULES[:]
    MIGRATION_MODULES[:] = original[:25]
    try:
        yield
    finally:
        MIGRATION_MODULES[:] = original
