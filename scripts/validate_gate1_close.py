"""Validate the separate Gate1-CLOSE decision against accepted current truth."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path
from typing import Any

from sqlalchemy import func, select

from app.db import migrations
from app.db.config import REPOSITORY_ROOT, DatabaseConfig
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
from app.persistence.sqlalchemy_core.food_ingredient_tables import food_ingredients_table
from app.persistence.sqlalchemy_core.food_recipe_composition import (
    create_food_recipe_catalogue_service,
)
from app.seed.dc4_a3_russian_step_corrections import (
    seed_dc4_a3_russian_step_corrections,
)

RERUN_SUMMARY = (
    REPOSITORY_ROOT / "data/curation/dc4-corpus-readiness/rerun-summary.json"
)
GATE1_MIN_VERIFIED_RECIPES = 30
GATE1_MIN_ACTIVE_FOODS = 80
REQUIRED_REUSED_EVIDENCE = {
    "MEAL_PATTERN_1_2_3_5_6_OPPORTUNITIES",
    "MEAL_PATTERN_SEVEN_OPPORTUNITY_BOUNDARY",
    "MEAL_PATTERN_ACCEPTANCE_PERSISTENCE",
    "MEAL_TYPE_DISTINCT_FROM_MEAL_ROLE",
    "MEAL_SOURCE_KIND_BOUNDARIES_NO_FABRICATION",
    "PROVENANCE_TAMPER_AND_PROCESS_DRIFT_FAIL_CLOSED",
    "NO_GATE_ONLY_AUTHORITY",
}


def _load_rerun_summary() -> dict[str, Any]:
    payload = json.loads(RERUN_SUMMARY.read_text(encoding="utf-8"))
    if payload.get("schema") != "DC4_READINESS_RERUN_EVIDENCE_V1":
        raise ValueError("Unexpected DC4 rerun evidence schema.")
    return payload


def _current_baseline(config: DatabaseConfig) -> dict[str, Any]:
    seed_dc4_a3_russian_step_corrections(config)
    engine = create_sqlite_engine(config)
    try:
        recipes = create_food_recipe_catalogue_service(engine)
        active_recipes = tuple(recipe for recipe in recipes.list_all() if recipe.is_active)
        verified_current = tuple(
            recipes.get_current_verified(recipe.id) for recipe in active_recipes
        )
        with engine.connect() as connection:
            active_food_count = connection.execute(
                select(func.count())
                .select_from(food_ingredients_table)
                .where(food_ingredients_table.c.is_active.is_(True))
            ).scalar_one()
    finally:
        engine.dispose()

    return {
        "active_food_ingredient_count": int(active_food_count),
        "active_recipe_count": len(active_recipes),
        "verified_current_recipe_count": len(verified_current),
    }


def validate(config: DatabaseConfig) -> dict[str, Any]:
    rerun = _load_rerun_summary()
    audit = rerun["audit"]
    reused = rerun.get("reused_evidence") or {}
    requirements = {
        row["requirement"]: row for row in reused.get("requirements", [])
    }

    baseline = _current_baseline(config)
    fixtures = audit["fixtures"]
    bounded = audit["bounded_infeasibility"]
    migration_ids = migrations.expected_migration_ids()
    ai_enabled = os.getenv("AI_ENABLED", "false").strip().lower() == "true"

    criteria = {
        "dc4_rerun_accepted_pass_receipt": (
            audit["overall_status"] == "PASS" and audit["blockers"] == []
        ),
        "three_materially_different_fixtures": (
            [row["member_count"] for row in fixtures] == [1, 2, 3]
            and [row["event_count"] for row in fixtures] == [7, 14, 21]
        ),
        "minimum_verified_recipes": (
            baseline["verified_current_recipe_count"] >= GATE1_MIN_VERIFIED_RECIPES
            and audit["catalogue"]["active_count"] >= GATE1_MIN_VERIFIED_RECIPES
            and audit["catalogue"]["blocked_count"] == 0
        ),
        "minimum_active_food_ingredients": (
            baseline["active_food_ingredient_count"] >= GATE1_MIN_ACTIVE_FOODS
        ),
        "planner_v05_current": audit["planner_version"] == "planner-v0.5",
        "planner_supply_reconciled": (
            audit["planner_supply"]["eligible_count"] == 51
            and audit["planner_supply"]["meal_type_counts"]
            == {"breakfast": 17, "main": 33, "sandwich": 1}
        ),
        "mandatory_fixtures_complete": (
            all(row["success"] for row in fixtures)
            and [row["serving_count"] for row in fixtures] == [7, 21, 42]
            and all(row["persistence_error"] is None for row in fixtures)
        ),
        "deterministic_replay": (
            all(row["deterministic"] for row in fixtures)
            and all(bool(row["trace_fingerprint"]) for row in fixtures)
        ),
        "hard_constraints_respected": all(
            row["selected_exclusions_respected"] for row in fixtures
        ),
        "bounded_failure_no_partial_state": (
            bounded["is_failure"]
            and bounded["failure_code"] == "NO_ELIGIBLE_CANDIDATE"
            and not bounded["returned_persisted_plan"]
            and not bounded["partial_plan_exists"]
            and bounded["hard_exclusion_rejections"] > 0
            and bounded["max_repetition_rejections"] > 0
        ),
        "reused_domain_evidence_complete": (
            set(requirements) == REQUIRED_REUSED_EVIDENCE
            and all(row.get("status") == "SUCCESS" for row in requirements.values())
        ),
        "unknown_not_promoted": all(
            row["available_nutrient_count"] == 1
            and row["unknown_nutrient_count"] == 53
            for row in audit["catalogue"]["recipes"]
        ),
        "migration_head_0042_no_0043": (
            migration_ids[-1] == "0042_recipe_prepared_output_nutrition"
            and not any(item.startswith("0043") for item in migration_ids)
            and audit["migration_ok"]
        ),
        "ai_disabled": not ai_enabled and audit["ai_enabled_required"] is False,
    }

    failed = sorted(key for key, passed in criteria.items() if not passed)
    return {
        "schema": "GATE1_CLOSE_DECISION_V1",
        "accepted_base": "c85fae8e8e2c135855f1ba64ca6722de20e1bd29",
        "decision": "CLOSE" if not failed else "BLOCKED",
        "planning_core_status": "COMPLETE" if not failed else "INCOMPLETE",
        "pr9_authorized_after_merge": not failed,
        "baseline": baseline,
        "gate1_thresholds": {
            "minimum_verified_recipes": GATE1_MIN_VERIFIED_RECIPES,
            "minimum_active_food_ingredients": GATE1_MIN_ACTIVE_FOODS,
        },
        "dc4_rerun_evidence": {
            "overall_status": audit["overall_status"],
            "planner_version": audit["planner_version"],
            "active_recipe_count": audit["catalogue"]["active_count"],
            "blocked_recipe_count": audit["catalogue"]["blocked_count"],
            "planner_eligible_count": audit["planner_supply"]["eligible_count"],
            "meal_type_counts": audit["planner_supply"]["meal_type_counts"],
            "fixture_event_counts": [row["event_count"] for row in fixtures],
            "fixture_serving_counts": [row["serving_count"] for row in fixtures],
            "bounded_failure_code": bounded["failure_code"],
        },
        "criteria": criteria,
        "failed_criteria": failed,
        "reused_evidence_requirements": sorted(requirements),
        "next_milestone_on_merge": (
            "PR9_SHOPPING_ENGINE" if not failed else None
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database")
    parser.add_argument("--output")
    parser.add_argument("--require-pass", action="store_true")
    args = parser.parse_args()

    if args.database:
        payload = validate(DatabaseConfig(path=Path(args.database)))
    else:
        with tempfile.TemporaryDirectory(prefix="family-food-gate1-close-") as tmp:
            payload = validate(DatabaseConfig(path=Path(tmp) / "gate1-close.sqlite"))

    rendered = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
    print(rendered)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered + "\n", encoding="utf-8")
    if args.require_pass and payload["decision"] != "CLOSE":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
