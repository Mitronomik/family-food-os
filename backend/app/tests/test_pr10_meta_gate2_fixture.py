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
    assert len(result["planner"]["expected_semantic_pins_sha256"]) == 64
    assert len({e["local_date"] for e in result["plan"]["events"]}) == 7
    assert all(Decimal(s["portion_servings"]) > 0 for s in result["plan"]["servings"])
    assert all(len(row["process_hash"]) == 64 for row in result["catalogue"])
    assert all(
        row["steps"]
        and all(len(step["instruction_sha256"]) == 64 for step in row["steps"])
        for row in result["catalogue"]
    )



def _move_to_valid_alternate_event(receipt):
    pairs = {
        (s["event_id"], s["member_id"]) for s in receipt["plan"]["servings"]
    }
    selected = receipt["plan"]["servings"][0]
    target = next(
        event["event_id"]
        for event in receipt["plan"]["events"]
        if event["event_id"] != selected["event_id"]
        and (event["event_id"], selected["member_id"]) not in pairs
    )
    selected["event_id"] = target


def _duplicate_event_member_pair(receipt):
    first = receipt["plan"]["servings"][0]
    other = next(
        s
        for s in receipt["plan"]["servings"][1:]
        if s["event_id"] != first["event_id"]
        or s["member_id"] != first["member_id"]
    )
    other["event_id"] = first["event_id"]
    other["member_id"] = first["member_id"]


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
        lambda r: r["counts"].update(meal_events=0),
        lambda r: r["counts"].update(servings=100),
        lambda r: r["counts"].update(current_verified_catalogue_versions=0),
        lambda r: r["counts"].update(unique_selected_versions=0),
        lambda r: r["plan"]["events"][0].update(
            recipe_version_id=r["catalogue"][-1]["recipe_version_id"]
            if r["catalogue"][-1]["recipe_version_id"]
            != r["plan"]["events"][0]["recipe_version_id"]
            else r["catalogue"][-2]["recipe_version_id"]
        ),
        _move_to_valid_alternate_event,
        _duplicate_event_member_pair,
        lambda r: r["plan"]["servings"][0].update(portion_servings="Infinity"),
        lambda r: r["plan"]["servings"][0].update(portion_servings="-Infinity"),
        lambda r: r["plan"]["servings"][0].update(portion_servings="NaN"),
        lambda r: r["catalogue"][0].update(process_hash="a" * 64),
        lambda r: r["catalogue"][0]["steps"][0].update(
            instruction_sha256="b" * 64
        ),
        lambda r: r["plan"]["events"][0].update(
            role="BREAKFAST"
            if r["plan"]["events"][0]["role"] != "BREAKFAST"
            else "DINNER"
        ),
        lambda r: r["plan"]["events"][0].update(
            local_date=r["plan"]["events"][1]["local_date"]
        ),
        lambda r: r["planner"].update(
            expected_semantic_pins_sha256="a" * 64
        ),
    ],
)
def test_receipt_fails_closed_for_changed_or_missing_pins(fixture_receipt, tamper):
    altered = deepcopy(fixture_receipt)
    tamper(altered)
    with pytest.raises(ValueError):
        validate_fixture_receipt(altered)

def test_forged_internal_baseline_fails_with_external_trusted_digest(fixture_receipt):
    altered = deepcopy(fixture_receipt)
    original_digest = fixture_receipt["planner"]["expected_semantic_pins_sha256"]
    altered["plan"]["events"][0]["recipe_version_id"] = next(
        version["recipe_version_id"]
        for version in altered["catalogue"]
        if version["recipe_version_id"]
        != altered["plan"]["events"][0]["recipe_version_id"]
    )
    from scripts.audit_pr10_meta_gate2_fixture import (
        _receipt_semantic_events,
        _semantic_pins,
    )

    altered["planner"]["expected_semantic_pins_sha256"] = _semantic_pins(
        _receipt_semantic_events(
            altered["plan"]["events"], altered["plan"]["servings"]
        )
    )
    with pytest.raises(ValueError):
        validate_fixture_receipt(
            altered, trusted_semantic_pins_sha256=original_digest
        )
