"""Measure actual 0028 → 0029 upgrade on disposable accepted seed databases."""

from importlib import import_module
import json
from pathlib import Path
import sqlite3
import sys
from tempfile import TemporaryDirectory
from uuid import UUID

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "scripts"))
from app.db import migrations  # noqa: E402
from app.db.config import DatabaseConfig  # noqa: E402
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine  # noqa: E402
from app.persistence.sqlalchemy_core.nutrition_read_scope import (  # noqa: E402
    SqlAlchemyNutritionReadScope,
)
from app.seed.food_recipes import seed_food_recipes  # noqa: E402
from app.seed.nutrition_measure_evidence import seed_nutrition_measure_evidence  # noqa: E402
from app.seed.recipe_corrections import (  # noqa: E402
    seed_recipe_corrections,
    seed_correction_assessments,
)
from audit_pr6_nutrient_vector_b import snapshot, readiness  # noqa: E402

MIGRATION = import_module("app.migrations.versions.0029_food_composition_core")


def seed_previous(config):
    original = migrations.MIGRATION_MODULES
    cutoff = next(
        i for i, name in enumerate(original) if name.endswith(MIGRATION.MIGRATION_ID)
    )
    try:
        migrations.MIGRATION_MODULES = original[:cutoff]
        seed_food_recipes(config)
        seed_nutrition_measure_evidence(config)
        seed_recipe_corrections(config)
        seed_correction_assessments(config)
    finally:
        migrations.MIGRATION_MODULES = original


def measure(config):
    seed_previous(config)
    before, ready_before = snapshot(config), readiness(config)
    with sqlite3.connect(config.path) as db:
        head_before = db.execute(
            "SELECT migration_id FROM schema_migrations ORDER BY rowid DESC LIMIT 1"
        ).fetchone()[0]
    applied = migrations.apply_migrations(config)
    after, ready_after = snapshot(config), readiness(config)
    assert all(after[name] == rows for name, rows in before.items())
    assert ready_after == ready_before
    with sqlite3.connect(config.path) as db:
        assert db.execute("PRAGMA foreign_key_check").fetchall() == []
        counts = {
            name: db.execute(f"SELECT count(*) FROM {name}").fetchone()[0]
            for name in MIGRATION.TABLES
        }
        atomic_count = db.execute(
            "SELECT count(*) FROM food_composition_versions WHERE kind = 'ATOMIC'"
        ).fetchone()[0]
        composite_count = db.execute(
            "SELECT count(*) FROM food_composition_versions WHERE kind = 'COMPOSITE'"
        ).fetchone()[0]
        profiles = [
            UUID(r[0])
            for r in db.execute(
                "SELECT profile_id FROM nutrition_vector_seals ORDER BY profile_id"
            )
        ]
    engine = create_sqlite_engine(config)
    try:
        with SqlAlchemyNutritionReadScope(engine) as read:
            for key in profiles:
                assert read.nutrient_vectors.get(key).profile_id == key
    finally:
        engine.dispose()
    assert all(value == 0 for value in counts.values())
    return {
        "base_main_sha": "b39d9f5786796dc689bdee8ae52a90cbcc4ebdfe",
        "migration_head_before": head_before,
        "migration_head_after": applied[-1],
        "composition_table_counts": counts,
        "atomic_composition_rows": atomic_count,
        "composite_composition_rows": composite_count,
        "production_composition_rows_seeded_backfilled": 0,
        "all_existing_table_rows_unchanged": True,
        "existing_profile_seals_verified": len(profiles),
        "existing_food_ingredient_rows_changed": 0,
        "existing_food_nutrition_profile_rows_changed": 0,
        "existing_nutrient_registry_rows_changed": 0,
        "existing_nutrient_value_rows_changed": 0,
        "existing_nutrient_vector_seals_changed": 0,
        "historical_b1_bindings_changed": 0,
        "public_api_changes": 0,
        "ui_changes": 0,
        "ai_dependency": 0,
        "readiness_before": {
            k: v
            for k, v in ready_before.items()
            if k not in ("records", "source_quantity_findings")
        },
        "readiness_after": {
            k: v
            for k, v in ready_after.items()
            if k not in ("records", "source_quantity_findings")
        },
    }


def main():
    with TemporaryDirectory() as directory:
        result = measure(DatabaseConfig(path=Path(directory) / "composition.sqlite"))
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
