"""Bounded Candidate A readback against disposable canonical seed databases."""

import json
import os
import shutil
import sqlite3
import subprocess
import sys
from contextlib import closing
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

import pytest
from app.db.config import DatabaseConfig
from app.db.migrations import expected_migration_ids
from app.domain.nutrient_vector_backfill_v1 import canonical_json, value_set_digest
from app.identity import WORKSPACE_SOURCE_SETTING_KEY
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
from app.persistence.sqlalchemy_core.food_recipe_composition import (
    create_food_recipe_catalogue_service,
)
from app.seed.r2c_breakfast_grain_diversity import (
    BUCKWHEAT_RECIPE_CODE,
    _load_contract,
    _recipe_seed,
    seed_r2c_breakfast_grain_diversity,
)

from scripts import read_pr10_candidate_a_predecessor as predecessor_reader
from scripts.read_pr10_candidate_a_predecessor import (
    PROCESS_SHA256,
    STEP4_SHA256,
    readback,
)

CANDIDATE_VERSION_SQL = """
    SELECT v.id
    FROM food_recipe_versions v
    JOIN food_recipes r ON r.id = v.recipe_id
    WHERE r.canonical_code = ? AND v.version_number = 1
"""


@pytest.fixture(scope="module")
def baseline(tmp_path_factory):
    path = tmp_path_factory.mktemp("candidate-a-readback") / "r2c.sqlite"
    seed_r2c_breakfast_grain_diversity(DatabaseConfig(path=path))
    return path


@pytest.fixture
def snapshot(baseline, tmp_path):
    path = tmp_path / "copy.sqlite"
    shutil.copyfile(baseline, path)
    return path


def audit(path):
    return readback(sqlite_path=path, target_id="test-r2c", context="disposable-test")


def assert_blocked_unchanged(path, reason):
    before = path.read_bytes()
    report = audit(path)
    assert report["status"] == "BLOCKED"
    assert report["reason"] == reason
    assert report["publication_gate"] == "NO_GO_TO_CORRECTION_PUBLICATION"
    assert path.read_bytes() == before
    return report


def test_reads_persisted_lineage_children_and_authority_without_writes(baseline):
    before = baseline.read_bytes()
    report = audit(baseline)
    assert report["status"] == "PREDECESSOR_MATCH", report
    assert report["publication_gate"] == "NO_GO_TO_CORRECTION_PUBLICATION"
    assert report["target"]["operator_declared_context"] == "disposable-test"
    assert report["target"]["schema_revision"] == expected_migration_ids()[-1]
    predecessor = report["predecessor"]
    assert predecessor["process_sha256"] == PROCESS_SHA256
    assert predecessor["steps"][3]["sha256"] == STEP4_SHA256
    assert predecessor["version"]["version_number"] == 1
    assert predecessor["version"]["created_from_version_id"] is None
    assert report["recipe"]["current_verified_version_id"] == str(
        predecessor["version"]["id"]
    )
    assert predecessor["ingredients"]
    assert len(predecessor["steps"]) == 4
    assert predecessor["equipment"] == []
    for rows in (predecessor["ingredients"], predecessor["steps"]):
        assert [row["position"] for row in rows] == list(range(1, len(rows) + 1))
        assert all(
            row["recipe_version_id"] == predecessor["version"]["id"] for row in rows
        )
    assert (
        report["prepared"]["authority"]["recipe_version_id"]
        == predecessor["version"]["id"]
    )
    assert report["prepared"]["authority"]["output_mass_g"] == Decimal(200)
    assert report["prepared"]["available"] == {"ENERGY_KCAL": Decimal("187.3")}
    assert len(report["prepared"]["unknown"]) == 53
    assert baseline.read_bytes() == before


def run_cli(path):
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "scripts.read_pr10_candidate_a_predecessor",
            "--sqlite",
            str(path),
            "--target-id",
            "test-r2c",
            "--context",
            "disposable-test",
        ],
        capture_output=True,
        text=True,
        check=False,
    )


