"""Real 0028 upgrade, transaction failure/resume, lineage and backup schema."""

from importlib import import_module
import sqlite3

import pytest
from app.db import migrations
from app.db.config import DatabaseConfig
from scripts.audit_pr6_composition_core import measure, seed_previous
from scripts.audit_pr6_nutrient_vector_b import snapshot
from app.tests.table_guards import assert_only_current_tables

MIGRATION = import_module("app.migrations.versions.0029_food_composition_core")


def test_real_0028_upgrade_preserves_every_row_readiness_and_vector_digest(tmp_path):
    report = measure(DatabaseConfig(path=tmp_path / "upgrade.sqlite"))
    assert report["migration_head_before"] == "0028_normalized_nutrient_vector"
    assert report["migration_head_after"] == MIGRATION.MIGRATION_ID
    assert report["readiness_before"] == report["readiness_after"]
    assert report["all_existing_table_rows_unchanged"]
    assert report["existing_profile_seals_verified"] == 183
    assert report["production_composition_rows_seeded_backfilled"] == 0
    assert set(report["composition_table_counts"]) == set(MIGRATION.TABLES)
    assert set(report["composition_table_counts"].values()) == {0}


def test_fresh_schema_foreign_keys_lineage_and_backup_inventory(tmp_path):
    from app.db.migration_lineage import REQUIRED_TABLES_BY_MIGRATION

    config = DatabaseConfig(path=tmp_path / "fresh.sqlite")
    assert migrations.apply_migrations(config) == migrations.expected_migration_ids()
    assert migrations.expected_migration_ids()[-1] == MIGRATION.MIGRATION_ID
    with sqlite3.connect(config.path) as db:
        assert db.execute("PRAGMA foreign_key_check").fetchall() == []
        names = {
            r[0]
            for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        assert_only_current_tables(names)
        assert REQUIRED_TABLES_BY_MIGRATION[MIGRATION.MIGRATION_ID] == set(
            MIGRATION.TABLES
        )
        for table in MIGRATION.TABLES:
            assert db.execute(f"SELECT count(*) FROM {table}").fetchone()[0] == 0
            columns = {
                row[1]: row[2] for row in db.execute(f"PRAGMA table_info({table})")
            }
            assert (
                not {
                    "fraction",
                    "coefficient",
                    "protein",
                    "protein_g",
                    "calcium",
                    "energy_kcal",
                }
                & columns.keys()
            )
        assert {
            row[1]: row[2]
            for row in db.execute("PRAGMA table_info(food_composition_nodes)")
        }["input_mass_g"] == "TEXT"
        assert {
            row[1]: row[2]
            for row in db.execute("PRAGMA table_info(food_retention_values)")
        }["factor"] == "TEXT"

        # SQLite native backups retain the complete empty schema and triggers.
        with sqlite3.connect(tmp_path / "backup.sqlite") as backup:
            db.backup(backup)
            assert (
                db.execute(
                    "SELECT type,name,sql FROM sqlite_master ORDER BY name"
                ).fetchall()
                == backup.execute(
                    "SELECT type,name,sql FROM sqlite_master ORDER BY name"
                ).fetchall()
            )


def schema(config):
    with sqlite3.connect(config.path) as db:
        return db.execute(
            "SELECT type,name,sql FROM sqlite_master ORDER BY name"
        ).fetchall(), db.execute(
            "SELECT * FROM schema_migrations ORDER BY rowid"
        ).fetchall()


def test_mid_migration_schema_data_marker_rollback_and_deterministic_resume(
    tmp_path, monkeypatch
):
    config = DatabaseConfig(path=tmp_path / "failure.sqlite")
    seed_previous(config)
    before, schema_before = snapshot(config), schema(config)
    statements = MIGRATION.STATEMENTS
    injected = (
        statements[:4]
        + (
            "CREATE TABLE composition_fault_probe (id INTEGER)",
            "INSERT INTO composition_fault_probe VALUES (7)",
            "UPDATE app_settings SET value = 'fault'",
            "INSERT INTO missing_composition_fault_table VALUES (1)",
        )
        + statements[4:]
    )
    with monkeypatch.context() as patch:
        patch.setattr(MIGRATION, "STATEMENTS", injected)
        with pytest.raises(
            sqlite3.OperationalError, match="missing_composition_fault_table"
        ):
            migrations.apply_migrations(config)
    assert snapshot(config) == before
    assert schema(config) == schema_before
    assert migrations.pending_migration_ids(config) == [MIGRATION.MIGRATION_ID]
    assert migrations.apply_migrations(config) == [MIGRATION.MIGRATION_ID]
    after, schema_after = snapshot(config), schema(config)
    assert all(after[name] == rows for name, rows in before.items())
    assert migrations.apply_migrations(config) == []
    assert snapshot(config) == after
    assert schema(config) == schema_after
