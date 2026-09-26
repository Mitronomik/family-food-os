import hashlib
import shutil
import sqlite3
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.db import migrations
from app.db.config import DatabaseConfig
from app.db.migrations import apply_migrations, current_migrations, expected_migration_ids


MIGRATION_ID = "0037_meal_plan_reference_methodology_pins"
PREVIOUS_HEAD = "0036_member_reference_methodology_selection"
TABLE = "meal_plan_member_reference_methodology_pins"


def _digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _through_0036(path):
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


def _seed_legacy_plan(path):
    household_id = uuid4().hex
    member_id = uuid4().hex
    selection_id = uuid4().hex
    plan_id = uuid4().hex
    now = datetime(2026, 9, 23, 10, 0, tzinfo=timezone.utc).isoformat()
    with sqlite3.connect(path) as db:
        db.execute(
            "INSERT INTO households VALUES (?, 'Home', 'Europe/Moscow', NULL, NULL, NULL, ?, ?)",
            (household_id, now, now),
        )
        db.execute(
            """
            INSERT INTO household_members (
                id, household_id, name, active, birth_date, sex,
                height_cm, weight_kg, activity_level, goal, created_at, updated_at
            ) VALUES (?, ?, 'Anna', 1, '1990-05-20', 'female',
                      '168.000', '62.000', 'moderate', 'maintain', ?, ?)
            """,
            (member_id, household_id, now, now),
        )
        db.execute(
            """
            INSERT INTO member_meal_pattern_selections (
                id, household_id, member_id, version_number, source_kind,
                program_version_id, recommender_version, has_user_overrides,
                accepted_at, supersedes_selection_id, created_at
            ) VALUES (?, ?, ?, 1, 'CUSTOM', NULL, NULL, 0, ?, NULL, ?)
            """,
            (selection_id, household_id, member_id, now, now),
        )
        for weekday in range(1, 8):
            db.execute(
                """
                INSERT INTO member_meal_pattern_opportunities
                    (selection_id, weekday, position, role_code)
                VALUES (?, ?, 1, 'DINNER')
                """,
                (selection_id, weekday),
            )
        db.execute(
            """
            INSERT INTO meal_plans (
                id, household_id, week_start, revision_number, status,
                config_version, supersedes_plan_id, created_at
            ) VALUES (?, ?, '2026-09-14', 1, 'CONFIRMED',
                      'manual-v1', NULL, ?)
            """,
            (plan_id, household_id, now),
        )
        db.execute(
            "INSERT INTO meal_plan_member_selections VALUES (?, ?, ?)",
            (plan_id, member_id, selection_id),
        )
    return plan_id


def test_0037_appends_after_0036_without_consuming_0033():
    expected = expected_migration_ids()
    position = expected.index(PREVIOUS_HEAD)
    assert expected[position : position + 2] == [PREVIOUS_HEAD, MIGRATION_ID]
    assert expected[-2:] == [
        "0038_transformation_applicability",
        "0039_recipe_ingredient_composition_binding",
    ]
    assert not any(value.startswith("0033_") for value in expected)


def test_populated_0036_upgrade_preserves_legacy_plan_without_backfill(tmp_path):
    database = tmp_path / "upgrade.sqlite"
    config = _through_0036(database)
    plan_id = _seed_legacy_plan(database)
    backup = tmp_path / "pre-0037.sqlite"
    shutil.copy2(database, backup)
    before_digest = _digest(backup)

    assert apply_migrations(config) == [
        MIGRATION_ID,
        "0038_transformation_applicability",
        "0039_recipe_ingredient_composition_binding",
    ]
    with sqlite3.connect(database) as db:
        assert db.execute("PRAGMA foreign_key_check").fetchall() == []
        assert db.execute(f"SELECT count(*) FROM {TABLE}").fetchone() == (0,)
        assert db.execute(
            "SELECT id FROM meal_plans WHERE id = ?", (plan_id,)
        ).fetchone() == (plan_id,)
    assert apply_migrations(config) == []

    shutil.copy2(backup, database)
    assert _digest(database) == before_digest
    assert MIGRATION_ID not in current_migrations(config)
    assert apply_migrations(config) == [
        MIGRATION_ID,
        "0038_transformation_applicability",
        "0039_recipe_ingredient_composition_binding",
    ]


def test_actual_0037_failure_rolls_back_table_and_marker(tmp_path):
    database = tmp_path / "rollback.sqlite"
    config = _through_0036(database)
    with sqlite3.connect(database) as db:
        db.execute(
            """
            CREATE TRIGGER trg_meal_plan_reference_methodology_pins_no_update
            BEFORE UPDATE ON households BEGIN SELECT 1; END
            """
        )
        db.commit()

    with pytest.raises(sqlite3.OperationalError, match="already exists"):
        apply_migrations(config)

    assert MIGRATION_ID not in current_migrations(config)
    with sqlite3.connect(database) as db:
        assert db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (TABLE,),
        ).fetchone() is None
        assert db.execute("PRAGMA foreign_key_check").fetchall() == []


def test_fresh_database_has_exact_0037_table_and_immutability(tmp_path):
    config = DatabaseConfig(path=tmp_path / "fresh.sqlite")
    assert apply_migrations(config) == expected_migration_ids()

    with sqlite3.connect(config.path) as db:
        columns = {row[1] for row in db.execute(f"PRAGMA table_info({TABLE})")}
        triggers = {
            row[0]
            for row in db.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type='trigger' "
                "AND name LIKE 'trg_meal_plan_reference_methodology_pins_%'"
            )
        }
        assert db.execute("PRAGMA foreign_key_check").fetchall() == []

    assert columns == {
        "plan_id",
        "member_id",
        "reference_methodology_selection_id",
        "birth_date",
        "sex",
        "height_cm",
        "weight_kg",
        "activity_level",
        "goal",
        "member_updated_at",
    }
    assert triggers == {
        "trg_meal_plan_reference_methodology_pins_no_update",
        "trg_meal_plan_reference_methodology_pins_no_delete",
    }
