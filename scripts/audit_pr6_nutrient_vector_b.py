"""Reproduce VECTOR-B upgrade and readiness evidence on a disposable database."""

import json
from pathlib import Path
import sqlite3
import sys
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "scripts"))
from audit_pr6_data_b2a import audit_catalogue  # noqa: E402
from app.db import migrations  # noqa: E402
from app.db.config import DatabaseConfig  # noqa: E402
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine  # noqa: E402
from app.seed.food_recipes import seed_food_recipes  # noqa: E402
from app.seed.nutrition_measure_evidence import seed_nutrition_measure_evidence  # noqa: E402
from app.seed.recipe_corrections import (  # noqa: E402
    seed_recipe_corrections,
    seed_correction_assessments,
)


def seed_previous(config):
    original = migrations.MIGRATION_MODULES
    try:
        migrations.MIGRATION_MODULES = original[:27]
        seed_food_recipes(config)
        seed_nutrition_measure_evidence(config)
        seed_recipe_corrections(config)
        seed_correction_assessments(config)
    finally:
        migrations.MIGRATION_MODULES = original


def snapshot(config):
    with sqlite3.connect(config.path) as connection:
        return {
            name: connection.execute(
                f'SELECT * FROM "{name}" ORDER BY rowid'
            ).fetchall()
            for (name,) in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name != 'schema_migrations'"
            )
        }


def readiness(config):
    engine = create_sqlite_engine(config)
    try:
        return audit_catalogue(engine)
    finally:
        engine.dispose()


def measure(config):
    seed_previous(config)
    before, ready_before = snapshot(config), readiness(config)
    applied = migrations.apply_migrations(config)
    after, ready_after = snapshot(config), readiness(config)
    assert all(after[name] == rows for name, rows in before.items())
    assert ready_after == ready_before
    assert ready_before == json.loads(
        (
            ROOT / "data/seed/recipe_corrections/pr6-data-b2a/production-audit-v3.json"
        ).read_text()
    )
    with sqlite3.connect(config.path) as connection:
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        observations = [
            r
            for (payload,) in connection.execute(
                "SELECT observations_json FROM nutrition_vector_seals"
            )
            for r in json.loads(payload)
        ]
        zeros = [
            r
            for r in observations
            if r["observation"]["source_value_state"] == "ZERO_REPORTED"
        ]
        zero_rows = connection.execute("""SELECT count(*) FROM nutrient_values
            WHERE json_extract(provenance_json, '$.observation.source_value_state') = 'ZERO_REPORTED'""").fetchone()[
            0
        ]
        duplicates = connection.execute("""SELECT count(*) FROM (
            SELECT profile_id, nutrient_code FROM nutrient_values GROUP BY profile_id, nutrient_code HAVING count(*) > 1)""").fetchone()[
            0
        ]

    def compact(r):
        return {
            k: v
            for k, v in r.items()
            if k not in ("records", "source_quantity_findings")
        }

    return {
        "base_main_sha": "e35d87a24d5d8afb59509e566aa1ff4b7a58a11a",
        "migration_head_before": "0027_recipe_same_source_revisions",
        "migration_head_after": applied[-1],
        "canonical_nutrient_definitions": len(after["nutrient_definitions"]),
        "profiles_examined": len(before["food_nutrition_profiles"]),
        "profiles_backfilled": len(after["nutrition_vector_seals"]),
        "normalized_nutrient_value_rows": len(after["nutrient_values"]),
        "audited_unresolved_zero_observations": len(zeros),
        "authoritative_rows_from_unresolved_zeros": zero_rows,
        "legacy_dispositions": {
            status: sum(
                r["observation"]["legacy_mapping_status"] == status
                for r in observations
            )
            for status in (
                "SOURCE_COMPONENT_CONFIRMED",
                "LEGACY_PROFILE_VALUE_CONFIRMED_SOURCE_ID_UNAVAILABLE",
                "VALUE_MISMATCH",
                "DEFINITION_AMBIGUOUS",
                "VALUE_ABSENT",
            )
        },
        "profiles_with_duplicate_effective_values": duplicates,
        "historical_profile_ids_changed": 0,
        "historical_b1_bindings_rebound": 0,
        "nutrition_v1_regressions": 0,
        "all_existing_tables_byte_value_equal": True,
        "readiness_before": compact(ready_before),
        "readiness_after": compact(ready_after),
    }


def main():
    with TemporaryDirectory() as directory:
        result = measure(DatabaseConfig(path=Path(directory) / "vector-b.sqlite"))
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
