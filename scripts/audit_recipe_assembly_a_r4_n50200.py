"""Independently audit N50200 research; never promote data or open a production DB.

--database creates and deletes a temporary accepted replay with AI disabled.
--adversarial exercises semantic gates, including a synthetic positive control.
--source-dir optionally verifies the previously downloaded full AFRS/SR originals.
A passing audit validates the evidence, not recipe readiness or kitchen testing.
"""

import argparse
import ast
from copy import deepcopy
from decimal import Decimal
import hashlib
import io
import json
import os
from pathlib import Path
import re
import sqlite3
import subprocess
import sys
from tempfile import TemporaryDirectory
import zipfile
import csv

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "data/curation/recipe-assembly-a-r4-n50200"
BASE = "a375f005b09880cf6a63cb5c8b1e964a0f558cb7"
R3_HEAD = "8a167bee3b8748d4280e69768b483dd9aa97238b"
BRANCH = "codex/recipe-assembly-a-r4-n50200"
LB = Decimal("453.59237")
OZ = LB / Decimal("16")
ALLOWED = {
    "scripts/audit_recipe_assembly_a_r4_n50200.py",
    "state/current-focus.md",
    "state/progress.md",
    "state/handoff.md",
    "docs/family-food/master-roadmap.md",
    "docs/family-food/food-composition-and-assembly.md",
}
# Independently transcribed and visually checked N50200 Weight inventory.
SOURCE = [
    ("TURKEY,GROUND,90% LEAN,RAW", "25-1/2 lbs"),
    ("ONIONS,FRESH,CHOPPED", "2-7/8 lbs"),
    ("PARSLEY,FRESH,BUNCH,CHOPPED", "3-1/2 oz"),
    ("BREADCRUMBS,DRY,GROUND,FINE", "3-1/8 lbs"),
    ("SALT", "1-1/4 oz"),
    ("GARLIC POWDER", "1-1/4 oz"),
    ("PEPPER,WHITE,GROUND", "1/2 oz"),
    ("WORCESTERSHIRE SAUCE", "8-1/2 oz"),
    ("MUSTARD,DRY", "3/4 oz"),
    ("CHEESE,MOZZARELLA,PART SKIM", "3 lbs"),
    ("ROLL,SANDWICH BUNS,SPLIT", "9-1/2 lbs"),
    ("TOMATOES,FRESH,SLICED", "2 lbs"),
    ("PEPPERS,GREEN,FRESH,MEDIUM,SLICED,THIN", "2 lbs"),
]
CODES = [
    "TURKEY_GROUND_90",
    "ONION_RAW_GENERIC",
    "PARSLEY",
    "BREADCRUMBS",
    "SALT",
    "GARLIC_POWDER",
    "WHITE_PEPPER",
    "WORCESTERSHIRE_SAUCE",
    "MUSTARD_GROUND",
    "CHEESE_MOZZARELLA_PART_SKIM_GENERIC",
    "SANDWICH_BUN",
    "TOMATO",
    "BELL_PEPPER_GREEN",
]
DISPOSITIONS = [
    "NEW_FOOD_INGREDIENT_REQUIRED",
    "NEW_FOOD_INGREDIENT_REQUIRED",
    "EXACT_EXISTING",
    "EXACT_EXISTING",
    "EXACT_EXISTING",
    "EXACT_EXISTING",
    "NEW_FOOD_INGREDIENT_REQUIRED",
    "NEW_FOOD_INGREDIENT_REQUIRED",
    "EXISTING_REQUIRES_COMPOSITION",
    "FORM_SPLIT_REQUIRED",
    "NEW_FOOD_INGREDIENT_REQUIRED",
    "EXACT_EXISTING",
    "EXACT_EXISTING",
]
ROW_IDS = [f"N50200-{i:02}" for i in range(1, 14)]
VARIANTS = {
    "BASE_NO_GARNISH": ROW_IDS[:11],
    "GREEN_PEPPER_GARNISH": ROW_IDS[:11] + [ROW_IDS[12]],
    "TOMATO_GARNISH": ROW_IDS[:11] + [ROW_IDS[11]],
}
CORE = {
    "1008": "ENERGY_KCAL",
    "1003": "PROTEIN",
    "1004": "FAT_TOTAL",
    "1005": "CARBOHYDRATE_BY_DIFFERENCE",
    "1079": "FIBER_TOTAL_DIETARY",
}
PIN_QUERY = """
SELECT f.canonical_code,f.canonical_name,c.version,c.input_state,c.kind,
       p.source_id,p.source_version,p.source_name,
       p.source_data_type,p.basis_grams,p.estimated
FROM food_ingredients f
LEFT JOIN food_composition_versions c ON c.food_ingredient_id=f.id
LEFT JOIN food_nutrition_profiles p ON p.id=c.profile_id
ORDER BY f.canonical_code
"""
PROFILE_QUERY = """
SELECT f.canonical_code,p.*,s.registry_version,s.value_count,s.value_sha256
FROM food_ingredients f
JOIN food_nutrition_profiles p ON p.food_ingredient_id=f.id
LEFT JOIN nutrition_vector_seals s ON s.profile_id=p.id
WHERE p.is_current=1
ORDER BY f.canonical_code,p.source_version,p.id
"""
VECTOR_QUERY = """
SELECT p.source_id,f.canonical_code,v.nutrient_code,v.amount,v.provenance_json
FROM food_ingredients f
JOIN food_nutrition_profiles p ON p.food_ingredient_id=f.id
JOIN nutrient_values v ON v.profile_id=p.id
WHERE p.is_current=1 ORDER BY f.canonical_code,v.nutrient_code
"""


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def reject_float(value):
    raise ValueError(f"Float or non-finite JSON value forbidden: {value}")