def test_cli_serializes_version_linked_receipt(baseline):
    result = run_cli(baseline)
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["status"] == "PREDECESSOR_MATCH"
    assert str(baseline) not in result.stdout + result.stderr
    version_id = report["predecessor"]["version"]["id"]
    assert report["prepared"]["authority"]["recipe_version_id"] == version_id
    assert report["prepared"]["authority"]["output_mass_g"] == "200"
    (value,) = report["prepared"]["values"]
    assert (value["recipe_version_id"], value["nutrient_code"], value["amount"]) == (
        version_id,
        "ENERGY_KCAL",
        "187.3",
    )
    assert value["provenance_json"] == canonical_json(
        json.loads(value["provenance_json"])
    )


def test_reports_exact_card_hash_as_manifest_evidence(baseline):
    result = run_cli(baseline)
    assert result.returncode == 0, result.stderr
    predecessor = json.loads(result.stdout)["predecessor"]
    assert predecessor["source_card"] == {
        "evidence": "R2C_PUBLICATION_MANIFEST",
        "exact_source_card_sha256": "4e7e2a8086ec8b94cbeb8e21861b4623d0e76daba0da67af080b8c2ad4787b83",
    }
    assert (
        predecessor["source_card"]["exact_source_card_sha256"]
        != predecessor["version"]["source_document_sha256"]
    )


def test_missing_snapshot_returns_machine_readable_blocker_without_creating_file(
    tmp_path,
):
    missing = tmp_path / "absent.sqlite"
    result = run_cli(missing)
    assert result.returncode == 2, result.stderr
    assert json.loads(result.stdout)["reason"] == "SQLITE_FILE_MISSING"
    assert str(missing) not in result.stdout + result.stderr
    assert not missing.exists()


def test_cli_masks_an_inaccessible_snapshot_path(snapshot, monkeypatch, capsys):
    is_file = Path.is_file

    def denied_for_snapshot(path):
        if path == snapshot:
            raise PermissionError(f"Cannot traverse {path}")
        return is_file(path)

    monkeypatch.setattr(Path, "is_file", denied_for_snapshot)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "read_pr10_candidate_a_predecessor",
            "--sqlite",
            str(snapshot),
            "--target-id",
            "test-r2c",
            "--context",
            "disposable-test",
        ],
    )
    with pytest.raises(SystemExit) as exc:
        predecessor_reader.main()

    assert exc.value.code == 2
    result = capsys.readouterr()
    assert result.err == ""
    assert str(snapshot) not in result.out
    report = json.loads(result.out)
    assert report["status"] == "BLOCKED"
    assert report["reason"] == "READBACK_INVALID_OR_UNAVAILABLE"


def test_blocks_stale_schema_without_migrating(snapshot):
    with sqlite3.connect(snapshot) as conn:
        conn.execute(
            "DELETE FROM schema_migrations WHERE migration_id = ?",
            (expected_migration_ids()[-1],),
        )
    report = assert_blocked_unchanged(snapshot, "SCHEMA_NOT_AT_ACCEPTED_REVISION")
    assert report["target"]["recorded_schema_revision"] == expected_migration_ids()[-2]
    assert "schema_revision" not in report["target"]


def test_blocks_missing_schema_table_despite_current_migration_history(snapshot):
    with sqlite3.connect(snapshot) as conn:
        conn.execute("DROP TABLE household_member_excluded_food_ingredients")

    report = assert_blocked_unchanged(snapshot, "REQUIRED_SCHEMA_TABLES_MISSING")
    assert report["target"]["recorded_schema_revision"] == expected_migration_ids()[-1]
    assert report["target"]["missing_required_tables"] == [
        "household_member_excluded_food_ingredients"
    ]
    assert "schema_revision" not in report["target"]
    assert "recipe" not in report


@pytest.mark.parametrize("marker", [None, "synthetic-other-workspace"])
def test_blocks_missing_or_incorrect_workspace_marker(snapshot, marker):
    with sqlite3.connect(snapshot) as conn:
        if marker is None:
            conn.execute(
                "DELETE FROM app_settings WHERE key = ?",
                (WORKSPACE_SOURCE_SETTING_KEY,),
            )
        else:
            conn.execute(
                "UPDATE app_settings SET value = ? WHERE key = ?",
                (marker, WORKSPACE_SOURCE_SETTING_KEY),
            )

    report = assert_blocked_unchanged(snapshot, "WORKSPACE_IDENTITY_MISMATCH")
    assert report["target"]["recorded_schema_revision"] == expected_migration_ids()[-1]
    assert "schema_revision" not in report["target"]
    assert "recipe" not in report


