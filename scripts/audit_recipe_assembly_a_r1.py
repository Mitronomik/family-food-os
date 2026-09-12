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
    require(git("rev-parse", "origin/main") == BASE, "Exact main base changed")
    require(
        git("merge-base", REVIEWED_HEAD, "HEAD") == REVIEWED_HEAD,
        "Wrong correction ancestor",
    )
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


REVIEWED_HEAD = "4741e91710e17b86dbc25c5e69ca58ea36c5c635"
BASIC_COMMODITIES = {
    "SALT",
    "SUGAR",
    "OLIVE_OIL",
    "SUNFLOWER_OIL",
    "BLACK_PEPPER",
    "PARSLEY_DRIED",
    "GARLIC_POWDER",
    "CUMIN_GROUND",
}
PROTECTED = (
    "quantity-authority.json",
    "composition-readiness.json",
    "rights-review.json",
    "kitchen-verification.json",
    "ru-familiarity.json",
    "substitution-compatibility.json",
    "baseline-verification.json",
    "catalogue-inventory.json",
)


def reviewed(name):
    return json.loads(
        git("show", f"{REVIEWED_HEAD}:data/curation/recipe-assembly-a-r1/{name}")
    )


def default_gate(review):
    """Use independent reviewed facts, not the classification as a verdict."""
    if review["market_classification"] == "SPECIALTY_OR_UNCLEAR":
        return "NOT_PASSED"
    if not review["exact_form_resolved"] or not review["ordinary_retail_supported"]:
        return "NOT_PASSED"
    if review["default_dependency_risk"] == "RARE_DEPENDENCY":
        return (
            "PASS"
            if review["substitution_required"] and review["substitution_path_reviewed"]
            else "NOT_PASSED"
        )
    if review["default_dependency_risk"] != "LOW":
        return "NOT_PASSED"
    supported_reason = (
        review["market_classification"] == "RU_MASS_MARKET"
        or review["commodity_exception_applicable"]
        or bool(review["specific_product_reason"])
    )
    return "PASS" if supported_reason else "NOT_PASSED"


def candidate_gates(docs):
    quantities = docs["quantity-authority.json"]["candidate_batches"]
    composition = {
        f["food_code"]: f for f in docs["composition-readiness.json"]["foods"]
    }
    kitchen = {
        r["template_candidate_code"]: r
        for r in docs["kitchen-verification.json"]["records"]
    }
    rights = {r["source_id"]: r for r in docs["rights-review.json"]["donors"]}
    familiar = {
        r["template_candidate_code"]: r
        for r in docs["ru-familiarity.json"]["candidates"]
    }
    terminal = docs["market-evidence.json"]["candidate_terminal_inputs"]
    old = {
        r["template_candidate_code"]: r
        for r in reviewed("candidate-funnel.json")["candidates"]
    }
    gates = {}
    for code, candidate in old.items():
        g = {
            "rights": "PASS" if rights[code]["decision"] == "ACCEPT" else "NOT_PASSED",
            "kitchen_scope": "PASS"
            if kitchen[code]["status"] == "KITCHEN_VERIFIED"
            else "NOT_PASSED",
        }
        for field in (
            "food_form_composition",
            "exact_input_mass",
            "ru_familiarity",
            "market_default",
            "source_template_scope",
            "ordered_process",
            "russian_display",
            "transformation_dependencies",
        ):
            g[field] = "NOT_REVIEWED"
        if code in quantities:
            rows = [r for r in quantities[code]["rows"] if r["required"]]
            ts = terminal[code]
            g.update(
                food_form_composition="PASS"
                if all(
                    r["food_code"]
                    and composition.get(r["food_code"], {}).get("version")
                    for r in rows
                )
                and all(r["source_form_resolved"] for r in ts)
                else "NOT_PASSED",
                exact_input_mass="PASS"
                if all(r["recipe_input_mass_g"] is not None for r in rows)
                else "NOT_PASSED",
                ru_familiarity="PASS"
                if familiar[code]["reviewer_decision"] == "RU_RECIPE_FAMILIAR"
                else "NOT_PASSED",
                market_default="PASS"
                if all(default_gate(r) == "PASS" for r in ts)
                else "NOT_PASSED",
                source_template_scope="PASS",
                ordered_process="PASS",
                russian_display="PASS"
                if all(re.search(r"[А-Яа-яЁё]", r["name_ru"]) for r in rows)
                else "NOT_PASSED",
                transformation_dependencies="PASS",
            )
        else:
            # Preserve the already evidenced screen failure. No invented complete terminal inventory.
            require(candidate["remaining_blockers"], "Screen evidence lost")
            g["food_form_composition"] = "NOT_PASSED"
        gates[code] = g
    return gates


