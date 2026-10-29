"""Option A preflight guard: original vs drift, with adversarial tamper rejection."""

from __future__ import annotations

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
        lambda r: r["plan"]["events"][0].update(position=r["plan"]["events"][1]["position"]),
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