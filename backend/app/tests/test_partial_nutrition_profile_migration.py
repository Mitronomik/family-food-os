import hashlib
import shutil
import sqlite3

import pytest

from app.db import migrations
from app.db.config import DatabaseConfig
from app.db.migrations import apply_migrations, current_migrations, expected_migration_ids
from app.seed.food_ingredients import seed_food_ingredients

MIGRATION_ID = "0034_partial_nutrition_profiles"
PREVIOUS_HEAD = "0032_meal_plan_serving"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def seed_pre_partial_profile_database(path):
    config = DatabaseConfig(path=path)
    original = list(migrations.MIGRATION_MODULES)
    cutoff = next(
        index
        for index, module_name in enumerate(original)
        if module_name.endswith(PREVIOUS_HEAD)
    )
    try:
        migrations.MIGRATION_MODULES[:] = original[: cutoff + 1]
        seed_food_ingredients(config)
    finally:
        migrations.MIGRATION_MODULES[:] = original
    return config


def profile_rows(path):
    with sqlite3.connect(path) as connection:
        return connection.execute(
            """
            SELECT
                id,
                food_ingredient_id,
                basis_grams,
                kcal,
                protein_g,
                fat_g,
                carbohydrates_g,
                fiber_g,
                source_name,
                source_id,
                source_version,
                source_data_type,
                verified_at,
                estimated,
                is_current,
                created_at
            FROM food_nutrition_profiles
            ORDER BY id
            """
        ).fetchall()


def vector_rows(path):
    with sqlite3.connect(path) as connection:
        seals = connection.execute(
            """
            SELECT profile_id, registry_version, value_count, value_sha256, observations_json
            FROM nutrition_vector_seals
            ORDER BY profile_id
            """
        ).fetchall()
        values = connection.execute(
            """
            SELECT profile_id, nutrient_code, amount, provenance_json
            FROM nutrient_values
            ORDER BY profile_id, nutrient_code
            """
        ).fetchall()
    return seals, values


def column_notnull(path, column):
    with sqlite3.connect(path) as connection:
        rows = connection.execute(
            "PRAGMA table_info(food_nutrition_profiles)"
        ).fetchall()
    return next(row[3] for row in rows if row[1] == column)


def test_0033_remains_reserved_while_partial_profiles_use_0034():
    expected = expected_migration_ids()

    assert expected[-3:] == [
        PREVIOUS_HEAD,
        MIGRATION_ID,
        "0035_versioned_nutrient_registry",
    ]
    assert not any(value.startswith("0033_") for value in expected)


def test_populated_0032_database_upgrades_without_rewriting_profiles_or_vectors(
    tmp_path,
):
    database = tmp_path / "upgrade.sqlite"
    config = seed_pre_partial_profile_database(database)
    before_profiles = profile_rows(database)
    before_seals, before_values = vector_rows(database)
    backup = tmp_path / "pre-0034-backup.sqlite"
    shutil.copy2(database, backup)
    backup_digest = digest(backup)

    assert MIGRATION_ID not in current_migrations(config)
    assert column_notnull(database, "kcal") == 1
    assert column_notnull(database, "protein_g") == 1
    assert column_notnull(database, "fat_g") == 1
    assert column_notnull(database, "carbohydrates_g") == 1

    assert apply_migrations(config) == [MIGRATION_ID]

    assert profile_rows(database) == before_profiles
    assert vector_rows(database) == (before_seals, before_values)
    assert column_notnull(database, "kcal") == 0
    assert column_notnull(database, "protein_g") == 0
    assert column_notnull(database, "fat_g") == 0
    assert column_notnull(database, "carbohydrates_g") == 0

    with sqlite3.connect(database) as connection:
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        assert connection.execute(
            "SELECT count(*) FROM food_nutrition_profile_observations"
        ).fetchone() == (0,)
        history = [
            row[0]
            for row in connection.execute(
                "SELECT migration_id FROM schema_migrations ORDER BY rowid"
            )
        ]
        trigger_sql = connection.execute(
            """
            SELECT sql
            FROM sqlite_master
            WHERE type = 'trigger'
              AND name = 'food_composition_versions_complete'
            """
        ).fetchone()[0]
    assert history[-1] == MIGRATION_ID
    assert "food_nutrition_profiles" in trigger_sql
    assert "food_composition_versions" in trigger_sql

    # Operational recovery proof: restore the exact pre-migration database copy.
    shutil.copy2(backup, database)
    assert digest(database) == backup_digest
    assert MIGRATION_ID not in current_migrations(config)
    assert column_notnull(database, "protein_g") == 1
    assert profile_rows(database) == before_profiles
    assert vector_rows(database) == (before_seals, before_values)

    # The restored copy remains upgradeable through the same migration.
    assert apply_migrations(config) == [MIGRATION_ID]
    assert profile_rows(database) == before_profiles
    assert vector_rows(database) == (before_seals, before_values)


def test_actual_0034_failure_rolls_back_rebuild_and_marker(tmp_path):
    database = tmp_path / "rollback.sqlite"
    config = seed_pre_partial_profile_database(database)
    before_profiles = profile_rows(database)

    # Force the real migration to fail after it has started rebuilding the
    # profile table. The runner must roll back schema, data and migration marker.
    with sqlite3.connect(database) as connection:
        connection.execute(
            "CREATE TABLE food_nutrition_profile_observations (id TEXT PRIMARY KEY)"
        )
        connection.commit()

    with pytest.raises(sqlite3.OperationalError, match="already exists"):
        apply_migrations(config)

    assert MIGRATION_ID not in current_migrations(config)
    assert profile_rows(database) == before_profiles
    assert column_notnull(database, "protein_g") == 1
    with sqlite3.connect(database) as connection:
        assert connection.execute(
            """
            SELECT name FROM sqlite_master
            WHERE type = 'table' AND name = 'food_nutrition_profiles_new'
            """
        ).fetchone() is None
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
