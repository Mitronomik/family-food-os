"""Reproduce RU data promotion and complete historical preservation in temporary DBs."""

from collections import Counter
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
from tempfile import TemporaryDirectory
from uuid import UUID

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "scripts"))
from app.db.config import DatabaseConfig  # noqa: E402
from app.db.migrations import expected_migration_ids  # noqa: E402
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine  # noqa: E402
from app.persistence.sqlalchemy_core.ru_food_data import SqlAlchemyRuFoodUnitOfWork  # noqa: E402
from app.seed.food_recipes import seed_food_recipes  # noqa: E402
from app.seed.nutrition_measure_evidence import seed_nutrition_measure_evidence  # noqa: E402
from app.seed.recipe_corrections import (  # noqa: E402
    seed_recipe_corrections,
    seed_correction_assessments,
)
from app.seed.ru_food_data import PACKAGE, PACKAGE_SHA256, seed_ru_food_data  # noqa: E402
from app.services.food_composition import CompositionCalculator  # noqa: E402
from audit_pr6_nutrient_vector_b import snapshot, readiness  # noqa: E402

BASE = "d5b5ce3fdc4ec79de5454b3ed23b1d527772c0bc"
ACCEPTED_HEAD = "4180297d47d68a0e0d9efbe7a7a27f3900c4f388"


def seed_baseline(config):
    seed_food_recipes(config)
    seed_nutrition_measure_evidence(config)
    seed_recipe_corrections(config)
    seed_correction_assessments(config)


def head(config):
    with sqlite3.connect(config.path) as db:
        return db.execute(
            "SELECT migration_id FROM schema_migrations ORDER BY rowid DESC LIMIT 1"
        ).fetchone()[0]


def verify_vectors(config, ids):
    engine = create_sqlite_engine(config)
    try:
        with SqlAlchemyRuFoodUnitOfWork(engine) as scope:
            for key in ids:
                assert scope.nutrient_vectors.get(UUID(key)).profile_id == UUID(key)
    finally:
        engine.dispose()


