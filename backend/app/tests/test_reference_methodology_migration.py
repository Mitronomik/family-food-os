import hashlib
import shutil
import sqlite3
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.db import migrations
from app.db.config import DatabaseConfig
from app.db.migrations import apply_migrations, current_migrations, expected_migration_ids


MIGRATION_ID = "0036_member_reference_methodology_selection"
PREVIOUS_HEAD = "0035_versioned_nutrient_registry"
TABLE = "member_reference_methodology_selections"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def migrate_through_0035(path):
    config = DatabaseConfig(path=path)
    original = list(migrations.MIGRATION_MODULES)
    cutoff = next(
        index
        for index, module_name in enumerate(original)
        if module_name.endswith(PREVIOUS_HEAD)
    )
    try:
        migrations.MIGRATION_MODULES[:] = original[: cutoff + 1]
        assert apply_migrations(config)[-1] == PREVIOUS_HEAD
    finally:
        migrations.MIGRATION_MODULES[:] = original
    return config


def seed_household(path):
    household_id = uuid4().hex
    member_id = uuid4().hex
    now = datetime(2026, 9, 23, 10, 0, tzinfo=timezone.utc).isoformat()
    with sqlite3.connect(path) as connection:
        connection.execute(
            """
            INSERT INTO households (
                id, name, timezone, city, default_weekly_budget,
                default_cooking_profile, created_at, updated_at
            ) VALUES (?, 'Home', 'Europe/Moscow', NULL, NULL, NULL, ?, ?)
            """,
            (household_id, now, now),
        )
        connection.execute(
            """
            INSERT INTO household_members (
                id, household_id, name, active, birth_date, sex,
                height_cm, weight_kg, activity_level, goal,
                created_at, updated_at
            ) VALUES (?, ?, 'Anna', 1, '1990-05-20', 'female',
                      NULL, NULL, 'moderate', 'maintain', ?, ?)
            """,
            (member_id, household_id, now, now),
        )
    return household_id, member_id


def existing_rows(path):
    with sqlite3.connect(path) as connection:
        return {
            "households": connection.execute(
                "SELECT * FROM households ORDER BY id"
            ).fetchall(),
            "household_members": connection.execute(
                "SELECT * FROM household_members ORDER BY id"
            ).fetchall(),
            "meal_plans": connection.execute(
                "SELECT * FROM meal_plans ORDER BY id"
            ).fetchall(),
            "nutrition_vector_seals": connection.execute(
                "SELECT * FROM nutrition_vector_seals ORDER BY profile_id"
            ).fetchall(),
        }


def test_0036_is_appended_after_0035_and_0033_remains_reserved():
    expected = expected_migration_ids()

    assert expected[-2:] == [PREVIOUS_HEAD, MIGRATION_ID]
    assert not any(value.startswith("0033_") for value in expected)


def test_populated_0035_upgrade_preserves_existing_state_and_restore_reupgrades(
    tmp_path,
):
    database = tmp_path / "upgrade.sqlite"
    config = migrate_through_0035(database)
    seed_household(database)
    before = existing_rows(database)
    backup = tmp_path / "pre-0036.sqlite"
    shutil.copy2(database, backup)
    backup_digest = digest(backup)

    assert MIGRATION_ID not in current_migrations(config)
    assert apply_migrations(config) == [MIGRATION_ID]
    assert existing_rows(database) == before
    assert apply_migrations(config) == []

    with sqlite3.connect(database) as connection:
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        assert connection.execute(f"SELECT COUNT(*) FROM {TABLE}").fetchone() == (
            0,
        )
        history = [
            row[0]
            for row in connection.execute(
                "SELECT migration_id FROM schema_migrations ORDER BY rowid"
            )
        ]
    assert history[-2:] == [PREVIOUS_HEAD, MIGRATION_ID]

    shutil.copy2(backup, database)
    assert digest(database) == backup_digest
    assert MIGRATION_ID not in current_migrations(config)
    assert existing_rows(database) == before

    assert apply_migrations(config) == [MIGRATION_ID]
    assert existing_rows(database) == before


def test_actual_0036_failure_rolls_back_table_and_marker(tmp_path):
    database = tmp_path / "rollback.sqlite"
    config = migrate_through_0035(database)
    seed_household(database)

    with sqlite3.connect(database) as connection:
        connection.execute(
            "CREATE TRIGGER trg_member_reference_methodology_no_update "
            "BEFORE UPDATE ON households BEGIN SELECT 1; END"
        )
        connection.commit()

    with pytest.raises(sqlite3.OperationalError, match="already exists"):
        apply_migrations(config)

    assert MIGRATION_ID not in current_migrations(config)
    with sqlite3.connect(database) as connection:
        assert connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (TABLE,),
        ).fetchone() is None
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []


def test_fresh_database_has_0036_schema_and_immutability_triggers(tmp_path):
    config = DatabaseConfig(path=tmp_path / "fresh.sqlite")
    assert apply_migrations(config) == expected_migration_ids()

    with sqlite3.connect(config.path) as connection:
        columns = {
            row[1]
            for row in connection.execute(f"PRAGMA table_info({TABLE})")
        }
        trigger_names = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type='trigger' AND name LIKE 'trg_member_reference_methodology_%'"
            )
        }
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []

    assert {
        "id",
        "household_id",
        "member_id",
        "version_number",
        "nutrition_config_version",
        "group_reference_methodology_version",
        "accepted_local_date",
        "household_timezone_at_acceptance",
        "member_updated_at_at_acceptance",
        "household_updated_at_at_acceptance",
        "acceptance_request_id",
        "accepted_at",
        "supersedes_selection_id",
        "created_at",
    } == columns
    assert trigger_names == {
        "trg_member_reference_methodology_no_update",
        "trg_member_reference_methodology_no_delete",
    }