def test_closed_wal_snapshot_does_not_create_sidecar_files(snapshot):
    with closing(sqlite3.connect(snapshot)) as conn:
        assert conn.execute("PRAGMA journal_mode = WAL").fetchone() == ("wal",)
    assert set(snapshot.parent.iterdir()) == {snapshot}
    before = snapshot.read_bytes()
    assert audit(snapshot)["status"] == "PREDECESSOR_MATCH"
    assert set(snapshot.parent.iterdir()) == {snapshot}
    assert snapshot.read_bytes() == before


def test_blocks_snapshot_with_active_journal_sidecars(snapshot):
    with closing(sqlite3.connect(snapshot)) as conn:
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("BEGIN IMMEDIATE")
        files = set(snapshot.parent.iterdir())
        assert len(files) > 1
        report = assert_blocked_unchanged(snapshot, "SQLITE_SNAPSHOT_HAS_SIDECARS")
        assert "predecessor" not in report
        assert set(snapshot.parent.iterdir()) == files


def test_discards_receipt_when_snapshot_changes_during_read(snapshot, monkeypatch):
    read_snapshot = predecessor_reader._read_snapshot

    def read_then_replace(engine, report):
        read_snapshot(engine, report)
        replacement = snapshot.with_suffix(".replacement")
        shutil.copyfile(snapshot, replacement)
        os.replace(replacement, snapshot)

    monkeypatch.setattr(predecessor_reader, "_read_snapshot", read_then_replace)
    report = assert_blocked_unchanged(snapshot, "SQLITE_SNAPSHOT_CHANGED")
    assert "predecessor" not in report
    assert "prepared" not in report


@pytest.mark.parametrize(
    ("column", "value"),
    [("instruction", "Тестовое расхождение."), ("stage_code", "test_stage")],
)
def test_blocks_persisted_step_drift(snapshot, column, value):
    with sqlite3.connect(snapshot) as conn:
        conn.execute("DROP TRIGGER trg_food_recipe_steps_no_update")
        conn.execute(
            f"UPDATE food_recipe_steps SET {column} = ? WHERE position = 4"
            f" AND recipe_version_id IN ({CANDIDATE_VERSION_SQL})",
            (value, BUCKWHEAT_RECIPE_CODE),
        )
    report = assert_blocked_unchanged(snapshot, "PINNED_R2C_CONTENT_MISMATCH")
    assert "predecessor" not in report
    assert "prepared" not in report


def test_blocks_text_drift_hidden_by_domain_whitespace_normalization(snapshot):
    with sqlite3.connect(snapshot) as conn:
        conn.execute("DROP TRIGGER trg_food_recipe_steps_no_update")
        conn.execute(
            "UPDATE food_recipe_steps SET instruction = replace(instruction, ' ', '  ')"
            f" WHERE position = 4 AND recipe_version_id IN ({CANDIDATE_VERSION_SQL})",
            (BUCKWHEAT_RECIPE_CODE,),
        )
    report = assert_blocked_unchanged(snapshot, "PERSISTED_TEXT_MISMATCH")
    assert "predecessor" not in report
    assert "prepared" not in report


@pytest.mark.parametrize(
    ("trigger", "mutation", "reason"),
    [
        (
            "recipe_prepared_nutrition_authorities_no_delete",
            "DELETE FROM recipe_prepared_nutrition_authorities WHERE",
            "PREPARED_AUTHORITY_MISSING",
        ),
        (
            "recipe_prepared_nutrient_values_no_update",
            "UPDATE recipe_prepared_nutrient_values SET amount = '188' WHERE",
            "PREPARED_AUTHORITY_INVALID",
        ),
    ],
)
def test_blocks_prepared_authority_loss_or_drift_without_repair(
    snapshot, trigger, mutation, reason
):
    with sqlite3.connect(snapshot) as conn:
        conn.execute(f"DROP TRIGGER {trigger}")
        conn.execute(
            f"{mutation} recipe_version_id IN ({CANDIDATE_VERSION_SQL})",
            (BUCKWHEAT_RECIPE_CODE,),
        )
    report = assert_blocked_unchanged(snapshot, reason)
    assert "prepared" not in report


