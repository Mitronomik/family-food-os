"""Gate1-A fresh-database audit regression proof."""

from collections import Counter
import json
from pathlib import Path

import pytest

from app.db.config import DatabaseConfig
from scripts.audit_gate1a_readiness import audit, capacity_audit


@pytest.fixture(scope="module")
def current_audit(tmp_path_factory):
    return audit(
        DatabaseConfig(path=tmp_path_factory.mktemp("gate1a") / "audit.sqlite")
    )


def test_generic_capacity_uses_one_sandwich_across_breakfast_and_lunch() -> None:
    capacity = capacity_audit()["generic_three_meal"]

    assert capacity == {
        "total": 7,
        "breakfast": 2,
        "main": 4,
        "sandwich": 1,
        "allocation": {"sandwich_breakfast_uses": 1, "sandwich_lunch_uses": 2},
    }


def test_actual_exclusion_and_fixed_event_fixture_capacity() -> None:
    capacity = capacity_audit()

    assert capacity["hard_exclusion"] == {
        "total": 8,
        "breakfast": 3,
        "main": 5,
        "sandwich": 0,
        "allocation": {"sandwich_breakfast_uses": 0, "sandwich_lunch_uses": 0},
    }
    assert capacity["heterogeneous_with_subset_fixed_event"] == {
        "total": 7,
        "breakfast": 2,
        "main": 4,
        "sandwich": 1,
        "allocation": {"sandwich_breakfast_uses": 1, "sandwich_lunch_uses": 2},
    }


def test_fresh_current_readiness_matrix(current_audit) -> None:
    result = current_audit

    assert result["accepted_starting_sha"] == (
        "ce5cf6e2faaf9159e74d8c235f334d47743ab2a0"
    )
    assert result["recipe_count"] == 30
    assert Counter(row["nutrition_status"] for row in result["recipes"]) == {
        "INCOMPLETE": 29,
        "CONDITIONAL": 1,
    }
    assert [
        row["recipe_code"]
        for row in result["recipes"]
        if row["technical_gate1_suitable"]
    ] == ["WIC1_OVERNIGHT_OATS_CINNAMON_APPLE"]
    assert all(not row["consumer_publication_ready"] for row in result["recipes"])
    assert [
        row["recipe_code"] for row in result["recipes"] if row["planner_eligible"]
    ] == ["WIC1_OVERNIGHT_OATS_CINNAMON_APPLE"]

    blockers = [
        blocker
        for row in result["recipes"]
        for blocker in row["blocking_ingredient_positions"]
    ]
    classes = {blocker["repair_class"] for blocker in blockers}
    assert "NEW_PRIMARY_EVIDENCE_REQUIRED" in classes
    assert "ALREADY_ACCEPTED_EVIDENCE_REBIND" in classes
    assert any(
        blocker["reusable_exact_evidence_keys"]
        for blocker in blockers
        if blocker["accepted_repository_evidence_resolves"]
    )
    assert all(
        blocker["new_external_primary_evidence_required"]
        == (blocker["repair_class"] == "NEW_PRIMARY_EVIDENCE_REQUIRED")
        for blocker in blockers
    )

    selected = result["repair_plan"]["selected_actual_fixture_targets"]
    assert len(selected) == 7
    assert Counter(row["meal_type_code"] for row in selected) == {
        "breakfast": 2,
        "main": 5,
    }


def test_committed_matrix_matches_fresh_current_truth(current_audit) -> None:
    result = current_audit
    committed = json.loads(
        (
            Path(__file__).resolve().parents[3]
            / "data/curation/gate1a-data-readiness/current-readiness.json"
        ).read_text(encoding="utf-8")
    )

    def without_local_ids(value):
        if isinstance(value, dict):
            return {
                key: without_local_ids(item)
                for key, item in value.items()
                if key not in {"id", "profile_id", "recipe_version_id"}
            }
        if isinstance(value, list):
            return [without_local_ids(item) for item in value]
        return value

    # Seed UUIDs are deployment-local; all semantic/provenance facts match.
    assert without_local_ids(result) == without_local_ids(committed)
