"""PR10-META fixture evidence: real persistence and adversarial receipt checks."""

from copy import deepcopy
from decimal import Decimal

import pytest
from app.db.config import DatabaseConfig

from scripts.audit_pr10_meta_gate2_fixture import (
    build_fixture_receipt,
    validate_fixture_receipt,
)


@pytest.fixture(scope="module")
def fixture_receipt(tmp_path_factory):
    path = tmp_path_factory.mktemp("pr10-meta") / "gate2-fixture.sqlite"
    return build_fixture_receipt(DatabaseConfig(path=path))


def test_frozen_repo_backed_fixture_has_valid_source_and_serving_pins(fixture_receipt):
    result = fixture_receipt
    validate_fixture_receipt(result)
    assert result["scope"] == "SYNTHETIC_FRESH_SQLITE_PERSISTED_DIAGNOSTIC_ONLY"
    assert result["gate_decision"] == "BLOCKED"
    assert result["counts"]["members"] == 3
    assert result["counts"]["meal_events"] == 21
    assert result["counts"]["servings"] == 42
    assert result["counts"]["current_verified_catalogue_versions"] >= 30
    assert result["plan"]["revision_number"] == 1
    assert result["planner"]["deterministic"] is True
    assert result["planner"]["selected_exclusion_violations"] == []
    assert len({e["local_date"] for e in result["plan"]["events"]}) == 7
    assert all(Decimal(s["portion_servings"]) > 0 for s in result["plan"]["servings"])
    assert all(len(row["process_hash"]) == 64 for row in result["catalogue"])
    assert all(
        row["steps"] and all(len(step["instruction_sha256"]) == 64 for step in row["steps"])
        for row in result["catalogue"]
    )


@pytest.mark.parametrize(
    "tamper",
    [
        lambda r: r["plan"]["events"][0].update(
            recipe_version_id="00000000-0000-4000-8000-000000000001"
        ),
        lambda r: r["plan"]["servings"][0].update(
            event_id="00000000-0000-4000-8000-000000000002"
        ),
        lambda r: r["plan"]["servings"][0].update(portion_servings="0"),
        lambda r: r["plan"]["events"][0].update(plan_id="foreign-plan"),
        lambda r: r["plan"]["events"].pop(),
        lambda r: r["plan"]["servings"].pop(),
        lambda r: r.update(gate_decision="READY"),
        lambda r: r["catalogue"].clear(),
        lambda r: r["members"].pop(),
    ],
)
def test_receipt_fails_closed_for_changed_or_missing_pins(fixture_receipt, tamper):
    altered = deepcopy(fixture_receipt)
    tamper(altered)
    with pytest.raises(ValueError):
        validate_fixture_receipt(altered)
