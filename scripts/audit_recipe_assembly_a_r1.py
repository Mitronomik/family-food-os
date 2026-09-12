"""Audit the R1 research package, not RecipeTemplate publication readiness.

Offline by default. --database rebuilds accepted truth in a disposable DB only.
Exit zero can report BLOCKED: arithmetic consistency is not culinary approval.
"""

import argparse
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import subprocess
import sys
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
BASE = "3c854f55323c895c1bdc5aabd5f1146fb6514935"
PACKAGE = ROOT / "data/curation/recipe-assembly-a-r1"
DEFERRED = {
    "APPLE_PEELED",
    "LEMON_JUICE",
    "ORANGE_JUICE",
    "PASTA_COOKED",
    "SPINACH_BABY",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def reject_float(value):
    raise ValueError(f"JSON float/constant forbidden: {value}")


def read(path):
    return json.loads(
        path.read_text(), parse_float=reject_float, parse_constant=reject_float
    )


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def scope_audit():
    require(git("merge-base", BASE, "HEAD") == BASE, "Wrong accepted merge ancestor")
    allowed = {
        "scripts/audit_recipe_assembly_a_r1.py",
        "state/current-focus.md",
        "state/progress.md",
        "state/handoff.md",
        "docs/family-food/food-composition-and-assembly.md",
        "docs/family-food/master-roadmap.md",
    }
    changed = set(git("diff", "--name-only", BASE).splitlines())
    untracked = set(git("ls-files", "--others", "--exclude-standard").splitlines())
    staged = set(git("diff", "--cached", "--name-only").splitlines())
    require(".DS_Store" not in staged, "Unrelated .DS_Store must not be staged")
    for path in (changed | untracked) - {".DS_Store"}:
        require(
            path in allowed or path.startswith("data/curation/recipe-assembly-a-r1/"),
            f"Out-of-scope change: {path}",
        )


def database_audit(package):
    sys.path[:0] = [str(ROOT / "backend"), str(ROOT / "scripts")]
    from app.db.config import DatabaseConfig
    from audit_pr6_close import measure, encode

    with TemporaryDirectory() as directory:
        config = DatabaseConfig(path=Path(directory) / "accepted.sqlite")
        reports = measure(config)
        for name in ("recipe-readiness.json", "food-readiness.json"):
            require(
                encode(reports[name])
                == (ROOT / "data/curation/pr6-close" / name).read_text(),
                f"Accepted report changed: {name}",
            )
        with sqlite3.connect(config.path) as db:
            foods = [
                dict(food_code=c, name_ru=n)
                for c, n in db.execute(
                    "SELECT canonical_code, canonical_name FROM food_ingredients ORDER BY canonical_code"
                )
            ]
        require(
            foods == read(package / "catalogue-inventory.json")["foods"],
            "Food inventory drift",
        )
    summary = reports["closure-evidence.json"]
    retained = read(package / "baseline-verification.json")
    for name in (
        "migration_head",
        "historical_replay",
        "deferred_forms_absent",
        "yield_rows",
    ):
        require(retained[name] == summary[name], f"Baseline drift: {name}")
    require(
        len(summary["estimate_usages_non_executable"]) == 40,
        "Estimate blockers changed",
    )
    require(
        summary["migration_head"] == "0029_food_composition_core",
        "Migration head changed",
    )
    require(
        set(summary["deferred_forms_absent"]) == DEFERRED, "PR6 form blockers changed"
    )
    print(
        "Disposable accepted DB: PASS; 185 foods / 63 compositions / 188 seals; head 0029"
    )


def audit(package):
    files = {
        p.name for p in package.iterdir() if p.is_file() and p.name != "checksums.json"
    }
    checks = read(package / "checksums.json")["files"]
    require(set(checks) == files, "Package hash inventory incomplete")
    for name, expected in checks.items():
        require(digest(package / name) == expected, f"Package drift: {name}")
    docs = {p.name: read(p) for p in package.glob("*.json")}
    manifest = docs["source-manifest.json"]
    require(manifest["accepted_merge_base"] == BASE, "Wrong base")
    for entry in manifest["input_files"]:
        require(
            digest(ROOT / entry["path"]) == entry["sha256"],
            f"Accepted evidence drift: {entry['path']}",
        )
    sources = {s["source_id"]: s for s in manifest["sources"]}
    observations = {
        r["source_id"] for r in docs["source-observations.json"]["observations"]
    }
    require(set(sources) == observations, "Source observations incomplete")
    for s in sources.values():
        for key in (
            "owner",
            "url",
            "identity",
            "version",
            "retrieval_date",
            "retention",
            "link_check",
        ):
            require(s.get(key), f"Missing source field: {key}")
        require(s["url"].startswith("https://"), "Invalid source URL")
        require(s["retrieval_date"] == "2026-09-12", "Wrong retrieval date")
        if s["byte_sha256"]:
            require(
                re.fullmatch(r"[0-9a-f]{64}", s["byte_sha256"]),
                "Invalid source byte hash",
            )
    funnel = docs["candidate-funnel.json"]
    candidates = {c["template_candidate_code"]: c for c in funnel["candidates"]}
    require(len(candidates) == funnel["screened_count"] == 23, "Screen count mismatch")
    deep = {c for c, r in candidates.items() if r["review_depth"] == "DEEP"}
    require(len(deep) == funnel["deep_review_count"] == 9, "Deep count mismatch")
    catalogue = {r["food_code"]: r for r in docs["catalogue-inventory.json"]["foods"]}
    require(
        len(catalogue) == 185 and not DEFERRED & catalogue.keys(),
        "Catalogue/form drift",
    )
    accepted = {
        r["food_code"]: r
        for r in read(ROOT / "data/curation/pr6-close/food-readiness.json")["foods"]
    }
    for c in candidates.values():
        require(
            re.search(r"[А-Яа-яЁё]", c["name_ru"]), "Missing Russian candidate display"
        )
        require(
            c["remaining_blockers"] and c["disposition"] == "DEFER",
            "Unsupported candidate approval",
        )
        for code in c["existing_codes_without_usable_composition"]:
            require(
                code in catalogue
                and not accepted.get(code, {}).get("composition_version"),
                f"Incorrect absent composition claim: {code}",
            )
    rights = {r["source_id"]: r for r in docs["rights-review.json"]["donors"]}
    kitchen = {
        r["template_candidate_code"]: r
        for r in docs["kitchen-verification.json"]["records"]
    }
    require(
        rights.keys() == kitchen.keys() == candidates.keys(), "Review coverage mismatch"
    )
    for code in candidates:
        require(
            rights[code]["decision"] in {"ACCEPT", "DEFER", "REJECT"},
            "Missing rights decision",
        )
        require(
            rights[code]["source_url"] == sources[code]["url"], "Rights source mismatch"
        )
        require(rights[code]["assets_excluded"], "Missing reuse boundary")
        require(
            all(ref in sources for ref in kitchen[code]["evidence_refs"]),
            "Missing kitchen evidence",
        )
        require(
            not kitchen[code]["production_publishable"],
            "Kitchen is not publication approval",
        )
    quantities = docs["quantity-authority.json"]["candidate_batches"]
    require(quantities.keys() == deep, "Missing deep quantity table")
    portions = {
        p["evidence_key"]: p
        for p in read(ROOT / "data/seed/nutrition_measure_evidence/evidence.json")[
            "evidence"
        ]
    }
    units = {"oz": Decimal("28.349523125"), "lb": Decimal("453.59237"), "g": Decimal(1)}
    normalized_ml = {"tsp": Decimal(5), "tbsp": Decimal(15), "cup": Decimal(240)}
    portion_food = {
        "FDC-PORTION-92594:exact": "SALT",
        "FDC-PORTION-93025:exact": "WATER",
        "FDC-PORTION-88667:exact": "OLIVE_OIL",
        "FDC-PORTION-88669:exact": "OLIVE_OIL",
        "FDC-PORTION-87560:exact": "BLACK_PEPPER",
        "FDC-PORTION-87558:exact": "PARSLEY_DRIED",
    }
    exact = unresolved = 0
    for code, batch in quantities.items():
        for row in batch["rows"]:
            require(
                row["food_code"] is None or row["food_code"] in catalogue,
                "Invented FoodIngredient",
            )
            require(
                re.search(r"[А-Яа-яЁё]", row["name_ru"]), "Missing Russian row display"
            )
            unit, quantity = row["source_unit"], row["source_quantity"]
            mass = row["recipe_input_mass_g"]
            if unit in units:
                require(
                    Decimal(row["source_mass_g"]) == Decimal(quantity) * units[unit],
                    "Wrong mass conversion",
                )
            else:
                require(
                    row["source_mass_g"] is None,
                    "Volume/piece mislabeled as source mass",
                )
            if mass is None:
                require(row["issue_ru"], "Unexplained unresolved mass")
                unresolved += 1
                continue
            exact += 1
            require(
                isinstance(mass, str)
                and Decimal(mass).is_finite()
                and Decimal(mass) > 0,
                "Invalid exact mass",
            )
            require(
                row["food_code"] and row["issue_ru"] is None,
                "Unresolved form promoted to mass",
            )
            if row["authority"] == "DIRECT_SOURCE_WEIGHT":
                require(mass == row["source_mass_g"], "Source weight silently altered")
            else:
                evidence = portions[row["authority"]]
                require(evidence["estimated"] is False, "Estimate used")
                require(
                    row["food_code"] == portion_food[row["authority"]],
                    "Cross-food portion used",
                )
                expected = (
                    Decimal(quantity)
                    * normalized_ml[unit]
                    * Decimal(evidence["gram_weight"])
                    / Decimal(evidence["normalized_input_quantity"])
                )
                require(Decimal(mass) == expected, "Wrong exact-portion calculation")
        require(
            batch["all_required_input_masses_resolved"]
            == all(
                r["recipe_input_mass_g"] is not None
                for r in batch["rows"]
                if r["required"]
            ),
            "Mass completeness mismatch",
        )
    for f in docs["composition-readiness.json"]["foods"]:
        a = accepted.get(f["food_code"], {})
        require(
            f["version"] == a.get("composition_version"), "Composition version mismatch"
        )
        require(
            f["authority"] == a.get("composition_authority"),
            "Legacy v1 used as composition",
        )
        require(
            f["unknown_nutrients"] == a.get("unknown_nutrients", []),
            "Unknown nutrients changed",
        )
        require(f["value_count"] == a.get("vector_value_count"), "Vector count changed")
        for key, value in f["profile"].items():
            require(
                value == a["current_profile_provenance"][key],
                "Composition profile pin changed",
            )
    familiar = {
        r["template_candidate_code"]: r
        for r in docs["ru-familiarity.json"]["candidates"]
    }
    require(familiar.keys() == deep, "Missing familiarity review")
    for f in familiar.values():
        for key in (
            "dish_family_identity_ru",
            "target_user_relevance_ru",
            "equipment_preparation_ru",
            "ingredient_form_familiarity_ru",
            "reviewer",
            "review_date",
        ):
            require(f[key], "Incomplete familiarity review")
        require(
            f["reviewer_decision"] in {"RU_RECIPE_FAMILIAR", "NOT_FAMILIAR", "UNCLEAR"},
            "Invalid familiarity",
        )
    market = docs["market-evidence.json"]
    for code, terminals in market["candidate_terminal_inputs"].items():
        require(
            {r["row_id"] for r in terminals}
            == {r["row_id"] for r in quantities[code]["rows"] if r["required"]},
            "Terminal input omission",
        )
        for r in terminals:
            require(
                r["classification"]
                == accepted.get(r["food_code"], {}).get(
                    "ru_classification", "SPECIALTY_OR_UNCLEAR"
                ),
                "Unsupported market promotion",
            )
            if r["classification"] != "RU_MASS_MARKET":
                require(
                    r["policy_gate"] == "NOT_PASSED", "RU_AVAILABLE default promotion"
                )
    salt_chains = {r["chain"] for r in market["new_observations"] if r["counted"]}
    require(
        len(salt_chains) == market["salt_r1_decision"]["distinct_verified_chains"] == 2,
        "Salt chain count mismatch",
    )
    final = docs["final-three.json"]
    require(
        final["selected"] == [] and final["required_family_count"] == 3,
        "Unsupported final three",
    )
    require(
        {r["template_candidate_code"] for r in final["near_misses"]} == deep,
        "Missing near-miss record",
    )
    require(
        all(
            r["remaining_blockers"] and not r["production_enabled"]
            for r in final["near_misses"]
        ),
        "Premature near-miss approval",
    )
    require(
        docs["substitution-compatibility.json"]["ready_substitution_count"] == 0,
        "Invented substitution",
    )
    for name in (
        "final-three.json",
        "implementation-readiness.json",
        "candidate-funnel.json",
    ):
        require(docs[name]["status"] == "BLOCKED", "Decision mismatch")
    scope_audit()
    print(
        json.dumps(
            dict(
                evidence_consistency="PASS",
                operation_status="BLOCKED",
                screened=23,
                deep_reviewed=9,
                selected=0,
                resolved_mass_rows=exact,
                unresolved_mass_rows=unresolved,
                no_float_audit="PASS",
                scope="PASS",
            )
        )
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", action="store_true")
    parser.add_argument("--package", type=Path, default=PACKAGE)
    args = parser.parse_args()
    audit(args.package)
    if args.database:
        database_audit(args.package)


if __name__ == "__main__":
    main()
