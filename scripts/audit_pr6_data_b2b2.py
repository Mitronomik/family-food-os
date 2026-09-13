"""Replay the bounded populated-0029 upgrade and verify every historical row."""

import argparse
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
from tempfile import TemporaryDirectory
from uuid import UUID

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "backend"), str(ROOT / "scripts")]
from app.db import migrations  # noqa: E402
from app.db.config import DatabaseConfig  # noqa: E402
from app.seed.b2b2 import PACKAGE, OPERATION, upgrade_b2b2  # noqa: E402
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine  # noqa: E402
from app.persistence.sqlalchemy_core.b2b2 import B2B2UnitOfWork  # noqa: E402
from app.services.food_composition import CompositionCalculator  # noqa: E402
from audit_pr6_nutrient_vector_b import snapshot, readiness  # noqa: E402
from audit_pr6_ru_food_data import seed_baseline, seed_ru_food_data, head  # noqa: E402


def baseline(config):
    # This is a frozen PR29 replay. Later migrations must not change the
    # historical implementation-evidence receipt being verified here.
    original = migrations.MIGRATION_MODULES
    cutoff = next(
        index
        for index, module_name in enumerate(original)
        if module_name.endswith("0029_food_composition_core")
    )
    try:
        migrations.MIGRATION_MODULES = original[: cutoff + 1]
        seed_baseline(config)
        seed_ru_food_data(config)
    finally:
        migrations.MIGRATION_MODULES = original


def replay(config):
    engine = create_sqlite_engine(config)
    try:
        with sqlite3.connect(config.path) as db:
            profile_ids = [
                UUID(r[0])
                for r in db.execute(
                    "SELECT profile_id FROM nutrition_vector_seals ORDER BY rowid"
                )
            ]
            composition_ids = [
                UUID(r[0])
                for r in db.execute(
                    "SELECT id FROM food_composition_versions ORDER BY rowid"
                )
            ]
        with B2B2UnitOfWork(engine) as uow:
            vectors = {key: uow.nutrient_vectors.get(key) for key in profile_ids}
            calc = CompositionCalculator(uow.compositions, uow.nutrient_vectors)
            compositions = {
                key: calc.calculate(
                    key,
                    nutrient_codes=(
                        "ENERGY_KCAL",
                        "PROTEIN",
                        "CALCIUM",
                        "FIBER_TOTAL_DIETARY",
                    ),
                )
                for key in composition_ids
            }
        return vectors, compositions
    finally:
        engine.dispose()


def preserved(config, before, after):
    switches = {}
    with sqlite3.connect(config.path) as db:
        for table, rows in before.items():
            prefix = after[table][: len(rows)]
            if table not in {
                "food_nutrition_profiles",
                "recipe_ingredient_nutrition_assessments",
            }:
                assert prefix == rows, table
                continue
            columns = [r[1] for r in db.execute(f'PRAGMA table_info("{table}")')]
            index = columns.index("is_current")
            changed = 0
            for old, new in zip(rows, prefix, strict=True):
                if old != new:
                    assert old[index] == 1 and new[index] == 0
                    assert (
                        old[:index] + old[index + 1 :] == new[:index] + new[index + 1 :]
                    )
                    changed += 1
            switches[table] = changed
    assert switches == {
        "food_nutrition_profiles": 3,
        "recipe_ingredient_nutrition_assessments": 7,
    }
    allowed_appends = {
        "food_recipe_versions",
        "food_recipe_ingredients",
        "food_recipe_steps",
        "food_recipe_equipment",
        "food_nutrition_profiles",
        "nutrient_values",
        "nutrition_vector_seals",
        "food_composition_versions",
        "nutrition_measure_evidence",
        "recipe_ingredient_nutrition_assessments",
        "recipe_ingredient_nutrition_assessment_issues",
    }
    for table in before:
        if table not in allowed_appends:
            assert before[table] == after[table], table
    return switches


