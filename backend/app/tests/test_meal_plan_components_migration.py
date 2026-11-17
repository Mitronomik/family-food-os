"""0044 genuinely runs on SQLite: full old lineage and atomic FK rebuild."""

import sqlite3
from importlib import import_module
from uuid import uuid4

import pytest
from app.db import migrations
from app.db.config import DatabaseConfig
from app.db.migrations import apply_migrations, expected_migration_ids

MIGRATION_ID = "0044_meal_plan_components"
TABLES = {
    "meal_plan_event_compositions",
    "meal_plan_event_components",
    "meal_plan_component_servings",
}


def _through_0043(config, monkeypatch):
    original = list(migrations.MIGRATION_MODULES)
    monkeypatch.setattr(migrations, "MIGRATION_MODULES", original[:-1])
    try:
        applied = apply_migrations(config)
        assert applied[-1] == "0043_shopping_engine"
    finally:
        monkeypatch.setattr(migrations, "MIGRATION_MODULES", original)


def _schema(config):
    with sqlite3.connect(config.path) as db:
        return {
            name: sql
            for name, sql in db.execute(
                "SELECT name, sql FROM sqlite_master "
                "WHERE type IN ('table','index','trigger') AND sql IS NOT NULL"
            )
        }


def test_fresh_0044_is_final_and_immutable_component_tables_present(tmp_path):
    config = DatabaseConfig(path=tmp_path / "fresh.sqlite")
    assert expected_migration_ids()[-2:] == [
        "0043_shopping_engine",
        MIGRATION_ID,
    ]
    assert apply_migrations(config)[-1] == MIGRATION_ID
    assert apply_migrations(config) == []
    with sqlite3.connect(config.path) as db:
        db.execute("PRAGMA foreign_keys=ON")
        names = {
            row[0]
            for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        assert TABLES <= names
        assert db.execute("PRAGMA foreign_key_check").fetchall() == []
        assert db.execute(
            "SELECT count(*) FROM meal_plan_event_compositions"
        ).fetchone() == (0,)
        assert (
            db.execute(
                "SELECT sql FROM sqlite_master WHERE type='table' AND name='meal_plan_events'"
            )
            .fetchone()[0]
            .find("COOK_COMPOSITION")
            >= 0
        )
        for table in TABLES:
            assert {
                x[0]
                for x in db.execute(
                    "SELECT name FROM sqlite_master WHERE type='trigger' AND tbl_name=?",
                    (table,),
                )
            } == {f"trg_{table}_no_update", f"trg_{table}_no_delete"}


def test_real_0043_upgrades_to_0044_without_rewriting_legacy_data(
    tmp_path, monkeypatch
):
    config = DatabaseConfig(path=tmp_path / "upgrade.sqlite")
    _through_0043(config, monkeypatch)
    household = uuid4().hex
    member = uuid4().hex
    selection = uuid4().hex
    plan = uuid4().hex
    event = uuid4().hex
    serving = uuid4().hex
    with sqlite3.connect(config.path) as db:
        db.execute("PRAGMA foreign_keys=ON")
        db.execute(
            "INSERT INTO households "
            "(id, name, timezone, created_at, updated_at) "
            "VALUES (?, 'Review Home', 'Europe/Moscow', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)",
            (household,),
        )
        db.execute(
            "INSERT INTO household_members "
            "(id, household_id, name, active, activity_level, goal, created_at, updated_at) "
            "VALUES (?, ?, 'Reviewer', 1, 'moderate', 'maintain', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)",
            (member, household),
        )
        db.execute(
            "INSERT INTO member_meal_pattern_selections "
            "(id, household_id, member_id, version_number, source_kind, has_user_overrides, accepted_at, created_at) "
            "VALUES (?, ?, ?, 1, 'CUSTOM', 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)",
            (selection, household, member),
        )
        db.execute(
            "INSERT INTO meal_plans "
            "(id, household_id, week_start, revision_number, status, config_version, created_at) "
            "VALUES (?, ?, '2026-11-02', 1, 'CONFIRMED', 'manual-v1', CURRENT_TIMESTAMP)",
            (plan, household),
        )
        db.execute(
            "INSERT INTO meal_plan_member_selections VALUES (?, ?, ?)",
            (plan, member, selection),
        )
        db.execute(
            "INSERT INTO meal_plan_events "
            "(id, plan_id, local_date, position, role_code, source_kind, created_at) "
            "VALUES (?, ?, '2026-11-02', 1, 'DINNER', 'EAT_OUT', CURRENT_TIMESTAMP)",
            (event, plan),
        )
        db.execute(
            "INSERT INTO servings (id, event_id, member_id, portion_servings, created_at) "
            "VALUES (?, ?, ?, '1.250000', CURRENT_TIMESTAMP)",
            (serving, event, member),
        )
        db.commit()
        old = {
            table: db.execute(f"SELECT * FROM {table}").fetchall()
            for table in (
                "meal_plans",
                "meal_plan_events",
                "servings",
                "meal_plan_member_selections",
            )
        }
    assert apply_migrations(config) == [MIGRATION_ID]
    with sqlite3.connect(config.path) as db:
        db.execute("PRAGMA foreign_keys=ON")
        for table, rows in old.items():
            assert db.execute(f"SELECT * FROM {table}").fetchall() == rows
        assert db.execute("PRAGMA foreign_key_check").fetchall() == []
        assert db.execute(
            "SELECT count(*) FROM schema_migrations WHERE migration_id=?",
            (MIGRATION_ID,),
        ).fetchone() == (1,)
        with pytest.raises(sqlite3.IntegrityError, match="immutable"):
            db.execute("UPDATE meal_plan_events SET position=9 WHERE id=?", (event,))
    assert apply_migrations(config) == []


def test_0044_injected_failed_rebuild_restores_schema_and_marker(tmp_path, monkeypatch):
    config = DatabaseConfig(path=tmp_path / "fail.sqlite")
    _through_0043(config, monkeypatch)
    before = _schema(config)
    module = import_module("app.migrations.versions.0044_meal_plan_components")
    real_upgrade = module.upgrade

    def fail_after_tables(db):
        real_upgrade(db)
        raise RuntimeError("injected pre-marker failure")

    monkeypatch.setattr(module, "upgrade", fail_after_tables)
    with pytest.raises(RuntimeError, match="injected"):
        apply_migrations(config)
    assert _schema(config) == before
    with sqlite3.connect(config.path) as db:
        assert db.execute("PRAGMA foreign_key_check").fetchall() == []
        assert db.execute(
            "SELECT count(*) FROM schema_migrations WHERE migration_id=?",
            (MIGRATION_ID,),
        ).fetchone() == (0,)
    monkeypatch.setattr(module, "upgrade", real_upgrade)
    assert apply_migrations(config) == [MIGRATION_ID]
