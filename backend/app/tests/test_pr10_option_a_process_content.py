"""Regression guard for the PR10 Option A *synthetic evidence* process digest.

No database, Planner, network, ingestion, or executable Prep authority is used.
"""

from __future__ import annotations

import hashlib
import json
import re
from copy import deepcopy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
RECEIPT = (
    ROOT
    / "docs/family-food/evidence/pr196-original-synthetic-fixture-receipt.json"
)
ORIGINAL_JSON_SHA256 = (
    "6c157ddead856ca2d109a698f221fc89472fda897c8f6473ceea0672afed04ec"
)
PROCESS_CONTENT_V1_SHA256 = (
    "d19f11a0074d095eaac02fc1d414a1f3d6a5088a884c78d27436984a63023d36"
)
HEX_SHA256 = re.compile(r"[0-9a-f]{64}\Z")


def _sha256(value: object) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _process_content_v1(catalogue: list[dict]) -> str:
    """Hash {canonical_code: SHA256(source identity + ordered UUID-free steps)}."""
    hashes: dict[str, str] = {}
    for recipe in catalogue:
        code = recipe["canonical_code"]
        if not isinstance(code, str) or not code or code in hashes:
            raise ValueError("Duplicate or invalid canonical recipe code")
        steps = sorted(recipe["steps"], key=lambda s: s["position"])
        if not steps or [s["position"] for s in steps] != list(
            range(1, len(steps) + 1)
        ):
            raise ValueError("Missing, duplicate or out-of-order step position")
        if any(
            not isinstance(s["instruction_sha256"], str)
            or HEX_SHA256.fullmatch(s["instruction_sha256"]) is None
            for s in steps
        ):
            raise ValueError("Invalid instruction SHA256")
        payload = {
            "canonical_code": code,
            "source_name": recipe["source_name"],
            "source_recipe_id": recipe["source_recipe_id"],
            "source_version": recipe["source_version"],
            "source_document_sha256": recipe["source_document_sha256"],
            "ordered_steps": [
                {
                    "position": s["position"],
                    "instruction_sha256": s["instruction_sha256"],
                    "stage_code": s["stage_code"],
                }
                for s in steps
            ],
        }
        hashes[code] = _sha256(payload)
    return _sha256(hashes)


@pytest.fixture(scope="module")
def original_receipt() -> dict:
    raw = RECEIPT.read_bytes()
    assert len(raw) == 110_511
    assert hashlib.sha256(raw).hexdigest() == ORIGINAL_JSON_SHA256
    receipt = json.loads(raw)
    assert receipt["schema"] == "PR10_META_GATE2_FIXTURE_PINS_V1"
    assert receipt["scope"] == "SYNTHETIC_FRESH_SQLITE_PERSISTED_DIAGNOSTIC_ONLY"
    assert receipt["gate_decision"] == "BLOCKED"
    assert receipt["counts"]["members"] == 3
    assert receipt["counts"]["meal_events"] == 21
    assert receipt["counts"]["servings"] == 42
    assert len(receipt["catalogue"]) == 51
    return receipt


def test_original_archive_matches_published_portable_process_digest(original_receipt):
    assert _process_content_v1(original_receipt["catalogue"]) == (
        PROCESS_CONTENT_V1_SHA256
    )


def test_uuid_and_run_local_process_hash_do_not_change_portable_digest(
    original_receipt,
):
    changed = deepcopy(original_receipt["catalogue"])
    for recipe in changed:
        recipe["process_hash"] = "0" * 64
        recipe["recipe_version_id"] = "00000000-0000-4000-8000-000000000001"
        for step in recipe["steps"]:
            step["recipe_step_id"] = "00000000-0000-4000-8000-000000000002"
    assert _process_content_v1(changed) == PROCESS_CONTENT_V1_SHA256


@pytest.mark.parametrize("tamper", ["step", "order", "source", "duplicate_code"])
def test_semantic_process_tampering_changes_digest_or_is_rejected(
    original_receipt, tamper
):
    changed = deepcopy(original_receipt["catalogue"])
    if tamper == "step":
        changed[0]["steps"][0]["instruction_sha256"] = "a" * 64
    elif tamper == "order":
        changed[0]["steps"][0]["position"] = 999
    elif tamper == "source":
        changed[0]["source_recipe_id"] += "-changed"
    else:
        changed[1]["canonical_code"] = changed[0]["canonical_code"]
    try:
        assert _process_content_v1(changed) != PROCESS_CONTENT_V1_SHA256
    except ValueError:
        pass  # Structural tampering fails closed rather than producing a digest.
