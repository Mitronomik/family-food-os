from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation
from pathlib import Path

EXPECTED_CANDIDATES = 68
EXPECTED_RELATIONSHIPS = 991
EXPECTED_DEMANDS = 96
EXPECTED_EXISTING = 33
EXPECTED_DC2_REQUIRED = 63
EXPECTED_PR39_CANDIDATES = 350
EXPECTED_PR39_MAPPINGS = 363
EXPECTED_PRODUCTION_NUTRITION_ROWS = 183
EXPECTED_SAFE_SIMPLE = 5
EXPECTED_REVIEW_REQUIRED = 63

EXISTING_STATES = {"EXACT_EXISTING", "ALIAS_EXISTING"}
WORK_STATES = {"NEW_FOOD_CANDIDATE", "FORM_SPLIT_CANDIDATE"}


def fail(msg: str) -> None:
    raise SystemExit(f"DC1 PACKAGE VALIDATION ERROR: {msg}")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            fail(f"missing CSV header: {path}")
        return [{k: (v or "") for k, v in row.items()} for row in reader]


def dec(value: str, ctx: str) -> Decimal:
    try:
        result = Decimal(value)
    except (InvalidOperation, ValueError) as exc:
        fail(f"invalid Decimal {ctx}: {value!r}: {exc}")
    if not result.is_finite():
        fail(f"non-finite Decimal {ctx}: {value!r}")
    return result


