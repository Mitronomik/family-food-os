"""Offline integrity checks and derived summary for curated PR6-DATA-A evidence.

This is a research validator, not a production importer or conversion engine.
Curated source matches require human review; passing structure cannot prove them.
"""

from __future__ import annotations

import argparse
from collections import Counter
import csv
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT / "data/curation/pr6-data-a"
BASE = "7c449672c039c66b8d475064462eba2a9f6d38e6"
DECISIONS = (
    "DIRECT_RECIPE_MASS",
    "FDC_EXACT_PORTION",
    "FDC_COMPATIBLE_ESTIMATE",
    "INFOODS_EXACT_OR_STRONG_MATCH",
    "INFOODS_COMPATIBLE_ESTIMATE",
    "OTHER_SOURCE_EXACT",
    "OTHER_SOURCE_ESTIMATE",
    "FOOD_FORM_MISMATCH",
    "CANONICAL_IDENTITY_MISMATCH",
    "MEASURE_OR_SIZE_AMBIGUOUS",
    "NO_ACCEPTABLE_SOURCE",
)
SEMANTICS = (
    "MATCH",
    "MATCH_WITH_FORM_QUALIFIER",
    "ACCEPTED_SUBSTITUTION",
    "FORM_MISMATCH",
    "IDENTITY_MISMATCH",
    "AMBIGUOUS",
)
EXACT = {
    "DIRECT_RECIPE_MASS",
    "FDC_EXACT_PORTION",
    "INFOODS_EXACT_OR_STRONG_MATCH",
    "OTHER_SOURCE_EXACT",
}
ESTIMATES = {
    "FDC_COMPATIBLE_ESTIMATE",
    "INFOODS_COMPATIBLE_ESTIMATE",
    "OTHER_SOURCE_ESTIMATE",
}
BLOCKED = set(DECISIONS) - EXACT - ESTIMATES
NUMERIC = ("candidate_mass_g", "candidate_g_per_ml", "candidate_g_per_piece")


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def identity(row):
    return tuple(
        row[key]
        for key in (
            "recipe_canonical_code",
            "recipe_source_id",
            "recipe_source_version",
            "ingredient_position",
            "food_ingredient_code",
            "source_amount_text",
        )
    )


def accepted_rows(root=ROOT):
    rows = []
    for recipe in read(root / "data/seed/recipes/recipes.json")["recipes"]:
        version = recipe["version"]
        for position, ingredient in enumerate(version["ingredients"], 1):
            rows.append(
                {
                    **ingredient,
                    "recipe_canonical_code": recipe["canonical_code"],
                    "recipe_source_id": version["source_recipe_id"],
                    "recipe_source_version": version["source_version"],
                    "ingredient_position": position,
                    "recipe_quantity": ingredient["quantity"],
                    "recipe_unit": ingredient["unit"],
                }
            )
    return rows


def summary(rows):
    conversions = [r for r in rows if r["recipe_unit"] in {"ml", "pcs"}]

    def count(subset):
        return {
            "rows": len(subset),
            "affected_recipes": len({r["recipe_canonical_code"] for r in subset}),
        }

    result = {
        "total_recipes": len({r["recipe_canonical_code"] for r in rows}),
        "total_rows": len(rows),
        "units": dict(sorted(Counter(r["recipe_unit"] for r in rows).items())),
        "conversion_optionality": {
            unit: {
                kind: count(
                    [
                        r
                        for r in conversions
                        if r["recipe_unit"] == unit and r["optional"] is optional
                    ]
                )
                for kind, optional in (("required", False), ("optional", True))
            }
            for unit in ("ml", "pcs")
        },
        "unique_conversion_foods": {
            key: len(
                {
                    r["food_ingredient_code"]
                    for r in conversions
                    if key == "either" or r["recipe_unit"] == key
                }
            )
            for key in ("ml", "pcs", "either")
        },
        "decisions": {
            code: count([r for r in conversions if r["decision_code"] == code])
            for code in DECISIONS
        },
        "readiness": {
            "implementation_ready_exact": count(
                [
                    r
                    for r in conversions
                    if r["implementation_ready"] and r["estimated"] is False
                ]
            ),
            "implementation_ready_estimated": count(
                [
                    r
                    for r in conversions
                    if r["implementation_ready"] and r["estimated"] is True
                ]
            ),
            "not_implementation_ready": count(
                [r for r in conversions if not r["implementation_ready"]]
            ),
            "candidate_exact": count(
                [r for r in conversions if r["estimated"] is False]
            ),
            "candidate_estimated": count(
                [r for r in conversions if r["estimated"] is True]
            ),
            "no_candidate": count(
                [r for r in conversions if r["candidate_mass_g"] is None]
            ),
        },
        "semantics": {
            code: count([r for r in rows if r["semantic_compatibility"] == code])
            for code in SEMANTICS
        },
        "additional_blockers": {
            code: count([r for r in rows if code in r["additional_blockers"]])
            for code in sorted(
                {code for r in rows for code in r["additional_blockers"]}
            )
        },
        "runtime_conversion_issues": {
            code: count([r for r in rows if r["conversion_issue"] == code])
            for code in ("MISSING_DENSITY", "UNSUPPORTED_PIECE_MASS")
        },
    }
    return result