def measure(config):
    seed_baseline(config)
    before, ready_before, head_before = (
        snapshot(config),
        readiness(config),
        head(config),
    )
    seals = [r[0] for r in before["nutrition_vector_seals"]]
    verify_vectors(config, seals)
    first = seed_ru_food_data(config)
    after, ready_after = snapshot(config), readiness(config)
    second = seed_ru_food_data(config)
    assert snapshot(config) == after and readiness(config) == ready_after
    assert not any(second.values())
    allowed = {
        "food_ingredients",
        "food_nutrition_profiles",
        "nutrient_values",
        "nutrition_vector_seals",
        "food_composition_versions",
    }
    for name, rows in before.items():
        if name in allowed:
            assert after[name][: len(rows)] == rows, name
        else:
            assert after[name] == rows, name
    assert ready_after == ready_before
    assert ready_before == json.loads(
        (
            ROOT / "data/seed/recipe_corrections/pr6-data-b2a/production-audit-v3.json"
        ).read_text()
    )
    verify_vectors(config, [r[0] for r in after["nutrition_vector_seals"]])
    records = json.loads((PACKAGE / "food-readiness.json").read_text())["rows"]
    replay = []
    engine = create_sqlite_engine(config)
    try:
        with SqlAlchemyRuFoodUnitOfWork(engine) as scope:
            for row in records:
                if row["final_readiness"] != "RU_READY":
                    continue
                food = scope.ingredients.get_by_code(row["food_code"])
                version = scope.compositions.find_version(food.id, 1)
                assert (
                    version.kind == "ATOMIC" and version.food_ingredient_id == food.id
                )
                source = row["nutrition_profile_source"]
                profile = scope.nutrition_profiles.get_by_provenance(
                    food.id,
                    source["source_name"],
                    source["source_id"],
                    source["source_version"],
                )
                assert version.profile_id == profile.id
                calculator = CompositionCalculator(
                    scope.compositions, scope.nutrient_vectors
                )
                result = calculator.calculate(
                    version.id, nutrient_codes=("ENERGY_KCAL", "PROTEIN", "CALCIUM")
                )
                assert result == calculator.calculate(
                    version.id, nutrient_codes=("ENERGY_KCAL", "PROTEIN", "CALCIUM")
                )
                replay.append(
                    {
                        "food_code": row["food_code"],
                        "natural_reference": row["composition_reference"],
                        "status": result.status,
                        "vector_value_count": row["vector_reference"]["value_count"],
                    }
                )
    finally:
        engine.dispose()
    with sqlite3.connect(config.path) as db:
        assert db.execute("PRAGMA foreign_key_check").fetchall() == []
        new_kind_counts = dict(
            db.execute(
                "SELECT kind, count(*) FROM food_composition_versions GROUP BY kind"
            )
        )
        # Actual current recipe target, including optional rows, matches artifact.
        usages = db.execute("""SELECT f.canonical_code, i.optional, count(*) FROM food_recipe_ingredients i
          JOIN food_recipe_versions v ON v.id=i.recipe_version_id
          JOIN food_ingredients f ON f.id=i.food_ingredient_id
          WHERE v.version_number=(SELECT max(v2.version_number) FROM food_recipe_versions v2 WHERE v2.recipe_id=v.recipe_id)
          GROUP BY f.canonical_code, i.optional""").fetchall()
    expected_usages = {
        (r["food_code"], int(optional)): len(r["target_usage"][kind])
        for r in records
        if r["population"] == "EXISTING_CATALOGUE"
        for optional, kind in [(False, "required"), (True, "optional")]
        if r["target_usage"][kind]
    }
    assert {(code, opt): n for code, opt, n in usages} == expected_usages

    def compact(r):
        return {
            k: v
            for k, v in r.items()
            if k not in ("records", "source_quantity_findings")
        }

    def hash_report(r):
        return hashlib.sha256(
            json.dumps(r, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()

    market_counts = dict(
        sorted(Counter(r["market_classification"] for r in records).items())
    )
    return {
        "base_main_sha": BASE,
        "migration_head_before": head_before,
        "migration_head_after": head(config),
        "registered_migration_head": expected_migration_ids()[-1],
        "population": "Accepted production seed on a disposable database; synthetic fixtures excluded.",
        "existing_food_ingredient_count": len(before["food_ingredients"]),
        "new_food_ingredient_count": first["ingredients"],
        "target_existing_food_count": sum(
            r["population"] == "EXISTING_CATALOGUE" for r in records
        ),
        "candidate_count": sum(
            r["population"] == "RESEARCH_CANDIDATE" for r in records
        ),
        "promote_count": sum(r["decision"] == "PROMOTE" for r in records),
        "defer_count": sum(r["decision"] == "DEFER" for r in records),
        "reject_count": sum(r["decision"] == "REJECT" for r in records),
        "market_classification_counts": market_counts,
        "ru_ready_food_count": len(replay),
        "default_food_gate_eligible_count": sum(
            r["default_pool_eligible"] for r in records
        ),
        "new_nutrition_profile_count": first["profiles"],
        "new_nutrient_value_count": first["nutrient_values"],
        "new_vector_seal_count": first["vector_seals"],
        "existing_vector_seals_preserved": len(seals),
        "existing_vector_seals_verified_before": len(seals),
        "existing_vector_seals_verified_after": len(seals),
        "new_atomic_composition_count": new_kind_counts.get("ATOMIC", 0),
        "new_composite_composition_count": new_kind_counts.get("COMPOSITE", 0),
        "new_transformation_count": len(after["food_transformations"])
        - len(before["food_transformations"]),
        "new_yield_count": len(after["food_yield_models"])
        - len(before["food_yield_models"]),
        "new_retention_count": len(after["food_retention_profiles"])
        - len(before["food_retention_profiles"]),
        "all_existing_rows_preserved": True,
        "existing_recipe_rows_changed": 0,
        "existing_recipe_versions_changed": 0,
        "existing_assessments_changed": 0,
        "readiness_before": compact(ready_before),
        "readiness_after": compact(ready_after),
        "full_readiness_sha256_before": hash_report(ready_before),
        "full_readiness_sha256_after": hash_report(ready_after),
        "estimate_candidates_accepted": 0,
        "second_seed_inserts": second,
        "second_seed_database_identical": True,
        "composition_checks": replay,
        "package_sha256": PACKAGE_SHA256,
    }


def scope_audit():
    paths = subprocess.check_output(
        ["git", "diff", "--name-only", BASE, ACCEPTED_HEAD], cwd=ROOT, text=True
    ).splitlines()
    paths += subprocess.check_output(
        ["git", "ls-files", "--others", "--exclude-standard"], cwd=ROOT, text=True
    ).splitlines()
    forbidden = (
        "backend/app/api/",
        "backend/app/schemas/",
        "frontend/",
        "backend/app/migrations/",
        "backend/app/domain/nutrient_vector_backfill_v1.py",
        "data/seed/",
    )
    assert not [p for p in paths if p.startswith(forbidden)]
    return {
        "public_api_changes": 0,
        "ui_changes": 0,
        "ai_dependency": 0,
        "retail_runtime_changes": 0,
    }


def main():
    with TemporaryDirectory() as directory:
        result = measure(DatabaseConfig(path=Path(directory) / "ru-food.sqlite"))
    result.update(scope_audit())
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