def validate(pkg: Path, *, check_checksums: bool = True) -> dict[str, int]:
    required = [
        "candidate-recipes.csv",
        "food-demand.csv",
        "compatibility.csv",
        "batch-plan.json",
        "source-artifacts.json",
        "summary.json",
        "README.md",
    ]
    for name in required:
        if not (pkg / name).exists():
            fail(f"missing package file {name}")

    candidates = read_csv(pkg / "candidate-recipes.csv")
    demands = read_csv(pkg / "food-demand.csv")
    compatibility = read_csv(pkg / "compatibility.csv")
    relationship_parts = sorted(pkg.glob("source-relationships-part*.csv"))
    if len(relationship_parts) != 4:
        fail(f"expected 4 source relationship shards, got {len(relationship_parts)}")

    relationships: list[dict[str, str]] = []
    for part in relationship_parts:
        relationships.extend(read_csv(part))

    summary = json.loads((pkg / "summary.json").read_text(encoding="utf-8"))
    plan = json.loads((pkg / "batch-plan.json").read_text(encoding="utf-8"))
    artifacts = json.loads((pkg / "source-artifacts.json").read_text(encoding="utf-8"))

    if len(candidates) != EXPECTED_CANDIDATES:
        fail(f"candidate count: {len(candidates)}")
    if len(relationships) != EXPECTED_RELATIONSHIPS:
        fail(f"relationship count: {len(relationships)}")
    if len(demands) != EXPECTED_DEMANDS:
        fail(f"demand count: {len(demands)}")
    if len(compatibility) != EXPECTED_CANDIDATES:
        fail(f"compatibility count: {len(compatibility)}")

    candidate_ids = [row["source_recipe_id"] for row in candidates]
    if len(set(candidate_ids)) != len(candidate_ids):
        fail("duplicate candidate IDs")
    demand_ids = [row["external_ingredient_id"] for row in demands]
    if len(set(demand_ids)) != len(demand_ids):
        fail("duplicate food-demand external IDs")
    compatibility_ids = [row["source_recipe_id"] for row in compatibility]
    if set(compatibility_ids) != set(candidate_ids):
        fail("compatibility candidate IDs mismatch")
    if len(set(compatibility_ids)) != len(compatibility_ids):
        fail("duplicate compatibility candidate IDs")

    candidate_id_set = set(candidate_ids)
    demand_id_set = set(demand_ids)
    relationships_by_recipe: dict[str, list[dict[str, str]]] = defaultdict(list)
    relationship_keys: set[tuple[str, ...]] = set()
    duplicate_fields = [
        "relationship_source",
        "source_recipe_id",
        "variant",
        "original_ingredient_id",
        "resolved_ingredient_id",
        "original_ingredient",
        "amount_g",
        "amount_status",
        "choice_group",
        "optional",
        "relationship_source_url",
        "nutrient_input_eligible",
    ]
    for row in relationships:
        recipe_id = row["source_recipe_id"]
        ingredient_id = row["resolved_ingredient_id"]
        if recipe_id not in candidate_id_set:
            fail(f"relationship references unknown candidate {recipe_id}")
        if ingredient_id not in demand_id_set:
            fail(f"relationship references unknown demand ID {ingredient_id}")
        amount = dec(row["amount_g"], f"{recipe_id}/{ingredient_id}/amount_g")
        if amount <= 0:
            fail(
                "unknown/invalid amount substituted by zero/non-positive for "
                f"{recipe_id}/{ingredient_id}"
            )
        key = tuple(row[field] for field in duplicate_fields)
        if key in relationship_keys:
            fail(f"duplicate relationship row {key}")
        relationship_keys.add(key)
        relationships_by_recipe[recipe_id].append(row)

    for candidate in candidates:
        recipe_id = candidate["source_recipe_id"]
        actual_rows = relationships_by_recipe.get(recipe_id, [])
        if not actual_rows:
            fail(f"candidate {recipe_id} lost all source relationships")
        if int(candidate["source_relationship_rows_v22_5"]) != len(actual_rows):
            fail(f"candidate {recipe_id} relationship summary mismatch")
        if int(candidate["source_calc_rows_v22_13"]) <= 0:
            fail(f"candidate {recipe_id} has zero v22.13 calculation rows")
        if candidate["production_ready"] != "NO":
            fail(f"candidate {recipe_id} incorrectly marked production-ready")

        status = candidate["variant_selection_status"]
        if status == "SIMPLE_SOURCE_BRANCH_CANDIDATE":
            if int(candidate["source_variant_count"]) != 1:
                fail(f"simple candidate {recipe_id} has multiple source variants")
            if candidate["choice_groups"]:
                fail(f"simple candidate {recipe_id} has ChoiceGroup debt")
            if int(candidate["optional_row_count"]) != 0:
                fail(f"simple candidate {recipe_id} has optional rows")
            if candidate["boundary_review_reasons"]:
                fail(f"simple candidate {recipe_id} has boundary debt")
            if (
                candidate["relationship_compatibility_status"]
                != "CALC_ROWS_MATCH_RELATIONSHIP_ROWS_MATCH"
            ):
                fail(
                    f"simple candidate {recipe_id} has relationship compatibility debt"
                )
            if candidate["semantic_label_review_ids"]:
                fail(f"simple candidate {recipe_id} has semantic-label debt")
            if candidate["proposed_dc3_batch"] == "DC3-C_REVIEW_REQUIRED":
                fail(f"simple candidate {recipe_id} is incorrectly in review batch")
        elif status == "REVIEW_REQUIRED":
            if candidate["proposed_dc3_batch"] != "DC3-C_REVIEW_REQUIRED":
                fail(f"review-required candidate {recipe_id} escaped review batch")
            if candidate["single_variant_required_ids"]:
                fail(
                    f"review-required candidate {recipe_id} exposes selected-branch "
                    "dependencies"
                )
        else:
            fail(f"candidate {recipe_id} has unknown variant-selection status {status}")

    existing_count = sum(row["map_state"] in EXISTING_STATES for row in demands)
    dc2_count = sum(row["map_state"] in WORK_STATES for row in demands)
    if existing_count != EXPECTED_EXISTING or dc2_count != EXPECTED_DC2_REQUIRED:
        fail(f"mapping split drift {existing_count}/{dc2_count}")
    if any(row["production_ready"] != "NO" for row in demands):
        fail("food demand marked production-ready")

    for row in demands:
        ingredient_id = row["external_ingredient_id"]
        state = row["map_state"]
        assignment = row.get("authority_assignment_status", "")
        if not assignment:
            fail(f"food demand {ingredient_id} missing authority assignment status")

        if state in EXISTING_STATES:
            if (
                row["current_profile_presence_status"]
                != "PRESENT_IN_REQUIRED_PRODUCTION_SEED"
            ):
                fail(
                    f"existing mapping {ingredient_id} lacks required production profile"
                )
            if (
                row["profile_suitability_for_recipe_form"]
                != "PROFILE_PRESENT_FORM_REVIEW_REQUIRED"
            ):
                fail(
                    f"existing mapping {ingredient_id} profile/form review is bypassed"
                )
            if (
                not row["authority_source_candidate"]
                or not row["authority_record_candidate"]
            ):
                fail(
                    f"existing mapping {ingredient_id} lacks exact current profile provenance"
                )
            if row["proposed_dc2_batch"] != "REUSE_EXISTING_PROFILE_FORM_REVIEW":
                fail(
                    f"existing mapping {ingredient_id} prematurely bypasses profile review"
                )
        elif assignment.startswith("BLOCKED_"):
            if row["authority_source_candidate"] or row["authority_record_candidate"]:
                fail(
                    f"blocked demand {ingredient_id} carries premature authority record"
                )
        elif assignment == "CANDIDATE_SOURCE_FAMILY_IDENTIFIED_EXACT_RECORD_UNPINNED":
            if not row["authority_source_candidate"]:
                fail(f"candidate-family assignment missing source for {ingredient_id}")
            if row["authority_record_candidate"]:
                fail(
                    f"candidate-family assignment pretends exact record for {ingredient_id}"
                )
        else:
            fail(f"unexpected authority assignment for {ingredient_id}: {assignment}")

    if any(row["proposed_dc2_batch"] == "REUSE_NO_DC2_WRITE" for row in demands):
        fail("legacy REUSE_NO_DC2_WRITE is forbidden before profile/form review")

    candidate_summary = summary["candidate_selection"]
    demand_summary = summary["food_demand"]
    expected_summary = {
        "candidate_count": len(candidates),
        "relationship_count": len(relationships),
        "demand_count": len(demands),
        "existing": existing_count,
        "dc2": dc2_count,
        "one_variant": sum(int(row["source_variant_count"]) == 1 for row in candidates),
        "multi_variant": sum(
            int(row["source_variant_count"]) > 1 for row in candidates
        ),
        "simple": sum(
            row["variant_selection_status"] == "SIMPLE_SOURCE_BRANCH_CANDIDATE"
            for row in candidates
        ),
        "review": sum(
            row["variant_selection_status"] == "REVIEW_REQUIRED" for row in candidates
        ),
    }
    actual_summary = {
        "candidate_count": candidate_summary["recipe_family_count"],
        "relationship_count": candidate_summary["source_relationship_rows_v22_5"],
        "demand_count": demand_summary["demand_row_count"],
        "existing": demand_summary["accepted_existing_identity_mapping_count"],
        "dc2": demand_summary["dc2_required_identity_count"],
        "one_variant": candidate_summary["source_variant_structure"][
            "one_source_variant"
        ],
        "multi_variant": candidate_summary["source_variant_structure"][
            "multiple_source_variants"
        ],
        "simple": candidate_summary["source_variant_structure"][
            "safe_simple_source_branch_candidate"
        ],
        "review": candidate_summary["source_variant_structure"]["review_required"],
    }
    if expected_summary != actual_summary:
        fail(f"summary mismatch expected={expected_summary} actual={actual_summary}")
    if expected_summary["simple"] != EXPECTED_SAFE_SIMPLE:
        fail(f"safe candidate count drift: {expected_summary['simple']}")
    if expected_summary["review"] != EXPECTED_REVIEW_REQUIRED:
        fail(f"review-required count drift: {expected_summary['review']}")

    expected_authority_counts = dict(
        sorted(Counter(row["authority_assignment_status"] for row in demands).items())
    )
    if demand_summary.get("authority_assignment_counts") != expected_authority_counts:
        fail("summary authority assignment counts mismatch")

    loaded = artifacts.get("repository", {}).get("mapping_rows_loaded", {})
    if (
        loaded.get("candidate_rows_total_from_full_pr39_package")
        != EXPECTED_PR39_CANDIDATES
    ):
        fail("source-artifacts does not prove full 350-row PR39 candidate input")
    if (
        loaded.get("ingredient_mapping_rows_total_from_full_pr39_package")
        != EXPECTED_PR39_MAPPINGS
    ):
        fail("source-artifacts does not prove full 363-row PR39 mapping input")

    nutrition_meta = artifacts.get("production_nutrition_seed", {})
    if nutrition_meta.get("row_count") != EXPECTED_PRODUCTION_NUTRITION_ROWS:
        fail("source-artifacts production nutrition row count mismatch")
    if nutrition_meta.get("relevant_existing_profiles_identified") != EXPECTED_EXISTING:
        fail("source-artifacts does not identify all 33 existing profiles")
    if not nutrition_meta.get("git_blob_sha1"):
        fail("source-artifacts missing production nutrition seed blob identity")

    for section, universe, list_key in [
        ("dc2", demand_id_set, "external_ingredient_ids"),
        ("dc3", candidate_id_set, "source_recipe_ids"),
    ]:
        flattened: list[str] = []
        for name, group in plan[section].items():
            if group["count"] != len(group[list_key]):
                fail(f"{section}/{name} declared count mismatch")
            flattened.extend(group[list_key])
        if set(flattened) != universe:
            fail(f"{section} batches omit or add IDs")
        overlaps = [key for key, count in Counter(flattened).items() if count != 1]
        if overlaps:
            fail(f"{section} batches overlap: {overlaps}")

    if check_checksums:
        checksum_file = pkg / "checksums.sha256"
        if not checksum_file.exists():
            fail("missing checksums.sha256")
        for line in checksum_file.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            digest, name = line.split("  ", 1)
            target = pkg / name
            if not target.exists():
                fail(f"checksum target missing {name}")
            if sha256(target) != digest:
                fail(f"checksum mismatch {name}")

    return expected_summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("package")
    parser.add_argument(
        "--skip-checksums",
        action="store_true",
        help="for adversarial mutation tests only",
    )
    args = parser.parse_args()
    result = validate(
        Path(args.package),
        check_checksums=not args.skip_checksums,
    )
    print(json.dumps({"status": "PASS", **result}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()