def measure(config):
    baseline(config)
    before, ready_before = snapshot(config), readiness(config)
    vectors_before, compositions_before = replay(config)
    first = upgrade_b2b2(config)
    after, ready_after = snapshot(config), readiness(config)
    vectors_after, compositions_after = replay(config)
    switches = preserved(config, before, after)
    for key, vector in vectors_before.items():
        # Reader includes mutable profile metadata; only the approved current flag
        # differs. Seal/value rows are separately compared byte-for-byte above.
        current = vectors_after[key]
        assert (
            replace(
                current,
                profile=replace(current.profile, is_current=vector.profile.is_current),
            )
            == vector
        )
    for key, result in compositions_before.items():
        assert compositions_after[key] == result
    second = upgrade_b2b2(config)
    assert not any(second.values()) and snapshot(config) == after
    assert readiness(config) == ready_after
    assert head(config) == "0029_food_composition_core"
    with sqlite3.connect(config.path) as db:
        assert db.execute("PRAGMA foreign_key_check").fetchall() == []
        assert db.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        schema = db.execute(
            "SELECT type,name,sql FROM sqlite_master ORDER BY name"
        ).fetchall()
        backup_path = config.path.with_name("post-upgrade-backup.sqlite")
        with sqlite3.connect(backup_path) as backup:
            db.backup(backup)
            assert (
                backup.execute(
                    "SELECT type,name,sql FROM sqlite_master ORDER BY name"
                ).fetchall()
                == schema
            )
    restored = DatabaseConfig(path=backup_path)
    assert snapshot(restored) == after
    assert readiness(restored) == ready_after
    assert replay(restored) == (vectors_after, compositions_after)
    assert not any(upgrade_b2b2(restored).values())
    proof = json.loads((PACKAGE / "row-resolution.json").read_text())
    repairs = {
        (r["identity"].split(":")[0], int(r["identity"].split(":")[-1])): r
        for r in proof["complete_impact_universe"]
    }
    delta = []
    for previous, current in zip(
        ready_before["records"], ready_after["records"], strict=True
    ):
        assert previous["recipe"] == current["recipe"]
        for old, new in zip(previous["rows"], current["rows"], strict=True):
            if old != new:
                repair = repairs[previous["recipe"], old["position"]]
                delta.append(
                    {
                        "identity_before": repair["identity"],
                        "identity_after": repair["current_after_identity"],
                        "before": old,
                        "after": new,
                        "review_reference": repair["review_reference"],
                        "explanation": repair["assessment_after"]["review_note"],
                    }
                )
    recipe_delta = [
        {
            "recipe": old["recipe"],
            "before": old["status"],
            "after": new["status"],
            "row_review_references": [
                r["review_reference"]
                for r in delta
                if r["identity_before"].startswith(old["recipe"] + ":")
            ],
        }
        for old, new in zip(
            ready_before["records"], ready_after["records"], strict=True
        )
        if old["status"] != new["status"]
    ]

    def digest(value):
        return hashlib.sha256(
            json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()

    result = dict(
        operation=OPERATION,
        base_main="4180297d47d68a0e0d9efbe7a7a27f3900c4f388",
        migration_head_before="0029_food_composition_core",
        migration_head_after=head(config),
        upgrade_strategy="Explicit hash-pinned app.seed.b2b2 operation on existing 0029; one UoW, complete before/after receipt, no schema change, idempotent replay; native backup/restore.",
        food_count_before=len(before["food_ingredients"]),
        food_count_after=len(after["food_ingredients"]),
        target_rows=37,
        impact_usages=46,
        first_run=first,
        second_run=second,
        historical_current_marker_retirements=switches,
        historical_rows_preserved=True,
        old_seals_read_unchanged=len(vectors_before),
        old_compositions_replayed_unchanged=len(compositions_before),
        native_backup_restore_replay=True,
        foreign_keys_clean=True,
        integrity_check="ok",
        readiness_before=ready_before,
        readiness_after=ready_after,
        full_readiness_sha256_before=digest(ready_before),
        full_readiness_sha256_after=digest(ready_after),
        row_delta=delta,
        recipe_status_delta=recipe_delta,
        pr6_status="NOT COMPLETE",
        estimate_policy="All historical estimated evidence preserved; only 3 current usages independently superseded by new exact authority. Remaining 40 estimates non-executable.",
    )
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    with TemporaryDirectory() as folder:
        result = measure(DatabaseConfig(path=Path(folder) / "audit.sqlite"))
    path = PACKAGE / "implementation-evidence.json"
    encoded = json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if args.write:
        path.write_text(encoded)
    else:
        assert path.read_text() == encoded, "B2-B2 implementation evidence differs"
    print(
        json.dumps(
            {
                k: v
                for k, v in result.items()
                if k not in {"readiness_before", "readiness_after", "row_delta"}
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
