from pathlib import Path

from app.db.config import DatabaseConfig
from scripts.audit_dc4_corpus_readiness import audit


def test_dc4_reproducible_corpus_and_gate1_evidence(tmp_path: Path) -> None:
    result = audit(DatabaseConfig(path=tmp_path / "dc4.sqlite"))

    catalogue = result["catalogue"]
    supply = result["planner_supply"]
    fixtures = result["fixtures"]
    bounded = result["bounded_infeasibility"]

    assert catalogue["active_count"] >= 51
    assert len(catalogue["recipes"]) == catalogue["active_count"]
    assert all(row["disposition"] in {"PASS", "BLOCKED"} for row in catalogue["recipes"])

    assert supply["eligible_count"] == 51
    assert supply["meal_type_counts"] == {
        "breakfast": 17,
        "main": 33,
        "sandwich": 1,
    }
    assert supply["matches_accepted_baseline"] is True

    assert [row["member_count"] for row in fixtures] == [1, 2, 3]
    assert [row["event_count"] for row in fixtures] == [7, 14, 21]
    assert [row["serving_count"] for row in fixtures] == [7, 21, 42]
    assert all(row["success"] for row in fixtures)
    assert all(row["deterministic"] for row in fixtures)
    assert fixtures[1]["hard_exclusion_rejections"] > 0
    assert fixtures[2]["hard_exclusion_rejections"] > 0

    assert bounded["is_failure"] is True
    assert bounded["returned_persisted_plan"] is False
    assert bounded["partial_plan_exists"] is False
    assert bounded["hard_exclusion_rejections"] > 0
    assert bounded["max_repetition_rejections"] > 0

    assert result["migration_head"] == "0042_recipe_prepared_output_nutrition"
    assert result["migration_ok"] is True
    assert result["ai_enabled_required"] is False


def test_dc4_audit_is_deterministic_at_gate_level(tmp_path: Path) -> None:
    first = audit(DatabaseConfig(path=tmp_path / "first.sqlite"))
    second = audit(DatabaseConfig(path=tmp_path / "second.sqlite"))

    assert first["catalogue"]["active_count"] == second["catalogue"]["active_count"]
    assert first["catalogue"]["blocked_recipe_codes"] == second["catalogue"]["blocked_recipe_codes"]
    assert first["planner_supply"]["eligible_count"] == second["planner_supply"]["eligible_count"]
    assert first["planner_supply"]["meal_type_counts"] == second["planner_supply"]["meal_type_counts"]
    assert [
        (row["fixture"], row["success"], row["event_count"], row["serving_count"])
        for row in first["fixtures"]
    ] == [
        (row["fixture"], row["success"], row["event_count"], row["serving_count"])
        for row in second["fixtures"]
    ]
    assert first["overall_status"] == second["overall_status"]
    assert first["blockers"] == second["blockers"]