def validate(audit, manifest, root=ROOT, check_protected=True, protected_revision=None):
    errors = []

    def require(condition, message):
        if not condition:
            errors.append(message)

    rows = audit["rows"]
    accepted = accepted_rows(root)
    require(audit["base_main_sha"] == BASE, "wrong accepted base")
    require(len(rows) == len(accepted) == 189, "expected 189 rows")
    require(
        len({r["recipe_canonical_code"] for r in accepted}) == 30, "expected 30 recipes"
    )
    require(
        Counter(map(identity, rows)) == Counter(map(identity, accepted)),
        "stable row coverage differs",
    )
    require(len(set(map(identity, rows))) == len(rows), "duplicate row identity")
    sources = {s["manifest_id"]: s for s in manifest["sources"]}
    require(len(sources) == len(manifest["sources"]), "duplicate source ID")
    profiles = {
        r["canonical_code"]: r
        for r in csv.DictReader(
            (root / "data/seed/food_ingredients/nutrition.csv").open(encoding="utf-8")
        )
    }
    existing = {identity(r): r for r in accepted}
    selections = read(root / "data/curation/pr4-data2/draft-ingredient-coverage.json")[
        "recipes"
    ]
    selections = {
        (r["source_recipe_id"], a["position"]): a for r in selections for a in r["rows"]
    }
    source_keys = {
        "manifest_id",
        "source_name",
        "source_type",
        "source_id",
        "source_version_or_release",
        "source_url",
        "retrieved_at",
        "food_description",
        "measure_description",
        "modifier_or_form",
        "amount",
        "gram_weight",
        "data_points",
        "footnote",
        "license_or_terms_note",
        "evidence_quality",
    }
    for source in sources.values():
        require(
            source_keys <= source.keys(),
            "missing source fields: " + source["manifest_id"],
        )
        for reference in source.get("source_manifest_ids", []) + source.get(
            "portion_manifest_ids", []
        ):
            require(
                reference in sources, "broken source foreign reference: " + reference
            )
        if source["source_type"] == "ORIGINAL_RECIPE":
            require(
                source["accepted_sha256"] == source["reopened_sha256"],
                "original source hash mismatch",
            )
    for row in rows:
        key = identity(row)
        prefix = f"{row['recipe_canonical_code']}:{row['ingredient_position']}: "
        original = existing.get(key)
        if original is None:
            continue
        for field in (
            "recipe_quantity",
            "recipe_unit",
            "optional",
            "normalization_note",
            "prep_note",
        ):
            require(
                row[field] == original[field], prefix + "source field changed: " + field
            )
        profile = profiles[row["food_ingredient_code"]]
        for field in ("name", "id", "version"):
            require(
                row["nutrition_source_" + field] == profile["source_" + field],
                prefix + "profile provenance differs",
            )
        food = sources.get("FDC-FOOD-" + row["nutrition_source_id"], {})
        require(
            food.get("food_description") == profile["source_description"],
            prefix + "official description differs",
        )
        selection = row["accepted_pr4_selection"]
        prior = selections[
            (selection["recipe_source_id"], selection["source_position"])
        ]
        require(
            row["food_ingredient_code"] in prior["selected_codes"],
            prefix + "wrong PR4 selection",
        )
        require(
            selection["quantity_text"] == prior["quantity_text"],
            prefix + "PR4 quantity changed",
        )
        require(
            selection["normalization_reason"] == prior["normalization_reason"],
            prefix + "PR4 reason changed",
        )
        require(
            row["semantic_compatibility"] in SEMANTICS,
            prefix + "invalid semantic class",
        )
        require(
            bool(
                row["semantic_evidence"] and row["review_note"] and row["next_action"]
            ),
            prefix + "missing review",
        )
        refs = row["source_manifest_ids"]
        require(
            bool(refs) and all(ref in sources for ref in refs),
            prefix + "invalid source references",
        )
        recipe_source = sources.get("RECIPE-" + row["recipe_source_id"], {})
        require(
            recipe_source.get("source_version_or_release")
            == row["recipe_source_version"],
            prefix + "source version changed",
        )
        conversion = row["recipe_unit"] in {"ml", "pcs"}
        require(
            (row["decision_code"] in DECISIONS)
            if conversion
            else row["decision_code"] is None,
            prefix + "invalid decision",
        )
        require(
            row["conversion_issue"]
            == {"ml": "MISSING_DENSITY", "pcs": "UNSUPPORTED_PIECE_MASS"}.get(
                row["recipe_unit"]
            ),
            prefix + "wrong baseline issue",
        )
        for field in NUMERIC:
            value = row[field]
            require(
                value is None
                or (
                    isinstance(value, str)
                    and Decimal(value).is_finite()
                    and Decimal(value) > 0
                ),
                prefix + "nonpositive/malformed candidate",
            )
        candidate = row["candidate_mass_g"] is not None
        require(
            (row["estimated"] in (True, False) and row["estimated"] is not None)
            if candidate
            else row["estimated"] is None,
            prefix + "invalid exact/estimated/null status",
        )
        if candidate:
            method = row["conversion_method"]
            require(bool(method), prefix + "missing conversion method")
            if not method:
                continue
            ref = method["source_manifest_id"]
            require(
                ref in refs and ref in sources, prefix + "candidate provenance absent"
            )
            if ref not in sources:
                continue
            source = sources[ref]
            if method["kind"] == "INFOODS_DENSITY":
                ratio = Decimal(source["density_g_per_ml"])
                require(
                    row["decision_code"] == "INFOODS_COMPATIBLE_ESTIMATE",
                    prefix + "INFOODS overclaimed",
                )
            else:
                ratio = Decimal(source["gram_weight"]) / Decimal(
                    method["portion_input_quantity"]
                )
                require(
                    Decimal(method["portion_input_quantity"]) > 0,
                    prefix + "invalid source measure",
                )
            expected = (Decimal(row["recipe_quantity"]) * ratio).quantize(
                Decimal(".000001"), rounding=ROUND_HALF_UP
            )
            require(
                Decimal(row["candidate_mass_g"]) == expected,
                prefix + "candidate arithmetic differs",
            )
            field = (
                "candidate_g_per_ml"
                if row["recipe_unit"] == "ml"
                else "candidate_g_per_piece"
            )
            require(
                Decimal(row[field])
                == ratio.quantize(Decimal(".000001"), rounding=ROUND_HALF_UP),
                prefix + "candidate ratio differs",
            )
            if row["estimated"] is False:
                require(
                    row["decision_code"] in EXACT,
                    prefix + "nonexact evidence marked exact",
                )
                require(
                    row["semantic_compatibility"]
                    not in {"FORM_MISMATCH", "IDENTITY_MISMATCH", "AMBIGUOUS"},
                    prefix + "exact incompatible food",
                )
            if row["decision_code"] == "FDC_EXACT_PORTION":
                require(
                    source["source_id"] == row["nutrition_source_id"],
                    prefix + "exact requires same FDC ID",
                )
                require(
                    source["source_type"] == "FOOD_PORTION",
                    prefix + "exact requires official portion",
                )
                if row["food_ingredient_code"] == "EGG":
                    require(
                        "large" in row["source_amount_text"].lower(),
                        prefix + "unspecified egg size",
                    )
                if row["food_ingredient_code"] == "BLACK_PEPPER":
                    require(
                        "ground" in row["source_amount_text"].lower(),
                        prefix + "unspecified pepper grind",
                    )
        else:
            require(
                all(row[f] is None for f in NUMERIC)
                and row["conversion_method"] is None,
                prefix + "partial candidate without mass",
            )
        if row["implementation_ready"]:
            require(
                candidate
                and row["decision_code"] not in BLOCKED
                and row["semantic_compatibility"]
                not in {"FORM_MISMATCH", "IDENTITY_MISMATCH", "AMBIGUOUS"}
                and not row["additional_blockers"],
                prefix + "blocked candidate marked ready",
            )
            require(
                row["estimated"] is False,
                prefix + "conversion estimate propagation is not implemented",
            )
        if row["recipe_unit"] == "pcs":
            require(bool(row["piece_review"]), prefix + "missing piece review")
            require(
                row["candidate_g_per_ml"] is None, prefix + "piece converted by density"
            )
        elif row["recipe_unit"] == "ml":
            require(
                row["candidate_g_per_piece"] is None,
                prefix + "volume converted by piece",
            )
    if check_protected:
        for path, digest in audit["protected_file_sha256"].items():
            payload = (
                subprocess.check_output(
                    ["git", "show", f"{protected_revision}:{path}"], cwd=root
                )
                if protected_revision
                else (root / path).read_bytes()
            )
            require(
                hashlib.sha256(payload).hexdigest() == digest,
                "protected file changed: " + path,
            )
        require(
            protected_revision is not None
            or not list((root / "backend/app/migrations/versions").glob("0026*")),
            "migration 0026 is prohibited",
        )
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-summary", action="store_true")
    parser.add_argument(
        "--protected-revision",
        help="Verify historical DATA-A protected files at this Git revision after authorized runtime work.",
    )
    args = parser.parse_args()
    audit, manifest = (
        read(DIRECTORY / "conversion-gap-audit.json"),
        read(DIRECTORY / "source-manifest.json"),
    )
    errors = validate(audit, manifest, protected_revision=args.protected_revision)
    if errors:
        raise SystemExit("\n".join(errors))
    result = summary(audit["rows"])
    encoded = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.write_summary:
        (DIRECTORY / "summary.json").write_text(encoded, encoding="utf-8")
    elif read(DIRECTORY / "summary.json") != result:
        raise SystemExit("Summary differs; regenerate with --write-summary")
    print(encoded, end="")


if __name__ == "__main__":
    main()
