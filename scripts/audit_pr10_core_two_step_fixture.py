"""Issue #245: two-step evidence from the *current* persisted synthetic Planner fixture.

Never uses production/user data; never publishes executable Prep permissions.
A historical fixture SHA is used only as an independent semantic baseline, not
as a reusable MealEvent/Serving/RecipeStep identity.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from app.db.config import DatabaseConfig

from scripts.audit_pr10_meta_gate2_fixture import (
    _hash,
    build_fixture_receipt,
    validate_fixture_receipt,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
# Independently logged and accepted in PR #196, workflow run 38059374826.
TRUSTED_SEMANTIC_SHA256 = (
    "2d6cb581649863b7edbd3c0efff2bae2934c6a512c99a45d10e92f92f514cb3d"
)
SOURCE_DOC_SHA256 = "c9264cf521ae699fb30a964d5668caec8f31ff1efc1f13a3dd055df40ebafb5d"
TARGETS = (
    {
        "code": "SCHOOL2022_54_1T_COTTAGE_CHEESE_CASSEROLE",
        "date": "2026-09-18",
        "manifest": "data/curation/r2e-cottage-casserole/publication-specs.json",
        "manifest_git_blob_sha": "52f966d60226aec852d06790fe912e36f168cbdc",
        "source_recipe_id": "ru-school2022:recipe:54-1т",
        "ingredient": "TVOROG_5",
        "step": "Творог протереть.",
    },
    {
        "code": "SCHOOL2022_54_1K_LIQUID_CORN_MILK_PORRIDGE",
        "date": "2026-09-19",
        "manifest": "data/curation/r3b-school2022-breakfast-batch/publication-specs.json",
        "manifest_git_blob_sha": "96d134265a8c256e34ad985670feed8ca56c295d",
        "source_recipe_id": "ru-school2022:recipe:54-1к",
        "ingredient": "CORN_GROATS",
        "step": "Перебрать и промыть кукурузную крупу, несколько раз меняя воду.",
    },
)


def _finite_positive(value: object) -> Decimal:
    if not isinstance(value, str):
        raise ValueError("Expected Decimal text, not a coerced float")
    try:
        number = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError("Invalid Decimal text") from exc
    if not number.is_finite() or number <= 0:
        raise ValueError("Nonfinite/nonpositive quantity")
    return number


def _source_version(target: dict[str, str], root: Path) -> tuple[dict, str]:
    path = root / target["manifest"]
    data = path.read_bytes()
    # Exact trusted Git blob bytes pinned in the merged #244 source inventory.
    blob_sha1 = hashlib.sha1(b"blob " + str(len(data)).encode() + bytes([0]) + data).hexdigest()
    if blob_sha1 != target["manifest_git_blob_sha"]:
        raise ValueError("Source publication manifest Git blob changed")
    manifest = json.loads(data.decode("utf-8"))
    if target["code"] == TARGETS[0]["code"]:
        row = manifest["recipe"]
        if row["canonical_code"] != target["code"]:
            raise ValueError("R2-E singular recipe manifest code mismatch")
        version = row["version"]
    else:
        row = manifest["recipes"][target["code"]]
        version = row["trusted_recipe_seed"]["version"]
    if (
        version["source_recipe_id"] != target["source_recipe_id"]
        or version["source_document_sha256"] != SOURCE_DOC_SHA256
        or version["rights_review_status"] != "REVIEWED"
        or version["verification_status"] != "SOURCE_VERIFIED"
        or version["steps"][0] != target["step"]
        or _finite_positive(str(version["base_servings"])) != Decimal(1)
    ):
        raise ValueError("Unreviewed or drifted source RecipeVersion")
    return version, hashlib.sha256(data).hexdigest()


def extract_two_step_evidence(
    fixture: dict[str, Any], *, root: Path = REPO_ROOT
) -> dict[str, Any]:
    """Re-pin both exact events and member portions from a validated *new* DB run.

    Any drift from the independently accepted Planner semantic baseline is a
    blocking evidence failure, never an alternative user recipe selection.
    """
    validate_fixture_receipt(
        fixture, trusted_semantic_pins_sha256=TRUSTED_SEMANTIC_SHA256
    )
    catalogue = {row["recipe_version_id"]: row for row in fixture["catalogue"]}
    all_events = fixture["plan"]["events"]
    members = {row["member_id"] for row in fixture["members"]}
    results = []
    for target in TARGETS:
        version, manifest_sha256 = _source_version(target, root)
        matching = [
            event for event in all_events
            if catalogue[event["recipe_version_id"]]["canonical_code"] == target["code"]
        ]
        if len(matching) != 1:
            raise ValueError("Expected exactly one pinned MealEvent for "+target["code"])
        event = matching[0]
        recipe = catalogue[event["recipe_version_id"]]
        if (
            event["local_date"] != target["date"]
            or event["source_kind"] != "COOK_RECIPE"
            or event["role"] != "BREAKFAST"
            or event["plan_id"] != fixture["plan"]["plan_id"]
            or recipe["source_recipe_id"] != target["source_recipe_id"]
            or recipe["source_document_sha256"] != SOURCE_DOC_SHA256
            or recipe["source_version"] != version["source_version"]
            or _finite_positive(recipe["base_servings"]) != Decimal(1)
            or _finite_positive(recipe["source_original_servings"]) != Decimal(1)
        ):
            raise ValueError("Current MealEvent/RecipeVersion source drift")
        step = recipe["steps"][0]
        if step["position"] != 1 or step["instruction_sha256"] != _hash(target["step"]):
            raise ValueError("Step 1 instruction/hash does not match source")
        # Original step order/process hash was already validated by the
        # fixture validator. Do not substitute historical ephemeral UUIDs.
        ingredients = [
            row for row in version["ingredients"]
            if row.get("food_ingredient_code") == target["ingredient"]
        ]
        if len(ingredients) != 1 or ingredients[0].get("unit") != "g":
            raise ValueError("Missing or non-gram source ingredient")
        source_amount = _finite_positive(str(ingredients[0]["quantity"]))
        source_servings = [
            row for row in fixture["plan"]["servings"]
            if row["event_id"] == event["event_id"]
        ]
        if not source_servings:
            raise ValueError("Source MealEvent has no Member Servings")
        if len({s["member_id"] for s in source_servings}) != len(source_servings):
            raise ValueError("Duplicate participant Serving")
        if any(row["member_id"] not in members for row in source_servings):
            raise ValueError("Cross-Household member Serving")
        contributions = [
            {
                "member_id": row["member_id"],
                "serving_id": row["serving_id"],
                "portion_servings": row["portion_servings"],
                "ingredient_net_g": format(
                    source_amount * _finite_positive(row["portion_servings"]), "f"
                ),
            }
            for row in sorted(source_servings, key=lambda r: r["member_id"])
        ]
        total_servings = sum(
            (_finite_positive(s["portion_servings"]) for s in source_servings),
            Decimal(0),
        )
        results.append(
            {
                "canonical_recipe_code": target["code"],
                "meal_event_id": event["event_id"],
                "local_date": event["local_date"],
                "role": event["role"],
                "recipe_version_id": recipe["recipe_version_id"],
                "recipe_version_number": recipe["version_number"],
                "recipe_process_hash": recipe["process_hash"],
                "recipe_step_id": step["recipe_step_id"],
                "recipe_step_position": 1,
                "recipe_step_instruction_sha256": step["instruction_sha256"],
                "instruction_ru": target["step"],
                "source_document_sha256": SOURCE_DOC_SHA256,
                "source_manifest_path": target["manifest"],
                "source_manifest_sha256": manifest_sha256,
                "source_manifest_git_blob_sha": target["manifest_git_blob_sha"],
                "source_recipe_id": target["source_recipe_id"],
                "source_base_servings": str(version["base_servings"]),
                "ingredient_code": target["ingredient"],
                "ingredient_source_net_g": str(ingredients[0]["quantity"]),
                "participant_servings": contributions,
                "sum_portion_servings": format(total_servings, "f"),
                "ingredient_net_g_research_projection": format(
                    source_amount * total_servings, "f"
                ),
                "numeric_syntax_observation": "NO_DIGITS_NOT_REVIEWED_APPROVAL",
                "immediate_eligibility": "PENDING_INDEPENDENT_REVIEW",
                "reviewer_identity": None,
                "reviewer_approved_at": None,
                "production_executable_task_allowed": False,
            }
        )
    return {
        "schema": "PR10_CORE_TWO_STEP_PERSISTED_FIXTURE_EVIDENCE_V1",
        "scope": "SYNTHETIC_FRESH_SQLITE_READBACK_DIAGNOSTIC_ONLY",
        "issue": 245,
        "fixture_planner_semantic_sha256": fixture["planner"][
            "expected_semantic_pins_sha256"
        ],
        "fixture_plan_id": fixture["plan"]["plan_id"],
        "fixture_household_id": fixture["plan"]["household_id"],
        "fixture_week_start": fixture["plan"]["week_start"],
        "fixture_counts": fixture["counts"],
        "candidates": results,
        "distinct_current_meal_events": len(
            {row["meal_event_id"] for row in results}
        ),
        "independently_approved_step_count": 0,
        "policy_publisher_reader": "NOT_IMPLEMENTED",
        "gate": "NO_GO_TO_PR10_CORE_RUNTIME",
        "safety": {
            "no_pantry_mutation": True,
            "no_scheduled_holding_or_freezing": True,
            "rinse_water_not_assigned_from_recipe_cooking_water": True,
            "portion_feasibility_not_evaluated": True,
        },
    }


def validate_two_step_evidence(
    evidence: dict[str, Any], fixture: dict[str, Any], *, root: Path = REPO_ROOT
) -> None:
    expected = extract_two_step_evidence(fixture, root=root)
    if evidence != expected:
        raise ValueError("Evidence differs from source/current fixture re-derivation")
    if (
        evidence["gate"] != "NO_GO_TO_PR10_CORE_RUNTIME"
        or evidence["independently_approved_step_count"] != 0
        or len(evidence["candidates"]) != 2
        or any(row["production_executable_task_allowed"] for row in evidence["candidates"])
    ):
        raise ValueError("Evidence cannot grant executable Prep authority")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="pr10-core-two-step-") as directory:
        fixture = build_fixture_receipt(
            DatabaseConfig(path=Path(directory) / "fixture.sqlite")
        )
        evidence = extract_two_step_evidence(fixture)
        validate_two_step_evidence(evidence, fixture)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for name, obj in (
        ("pr10-meta-fresh-fixture.json", fixture),
        ("pr10-core-two-step-evidence.json", evidence),
    ):
        (args.output_dir / name).write_text(
            json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
    print(
        json.dumps(
            {
                "status": "TWO_SOURCE_STEPS_PINNED_NOT_APPROVED",
                "gate": evidence["gate"],
                "event_count": evidence["fixture_counts"]["meal_events"],
                "source_steps": len(evidence["candidates"]),
                "planner_semantic_sha256": evidence["fixture_planner_semantic_sha256"],
                "output_dir": str(args.output_dir),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