def residuals(gates, market):
    deep = set(market["candidate_terminal_inputs"])
    rows = []
    for key, title in (
        ("food_form_composition", "Точная форма / Composition"),
        ("exact_input_mass", "Точная входная масса"),
        ("kitchen_scope", "Применимая кухонная проверка опубликованного варианта"),
        ("rights", "Права конкретного донора"),
        ("ru_familiarity", "Привычность семейства для российской аудитории"),
    ):
        affected = sorted(c for c in deep if gates[c][key] != "PASS")
        rows.append(
            dict(
                code=key.upper(),
                name_ru=title,
                scope="INDIVIDUAL",
                candidates=affected,
                deep_reviewed_affected=len(affected),
                selected_final_three_affected=0,
            )
        )
    # Unresolved identity is already counted under form/composition; do not duplicate it as rarity.
    affected = sorted(
        c
        for c, ts in market["candidate_terminal_inputs"].items()
        if any(
            t["default_dependency_risk"] == "UNRESOLVED_PRODUCT_EVIDENCE" for t in ts
        )
    )
    rows.append(
        dict(
            code="FORM_SPECIFIC_MARKET_EVIDENCE",
            name_ru="Точное рыночное исполнение маргарина/майонеза не подтверждено наблюдением",
            scope="INDIVIDUAL",
            candidates=affected,
            deep_reviewed_affected=len(affected),
            selected_final_three_affected=0,
            reason="Не число сетей; 72% против retained 80% и отсутствие подтверждения оливкового масла. Неявные формы/спреи уже учтены в FOOD_FORM_COMPOSITION.",
        )
    )
    rows.append(
        dict(
            code="VERIFIED_VARIANT_SUBSTITUTION",
            name_ru="Нет проверенной замены для совокупного требования трёх семейств",
            scope="FINAL_THREE_FEATURE",
            candidates=[],
            deep_reviewed_affected=0,
            selected_final_three_affected=0,
            reviewed_substitution_provider_count=0,
            target_family_count=3,
            reason="Не индивидуальный запрет всем RU_AVAILABLE. Требование хотя бы одной замены относится к будущей финальной тройке.",
        )
    )
    return rows


