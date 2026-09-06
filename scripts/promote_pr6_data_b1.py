"""Offline, deterministic promotion of accepted DATA-A decisions, never a runtime resolver."""

import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = "60908eb8270ef356eff8552855b4cc5d2aa9ee44"
DIRECTORY = ROOT / "data/seed/nutrition_measure_evidence"
REVIEWED_AT = "2026-09-07T00:00:00+00:00"


def encoded(value):
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode()


def promote(root=ROOT):
    source_dir = root / "data/curation/pr6-data-a"
    audit = json.loads((source_dir / "conversion-gap-audit.json").read_text())
    sources = {
        s["manifest_id"]: s
        for s in json.loads((source_dir / "source-manifest.json").read_text())[
            "sources"
        ]
    }
    recipes = {
        r["canonical_code"]: r["version"]
        for r in json.loads((root / "data/seed/recipes/recipes.json").read_text())[
            "recipes"
        ]
    }
    with (root / "data/seed/food_ingredients/nutrition.csv").open() as file:
        profiles = {r["canonical_code"]: r for r in csv.DictReader(file)}
    evidence, assessments = {}, []
    for row in sorted(
        audit["rows"],
        key=lambda r: (r["recipe_canonical_code"], r["ingredient_position"]),
    ):
        issues = set(row["additional_blockers"])
        if "CONVERSION_ESTIMATION_PROPAGATION_NOT_IMPLEMENTED" in issues:
            issues.remove("CONVERSION_ESTIMATION_PROPAGATION_NOT_IMPLEMENTED")
            issues.add("CONVERSION_ESTIMATE_NOT_ACCEPTED")
        semantic_issue = {
            "FORM_MISMATCH": "FOOD_FORM_MISMATCH",
            "IDENTITY_MISMATCH": "IDENTITY_MISMATCH",
            "AMBIGUOUS": "PROFILE_REPRESENTATIVENESS_REVIEW",
        }.get(row["semantic_compatibility"])
        if semantic_issue:
            issues.add(semantic_issue)
        decision_issue = {
            "FOOD_FORM_MISMATCH": "FOOD_FORM_MISMATCH",
            "CANONICAL_IDENTITY_MISMATCH": "IDENTITY_MISMATCH",
            "MEASURE_OR_SIZE_AMBIGUOUS": "MEASURE_OR_SIZE_AMBIGUOUS",
            "NO_ACCEPTABLE_SOURCE": "NO_ACCEPTABLE_SOURCE",
        }.get(row["decision_code"])
        if decision_issue:
            issues.add(decision_issue)
        key = None
        method = row["conversion_method"]
        if method:
            source = sources[method["source_manifest_id"]]
            # The same cheddar portion is exact for shredded and estimated for grated.
            # Preserve each reviewed uncertainty class; neither may overwrite the other.
            key = source["manifest_id"] + (
                ":estimate" if row["estimated"] else ":exact"
            )
            density = method["kind"] == "INFOODS_DENSITY"
            retrieved = source["retrieved_at"]
            if len(retrieved) == 10:
                retrieved = None  # Source recorded date only: do not invent a retrieval instant.
            fact = dict(
                evidence_key=key,
                source_name=source["source_name"],
                source_type=source["source_type"],
                source_id=source["source_id"],
                source_version=source["source_version_or_release"],
                source_url=source["source_url"],
                food_description=source["food_description"],
                form_modifier=source["modifier_or_form"],
                edible_basis=source.get("edible_basis"),
                source_measure_amount=source["amount"],
                source_measure_text=source["measure_description"],
                normalized_input_quantity="1"
                if density
                else method["portion_input_quantity"],
                normalized_input_unit="ml" if density else method["portion_input_unit"],
                gram_weight=source["density_g_per_ml"]
                if density
                else source["gram_weight"],
                evidence_quality=source["evidence_quality"],
                estimated=row["estimated"],
                retrieved_at=retrieved,
                created_at=REVIEWED_AT,
            )
            if key in evidence and evidence[key] != fact:
                raise ValueError("Contradictory reusable evidence: " + key)
            evidence[key] = fact
        hard_issues = issues - {"CONVERSION_ESTIMATE_NOT_ACCEPTED"}
        if hard_issues:
            status = "BLOCKED"
        elif row["estimated"] is True:
            status = "REVIEW_REQUIRED_ESTIMATE"
        elif row["recipe_unit"] == "g":
            status = "APPROVED_NO_CONVERSION"
        elif row["implementation_ready"] and row["estimated"] is False:
            status = "APPROVED_EXACT"
        else:
            raise ValueError("Unmapped DATA-A decision")
        version = recipes[row["recipe_canonical_code"]]
        profile = profiles[row["food_ingredient_code"]]
        profile_values = {
            k: profile[k]
            for k in (
                "basis_grams",
                "kcal",
                "protein_g",
                "fat_g",
                "carbohydrates_g",
                "fiber_g",
                "source_name",
                "source_id",
                "source_version",
                "source_data_type",
                "verified_at",
                "estimated",
            )
        }
        for k in ("fiber_g", "estimated"):
            if profile_values[k] == "":
                profile_values[k] = None
        if profile_values["estimated"] is not None:
            profile_values["estimated"] = profile_values["estimated"].lower() == "true"
        descriptor = {
            k: row[k]
            for k in (
                "recipe_canonical_code",
                "recipe_source_id",
                "recipe_source_version",
                "ingredient_position",
                "food_ingredient_code",
                "recipe_quantity",
                "recipe_unit",
                "optional",
                "source_amount_text",
                "normalization_note",
                "prep_note",
            )
        }
        descriptor.update(
            recipe_source_name=version["source_name"],
            profile=profile_values,
            assessment_version=1,
            status_code=status,
            semantic_compatibility_code=row["semantic_compatibility"],
            conversion_decision_code=row["decision_code"],
            evidence_key=key,
            source_audit_operation="PR6-DATA-A",
            source_audit_key=f"{row['recipe_canonical_code']}:{row['recipe_source_id']}:{row['recipe_source_version']}:{row['ingredient_position']}:{row['food_ingredient_code']}",
            review_note=row["semantic_evidence"] + " " + row["review_note"],
            reviewed_at=REVIEWED_AT,
            created_at=REVIEWED_AT,
            issues=sorted(issues),
        )
        assessments.append(descriptor)
    statuses = dict(sorted(Counter(r["status_code"] for r in assessments).items()))
    if statuses["APPROVED_EXACT"] != 66:
        raise ValueError("DATA-A contradiction: exact approved set differs from 66")
    result = {
        "evidence.json": {
            "schema_version": 1,
            "evidence": sorted(evidence.values(), key=lambda r: r["evidence_key"]),
        },
        "assessments.json": {"schema_version": 1, "assessments": assessments},
    }
    result["manifest.json"] = dict(
        schema_version=1,
        source_operation="PR6-DATA-A",
        source_merged_main=BASE,
        source_sha256={
            f"data/curation/pr6-data-a/{name}.json": hashlib.sha256(
                (source_dir / f"{name}.json").read_bytes()
            ).hexdigest()
            for name in ("conversion-gap-audit", "source-manifest", "summary")
        },
        production_input_sha256={
            p: hashlib.sha256((root / p).read_bytes()).hexdigest()
            for p in (
                "data/seed/recipes/recipes.json",
                "data/seed/food_ingredients/nutrition.csv",
            )
        },
        payload_sha256={
            k: hashlib.sha256(encoded(v)).hexdigest() for k, v in result.items()
        },
        evidence_count=len(evidence),
        assessment_count=len(assessments),
        issue_count=sum(len(r["issues"]) for r in assessments),
        status_counts=statuses,
        issue_counts=dict(
            sorted(Counter(i for r in assessments for i in r["issues"]).items())
        ),
    )
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    result = promote()
    for name, value in result.items():
        path = DIRECTORY / name
        if args.write:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(encoded(value))
        elif path.read_bytes() != encoded(value):
            raise SystemExit("Promotion differs: " + name)
    print(json.dumps(result["manifest.json"], sort_keys=True))


if __name__ == "__main__":
    main()