def test_corrupt_decimal_is_reported_without_traceback(snapshot):
    with sqlite3.connect(snapshot) as conn:
        conn.execute("PRAGMA ignore_check_constraints=ON")
        conn.execute("DROP TRIGGER recipe_prepared_nutrient_values_no_update")
        conn.execute(
            "UPDATE recipe_prepared_nutrient_values SET amount = 'invalid-test-value'"
            f" WHERE recipe_version_id IN ({CANDIDATE_VERSION_SQL})",
            (BUCKWHEAT_RECIPE_CODE,),
        )
    before = snapshot.read_bytes()
    result = run_cli(snapshot)
    assert result.returncode == 2
    assert result.stderr == ""
    assert "invalid-test-value" not in result.stdout
    assert json.loads(result.stdout)["reason"] == "PREPARED_AUTHORITY_INVALID"
    assert snapshot.read_bytes() == before


def test_blocks_resealed_provenance_with_duplicate_key_without_exposing_value(snapshot):
    marker = "synthetic-unapproved-value"
    with sqlite3.connect(snapshot) as conn:
        version_id, nutrient_code, amount, provenance = conn.execute(
            "SELECT recipe_version_id, nutrient_code, amount, provenance_json "
            "FROM recipe_prepared_nutrient_values "
            f"WHERE recipe_version_id IN ({CANDIDATE_VERSION_SQL})",
            (BUCKWHEAT_RECIPE_CODE,),
        ).fetchone()
        duplicate = '{"source_id":' + json.dumps(marker) + "," + provenance[1:]
        assert json.loads(duplicate) == json.loads(provenance)
        digest = value_set_digest(
            [
                {
                    "nutrient_code": nutrient_code,
                    "amount": Decimal(amount),
                    "provenance_json": duplicate,
                }
            ]
        )
        conn.execute("DROP TRIGGER recipe_prepared_nutrient_values_no_update")
        conn.execute("DROP TRIGGER recipe_prepared_nutrition_authorities_no_update")
        conn.execute(
            "UPDATE recipe_prepared_nutrient_values SET provenance_json = ? "
            "WHERE recipe_version_id = ? AND nutrient_code = ?",
            (duplicate, version_id, nutrient_code),
        )
        conn.execute(
            "UPDATE recipe_prepared_nutrition_authorities SET value_sha256 = ? "
            "WHERE recipe_version_id = ?",
            (digest, version_id),
        )

    before = snapshot.read_bytes()
    result = run_cli(snapshot)
    assert result.returncode == 2
    assert result.stderr == ""
    assert marker not in result.stdout
    report = json.loads(result.stdout)
    assert report["status"] == "BLOCKED"
    assert report["reason"] == "PREPARED_NUTRIENT_PROVENANCE_MISMATCH"
    assert "prepared" not in report
    assert snapshot.read_bytes() == before


def test_report_includes_later_version_and_blocks_instead_of_selecting_it(snapshot):
    _, _, specs = _load_contract()
    seed = _recipe_seed(specs["recipes"][BUCKWHEAT_RECIPE_CODE])
    engine = create_sqlite_engine(DatabaseConfig(path=snapshot))
    try:
        catalogue = create_food_recipe_catalogue_service(engine)
        recipe = catalogue.get_by_code(BUCKWHEAT_RECIPE_CODE)
        later = catalogue.append_trusted_version(
            recipe.id,
            replace(seed.version, change_note="Синтетическая более поздняя версия."),
        )
    finally:
        engine.dispose()
    report = assert_blocked_unchanged(snapshot, "LATER_VERSION_PRESENT")
    assert [ref["version_number"] for ref in report["recipe"]["versions"]] == [1, 2]
    assert report["recipe"]["current_verified_version_id"] == str(later.version.id)
    assert "prepared" not in report