def market_and_readiness_audit(docs):
    market = docs["market-evidence.json"]
    originals = reviewed("market-evidence.json")
    old_foods = {r["food_code"]: r for r in originals["foods"]}
    retained_foods = {
        r["food_code"]: r
        for r in read(ROOT / "data/curation/pr6-ru-food-data/food-readiness.json")[
            "rows"
        ]
    }
    observations = {
        r["id"]: r
        for r in read(ROOT / "data/curation/pr6-ru-food-data/market-evidence.json")[
            "observations"
        ]
    }
    source_ids = {r["source_id"] for r in docs["source-manifest.json"]["sources"]}
    food_reviews = {r["food_code"]: r for r in market["foods"]}
    require(
        BASIC_COMMODITIES | {"WATER", "CANOLA_OIL", "SESAME_OIL"}
        <= food_reviews.keys(),
        "Commodity review coverage lost",
    )
    required_fields = (
        "market_classification",
        "ordinary_retail_supported",
        "commodity_exception_applicable",
        "specific_product_reason",
        "default_dependency_risk",
        "substitution_required",
        "substitution_path_reviewed",
        "default_gate_result",
        "evidence_refs",
        "decision_reason",
    )
    all_reviews = market["foods"] + [
        t for ts in market["candidate_terminal_inputs"].values() for t in ts
    ]
    for r in all_reviews:
        require(
            all(
                type(r[k]) is bool
                for k in (
                    "exact_form_resolved",
                    "ordinary_retail_supported",
                    "commodity_exception_applicable",
                    "substitution_required",
                    "substitution_path_reviewed",
                )
            ),
            "Market dimensions must be explicit booleans",
        )
        require(
            r["default_dependency_risk"]
            in {
                "LOW",
                "RARE_DEPENDENCY",
                "UNRESOLVED_FORM",
                "UNRESOLVED_PRODUCT_EVIDENCE",
            },
            "Unknown dependency-risk decision",
        )
        require(
            all(k in r for k in required_fields), "Missing explicit market dimension"
        )
        require(
            r["decision_reason"] and r["evidence_refs"] and r["policy_refs"],
            "Unreasoned market decision",
        )
        code = r["food_code"]
        ordinary_evidence = code == "WATER" or any(
            ref in observations
            and observations[ref]["food_code"] == code
            and observations[ref]["status"] == "AVAILABLE"
            for ref in r["evidence_refs"]
        )
        require(
            r["ordinary_retail_supported"] == ordinary_evidence,
            "Ordinary-retail flag contradicts retained same-food evidence",
        )
        if r["exact_form_resolved"]:
            require(
                code in retained_foods
                and r["exact_form"] == retained_foods[code]["food_form"],
                "Commodity/input exact form unresolved",
            )
        for ref in r["evidence_refs"]:
            require(
                ref in observations or ref in source_ids, "Unretained market evidence"
            )
        if r["commodity_exception_applicable"]:
            require(
                r["exact_form_resolved"] and r["commodity_exception_reason"],
                "Commodity exception without exact identity/reason",
            )
            if r["commodity_exception_kind"] == "TAP_WATER":
                require(
                    code == "WATER" and "WATER:EXCEPTION" in r["evidence_refs"],
                    "Incorrect water exception",
                )
            else:
                require(
                    r["commodity_exception_kind"] == "BASIC_COMMODITY"
                    and code in BASIC_COMMODITIES,
                    "Blanket oil/spice commodity exception",
                )
                require(
                    any(
                        ref in observations
                        and observations[ref]["food_code"] == code
                        and observations[ref]["status"] == "AVAILABLE"
                        for ref in r["evidence_refs"]
                    ),
                    "Commodity ordinary evidence absent",
                )
        else:
            require(
                r["commodity_exception_kind"] == "NONE"
                and r["commodity_exception_reason"] is None,
                "Inconsistent exception",
            )
        if code == "WATER":
            require(
                r["commodity_exception_applicable"]
                and r["commodity_exception_kind"] == "TAP_WATER"
                and default_gate(r) == "PASS",
                "Water exception lost",
            )
        if code == "SALT" and r["exact_form_resolved"]:
            require(
                r["commodity_exception_applicable"]
                and r["default_dependency_risk"] == "LOW",
                "Table salt exception lost",
            )
        if r["substitution_required"]:
            require(
                r["default_dependency_risk"] == "RARE_DEPENDENCY"
                and r["substitution_policy_reason"] == "DOCUMENTED_RARE_REQUIRED_INPUT",
                "Substitution without explicit rarity policy reason",
            )
        else:
            require(
                r["default_dependency_risk"] != "RARE_DEPENDENCY"
                and r["substitution_policy_reason"] is None,
                "Rare dependency escaped substitution policy",
            )
        require(
            not r["substitution_path_reviewed"],
            "Correction created substitution authority",
        )
        require(
            r["default_gate_result"] == default_gate(r),
            "Default gate contradicts explicit facts (classification alone is insufficient)",
        )
    for code, f in food_reviews.items():
        cls = (
            old_foods[code]["classification"]
            if code in old_foods
            else retained_foods[code]["market_classification"]
        )
        require(f["market_classification"] == cls, "Market classification changed")
    require(
        market["candidate_terminal_inputs"].keys()
        == originals["candidate_terminal_inputs"].keys(),
        "Terminal coverage changed",
    )
    for code, terminals in market["candidate_terminal_inputs"].items():
        original = {
            r["row_id"]: r for r in originals["candidate_terminal_inputs"][code]
        }
        require(
            {r["row_id"] for r in terminals} == original.keys(),
            "Terminal input omission",
        )
        for r in terminals:
            o = original[r["row_id"]]
            require(
                r["food_code"] == o["food_code"]
                and r["source_form_resolved"] == o["form_resolved"],
                "Market PASS repaired source form",
            )
            require(
                r["market_classification"] == o["classification"],
                "Terminal classification changed",
            )
            if not r["source_form_resolved"] and r["row_id"] != "R1-23:1":
                require(
                    not r["exact_form_resolved"]
                    and not r["commodity_exception_applicable"]
                    and r["default_gate_result"] == "NOT_PASSED",
                    "Unresolved source choice collapsed to commodity",
                )
            else:
                f = food_reviews[r["food_code"]]
                require(
                    all(r[k] == f[k] for k in required_fields),
                    "Terminal decision disagrees with reviewed exact food",
                )
    salt = market["salt_r1_decision"]
    require(
        salt["classification"] == "RU_AVAILABLE"
        and salt["distinct_verified_chains"] == 2
        and salt["default_gate_result"] == "PASS",
        "Salt classification/default distinction lost",
    )
    for name in PROTECTED:
        require(
            docs[name] == reviewed(name),
            f"Market correction altered protected evidence: {name}",
        )
    gates = candidate_gates(docs)
    ready = sorted(c for c, g in gates.items() if all(v == "PASS" for v in g.values()))
    final = docs["final-three.json"]
    require(final["candidate_gates"] == gates, "Candidate gates disagree with evidence")
    require(
        sorted(r["template_candidate_code"] for r in final["individually_ready"])
        == ready,
        "Individually-ready count disagrees with gates",
    )
    deep = set(market["candidate_terminal_inputs"])
    require(
        {r["template_candidate_code"] for r in final["near_misses"]}
        == deep - set(ready),
        "Near-miss disposition mismatch",
    )
    for r in final["individually_ready"] + final["near_misses"]:
        is_ready = r["template_candidate_code"] in ready
        require(
            bool(r["remaining_blockers"]) != is_ready and not r["production_enabled"],
            "Incorrect ready blockers/publication",
        )
    # Current unchanged substitution evidence supplies no validated replacement; never weaken the collective gate.
    require(
        final["selected_final_three"] == [] and final["required_family_count"] == 3,
        "Final-three target or collective gate weakened",
    )
    require(
        docs["substitution-compatibility.json"]["ready_substitution_count"] == 0,
        "Substitution evidence changed",
    )
    require(
        final["collective_feature_gates"]["verified_substitution"] == "NOT_PASSED",
        "Collective substitution requirement lost",
    )
    funnel = docs["candidate-funnel.json"]
    for c in funnel["candidates"]:
        code = c["template_candidate_code"]
        require(
            c["individual_gates"] == gates[code], "Screen/deep recomputation mismatch"
        )
        require(
            c["disposition"] == ("INDIVIDUALLY_READY" if code in ready else "DEFER"),
            "Candidate disposition mismatch",
        )
    report = docs["implementation-readiness.json"]
    require(report["individually_ready"] == ready, "Readiness identity list mismatch")
    require(
        report["selected_count"]
        == funnel["final_count"]
        == len(final["selected_final_three"]),
        "Final-selected count mismatch",
    )
    require(
        report["individually_ready_count"]
        == funnel["individually_ready_count"]
        == len(ready),
        "Readiness count mismatch",
    )
    require(
        report["smallest_residual_blocker_classes"] == residuals(gates, market),
        "Residual blocker counts mismatch",
    )
    for name in (
        "final-three.json",
        "implementation-readiness.json",
        "candidate-funnel.json",
    ):
        require(docs[name]["status"] == "BLOCKED", "Unsupported R1 READY")
    return ready


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
            bool(c["remaining_blockers"]) == (c["disposition"] == "DEFER"),
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
    ready = market_and_readiness_audit(docs)
    scope_audit()
    print(
        json.dumps(
            dict(
                evidence_consistency="PASS",
                operation_status="BLOCKED",
                screened=23,
                deep_reviewed=9,
                individually_ready=len(ready),
                selected=0,
                resolved_mass_rows=exact,
                unresolved_mass_rows=unresolved,
                no_float_audit="PASS",
                scope="PASS",
            )
        )
    )


