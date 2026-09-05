import sqlite3

import pytest

from app.db.config import DatabaseConfig
from app.db.migrations import (
    MIGRATION_MODULES,
    apply_migrations,
    expected_migration_ids,
)

RECIPE_TABLES = {
    "food_recipes",
    "food_recipe_versions",
    "food_recipe_ingredients",
    "food_recipe_steps",
    "food_recipe_equipment",
}


def _migrate_through(database_path, suffix):
    original = list(MIGRATION_MODULES)
    cutoff = next(
        index for index, module in enumerate(original) if module.endswith(suffix)
    )
    try:
        MIGRATION_MODULES[:] = original[: cutoff + 1]
        return apply_migrations(DatabaseConfig(path=database_path))
    finally:
        MIGRATION_MODULES[:] = original


def _table_shape(connection, table):
    return connection.execute(f"PRAGMA table_info('{table}')").fetchall()


def test_migration_chain_appends_0024_after_0023():
    assert expected_migration_ids()[-2:] == [
        "0023_food_ingredient_catalogue",
        "0024_food_recipe_catalogue",
    ]


def test_fresh_database_migrates_through_0024_without_future_tables(tmp_path):
    database = tmp_path / "fresh.sqlite"
    assert apply_migrations(DatabaseConfig(path=database)) == expected_migration_ids()
    with sqlite3.connect(database) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
    assert RECIPE_TABLES <= tables
    assert not {"pantry_items", "meal_plans", "servings", "retail_skus"} & tables


def test_0023_to_0024_preserves_legacy_household_and_food_catalogue_shapes(tmp_path):
    database = tmp_path / "upgrade.sqlite"
    _migrate_through(database, "0023_food_ingredient_catalogue")
    preserved = (
        "ingredients",
        "recipe_templates",
        "recipe_versions",
        "recipe_ingredients",
        "households",
        "household_members",
        "food_ingredients",
        "food_ingredient_aliases",
        "food_nutrition_profiles",
        "food_ingredient_allergens",
    )
    with sqlite3.connect(database) as connection:
        before = {table: _table_shape(connection, table) for table in preserved}
    assert apply_migrations(DatabaseConfig(path=database)) == [
        "0024_food_recipe_catalogue"
    ]
    with sqlite3.connect(database) as connection:
        assert {table: _table_shape(connection, table) for table in preserved} == before


@pytest.mark.parametrize(
    "table",
    [
        "food_recipe_versions",
        "food_recipe_ingredients",
        "food_recipe_steps",
        "food_recipe_equipment",
    ],
)
def test_version_owned_tables_have_update_and_delete_guards(tmp_path, table):
    database = tmp_path / "triggers.sqlite"
    apply_migrations(DatabaseConfig(path=database))
    with sqlite3.connect(database) as connection:
        names = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='trigger' AND tbl_name=?",
                (table,),
            )
        }
    assert any(name.endswith("no_update") for name in names)
    assert any(name.endswith("no_delete") for name in names)


def test_recipe_ingredient_foreign_key_targets_food_ingredients(tmp_path):
    database = tmp_path / "foreign-keys.sqlite"
    apply_migrations(DatabaseConfig(path=database))
    with sqlite3.connect(database) as connection:
        targets = {
            row[2]
            for row in connection.execute(
                "PRAGMA foreign_key_list(food_recipe_ingredients)"
            )
        }
    assert "food_ingredients" in targets
    assert "ingredients" not in targets
