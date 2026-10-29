"""Option A preflight guard: original vs drift, with adversarial tamper rejection."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from decimal import Decimal

import pytest

from scripts.pr10_option_a_probe import (
    ORIGINAL,
    ORIGINAL_SHA,
    ORIGINAL_WEEK_SHA,
    _hash,
    _original_week,
    normalize_receipt,
)


def _original():
    return json.loads(ORIGINAL.read_bytes())


def test_archived_original_week_is_not_only_a_structural_fixture():
    rows, digest = _original_week()
    assert len(rows) == 21
    assert sum(len(row["servings"]) for row in rows) == 42
    assert len({(row["local_date"], row["position"]) for row in rows}) == 21
    assert digest == ORIGINAL_WEEK_SHA
    assert _hash(rows) == ORIGINAL_WEEK_SHA
    assert len(ORIGINAL_SHA) == 64
    assert all(
        Decimal(value["portion_servings"]) > 0
        for row in rows
        for value in row["servings"]
    )


def test_generated_ids_may_change_without_affecting_portable_week_digest():
    receipt = _original()
    for row in receipt["members"]:
        original = row["member_id"]
        replacement = "synthetic-" + original
        row["member_id"] = replacement
        for serving in receipt["plan"]["servings"]:
            if serving["member_id"] == original:
                serving["member_id"] = replacement
    for row in receipt["catalogue"]:
        old = row["recipe_version_id"]
        new = "synthetic-" + old
        row["recipe_version_id"] = new
        for event in receipt["plan"]["events"]:
            if event["recipe_version_id"] == old:
                event["recipe_version_id"] = new
    assert _hash(normalize_receipt(receipt)) == ORIGINAL_WEEK_SHA


@pytest.mark.parametrize(
    "change",
    [
        lambda r: r["counts"].update(servings=41),
        lambda r: r["plan"]["events"].pop(),
        lambda r: r["plan"]["servings"].pop(),
        lambda r: r["plan"]["servings"][0].update(portion_servings="NaN"),
        lambda r: r["plan"]["servings"][0].update(portion_servings="0.000000"),
        lambda r: r["plan"]["servings"][0].update(portion_servings=1.0),
        lambda r: r["plan"]["servings"][0].update(member_id="foreign-household"),
        lambda r: r["plan"]["events"][0].update(source_kind="OTHER"),
        lambda r: r["plan"]["events"][0].update(
            position=r["plan"]["events"][1]["position"]
        ),
        lambda r: r.update(gate_decision="READY"),
    ],
)
def test_invalid_current_receipt_fails_closed(change):
    receipt = deepcopy(_original())
    change(receipt)
    with pytest.raises((ValueError, KeyError, TypeError)):
        normalize_receipt(receipt)


def test_semantically_different_recipe_with_unchanged_counts_is_no_go():
    receipt = deepcopy(_original())
    original = normalize_receipt(receipt)
    first = receipt["plan"]["events"][0]
    alternative = next(
        item["recipe_version_id"]
        for item in receipt["catalogue"]
        if item["recipe_version_id"] != first["recipe_version_id"]
    )
    first["recipe_version_id"] = alternative
    changed = normalize_receipt(receipt)
    assert len(changed) == len(original) == 21
    assert _hash(changed) != ORIGINAL_WEEK_SHA


def test_one_decimal_digit_changes_frozen_semantics_even_if_positive():
    receipt = deepcopy(_original())
    first = receipt["plan"]["servings"][0]
    original = first["portion_servings"]
    first["portion_servings"] = original[:-1] + ("7" if original[-1] != "7" else "8")
    assert _hash(normalize_receipt(receipt)) != ORIGINAL_WEEK_SHA


@pytest.mark.parametrize(
    ("filename", "expected_size", "expected_raw_sha", "expected_week_sha", "matches"),
    [
        (
            "pr10-option-a-issue252-2026-10-29-run1.json",
            89291,
            "87789288aadfeca6f2a3bd4ec63cb1c69d19630df0d8dce933928224979a53b5",
            "4c1c574c26b5262edd64687cde292f16ecfc262111233bf60ad003cfbd47fb0f",
            0,
        ),
        (
            "pr10-option-a-issue252-2026-10-29-run2.json",
            89290,
            "b8c90d753447e4781b97f6e3207ca29d8809919c1e1b546ac1813ca3a0d7c4c5",
            "a7948dcc11e36131b11cd4397436ba30b9257a5b344d928d6430023258d36f04",
            1,
        ),
    ],
)
def test_archived_actual_two_process_receipts_are_source_pinned(
    filename, expected_size, expected_raw_sha, expected_week_sha, matches
):
    """An archived NO_GO cannot silently rewrite original/source/process truth."""
    raw = (ORIGINAL.parent / filename).read_bytes()
    assert len(raw) == expected_size
    assert hashlib.sha256(raw).hexdigest() == expected_raw_sha
    receipt = json.loads(raw)
    historical_receipt = _original()
    assert len(receipt["catalogue"]) == 51
    assert len(receipt["plan"]["events"]) == 21
    assert len(receipt["plan"]["servings"]) == 42
    assert receipt["gate_decision"] == "BLOCKED"

    def source_steps(data):
        return {
            row["canonical_code"]: (
                row["source_name"],
                row["source_recipe_id"],
                row["source_version"],
                row["source_document_sha256"],
                tuple(
                    (step["position"], step["instruction_sha256"], step["stage_code"])
                    for step in sorted(row["steps"], key=lambda s: s["position"])
                ),
            )
            for row in data["catalogue"]
        }

    assert source_steps(receipt) == source_steps(historical_receipt)
    historical_rows = {
        (row["local_date"], row["position"]): row
        for row in normalize_receipt(historical_receipt)
    }
    actual_rows = normalize_receipt(receipt)
    assert _hash(actual_rows) == expected_week_sha
    assert expected_week_sha != ORIGINAL_WEEK_SHA
    observed_matches = sum(
        historical_rows[(row["local_date"], row["position"])]["canonical_recipe_code"]
        == row["canonical_recipe_code"]
        for row in actual_rows
    )
    assert observed_matches == matches


def test_machine_diagnostic_is_immutable_no_go_not_positive_fixture():
    """The old, pre-sentinel-rename CI receipt is immutable historic evidence."""
    path = ORIGINAL.parent / "pr10-option-a-issue252-2026-10-29-report.json"
    raw = path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == (
        "7ef0ba589c09bdb43e2d68b6a938937bedc4f2de21a118fc0f39e3bec8decf79"
    )
    report = json.loads(raw)
    assert report["schema"] == "PR10_OPTION_A_TWO_RUN_DIAGNOSTIC_V1"
    assert report["status"] == (
        "NO_GO_OPTION_A_UNACHIEVABLE_WITH_CURRENT_UNSTABILIZED_SEED"
    )
    assert report["approved_immediate"] == 0
    assert report["production_planner_modified"] is False
    assert report["independent_processes"] == 2
    assert [run["matching_original_slot_recipes"] for run in report["runs"]] == [
        0,
        1,
    ]
    assert all(
        run["matches_original"] is False and run["real_plan_readback"] is True
        for run in report["runs"]
    )
