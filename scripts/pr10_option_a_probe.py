"""Option A synthetic fixture cross-process diagnostic; no runtime authority.

Run with ``python -m scripts.pr10_option_a_probe --output /tmp/proof.json``.
A NO_GO exits non-zero and must not be misreported as successful reproduction.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from decimal import Decimal, InvalidOperation
from pathlib import Path

from app.db.config import DatabaseConfig

from scripts.audit_pr10_meta_gate2_fixture import (
    build_fixture_receipt,
    validate_fixture_receipt,
)

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = ROOT / "docs/family-food/evidence/pr196-original-synthetic-fixture-receipt.json"
ORIGINAL_SHA = "6c157ddead856ca2d109a698f221fc89472fda897c8f6473ceea0672afed04ec"
ORIGINAL_WEEK_SHA = "731ef32e7137740ed5b46a6044a85d8b2f818a847fdc039842460d442df5aeb6"
CANONICAL_DECIMAL = re.compile(r"[0-9]+\.[0-9]{6}\Z")


def _hash(value: object) -> str:
    raw = json.dumps(
        value, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def normalize_receipt(receipt: dict) -> list[dict]:
    """Portable comparison of real persisted MealEvents and Servings, never UUIDs."""
    if receipt.get("scope") != "SYNTHETIC_FRESH_SQLITE_PERSISTED_DIAGNOSTIC_ONLY":
        raise ValueError("wrong receipt scope")
    if receipt.get("gate_decision") != "BLOCKED":
        raise ValueError("receipt must never confer Prep approval")
    counts = receipt["counts"]
    if any(
        counts.get(key) != expected
        for key, expected in (("members", 3), ("meal_events", 21), ("servings", 42))
    ):
        raise ValueError("3/21/42 structure missing")
    member_ordinal = {row["member_id"]: row["fixture_ordinal"] for row in receipt["members"]}
    if len(member_ordinal) != 3 or set(member_ordinal.values()) != {1, 2, 3}:
        raise ValueError("invalid unique synthetic member ordinals")
    by_version = {row["recipe_version_id"]: row for row in receipt["catalogue"]}
    if len(by_version) != 51 or len({r["canonical_code"] for r in by_version.values()}) != 51:
        raise ValueError("unverified or ambiguous source catalogue")
    events = receipt["plan"]["events"]
    if len({e["event_id"] for e in events}) != 21:
        raise ValueError("duplicate event UUID")
    if len({(e["local_date"], e["position"]) for e in events}) != 21:
        raise ValueError("duplicate date/position")
    by_event = {e["event_id"]: [] for e in events}
    for row in receipt["plan"]["servings"]:
        amount = row["portion_servings"]
        if not isinstance(amount, str) or CANONICAL_DECIMAL.fullmatch(amount) is None:
            raise ValueError("Serving is not an exact six-place Decimal string")
        try:
            n = Decimal(amount)
        except InvalidOperation as exc:
            raise ValueError("Serving Decimal invalid") from exc
        if not n.is_finite() or n <= 0:
            raise ValueError("Serving must be finite and positive")
        if row["member_id"] not in member_ordinal or row["event_id"] not in by_event:
            raise ValueError("unbound member/event relationship")
        by_event[row["event_id"]].append(
            {
                "member_ordinal": member_ordinal[row["member_id"]],
                "portion_servings": amount,
            }
        )
    if sum(map(len, by_event.values())) != counts["servings"]:
        raise ValueError("Serving count differs from immutable 3/21/42 claim")
    normalized = []
    for e in events:
        if e["source_kind"] != "COOK_RECIPE" or e["recipe_version_id"] not in by_version:
            raise ValueError("non-canonical selected recipe")
        r = by_version[e["recipe_version_id"]]
        serving_rows = sorted(by_event[e["event_id"]], key=lambda x: x["member_ordinal"])
        if not serving_rows or len({s["member_ordinal"] for s in serving_rows}) != len(serving_rows):
            raise ValueError("missing or duplicated participant Serving")
        normalized.append(
            {
                "local_date": e["local_date"],
                "position": e["position"],
                "role": e["role"],
                "source_kind": e["source_kind"],
                "canonical_recipe_code": r["canonical_code"],
                "source_recipe_id": r["source_recipe_id"],
                "source_version": r["source_version"],
                "source_document_sha256": r["source_document_sha256"],
                "servings": serving_rows,
            }
        )
    return sorted(normalized, key=lambda x: (x["local_date"], x["position"]))


def _original_week() -> tuple[list[dict], str]:
    raw = ORIGINAL.read_bytes()
    if len(raw) != 110511 or hashlib.sha256(raw).hexdigest() != ORIGINAL_SHA:
        raise ValueError("original external raw artifact pin mismatch")
    rows = normalize_receipt(json.loads(raw))
    digest = _hash(rows)
    if digest != ORIGINAL_WEEK_SHA:
        raise ValueError("original canonical week digest mismatch")
    return rows, digest


def _run_one(path: Path) -> None:
    """Use the unmodified existing real PlannerService → persisted-readback path."""
    with tempfile.TemporaryDirectory(prefix="pr10-option-a-sqlite-") as tmp:
        receipt = build_fixture_receipt(DatabaseConfig(path=Path(tmp) / "fixture.sqlite"))
        validate_fixture_receipt(receipt)
        normalize_receipt(receipt)
        path.write_text(json.dumps(receipt, sort_keys=True, ensure_ascii=False), encoding="utf-8")


def _probe(output: Path) -> int:
    original_events, expected = _original_week()
    report: dict = {
        "schema": "PR10_OPTION_A_TWO_RUN_DIAGNOSTIC_V1",
        "source_raw_sha256": ORIGINAL_SHA,
        "expected_uuid_free_week_sha256": expected,
        "planner_execution": "existing_build_fixture_receipt_real_PlannerService_and_persisted_readback",
        "independent_processes": 2,
        "production_planner_modified": False,
        "status": "NO_GO_UNVERIFIED",
        "runs": [],
        "approved_immediate": 0,
        "safe_batch_ready": False,
        "portion_release_ready": "NOT_PROVEN",
    }
    with tempfile.TemporaryDirectory(prefix="pr10-option-a-processes-") as temp:
        for n in range(2):
            path = Path(temp) / f"run-{n + 1}.json"
            step = subprocess.run(
                [sys.executable, "-m", "scripts.pr10_option_a_probe", "--run-one", str(path)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            if step.returncode:
                report["runs"].append({"ordinal": n + 1, "result": "FAILED_REAL_PIPELINE"})
                report["status"] = "NO_GO_REAL_PIPELINE_FAILURE"
                break
            raw = path.read_bytes()
            receipt = json.loads(raw)
            actual_rows = normalize_receipt(receipt)
            actual = _hash(actual_rows)
            matches = sum(
                x["canonical_recipe_code"] == y["canonical_recipe_code"]
                for x, y in zip(original_events, actual_rows)
                if (x["local_date"], x["position"]) == (y["local_date"], y["position"])
            )
            report["runs"].append(
                {
                    "ordinal": n + 1,
                    "receipt_raw_sha256": hashlib.sha256(raw).hexdigest(),
                    "portable_week_sha256": actual,
                    "matches_original": actual == expected,
                    "matching_original_slot_recipes": matches,
                    "real_plan_readback": True,
                    "catalogue_source_versions": len(receipt["catalogue"]),
                    "counts": receipt["counts"],
                }
            )
        if len(report["runs"]) == 2 and all(r["matches_original"] for r in report["runs"]):
            report["status"] = "CANDIDATE_TWO_RUN_PASS_AWAIT_INDEPENDENT_REVIEW"
        elif report["status"] == "NO_GO_UNVERIFIED":
            report["status"] = "NO_GO_OPTION_A_UNACHIEVABLE_WITH_CURRENT_UNSTABILIZED_SEED"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "runs": report["runs"]}, ensure_ascii=False))
    return 0 if report["status"].startswith("CANDIDATE_TWO_RUN_PASS") else 3


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-one", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if bool(args.run_one) == bool(args.output):
        parser.error("pass exactly --run-one or --output")
    if args.run_one:
        _run_one(args.run_one)
        return 0
    return _probe(args.output)


if __name__ == "__main__":
    raise SystemExit(main())