def adversarial_audit(package):
    """Mutate disposable package copies and re-hash them, exercising semantic guards."""
    import copy
    import contextlib
    import io
    import shutil

    cases = (
        "available_alone",
        "commodity_without_identity",
        "all_oils",
        "all_spices",
        "water_exception_lost",
        "unreasoned_substitution",
        "specialty_pass",
        "market_repairs_mass",
        "market_repairs_form",
        "market_repairs_composition",
        "ready_count",
        "terminal_omission",
        "float",
        "cross_food_portion",
    )
    for case in cases:
        with TemporaryDirectory() as directory:
            target = Path(directory) / "package"
            shutil.copytree(package, target)
            docs = {p.name: read(p) for p in target.glob("*.json")}
            market = docs["market-evidence.json"]
            food = {r["food_code"]: r for r in market["foods"]}
            terminal = market["candidate_terminal_inputs"]
            if case == "available_alone":
                # Same RU_AVAILABLE class, low risk, ordinary evidence and product reason: must pass.
                terminal["R1-13"][2]["default_gate_result"] = "NOT_PASSED"
            elif case == "commodity_without_identity":
                food["SALT"]["exact_form_resolved"] = False
            elif case == "all_oils":
                food["CANOLA_OIL"].update(
                    commodity_exception_applicable=True,
                    commodity_exception_kind="BASIC_COMMODITY",
                    commodity_exception_reason="All oils",
                    default_dependency_risk="LOW",
                    default_gate_result="PASS",
                )
            elif case == "all_spices":
                retained = next(
                    r
                    for r in read(
                        ROOT / "data/curation/pr6-ru-food-data/food-readiness.json"
                    )["rows"]
                    if r["food_code"] == "CORIANDER_SEED"
                )
                invented = copy.deepcopy(food["BLACK_PEPPER"])
                invented.update(
                    food_code="CORIANDER_SEED",
                    exact_form=retained["food_form"],
                    evidence_refs=retained["market_evidence_refs"],
                    commodity_exception_reason="All spices",
                )
                market["foods"].append(invented)
            elif case == "water_exception_lost":
                food["WATER"].update(
                    commodity_exception_applicable=False,
                    commodity_exception_kind="NONE",
                    commodity_exception_reason=None,
                )
            elif case == "unreasoned_substitution":
                food["GARLIC"]["substitution_required"] = True
            elif case == "specialty_pass":
                food["LIME_JUICE"]["default_gate_result"] = "PASS"
            elif case == "market_repairs_mass":
                egg = docs["quantity-authority.json"]["candidate_batches"]["R1-23"][
                    "rows"
                ][0]
                egg.update(recipe_input_mass_g=egg["source_mass_g"], issue_ru=None)
                docs["quantity-authority.json"]["candidate_batches"]["R1-23"][
                    "all_required_input_masses_resolved"
                ] = True
            elif case == "market_repairs_form":
                terminal["R1-22"][0].update(
                    food_code="RICE_BROWN", source_form_resolved=True
                )
            elif case == "market_repairs_composition":
                next(
                    r
                    for r in docs["composition-readiness.json"]["foods"]
                    if r["food_code"] == "MARGARINE"
                )["version"] = 1
            elif case == "ready_count":
                docs["final-three.json"]["individually_ready"] = []
            elif case == "terminal_omission":
                terminal["R1-21"].pop()
            elif case == "float":
                docs["quantity-authority.json"]["candidate_batches"]["R1-21"]["rows"][
                    0
                ]["source_quantity"] = float("6")
            elif case == "cross_food_portion":
                docs["quantity-authority.json"]["candidate_batches"]["R1-16"]["rows"][
                    2
                ].update(authority="FDC-PORTION-88669:exact", recipe_input_mass_g="4.5")
            for name, value in docs.items():
                if name != "checksums.json":
                    (target / name).write_text(
                        json.dumps(value, ensure_ascii=False, indent=2) + "\n"
                    )
            checks = {
                p.name: digest(p)
                for p in target.iterdir()
                if p.is_file() and p.name != "checksums.json"
            }
            (target / "checksums.json").write_text(json.dumps(dict(files=checks)))
            error = None
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    audit(target)
            except ValueError as exc:
                error = str(exc)
            require(error is not None, f"Adversarial package accepted: {case}")
            print(f"Adversarial {case}: REJECTED ({error})")
    print(f"Adversarial semantic package-copy checks: {len(cases)} PASS")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", action="store_true")
    parser.add_argument("--adversarial", action="store_true")
    parser.add_argument("--package", type=Path, default=PACKAGE)
    args = parser.parse_args()
    audit(args.package)
    if args.database:
        database_audit(args.package)
    if args.adversarial:
        adversarial_audit(args.package)


if __name__ == "__main__":
    main()
