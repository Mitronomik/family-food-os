"""Migration 0039: immutable RecipeIngredient → Composition authority binding."""

import sqlite3

import pytest

from app.db import migrations
from app.db.config import DatabaseConfig
from app.db.migrations import apply_migrations, current_migrations
from app.seed.food_recipes import seed_food_recipes
from app.seed.ru_nut_db_step8_butter import seed_ru_nut_db_step8_butter
from app.seed.ru_school2022_step9_recipe import seed_ru_school2022_step9_recipe

MIGRATION_ID = "0039_recipe_ingredient_composition_binding"
TABLE = "recipe_ingredient_composition_bindings"


def through_0038(path, *, seed=False):
    original = list(migrations.MIGRATION_MODULES)
    config = DatabaseConfig(path=path)
    try:
        migrations.MIGRATION_MODULES[:] = [
            name
            for name in original
            if not name.endswith(
                (
                    "0039_recipe_ingredient_composition_binding",
                    "0040_recipe_version_source_output",
                )
            )
        ]
        apply_migrations(config)
        if seed:
            seed_food_recipes(config)
            seed_ru_nut_db_step8_butter(config)
            seed_ru_school2022_step9_recipe(config)
    finally:
        migrations.MIGRATION_MODULES[:] = original
    return config


def test_0039_and_0040_create_only_their_bounded_schema(tmp_path):
    config = through_0038(tmp_path / "upgrade.sqlite")
    before = set(current_migrations(config))
    assert MIGRATION_ID not in before

    assert apply_migrations(config) == [
        MIGRATION_ID,
        "0040_recipe_version_source_output",
    ]
    assert current_migrations(config) == set(migrations.expected_migration_ids())

    with sqlite3.connect(config.path) as db:
        columns = {row[1]: row[2] for row in db.execute(f"PRAGMA table_info({TABLE})")}
        triggers = {
            row[0]
            for row in db.execute(
                "SELECT name FROM sqlite_master WHERE type='trigger' AND name LIKE ?",
                (f"{TABLE}_%",),
            )
        }
        assert db.execute("PRAGMA foreign_key_check").fetchall() == []

    assert columns == {
        "recipe_ingredient_id": "CHAR(32)",
        "composition_version_id": "CHAR(32)",
        "registry_version": "TEXT",
        "nutrient_set_version": "TEXT",
        "composition_calculation_version": "TEXT",
        "recipe_calculation_version": "TEXT",
        "created_at": "DATETIME",
    }
    assert triggers == {
        f"{TABLE}_food_match",
        f"{TABLE}_no_update",
        f"{TABLE}_no_delete",
        f"{TABLE}_no_replace",
    }


def test_populated_0038_upgrade_preserves_recipe_and_nutrition_history(tmp_path):
    config = through_0038(tmp_path / "populated.sqlite", seed=True)
    tables = (
        "food_recipes",
        "food_recipe_versions",
        "food_recipe_ingredients",
        "food_recipe_steps",
        "food_ingredients",
        "food_nutrition_profiles",
        "nutrient_values",
        "nutrition_vector_seals",
        "food_composition_versions",
    )
    with sqlite3.connect(config.path) as db:
        before = {
            table: db.execute(f'SELECT * FROM "{table}" ORDER BY rowid').fetchall()
            for table in tables
        }
        assert (
            db.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (TABLE,)
            ).fetchone()
            is None
        )

    assert apply_migrations(config) == [
        MIGRATION_ID,
        "0040_recipe_version_source_output",
    ]

    with sqlite3.connect(config.path) as db:
        after = {
            table: db.execute(f'SELECT * FROM "{table}" ORDER BY rowid').fetchall()
            for table in tables
        }
        for table in tables:
            if table == "food_recipe_versions":
                assert [row[:-2] for row in after[table]] == before[table]
                assert all(row[-2:] == (None, None) for row in after[table])
            else:
                assert after[table] == before[table]
        assert db.execute(f"SELECT COUNT(*) FROM {TABLE}").fetchone() == (0,)
        assert db.execute("PRAGMA foreign_key_check").fetchall() == []


def test_0039_failure_is_atomic(tmp_path):
    config = through_0038(tmp_path / "failure.sqlite")
    with sqlite3.connect(config.path) as db:
        db.execute(
            f"""
            CREATE TRIGGER {TABLE}_no_update
            BEFORE UPDATE ON households
            BEGIN SELECT 1; END
            """
        )
        db.commit()

    with pytest.raises(sqlite3.OperationalError, match="already exists"):
        apply_migrations(config)

    assert MIGRATION_ID not in current_migrations(config)
    with sqlite3.connect(config.path) as db:
        assert (
            db.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (TABLE,)
            ).fetchone()
            is None
        )
        assert db.execute(
            "SELECT 1 FROM sqlite_master WHERE type='trigger' AND name=?",
            (f"{TABLE}_no_update",),
        ).fetchone() == (1,)
        assert db.execute("PRAGMA foreign_key_check").fetchall() == []