def read(path):
    return json.loads(
        path.read_text(), parse_float=reject_float, parse_constant=reject_float
    )


def encode(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def source_text(path):
    return subprocess.check_output(["pdftotext", "-layout", str(path), "-"], text=True)


def fractional(value):
    whole, _, fraction = value.rpartition("-")
    if not fraction:
        fraction = value
    if "/" in fraction:
        numerator, denominator = fraction.split("/")
        return Decimal(whole or "0") + Decimal(numerator) / Decimal(denominator)
    return Decimal(value)


def weight_grams(weight):
    value, unit = weight.split()
    require(unit in {"lbs", "oz"}, "Unexpected source weight unit")
    return fractional(value) * (LB if unit == "lbs" else OZ)


def scope_names(names):
    for name in names - {".DS_Store"}:
        require(
            name in ALLOWED or name.startswith(str(PACKAGE.relative_to(ROOT)) + "/"),
            f"Out of scope: {name}",
        )


def check_frozen(expected, actual):
    require(expected == actual, "Frozen R1/R2/R3 bytes or inventory changed")


def scope(d):
    b = d["baseline.json"]
    require(
        b["accepted_main"] == BASE and git("rev-parse", "origin/main") == BASE,
        "Exact accepted main differs",
    )
    require(git("merge-base", BASE, "HEAD") == BASE, "Wrong branch base")
    require(git("merge-base", R3_HEAD, BASE) == R3_HEAD, "R3 head not merged")
    require(git("rev-parse", "--abbrev-ref", "HEAD") == BRANCH, "Wrong branch")
    receipt = d["pr34-receipt.json"]
    for key, value in {
        "number": 34,
        "merged": True,
        "state": "closed",
        "merge_commit_sha": BASE,
        "head_sha": R3_HEAD,
        "base_ref": "main",
    }.items():
        require(receipt[key] == value, f"PR34 receipt differs: {key}")
    require(
        git("log", "-1", "--format=%B", BASE).splitlines()[0]
        == "Merge pull request #34 from Mitronomik/codex/recipe-assembly-a-r3",
        "Merge commit lineage differs",
    )
    for key, value in {
        "pr34": "MERGED",
        "pr6": "COMPLETE",
        "r1": "COMPLETE AS BLOCKED RESEARCH",
        "r2": "COMPLETE AS BLOCKED RESEARCH",
        "r3": "COMPLETE AS BLOCKED RESEARCH",
        "ready_count": 2,
        "required_count": 3,
        "individually_ready": ["R1-21", "R1-23"],
        "third_candidate": None,
        "assembly_a": "BLOCKED",
        "assembly_b": "NOT STARTED",
        "pr7_plus": "NOT STARTED",
        "migration": "0029_food_composition_core",
        "open_gates": ["family_count", "optional_role", "verified_substitution"],
    }.items():
        require(b[key] == value, f"Baseline drift: {key}")
    actual = {
        str(p.relative_to(ROOT)): digest(p)
        for n in [1, 2, 3]
        for p in (ROOT / f"data/curation/recipe-assembly-a-r{n}").rglob("*")
        if p.is_file()
    }
    check_frozen(b["frozen_packages_sha256"], actual)
    tracked = git(
        "ls-tree",
        "-r",
        "--name-only",
        BASE,
        *[f"data/curation/recipe-assembly-a-r{n}" for n in [1, 2, 3]],
    ).splitlines()
    require(set(tracked) == set(actual), "Frozen baseline inventory differs")
    for name, sha in actual.items():
        require(
            hashlib.sha256(
                subprocess.check_output(["git", "show", f"{BASE}:{name}"], cwd=ROOT)
            ).hexdigest()
            == sha,
            f"Frozen base hash: {name}",
        )
    names = set(git("diff", "--name-only", BASE).splitlines()) | set(
        git("ls-files", "--others", "--exclude-standard").splitlines()
    )
    scope_names(names)
    require(
        ".DS_Store" not in git("diff", "--cached", "--name-only").splitlines(),
        "Unrelated .DS_Store staged",
    )
    for name, tree in b["production_trees"].items():
        require(
            git("rev-parse", f"{BASE}:{name}") == tree
            and git("rev-parse", f"HEAD:{name}") == tree,
            f"Production tree changed: {name}",
        )
    print("Exact merged PR34/main, frozen R1/R2/R3 and production scope: PASS")


def package(d, source_dir):
    for name, expected in {
        "sources/fdc-candidates.json": "4ab8f56333f2114ddcc96d060c18e4ee9cebe0e6c6ee3ac6df8776e2857e76e9",
        "sources/turkey-dataset-search.json": "c5cc2e449642f9d3c93d2dc06ba466f3883efd74889dc7fb165b7557e2424e46",
        "sources/n50200.txt": "51c3a02c654498a09d1393b80d5a8fe4c5e81557db68f5ab409fa936cd100225",
    }.items():
        require(
            digest(PACKAGE / name) == expected,
            f"Reviewed source extract changed: {name}",
        )
    manifest = d["source-manifest.json"]["afrs"]
    require(
        manifest["version"] == "June 2003"
        and manifest["page"] == 1329
        and manifest["card"] == "N50200"
        and manifest["yield_portions"] == 100
        and manifest["original_sha256"]
        == "2f6795b5fc39b167fb2913bfccb720948dd257f6a90ca3fa7e228d7fb87ec090",
        "AFRS source/version lineage changed",
    )
    actual = {
        str(p.relative_to(PACKAGE)): digest(p)
        for p in PACKAGE.rglob("*")
        if p.is_file() and p.name != "checksums.json"
    }
    require(
        actual == d["checksums.json"]["files"], "Package hashes or inventory changed"
    )
    require(
        not any(
            isinstance(n, ast.Constant) and isinstance(n.value, float)
            for n in ast.walk(ast.parse(Path(__file__).read_text()))
        ),
        "Auditor float literal",
    )
    # Independent primary-PDF extraction, never trust editable row labels alone.
    pdf = ROOT / "data/curation/recipe-assembly-a-r3/sources/afrs-prefilter.pdf"
    text = source_text(pdf).split("\f")[1] + "\f"
    require(
        text == (PACKAGE / "sources/n50200.txt").read_text(),
        "Retained N50200 transcription drift",
    )
    primary_rows = []
    in_rows = False
    for line in text.splitlines():
        if line.startswith("Ingredient "):
            in_rows = True
        elif line == "Method":
            break
        elif in_rows and line.strip():
            cells = re.split(r"\s{2,}", line.strip())
            primary_rows.append(tuple(cells[:2]))
    require(primary_rows == SOURCE, "Exact primary row inventory/Weight differs")
    std = source_text(
        ROOT / "data/curation/recipe-assembly-a-r2/sources/afrs-full-excerpt.pdf"
    )
    for token in [
        "June 2003",
        "developed, tested",
        "100 portions",
        "Edible Portion (E.P.)",
        "As Purchased (A.P.)",
    ]:
        require(token in std, f"AFRS standardization/EP source missing: {token}")
    require(
        "Garnish with slice of fresh green pepper or tomato (optional)." in text,
        "Source omission/choice absent",
    )
    if source_dir:
        afrs = source_dir / "afrs-full.pdf"
        require(
            digest(afrs) == d["source-manifest.json"]["afrs"]["original_sha256"],
            "Full AFRS hash mismatch",
        )
        require(afrs.stat().st_size == 10602998, "Full AFRS size mismatch")
        require(
            " ".join(source_text(afrs).split("\f")[1328].split())
            == " ".join(text.split()),
            "Full source page lineage mismatch",
        )
        archive = source_dir / "sr.zip"
        require(
            digest(archive) == d["sources/fdc-candidates.json"]["archive_sha256"],
            "SR archive hash mismatch",
        )
        with zipfile.ZipFile(archive) as z:
            fdc = d["sources/fdc-candidates.json"]
            ids = {r["fdc_id"] for r in fdc["foods"]}
            for filename, key in [
                ("food.csv", "foods"),
                ("food_nutrient.csv", "nutrients"),
                ("food_portion.csv", "portions"),
            ]:
                source = next(n for n in z.namelist() if n.endswith("/" + filename))
                selected = [
                    r
                    for r in csv.DictReader(io.TextIOWrapper(z.open(source)))
                    if r["fdc_id"] in ids
                ]
                require(selected == fdc[key], f"Primary USDA extraction differs: {key}")
        for record in d["sources/turkey-dataset-search.json"]:
            archive = source_dir / (record["dataset"] + ".zip")
            require(
                digest(archive) == record["archive_sha256"],
                "Turkey dataset hash differs",
            )
            with zipfile.ZipFile(archive) as z:
                member = next(n for n in z.namelist() if n.endswith("/food.csv"))
                matches = [
                    r
                    for r in csv.DictReader(io.TextIOWrapper(z.open(member)))
                    if r["data_type"] in {"sr_legacy_food", "foundation_food"}
                    and "turkey" in r["description"].lower()
                    and "ground" in r["description"].lower()
                ]
            require(
                matches == record["description_matches"],
                "Turkey full dataset search differs",
            )
    print(
        "Primary PDF inventory/EP contract, package/source hashes, Decimal/no-float: PASS"
    )


def market_pass(row):
    classification = row["market_classification"]
    require(
        classification in {"RU_MASS_MARKET", "RU_AVAILABLE", "SPECIALTY_OR_UNCLEAR"},
        "Unknown market class",
    )
    if classification == "RU_MASS_MARKET":
        require(
            len(
                set(row["panel_chains"])
                & {"LENTA", "MAGNIT", "OKEY", "PEREKRESTOK", "PYATEROCHKA"}
            )
            >= 3,
            "Mass-market panel unsupported",
        )
    return bool(
        classification != "SPECIALTY_OR_UNCLEAR"
        and row["ordinary_retail_supported"]
        and row["exact_form_supported"]
        and row["default_dependency_risk"] == "LOW_CATALOGUE_LEVEL"
        and (
            classification == "RU_MASS_MARKET"
            or row["commodity_exception_applicable"]
            or row["specific_product_reason"]
        )
    )


def quantities(d):
    q = d["quantity-authority.json"]
    require(
        q["batch_portions"] == 100
        and q["household_scaling"] is False
        and q["basis"] == "INPUT",
        "Household scaling or basis changed",
    )
    require(
        q["lb_grams"] == str(LB) and Decimal(q["oz_grams"]) == OZ,
        "Unit constants changed",
    )
    require([r["row_id"] for r in q["rows"]] == ROW_IDS, "Missing source quantity row")
    for row, (form, weight) in zip(q["rows"], SOURCE, strict=True):
        require(
            row["source_form"] == form and row["source_weight"] == weight,
            "Quantity not bound to source Weight",
        )
        require(
            row["authority"] == "AFRS_WEIGHT_COLUMN" and row["mass_basis"] == "EP",
            "AP/Measure/estimate authority rejected",
        )
        for flag in [
            "estimated",
            "measure_used",
            "issue_used",
            "piece_used",
            "density_used",
            "package_used",
        ]:
            require(row[flag] is False, f"Estimate or non-Weight mass: {flag}")
        require(
            not any(
                k in row
                for k in [
                    "density_g_ml",
                    "piece_mass_g",
                    "measure_ml",
                    "package_weight_g",
                ]
            ),
            "Derived recipe measure rejected",
        )
        require(
            all(isinstance(row[k], str) for k in ["grams", "lb", "oz"]),
            "Mass must be Decimal string",
        )
        require(
            Decimal(row["grams"])
            == weight_grams(weight)
            == Decimal(row["lb"]) * LB + Decimal(row["oz"]) * OZ,
            "EP Decimal arithmetic mismatch",
        )
    require(
        Decimal(q["required_base_grams"])
        == sum((weight_grams(w) for _, w in SOURCE[:11]), Decimal("0")),
        "Required base mass differs",
    )
    require(q["garnish_each_grams"] == "907.18474", "Exact garnish mass absent")
    require(
        q["yield_required_for_input"] is False
        and q["retention_required_for_input"] is False
        and q["prepared_nutrition_established"] is False,
        "Input/output nutrition conflation",
    )
    # Process quantities are recorded as conflicts, never alternate input authority.
    conflicts = q["source_process_mass_discrepancies"]
    require(
        len(conflicts) == 2
        and conflicts[0]["weight_column_oz"] == "48"
        and conflicts[0]["method_total_oz"] == "50",
        "Cheese process conflict hidden",
    )
    mixture = sum((weight_grams(w) for _, w in SOURCE[:9]), Decimal("0")) / OZ
    require(
        mixture
        == Decimal(conflicts[1]["patty_mixture_weight_oz"])
        == Decimal("519.75"),
        "Patty mixture conflict changed",
    )
    require(conflicts[1]["method_total_oz"] == "500", "Patty process mass changed")


def current_composition_ok(row, inventory):
    pin = inventory.get(row["food_code"])
    return bool(
        pin
        and pin["version"]
        and pin["kind"] == "ATOMIC"
        and pin["input_state"] == "INPUT"
        and pin["source_id"]
        and pin["source_version"]
        and pin["estimated"] is not True
        and row["current_composition"] == pin
    )


def profile_audit(d):
    candidates = d["profile-candidates.json"]
    require(
        candidates["production_promotion"] is False, "Production promotion forbidden"
    )
    rows = candidates["rows"]
    require([r["row_id"] for r in rows] == ROW_IDS, "Missing profile row")
    fdc = d["sources/fdc-candidates.json"]
    require(
        fdc["version"] == "2018-04"
        and fdc["basis_grams"] == "100"
        and fdc["archive_sha256"]
        == "b80817294b8850530aaedf2e515c02593b1824f763a0ff356e5c2081643e6fd0",
        "USDA authority/version drift",
    )
    expected_ids = {
        1: "223620",
        2: "170000",
        3: "170416",
        4: "174928",
        5: "173468",
        6: "171325",
        7: "170933",
        8: "171610",
        9: "170929",
        10: "170847",
        11: "172796",
        12: "170457",
        13: "2258588",
    }
    for i, p in enumerate(rows, 1):
        require(
            p["food_code"] == CODES[i - 1] and p["source_id"] == expected_ids[i],
            "Profile identity drift; no 93-to-90 conflation",
        )
        require(
            p["estimated"] is False and p["operation_not_authorized"] is True,
            "Estimate profile/promotion rejected",
        )
        require(
            Decimal(p["basis_grams"]) == (Decimal("112") if i == 1 else Decimal("100")),
            "Profile basis mismatch",
        )
        if "core_nutrient_candidates" in p:
            primary = {
                n["nutrient_id"]: n["amount"]
                for n in fdc["nutrients"]
                if n["fdc_id"] == p["source_id"]
            }
            require(
                p["core_nutrient_candidates"]
                == {code: primary.get(nid) for nid, code in CORE.items()},
                "Nutrient candidate values differ from source",
            )
        if i == 1:
            require(
                p["candidate_complete"] is False
                and p["missing_required_nutrients"]
                == ["CARBOHYDRATE_BY_DIFFERENCE", "FIBER_TOTAL_DIETARY"],
                "Blank turkey values converted to complete profile",
            )
        elif i == 11:
            require(
                p["candidate_complete"] is False
                and p["form_compatibility"] == "REVIEW_REQUIRED",
                "Bun profile compatibility invented",
            )
        else:
            require(
                p["candidate_complete"] is True and not p["missing_required_nutrients"],
                "Reviewed candidate completeness drift",
            )
    require(
        any(
            p["fdc_id"] == "170933" and p["modifier"] == "tsp, ground"
            for p in fdc["portions"]
        ),
        "White pepper ground-form evidence absent",
    )
    require(
        fdc["portion_use"] == "IDENTITY_FORM_ONLY_NOT_RECIPE_MASS",
        "FDC portion misused for recipe mass",
    )
    require(
        all(
            not x["exact_90_raw_matches"]
            for x in d["sources/turkey-dataset-search.json"]
        ),
        "Generic turkey profile invented",
    )


def kitchen(d):
    k = d["kitchen-branches.json"]
    require(k["household_scaling"] is False, "Household kitchen scaling rejected")
    require({v["id"] for v in k["branches"]} == set(VARIANTS), "Missing kitchen branch")
    for v in k["branches"]:
        require(
            v["row_ids"] == VARIANTS[v["id"]] and v["family"] == "N50200",
            "Kitchen full branch inventory mismatch",
        )
        require(
            v["batch_portions"] == 100 and v["household_scaling"] is False,
            "Household scaling rejected",
        )
        require(
            v["standardization_applies"] is True
            and v["branch_explicit"] is True
            and v["independent_test_log_available"] is False,
            "Kitchen evidence scope missing/invented",
        )
        require(
            v["status"] == "NOT_ESTABLISHED",
            "Kitchen verification inferred despite source process conflict",
        )
        require(
            v["process_conflict_ref"] == "quantity-authority.json",
            "Branch kitchen conflict evidence absent",
        )
    process = k["process"]
    for key, value in {
        "oven": "CONVECTION_HIGH_FAN_OPEN_VENT",
        "oven_f": "325",
        "internal_f": "165",
        "internal_hold_seconds": 15,
        "service_minimum_f": "140",
        "new_household_process": False,
    }.items():
        require(process[key] == value, f"Published process changed: {key}")


def gate_contract(gates):
    """All ten readiness conditions; used for real and synthetic truth tables."""
    require(
        set(gates)
        == {
            "source_identity",
            "exact_ep_mass",
            "profile_authority",
            "ru_familiarity",
            "mandatory_market",
            "optional_semantics",
            "kitchen_branches",
            "complete_variant_substitution",
            "rights",
            "input_without_estimates_yield_retention",
        },
        "Incomplete gate inventory",
    )
    require(all(type(v) is bool for v in gates.values()), "Gate must be boolean")
    return "READY_FOR_DATA_ENABLEMENT" if all(gates.values()) else "BLOCKED"


def complete_variant(v, rows, profiles, markets, kitchen_rows, proposed):
    require(
        v["family"] == "N50200" and v["row_ids"] == VARIANTS[v["id"]],
        "Single garnish is not a full substitution variant",
    )
    return (
        all(
            rows[r]["source_identity_established"]
            and (
                profiles[r]["candidate_complete"]
                if proposed
                else rows[r]["current_composition"] is not None
            )
            and market_pass(markets[r])
            for r in v["row_ids"]
        )
        and kitchen_rows[v["id"]]["status"] == "KITCHEN_VERIFIED"
    )


def derive(d):
    quantities(d)
    profile_audit(d)
    inv = {r["canonical_code"]: r for r in d["catalogue-readiness.json"]["inventory"]}
    bindings = d["source-bindings.json"]
    require(
        [r["row_id"] for r in bindings["rows"]] == ROW_IDS,
        "Missing required base row (including Worcestershire and bun)",
    )
    for i, row in enumerate(bindings["rows"]):
        require(
            (row["source_form"], row["source_ep_weight"]) == SOURCE[i],
            "Source row binding mismatch",
        )
        require(
            row["food_code"] == CODES[i]
            and row["identity_disposition"] == DISPOSITIONS[i],
            "Food identity/disposition conflation",
        )
        require(
            row["required"] is (i < 11) and row["source_identity_established"] is True,
            "Required/source identity drift",
        )
        require(
            row["profile_candidate_ref"] == f"PROFILE-{i + 1:02}"
            and row["mass_authority_ref"] == row["row_id"]
            and row["market_ref"] == row["row_id"],
            "Disconnected evidence reference",
        )
        if row["identity_disposition"] == "EXACT_EXISTING":
            require(
                current_composition_ok(row, inv),
                "Current Composition/profile incomplete",
            )
        else:
            require(
                row["current_composition"] is None, "Missing Composition fabricated"
            )
    onion = bindings["rows"][1]
    require(
        onion["onion_colour"] is None
        and "ONION-CID" in onion["source_identity_evidence"]
        and bindings["onion_decision"] == "NEW_GENERIC_ONION_IDENTITY_REQUIRED",
        "Arbitrary onion colour rejected",
    )
    require(
        "TURKEY_GROUND_90" not in inv and "TURKEY_GROUND_93" in inv,
        "Turkey catalogue absence drift",
    )
    m = d["market-evidence.json"]
    require(
        m["reviewed_before_production"] is True
        and m["production_enablement_allowed"] is False,
        "Market-before-production guard missing",
    )
    require([r["row_id"] for r in m["rows"]] == ROW_IDS, "Market inventory incomplete")
    sources = {s["id"]: s for s in d["web-evidence.json"]["sources"]}
    for i, row in enumerate(m["rows"], 1):
        require(
            bindings["rows"][i - 1]["market_status"]
            == {
                "market_classification": row["market_classification"],
                "default_gate_result": row["default_gate_result"],
            },
            "Binding market status differs",
        )
        require(
            row["food_code"] == CODES[i - 1]
            and row["required"] is (i <= 11)
            and row["purchase_required"] is True,
            "Market terminal inventory drift",
        )
        require(
            all(ref in sources for ref in row["evidence_refs"]),
            "Missing market evidence",
        )
        fail = i in [1, 8, 9, 10, 11]
        require(
            row["exact_form_supported"] is not fail,
            "Exact market form support invented",
        )
        require(
            row["market_classification"]
            == ("SPECIALTY_OR_UNCLEAR" if fail else "RU_AVAILABLE"),
            "Market classification contradicts reviewed exact form evidence",
        )
        require(
            row["default_gate_result"] == ("PASS" if market_pass(row) else "BLOCKED"),
            "Rare mandatory input forced through RU_AVAILABLE",
        )
        require(
            row["substitution_required"] is fail
            and row["source_published_substitution_available"] is (i in [12, 13]),
            "Mandatory substitution invented",
        )
    opt = d["optional-role.json"]
    for key, value in {
        "family": "N50200",
        "role": "GARNISH",
        "optional": True,
        "component_kind": "FOOD_COMPONENT",
        "omission_explicit": True,
        "included_row_ids": [ROW_IDS[12], ROW_IDS[11]],
        "selection_cardinality": [0, 1],
        "required_base_unchanged": True,
        "added_after_cooking": True,
        "exact_included_mass_required": True,
        "semantics_result": "PASS",
        "closure_contribution": False,
    }.items():
        require(opt[key] == value, f"Optional food semantics mismatch: {key}")
    kitchen(d)
    sub = d["substitution-matrix.json"]
    require(
        sub["substitution_kind"] == "COMPLETE_RECIPE_VARIANTS"
        and sub["same_required_base"] == ROW_IDS[:11],
        "Substitution must contain full required base",
    )
    require(
        [v["id"] for v in sub["variants"]]
        == ["GREEN_PEPPER_GARNISH", "TOMATO_GARNISH"],
        "Both substitution branches required",
    )
    rows = {r["row_id"]: r for r in bindings["rows"]}
    profiles = {r["row_id"]: r for r in d["profile-candidates.json"]["rows"]}
    markets = {r["row_id"]: r for r in m["rows"]}
    kitchens = {v["id"]: v for v in d["kitchen-branches.json"]["branches"]}
    for v in sub["variants"]:
        for proposed, field in [
            (False, "current_complete"),
            (True, "proposed_complete"),
        ]:
            require(
                v[field]
                is complete_variant(v, rows, profiles, markets, kitchens, proposed),
                "Incomplete branch Composition/kitchen/market claimed complete",
            )
    require(
        sub["status"] == "UNVERIFIED"
        and sub["verified_curated_substitution"] is False
        and sub["after_planned_data_promotion"] == "NOT_ESTABLISHED",
        "Unverified full substitution claimed verified",
    )
    ru = d["ru-familiarity.json"]
    require(
        ru["dish_identity"] == "RU_RECIPE_FAMILIAR"
        and ru["decision"] == "NOT_ESTABLISHED"
        and ru["household_scaling"] is False,
        "Translation/dish familiarity confused with exact recipe eligibility",
    )
    rights = d["rights-provenance.json"]
    require(
        rights["decision"] == "PASS"
        and rights["policy"] == "AFRS RIGHTS-FACTS"
        and rights["same_edition"] is True
        and rights["source_facts_only"] is True
        and rights["logos_photos_layout_reuse"] is False
        and rights["recipe_publication_authorized"] is False,
        "Rights scope drift",
    )
    gates = dict(
        source_identity=all(r["source_identity_established"] for r in rows.values()),
        exact_ep_mass=True,
        profile_authority=all(p["candidate_complete"] for p in profiles.values()),
        ru_familiarity=ru["decision"] == "RU_RECIPE_FAMILIAR",
        mandatory_market=all(market_pass(r) for r in markets.values() if r["required"]),
        optional_semantics=opt["semantics_result"] == "PASS",
        kitchen_branches=all(
            v["status"] == "KITCHEN_VERIFIED" for v in kitchens.values()
        ),
        complete_variant_substitution=all(
            v["proposed_complete"] for v in sub["variants"]
        ),
        rights=rights["decision"] == "PASS",
        input_without_estimates_yield_retention=True,
    )
    blockers = []
    for rid in ROW_IDS[:11]:
        causes = []
        if not profiles[rid]["candidate_complete"]:
            causes.append("PROFILE_AUTHORITY_OR_COMPATIBILITY")
        if not market_pass(markets[rid]):
            causes.append("EXACT_ORDINARY_RU_MARKET")
        if causes:
            blockers.append(dict(id=f"BLOCK-{rid}", row_ids=[rid], gates=causes))
    if not gates["kitchen_branches"]:
        blockers.append(
            dict(
                id="BLOCK-PUBLISHED-PROCESS-MASS",
                row_ids=ROW_IDS[:11],
                gates=["KITCHEN_ALL_THREE_BRANCHES"],
            )
        )
    result = dict(
        operation="RECIPE-ASSEMBLY-A-R4-N50200",
        result=gate_contract(gates),
        gates=gates,
        minimal_root_blockers=blockers,
        current_composition_gaps=[
            r["row_id"] for r in rows.values() if r["current_composition"] is None
        ],
        dependent_failures=[
            "RU_EXACT_RECIPE_FAMILIARITY",
            "VERIFIED_CURATED_SUBSTITUTION",
        ],
        ready_count=2,
        third_candidate=None,
        assembly_a="BLOCKED",
        assembly_b="NOT STARTED",
        pr7_plus="NOT STARTED",
        migration="0029_food_composition_core",
        production_delta=None,
        next_operation_authorized=False,
    )
    plan = d["data-enablement-plan.json"]
    require(
        plan["status"] == "WITHHELD_NON_DATA_GATES"
        and plan["changes"] == []
        and plan["production_delta"] is None
        and plan["is_executable_plan"] is False,
        "False data-enablement plan",
    )
    return result


def russian(d):
    def walk(v, key=""):
        if isinstance(v, dict):
            for k, value in v.items():
                walk(value, key if key.endswith("_ru") else k)
        elif isinstance(v, list):
            for value in v:
                walk(value, key)
        elif key.endswith("_ru") and v:
            require(
                isinstance(v, str)
                and re.search(r"[А-Яа-яЁё]", v)
                and not re.search(r"[A-Za-z]", v),
                f"Russian display missing/English fallback: {key}",
            )

    for value in d.values():
        walk(value)
    display = d["russian-display.json"]
    require(
        display["english_fallback"] is False
        and display["consumer_ui_created"] is False,
        "Consumer UI/fallback forbidden",
    )
    require(
        set(display["required_roles_ru"])
        == {r["role"] for r in d["source-bindings.json"]["rows"] if r["required"]},
        "Missing Russian role",
    )
    require(set(display["branches_ru"]) == set(VARIANTS), "Missing Russian branch")


def profile_facts(profile):
    """Seed UUIDs/timestamps differ per disposable replay; retain all food truth."""
    return {
        key: value
        for key, value in profile.items()
        if key not in {"id", "food_ingredient_id", "created_at"}
    }


def database(d):
    require(os.environ.get("AI_ENABLED") == "false", "AI_ENABLED=false required")
    sys.path[:0] = [str(ROOT / "backend"), str(ROOT / "scripts")]
    from app.db.config import DatabaseConfig
    from audit_pr6_close import measure, encode as accepted_encode

    catalogue = d["catalogue-readiness.json"]
    with TemporaryDirectory(prefix="n50200-r4-") as directory:
        config = DatabaseConfig(path=Path(directory) / "accepted.sqlite")
        reports = measure(config)
        for name in ["food-readiness.json", "recipe-readiness.json"]:
            require(
                accepted_encode(reports[name])
                == (ROOT / "data/curation/pr6-close" / name).read_text(),
                f"Accepted replay differs: {name}",
            )
        with sqlite3.connect(config.path) as db:
            db.row_factory = sqlite3.Row
            inventory = [dict(r) for r in db.execute(PIN_QUERY)]
            require(
                inventory == catalogue["inventory"], "Current Composition pins differ"
            )
            codes = set(catalogue["requested_code_presence"])
            profiles = [
                profile_facts(dict(r))
                for r in db.execute(PROFILE_QUERY)
                if r["canonical_code"] in codes
            ]
            require(
                profiles == catalogue["current_profiles"],
                "Standalone profile/seal pins differ",
            )
            vectors = [
                dict(r)
                for r in db.execute(VECTOR_QUERY)
                if r["canonical_code"] in codes
            ]
            for r in vectors:
                r["provenance_json"] = json.loads(
                    r["provenance_json"], parse_float=reject_float
                )
            require(
                vectors == catalogue["current_vector_rows"],
                "Current nutrient vectors differ",
            )
            presence = {
                code: any(r["canonical_code"] == code for r in inventory)
                for code in codes
            }
            require(
                presence == catalogue["requested_code_presence"],
                "Food presence audit differs",
            )
            require(
                len(inventory) == catalogue["food_count"] == 185
                and sum(r["version"] is not None for r in inventory)
                == catalogue["composition_count"]
                == 63,
                "Catalogue counts differ",
            )
            require(
                db.execute("SELECT COUNT(*) FROM nutrition_vector_seals").fetchone()[0]
                == catalogue["vector_seals"]
                == 188,
                "Vector seal count drift",
            )
        closure = reports["closure-evidence.json"]
        accepted = read(
            ROOT / "data/curation/recipe-assembly-a-r1/baseline-verification.json"
        )
        for key in [
            "migration_head",
            "historical_replay",
            "deferred_forms_absent",
            "yield_rows",
        ]:
            require(closure[key] == accepted[key], f"Closure drift: {key}")
        require(
            closure["migration_head"] == "0029_food_composition_core"
            and len(closure["estimate_usages_non_executable"]) == 40,
            "Migration/estimate drift",
        )
        measured = {r["canonical_code"]: r for r in profiles}
        for row in d["source-bindings.json"]["rows"]:
            require(
                row["current_profile"] == measured.get(row["food_code"]),
                "Row standalone profile not DB-bound",
            )
            for candidate in row["existing_catalogue_candidates"]:
                code = candidate["food_code"]
                require(
                    candidate["current_profile"] == measured.get(code),
                    "Rejected/alternative catalogue candidate not DB-bound",
                )
                require(
                    candidate["present"]
                    is any(p["canonical_code"] == code for p in inventory),
                    "Candidate presence differs",
                )
    print(
        "Disposable accepted DB replay / 185 foods / 63 Composition / 188 seals / 40 estimates / 0029: PASS"
    )


def check_report(reported, derived):
    require(
        reported == derived, "False READY or blocker register differs from derivation"
    )


def adversarial(d):
    def rowset(doc, index, key, value):
        return lambda x: x[doc]["rows"][index].__setitem__(key, value)

    cases = [
        (
            "90-to-93 turkey",
            rowset("source-bindings.json", 0, "food_code", "TURKEY_GROUND_93"),
        ),
        (
            "Arbitrary yellow onion",
            rowset("source-bindings.json", 1, "food_code", "ONION_YELLOW"),
        ),
        ("Missing Worcestershire", lambda x: x["source-bindings.json"]["rows"].pop(7)),
        ("Missing bun", lambda x: x["source-bindings.json"]["rows"].pop(10)),
        ("Garnish no exact mass", rowset("quantity-authority.json", 12, "grams", None)),
        ("AP mass", rowset("quantity-authority.json", 1, "mass_basis", "AP")),
        ("Measure mass", rowset("quantity-authority.json", 1, "measure_used", True)),
        ("Piece mass", rowset("quantity-authority.json", 10, "piece_used", True)),
        ("Density mass", rowset("quantity-authority.json", 7, "density_used", True)),
        ("Package mass", rowset("quantity-authority.json", 10, "package_used", True)),
        ("Estimate mass", rowset("quantity-authority.json", 0, "estimated", True)),
        ("Estimate profile", rowset("profile-candidates.json", 0, "estimated", True)),
        (
            "One branch no Composition",
            rowset("source-bindings.json", 12, "current_composition", None),
        ),
        (
            "One branch profile incomplete",
            rowset("profile-candidates.json", 12, "candidate_complete", False),
        ),
        (
            "Rare forced RU_AVAILABLE",
            rowset("market-evidence.json", 7, "market_classification", "RU_AVAILABLE"),
        ),
        (
            "False ordinary turkey",
            rowset("market-evidence.json", 0, "exact_form_supported", True),
        ),
        (
            "Float-like profile basis estimate",
            rowset("profile-candidates.json", 0, "basis_grams", "100"),
        ),
        (
            "Optional process medium",
            lambda x: x["optional-role.json"].__setitem__(
                "component_kind", "PROCESSING_MEDIUM"
            ),
        ),
        (
            "Optional changes base",
            lambda x: x["optional-role.json"].__setitem__(
                "required_base_unchanged", False
            ),
        ),
        (
            "Single garnish substitution",
            lambda x: x["substitution-matrix.json"]["variants"][0].__setitem__(
                "row_ids", [ROW_IDS[12]]
            ),
        ),
        (
            "One kitchen branch missing",
            lambda x: x["kitchen-branches.json"]["branches"].pop(),
        ),
        (
            "One branch no kitchen evidence",
            lambda x: x["kitchen-branches.json"]["branches"][1].__setitem__(
                "standardization_applies", False
            ),
        ),
        (
            "Kitchen falsely verified",
            lambda x: x["kitchen-branches.json"]["branches"][2].__setitem__(
                "status", "KITCHEN_VERIFIED"
            ),
        ),
        (
            "Household scaling",
            lambda x: x["kitchen-branches.json"].__setitem__("household_scaling", True),
        ),
        (
            "Blank turkey nutrients filled",
            rowset("profile-candidates.json", 0, "candidate_complete", True),
        ),
        (
            "Bun profile guessed",
            rowset("profile-candidates.json", 10, "candidate_complete", True),
        ),
        (
            "Substitution falsely complete",
            lambda x: x["substitution-matrix.json"]["variants"][0].__setitem__(
                "proposed_complete", True
            ),
        ),
        (
            "Rights deferred",
            lambda x: x["rights-provenance.json"].__setitem__("decision", "DEFER"),
        ),
        (
            "Familiarity by translation",
            lambda x: x["ru-familiarity.json"].__setitem__(
                "decision", "RU_RECIPE_FAMILIAR"
            ),
        ),
        (
            "Process conflict hidden",
            lambda x: x["quantity-authority.json"].__setitem__(
                "source_process_mass_discrepancies", []
            ),
        ),
        (
            "English display",
            lambda x: x["russian-display.json"].__setitem__(
                "family_name_ru", "Turkey burger"
            ),
        ),
    ]
    count = 0
    for name, mutate in cases:
        x = deepcopy(d)
        mutate(x)
        try:
            derive(x)
            russian(x)
        except (ValueError, TypeError):
            count += 1
        else:
            raise ValueError(f"Adversarial accepted: {name}")
    for path in [
        "backend/app/migrations/versions/0030_recipe_template_catalogue.py",
        "data/seed/food_ingredients/ingredients.csv",
        *[f"data/curation/recipe-assembly-a-r{n}/README.md" for n in [1, 2, 3]],
    ]:
        try:
            scope_names({path})
        except ValueError:
            count += 1
        else:
            raise ValueError(f"Out-of-scope accepted: {path}")
    for n in [1, 2, 3]:
        try:
            check_frozen({f"R{n}": "accepted"}, {f"R{n}": "changed"})
        except ValueError:
            count += 1
        else:
            raise ValueError("Frozen package mutation accepted")
    false_ready = deepcopy(derive(d))
    false_ready["result"] = "READY_FOR_DATA_ENABLEMENT"
    try:
        check_report(false_ready, derive(d))
    except ValueError:
        count += 1
    else:
        raise ValueError("False READY accepted")
    try:
        json.loads('{"grams": 1.25}', parse_float=reject_float)
    except ValueError:
        count += 1
    else:
        raise ValueError("Float accepted")
    # Synthetic truth-table test, no donor/source/profile/market claim.
    positive = dict.fromkeys(derive(d)["gates"], True)
    require(
        gate_contract(positive) == "READY_FOR_DATA_ENABLEMENT",
        "Positive gate control failed",
    )
    for key in positive:
        negative = {**positive, key: False}
        require(gate_contract(negative) == "BLOCKED", f"Gate ignored: {key}")
        count += 1
    print(f"Adversarial: PASS; {count} negative cases and positive all-gates control")


def local_links():
    count = 0
    for path in [PACKAGE / "README.md"] + [
        ROOT / p for p in sorted(ALLOWED) if p.endswith(".md")
    ]:
        for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", path.read_text()):
            if re.match(r"[a-z]+://", target):
                continue
            name, _, anchor = target.strip("<>").partition("#")
            destination = (path.parent / name).resolve() if name else path
            require(destination.exists(), f"Broken local link: {path}: {target}")
            if anchor and destination.suffix == ".md":
                headings = re.findall(r"^#+\s+(.+)$", destination.read_text(), re.M)
                slugs = {
                    re.sub(r"[^\w\- ]", "", h.lower().replace("`", "")).replace(
                        " ", "-"
                    )
                    for h in headings
                }
                require(anchor in slugs, f"Broken anchor: {path}: {target}")
            count += 1
    print(f"Russian display / local links and anchors: PASS; {count} links")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", action="store_true")
    parser.add_argument("--adversarial", action="store_true")
    parser.add_argument("--source-dir", type=Path)
    parser.add_argument(
        "--derive", action="store_true", help="Print derived JSON, no writes"
    )
    args = parser.parse_args()
    d = {str(p.relative_to(PACKAGE)): read(p) for p in PACKAGE.rglob("*.json")}
    result = derive(d)
    if args.derive:
        print(encode(result), end="")
        return
    scope(d)
    package(d, args.source_dir)
    check_report(d["final-decision.json"], result)
    russian(d)
    if args.database:
        database(d)
    if args.adversarial:
        adversarial(d)
    local_links()
    print(
        "R4 = BLOCKED; data-enablement withheld; Assembly A BLOCKED; ready 2/3; 0029 unchanged"
    )


if __name__ == "__main__":
    main()
