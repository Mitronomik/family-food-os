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


def through_0038(path):
    original = list(migrations.MIGRATION_MODULES)
    config = DatabaseConfig(path=path)
    try:
        migrations.MIGRATION_MODULES[:] = [
            name
            for name in original
            if not name.endswith("0039_recipe_ingredient_composition_binding")
        ]
        apply_migrations(config)
    finally:
        migrations.MIGRATION_MODULES[:] = original
    return config


def test_0039_is_current_head_and_creates_only_bounded_table(tmp_path):
    config = through_0038(tmp_path / "upgrade.sqlite")
    before = set(current_migrations(config))
    assert MIGRATION_ID not in before

    assert apply_migrations(config) == [MIGRATION_ID]
    assert current_migrations(config) == set(migrations.expected_migration_ids())

    with sqlite3.connect(config.path) as db:
        columns = {
            row[1]: row[2] for row in db.execute(f"PRAGMA table_info({TABLE})")
        }
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
        assert db.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (TABLE,)
        ).fetchone() is None
        assert db.execute(
            "SELECT 1 FROM sqlite_master WHERE type='trigger' AND name=?",
            (f"{TABLE}_no_update",),
        ).fetchone() == (1,)
        assert db.execute("PRAGMA foreign_key_check").fetchall() == []
