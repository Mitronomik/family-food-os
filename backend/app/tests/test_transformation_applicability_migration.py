"""Migration 0038 fresh/populated/failure/restore contract tests."""

import shutil
import sqlite3

import pytest

from app.db import migrations
from app.db.config import DatabaseConfig
from app.db.migrations import apply_migrations, current_migrations, expected_migration_ids
from app.seed.food_ingredients import seed_food_ingredients
from scripts.audit_pr6_nutrient_vector_b import snapshot

MIGRATION_ID = "0038_transformation_applicability"
PREVIOUS_HEAD = "0037_meal_plan_reference_methodology_pins"
TABLE = "food_transformation_applicability"


def through_0037(path, *, seed=False):
    config = DatabaseConfig(path=path)
    original = list(migrations.MIGRATION_MODULES)
    cutoff = next(
        index
        for index, module_name in enumerate(original)
        if module_name.endswith(PREVIOUS_HEAD)
    )
    try:
        migrations.MIGRATION_MODULES[:] = original[: cutoff + 1]
        if seed:
            seed_food_ingredients(config)
        else:
            assert apply_migrations(config)[-1] == PREVIOUS_HEAD
    finally:
        migrations.MIGRATION_MODULES[:] = original
    return config


def test_0038_appends_after_0037_without_consuming_reserved_0033():
    expected = expected_migration_ids()
    assert expected[-3:] == [
        PREVIOUS_HEAD,
        MIGRATION_ID,
        "0039_recipe_ingredient_composition_binding",
    ]
    assert not any(value.startswith("0033_") for value in expected)


def test_populated_0037_upgrade_preserves_every_existing_row(tmp_path):
    config = through_0037(tmp_path / "populated.sqlite", seed=True)
    before = snapshot(config)

    assert apply_migrations(config) == [
        MIGRATION_ID,
        "0039_recipe_ingredient_composition_binding",
    ]

    after = snapshot(config)
    assert all(after[name] == rows for name, rows in before.items())
    with sqlite3.connect(config.path) as db:
        assert db.execute(f"SELECT count(*) FROM {TABLE}").fetchone() == (0,)
        assert db.execute("PRAGMA foreign_key_check").fetchall() == []


def test_fresh_schema_has_exact_table_checks_and_triggers(tmp_path):
    config = DatabaseConfig(path=tmp_path / "fresh.sqlite")
    assert apply_migrations(config) == expected_migration_ids()

    with sqlite3.connect(config.path) as db:
        columns = {
            row[1]: row[2] for row in db.execute(f"PRAGMA table_info({TABLE})")
        }
        triggers = {
            row[0]
            for row in db.execute(
                """
                SELECT name FROM sqlite_master
                WHERE type='trigger'
                  AND (
                    name LIKE 'food_transformation_applicability_%'
                    OR name = 'food_retention_values_single_registry'
                  )
                """
            )
        }
        assert db.execute("PRAGMA foreign_key_check").fetchall() == []

    assert columns == {
        "transformation_id": "CHAR(32)",
        "food_ingredient_id": "CHAR(32)",
        "retention_registry_version": "TEXT",
        "season_scope": "TEXT",
        "season_reference": "TEXT",
        "evidence_scope_id": "TEXT",
        "provenance_json": "TEXT",
        "snapshot_sha256": "TEXT",
    }
    assert triggers == {
        "food_transformation_applicability_no_update",
        "food_transformation_applicability_no_delete",
        "food_transformation_applicability_no_replace",
        "food_transformation_applicability_no_late_insert",
        "food_transformation_applicability_retention_binding",
        "food_retention_values_single_registry",
    }


def test_injected_0038_failure_rolls_back_table_triggers_and_marker(tmp_path):
    config = through_0037(tmp_path / "failure.sqlite")
    with sqlite3.connect(config.path) as db:
        db.execute(
            """
            CREATE TRIGGER food_transformation_applicability_no_delete
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
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (TABLE,),
        ).fetchone() is None
        assert db.execute(
            """
            SELECT name FROM sqlite_master
            WHERE type='trigger'
              AND name='food_transformation_applicability_no_update'
            """
        ).fetchone() is None
        assert db.execute("PRAGMA foreign_key_check").fetchall() == []


def test_backup_restore_and_reupgrade_are_deterministic(tmp_path):
    database = tmp_path / "restore.sqlite"
    config = through_0037(database, seed=True)
    backup = tmp_path / "pre-0038.sqlite"
    shutil.copy2(database, backup)
    before = snapshot(config)

    assert apply_migrations(config) == [
        MIGRATION_ID,
        "0039_recipe_ingredient_composition_binding",
    ]
    after = snapshot(config)
    assert all(after[name] == rows for name, rows in before.items())

    shutil.copy2(backup, database)
    assert MIGRATION_ID not in current_migrations(config)
    assert apply_migrations(config) == [
        MIGRATION_ID,
        "0039_recipe_ingredient_composition_binding",
    ]
    restored = snapshot(config)
    assert all(restored[name] == rows for name, rows in before.items())
    with sqlite3.connect(database) as db:
        assert db.execute("PRAGMA foreign_key_check").fetchall() == []
