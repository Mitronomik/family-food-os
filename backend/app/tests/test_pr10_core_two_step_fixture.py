"""Issue #245: independent exact two-step readback/negative fixture checks."""

from copy import deepcopy
from decimal import Decimal

import pytest
from app.db.config import DatabaseConfig

from scripts.audit_pr10_core_two_step_fixture import (
    REPO_ROOT,
    TARGETS,
    TRUSTED_SEMANTIC_SHA256,
    extract_two_step_evidence,
    validate_two_step_evidence,
)
from scripts.audit_pr10_meta_gate2_fixture import (
    _hash,
    build_fixture_receipt,
)


@pytest.fixture(scope="module")
def fixture_and_evidence(tmp_path_factory):
    path = tmp_path_factory.mktemp("pr10-core-two-step") / "fresh-fixture.sqlite"
    fixture = build_fixture_receipt(DatabaseConfig(path=path))
    evidence = extract_two_step_evidence(fixture)
    return fixture, evidence


def test_current_persisted_receipt_pins_two_distinct_steps(fixture_and_evidence):
    fixture, receipt = fixture_and_evidence
    validate_two_step_evidence(receipt, fixture)
    assert receipt["schema"] == "PR10_CORE_TWO_STEP_PERSISTED_FIXTURE_EVIDENCE_V1"
    assert receipt["scope"] == "SYNTHETIC_FRESH_SQLITE_READBACK_DIAGNOSTIC_ONLY"
    assert receipt["fixture_planner_semantic_sha256"] == TRUSTED_SEMANTIC_SHA256
    assert receipt["fixture_counts"]["members"] == 3
    assert receipt["fixture_counts"]["meal_events"] == 21
    assert receipt["fixture_counts"]["servings"] == 42
    assert receipt["distinct_current_meal_events"] == 2
    assert receipt["gate"] == "NO_GO_TO_PR10_CORE_RUNTIME"
    assert receipt["independently_approved_step_count"] == 0
    assert receipt["policy_publisher_reader"] == "NOT_IMPLEMENTED"
    assert receipt["safety"]["no_pantry_mutation"] is True
    assert all(not c["production_executable_task_allowed"] for c in receipt["candidates"])
    assert all(c["reviewer_identity"] is None for c in receipt["candidates"])
    assert {c["canonical_recipe_code"] for c in receipt["candidates"]} == {
        t["code"] for t in TARGETS
    }
    assert all(c["recipe_step_position"] == 1 for c in receipt["candidates"])
    assert all(c["recipe_step_instruction_sha256"] == _hash(c["instruction_ru"]) for c in receipt["candidates"])
    assert all(len(c["recipe_process_hash"]) == 64 for c in receipt["candidates"])

    by_code = {c["canonical_recipe_code"]: c for c in receipt["candidates"]}
    assert Decimal(by_code[TARGETS[0]["code"]]["ingredient_source_net_g"]) == Decimal("139.5")
    assert Decimal(by_code[TARGETS[1]["code"]]["ingredient_source_net_g"]) == Decimal("40")
    for row in receipt["candidates"]:
        contributions = row["participant_servings"]
        assert contributions
        assert len({c["member_id"] for c in contributions}) == len(contributions)
        factor = sum((Decimal(c["portion_servings"]) for c in contributions), Decimal(0))
        original_g = Decimal(row["ingredient_source_net_g"])
        assert Decimal(row["sum_portion_servings"]) == factor
        assert Decimal(row["ingredient_net_g_research_projection"]) == factor * original_g
        assert all(
            Decimal(c["ingredient_net_g"]) == Decimal(c["portion_servings"]) * original_g
            for c in contributions
        )


@pytest.mark.parametrize(
    "field,value",
    [
        ("meal_event_id", "foreign-household-event"),
        ("recipe_version_id", "stale-recipe-version"),
        ("recipe_step_id", "stale-step"),
        ("recipe_step_instruction_sha256", "a" * 64),
        ("ingredient_source_net_g", "0"),
        ("sum_portion_servings", "NaN"),
        ("immediate_eligibility", "APPROVED_IMMEDIATE"),
        ("production_executable_task_allowed", True),
        ("source_manifest_git_blob_sha", "b" * 40),
    ],
)
def test_source_or_authority_tamper_is_rejected(
    fixture_and_evidence, field, value
):
    fixture, receipt = fixture_and_evidence
    forged = deepcopy(receipt)
    forged["candidates"][0][field] = value
    with pytest.raises(ValueError):
        validate_two_step_evidence(forged, fixture)


def test_cross_event_serving_and_nonfinite_source_are_rejected(fixture_and_evidence):
    fixture, _ = fixture_and_evidence
    changed = deepcopy(fixture)
    selected = next(
        row for row in changed["plan"]["servings"]
        if any(
            event["event_id"] == row["event_id"]
            and event["local_date"] == "2026-09-18"
            for event in changed["plan"]["events"]
        )
    )
    selected["portion_servings"] = "Infinity"
    with pytest.raises(ValueError):
        extract_two_step_evidence(changed)


def test_both_source_manifests_have_trusted_git_blob_pins(fixture_and_evidence, tmp_path):
    fixture, _ = fixture_and_evidence
    for target in TARGETS:
        source = REPO_ROOT / target["manifest"]
        alternate = tmp_path / target["manifest"]
        alternate.parent.mkdir(parents=True, exist_ok=True)
        # One-byte/source-file difference must not be accepted as an eligibility
        # input even when its RecipeVersion instruction looks otherwise similar.
        alternate.write_bytes(source.read_bytes() + b" ")
    with pytest.raises(ValueError, match="manifest Git blob changed"):
        extract_two_step_evidence(fixture, root=tmp_path)


def test_unreviewed_but_valid_source_never_grants_permission(fixture_and_evidence):
    _, receipt = fixture_and_evidence
    assert len(receipt["candidates"]) == 2
    assert all(c["numeric_syntax_observation"] == "NO_DIGITS_NOT_REVIEWED_APPROVAL" for c in receipt["candidates"])
    assert all(c["immediate_eligibility"] == "PENDING_INDEPENDENT_REVIEW" for c in receipt["candidates"])
    assert receipt["independently_approved_step_count"] == 0
