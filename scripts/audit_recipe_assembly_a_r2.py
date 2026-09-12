"""Read-only R2 evidence audit; exit zero does not mean Assembly A is ready.

Default: retained sources, accepted Git base, scope, hashes, semantic derivation.
--database reconstructs accepted truth only in a temporary directory (AI off).
--source-dir verifies the three full original downloads without publishing them.
--adversarial exercises semantic failures independently of package checksums.
Requires pdftotext for the retained primary AFRS excerpt; no network or writes.
"""

import argparse
import ast
from copy import deepcopy
from decimal import Decimal
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import subprocess
import sys
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "data/curation/recipe-assembly-a-r2"
R1 = ROOT / "data/curation/recipe-assembly-a-r1"
BASE = "8730b9fcfdb56cec2215f7e70319241c83431371"
R1_HEAD = "6bfabf13846a350c3fe38147f4cc452cc1fae72d"
LB = Decimal("453.59237")
OZ = Decimal("28.349523125")
ALLOWED = {
    "scripts/audit_recipe_assembly_a_r2.py",
    "state/current-focus.md",
    "state/progress.md",
    "state/handoff.md",
    "docs/family-food/master-roadmap.md",
    "docs/family-food/food-composition-and-assembly.md",
}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def reject_float(value):
    raise ValueError(f"Float/constant forbidden: {value}")


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


def pdf_text(path):
    return subprocess.check_output(["pdftotext", "-layout", str(path), "-"], text=True)


def scope_audit(docs):
    b = docs["baseline.json"]
    require(b["accepted_base"] == BASE, "Wrong merged base")
    require(git("rev-parse", "origin/main") == BASE, "Fetched main changed")
    require(git("merge-base", BASE, "HEAD") == BASE, "Wrong merge ancestor")
    require(git("merge-base", R1_HEAD, BASE) == R1_HEAD, "R1 not merged")
    require(git("rev-parse", "--abbrev-ref", "HEAD") == b["branch"], "Wrong branch")
    receipt = docs["pr32-receipt.json"]
    require(
        receipt["number"] == 32
        and receipt["merged"] is True
        and receipt["state"] == "closed"
        and receipt["merge_commit_sha"] == BASE
        and receipt["head_sha"] == R1_HEAD,
        "PR32 merge receipt mismatch",
    )
    require(
        b["r1"] == "COMPLETE AS BLOCKED RESEARCH"
        and b["r1_individually_ready"] == ["R1-21"]
        and b["r1_selected_final_three"] == []
        and b["researched_candidates"] == ["R1-23", "R1-13"],
        "Wrong accepted R1/scope state",
    )
    for name in ("assembly_a", "assembly_b", "pr7", "migration"):
        expected = {
            "assembly_a": "BLOCKED",
            "assembly_b": "NOT STARTED",
            "pr7": "NOT STARTED",
            "migration": "0029_food_composition_core",
        }[name]
        require(b[name] == expected, f"Unauthorized state: {name}")
    frozen = b["frozen_r1_sha256"]
    require(
        set(frozen) == {str(p.relative_to(ROOT)) for p in R1.rglob("*") if p.is_file()},
        "R1 package inventory changed",
    )
    for name, expected in {**frozen, **b["accepted_input_sha256"]}.items():
        base_bytes = subprocess.check_output(
            ["git", "show", f"{BASE}:{name}"], cwd=ROOT
        )
        require(
            hashlib.sha256(base_bytes).hexdigest() == expected, f"Base hash: {name}"
        )
        require(digest(ROOT / name) == expected, f"Accepted bytes changed: {name}")
    for name, tree in b["frozen_production_trees"].items():
        require(git("rev-parse", f"{BASE}:{name}") == tree, f"Wrong tree: {name}")
    changed = set(git("diff", "--name-only", BASE).splitlines())
    changed |= set(git("ls-files", "--others", "--exclude-standard").splitlines())
    require(
        ".DS_Store" not in git("diff", "--cached", "--name-only").splitlines(),
        "Staged .DS_Store",
    )
    for name in changed - {".DS_Store"}:
        require(
            name in ALLOWED or name.startswith(str(PACKAGE.relative_to(ROOT)) + "/"),
            f"Out of scope: {name}",
        )
    print("Exact merged base / PR32 / frozen R1 and production scope: PASS")


def package_audit(docs, source_dir=None):
    checksums = docs["checksums.json"]
    actual = {
        str(p.relative_to(PACKAGE)): digest(p)
        for p in PACKAGE.rglob("*")
        if p.is_file() and p.name != "checksums.json"
    }
    require(actual == checksums["files"], "Package SHA-256/inventory mismatch")
    tree = ast.parse(Path(__file__).read_text())
    require(
        not any(
            isinstance(n, ast.Constant) and isinstance(n.value, float)
            for n in ast.walk(tree)
        ),
        "Script float literal",
    )
    excerpt = PACKAGE / "sources/afrs-full-excerpt.pdf"
    text = pdf_text(excerpt)
    require(
        text == (PACKAGE / "sources/afrs-full-excerpt.txt").read_text(),
        "AFRS extraction differs",
    )
    compact = re.sub(r"\s+", " ", text)
    for value in [
        "June 2003",
        "Edible Portion (E.P.)",
        "As Purchased (A.P.)",
        "22 lbs",
        "200 each",
        "Refrigerate at 41 F.",
    ]:
        require(value in compact, f"Primary AFRS missing: {value}")
    require(
        "developed, tested and standardized" in compact,
        "AFRS standardization evidence",
    )
    if source_dir is not None:
        for name, source in docs["source-manifest.json"]["originals"].items():
            path = source_dir / source["filename"]
            require(
                digest(path) == source["sha256"]
                and path.stat().st_size == source["bytes"],
                f"Original SHA/size: {name}",
            )
        full = pdf_text(source_dir / "afrs-full.pdf").split("\f")
        retained = text.split("\f")
        # Whitespace is normalized because per-document layout widths can differ.
        for index, original_page in enumerate([1, 2, 3, 7, 8, 335]):
            require(
                " ".join(full[original_page - 1].split())
                == " ".join(retained[index].split()),
                f"Mixed AFRS revision/page: {original_page}",
            )
        rice = pdf_text(source_dir / "rice.pdf")
        for token in [
            "USDA Standardized Recipes Project",
            "1 lb 13 oz",
            "1 lb 14 oz",
            "1 lb 11 oz",
            "Garlic, minced",
            "2 Tbsp",
            "1/4 cup",
            "Variation",
            "2019",
        ]:
            require(token in rice, f"Rice original evidence missing: {token}")
        require(
            re.search(r"3 Place.*?1 lb 13 oz", rice), "Rice instruction mass evidence"
        )
        garlic = pdf_text(source_dir / "fbg-a.pdf").split("\f")[5]
        require(
            re.search(r"Fresh garlic, minced\s+21/2 oz\s+1/4 cup", garlic),
            "Exact same-form garlic row absent",
        )
        print(
            "Full-source SHA-256 / same-edition AFRS pages / rice and garlic facts: PASS"
        )
    print("Package SHA-256 / retained primary AFRS / no-float: PASS")


def validate_evidence(d):
    """Semantic constraints are checked even after a mutant re-hashes its package."""
    facts = d["source-facts.json"]
    a, rice, garlic = facts["afrs"], facts["rice"], facts["garlic"]
    e = d["ep-ap-and-egg-decision.json"]
    g = d["garlic-mass-review.json"]
    rights = d["rice-rights-review.json"]
    m = d["rice-variant-matrix.json"]
    optional = d["optional-role-decision.json"]
    require(
        a["weight_semantics"] == a["measure_semantics"] == e["mass_basis"] == "EP"
        and a["issue_semantics"] == "AP"
        and e["authority_column"] == "Weight",
        "AP cannot become EP",
    )
    require(
        e["piece_mass_g"] is None
        and not e["piece_mass_authority"]
        and e["mass_expression"] == "Decimal(source_lb) * Decimal(lb_to_g)",
        "Universal egg piece inference",
    )
    require(
        e["system"] == a["system"] == "MCO P10110.42B June 2003"
        and e["general_source"] == e["card_source"] == "afrs-full"
        and (e["general_page"], e["card_page"]) == (8, 335),
        "Mixed F00400 revision",
    )
    require(
        Decimal(e["lb_to_g"]) == LB
        and e["source_lb"] == a["weight_lb"] == "22"
        and Decimal(e["input_g"]) == Decimal(a["weight_lb"]) * LB,
        "Wrong Decimal egg mass",
    )
    require(
        e["source_form"] == "FRESH_WHOLE_CHICKEN_EGG_EDIBLE_CONTENT"
        and e["food_code"] == "EGG"
        and e["composition_source_id"] == "748967"
        and e["input_state"] == "INPUT"
        and e["form_compatible"],
        "Egg edible-input profile mismatch",
    )
    require(
        e["method_id"] == 1
        and e["servings"] == 100
        and e["kitchen_scope"] == "EXACT_PUBLISHED_100_PORTION_HOT_WATER_HARD_COOKED"
        and not e["household_kitchen_verified"],
        "Unverified household/egg method scaling",
    )
    require(
        all(e[k] is None for k in ["cooked_output_g", "yield_factor", "retention"]),
        "Unverified cooked output",
    )
    require(
        not e["process_water"]["consumed"]
        and not e["process_water"]["optional_component"]
        and not e["optional_components"]
        and not e["substitutions"],
        "Process medium/egg variant promoted",
    )
    require(
        garlic["food"] == g["food_code"] == "GARLIC"
        and garlic["form"]
        == g["form"]
        == rice["garlic"]["reviewed_form"]
        == "FRESH_MINCED",
        "Cross-food/form garlic authority",
    )
    require(
        not garlic["estimated"]
        and not g["estimated"]
        and garlic["qualifier"] == "PUBLISHED_WEIGHT_MEASURE_PAIR"
        and g["source_id"] == garlic["source_id"] == "FBG-A-2025-A5-GARLIC",
        "Estimate garlic authority",
    )
    require(
        g["source_oz"] == garlic["source_oz"] == "2.5"
        and g["source_cups"] == garlic["source_cups"] == "0.25"
        and Decimal(g["oz_to_g"]) == OZ,
        "Garlic source observation changed",
    )
    require(
        Decimal(g["tbsp_per_cup"]) == 16
        and (g["scale25_numerator"], g["scale25_denominator"]) == (1, 2),
        "Wrong rational garlic scaling",
    )
    observed = Decimal(garlic["source_oz"]) * OZ
    scale = Decimal(rice["garlic"]["tbsp25"]) / (
        Decimal(garlic["source_cups"]) * Decimal(g["tbsp_per_cup"])
    )
    require(
        Decimal(g["source_mass_g"]) == Decimal(g["input50_g"]) == observed
        and Decimal(g["input25_g"]) == observed * scale,
        "Wrong Decimal garlic mass",
    )
    require(
        not g["production_mass_row_created"]
        and g["universal_density_g_ml"] is None
        and g["source_scope"] == "REVIEWED_R2_EVIDENCE_ONLY",
        "Mass evidence promoted into production/density",
    )
    require(
        rights["disposition"] in {"ACCEPT", "DEFER", "REJECT"},
        "Missing rights disposition",
    )
    if rights["disposition"] == "ACCEPT":
        require(
            rights["policy"] == "RIGHTS-FACTS"
            and rights["scope"] == "FACTUAL_DATA_AND_INDEPENDENT_RUSSIAN_RULES"
            and not rights["hosting_is_authorship"]
            and not rights["federal_employee_authorship_claim"]
            and rights["whole_artifact_license"] == "NOT_ESTABLISHED"
            and len(rights["attribution_observed"]) == 4,
            "Unsupported rights acceptance",
        )
    require(
        [(r["id"], r["oz25"], r["oz50"]) for r in rice["rice_choices"]]
        == [
            ("PARBOILED_LONG_BROWN", "29", "58"),
            ("MEDIUM_BROWN", "30", "60"),
            ("REGULAR_LONG_BROWN", "27", "54"),
        ],
        "Rice form/mass conflation",
    )
    require(
        rice["method"]["step3_rice_oz_per_pan"] == "29"
        and not rice["method"]["separate_rice_variant_instructions"]
        and not rice["method"]["explicit_alternative_kitchen_test_record"],
        "Invented alternative kitchen evidence",
    )
    require(
        optional["semantics"] == "ALTERNATIVE_REQUIRED_VARIANT"
        and optional["scope"] == "WITHIN_SELECTED_SEASONING_VARIATION"
        and not optional["independent_component_omission_explicit"]
        and not optional["eligible_optional_role"]
        and optional["optional_component_providers"] == [],
        "Alternative relabeled optional",
    )
    require(
        rice["seasoning"]["operator"] == "OR"
        and rice["seasoning"]["cilantro_lime_operator"] == "AND"
        and not rice["seasoning"]["explicit_optional_component_label"],
        "Source optional semantics changed",
    )
    expected = {
        "BASE_WATER_REGULAR": ("WATER", "REGULAR_LONG_BROWN", "NONE"),
        "BROTH_REGULAR": ("LOW_SODIUM_BROTH", "REGULAR_LONG_BROWN", "NONE"),
        "WATER_PARBOILED": ("WATER", "PARBOILED_LONG_BROWN", "NONE"),
        "WATER_MEDIUM": ("WATER", "MEDIUM_BROWN", "NONE"),
        "BASE_CILANTRO_LIME": ("WATER", "REGULAR_LONG_BROWN", "CILANTRO_LIME"),
        "BASE_TURMERIC": ("WATER", "REGULAR_LONG_BROWN", "TURMERIC"),
        "PUBLISHED_FIRST_BRANCH": ("LOW_SODIUM_BROTH", "PARBOILED_LONG_BROWN", "NONE"),
    }
    require(
        {v["id"] for v in m["variants"]} == set(expected),
        "Missing/extra source variants",
    )
    for v in m["variants"]:
        require(
            (v["liquid"], v["rice"], v["seasoning"]) == expected[v["id"]],
            "Wrong variant identity",
        )
        require(
            v["servings"] == 25 and not v["household_kitchen_verified"],
            "Unverified household rice scaling",
        )
        status = (
            "PUBLISHED_BASE"
            if v["id"] == "PUBLISHED_FIRST_BRANCH"
            else "NOT_ESTABLISHED"
        )
        require(
            v["kitchen_status"] == status, "Source OR is not alternative kitchen proof"
        )
        require(v["rights"] == rights["disposition"], "Variant rights drift")
        inputs = v["inputs"]
        require(
            len(inputs)
            == (
                6
                if v["seasoning"] == "CILANTRO_LIME"
                else 5
                if v["seasoning"] == "TURMERIC"
                else 4
            ),
            "Incomplete branch inputs",
        )
        liquid, salt, minced, grain = inputs[:4]
        require(
            salt["food_code"] == "SALT"
            and Decimal(salt["input_g"]) == 6
            and minced["food_code"] == "GARLIC"
            and minced["input_g"] == g["input25_g"]
            and minced["mass_authority"] == g["source_id"],
            "Base salt/garlic authority mismatch",
        )
        water = v["liquid"] == "WATER"
        require(
            liquid["food_code"] == ("WATER" if water else "VEGETABLE_BROTH")
            and liquid["input_g"] == ("1440" if water else None)
            and liquid["form_compatible"] == water,
            "Unproved low-sodium broth form/mass",
        )
        regular = v["rice"] == "REGULAR_LONG_BROWN"
        mass = next(x["oz25"] for x in rice["rice_choices"] if x["id"] == v["rice"])
        require(
            grain["food_code"] == ("RICE_BROWN" if regular else None)
            and grain["form_compatible"] == regular
            and Decimal(grain["input_g"]) == Decimal(mass) * OZ,
            "Rice alternatives need exact identities",
        )
        if v["seasoning"] == "CILANTRO_LIME":
            require(
                inputs[4]["food_code"] == "CILANTRO"
                and Decimal(inputs[4]["input_g"]) == OZ
                and inputs[5]["food_code"] == "LIME_JUICE"
                and inputs[5]["input_g"] is None,
                "Lime piece/juice inference",
            )
        if v["seasoning"] == "TURMERIC":
            require(
                inputs[4]["food_code"] == "TURMERIC_GROUND"
                and inputs[4]["input_g"] is None,
                "Unevidenced turmeric mass",
            )
        for row in inputs:
            require(
                re.search(r"[А-Яа-яЁё]", row["name_ru"])
                and not re.search(r"[A-Za-z]", row["name_ru"]),
                "Missing Russian ingredient display",
            )
    return True


def derive(d):
    """Recompute every individual and collective gate; no trusted READY flag."""
    from audit_recipe_assembly_a_r1 import default_gate

    validate_evidence(d)
    frozen = read(R1 / "final-three.json")
    require(
        [r["template_candidate_code"] for r in frozen["individually_ready"]]
        == ["R1-21"]
        and frozen["selected_final_three"] == [],
        "Frozen R1 readiness changed",
    )
    cf = d["market-familiarity-carry-forward.json"]
    original_market = read(R1 / "market-evidence.json")["candidate_terminal_inputs"]
    require(
        cf["market"] == {c: original_market[c] for c in ["R1-13", "R1-23"]},
        "Market carry-forward drift",
    )
    original_familiar = read(R1 / "ru-familiarity.json")["candidates"]
    require(
        cf["familiarity"]
        == [
            x
            for x in original_familiar
            if x["template_candidate_code"] in ["R1-13", "R1-23"]
        ],
        "Familiarity carry-forward drift",
    )
    pins = {x["canonical_code"]: x for x in d["composition-pins.json"]["foods"]}
    require(
        set(pins)
        == {
            "EGG",
            "GARLIC",
            "RICE_BROWN",
            "WATER",
            "SALT",
            "CILANTRO",
            "LIME_JUICE",
            "TURMERIC_GROUND",
            "VEGETABLE_BROTH",
        },
        "Composition inventory scope",
    )
    known = {
        x["food_code"]: x for x in read(R1 / "composition-readiness.json")["foods"]
    }
    for code in ["EGG", "GARLIC", "RICE_BROWN", "WATER", "SALT", "CILANTRO"]:
        require(
            pins[code]["version"] == 1
            and pins[code]["input_state"] == "INPUT"
            and pins[code]["source_name"] == "USDA_FDC",
            f"Missing accepted Composition: {code}",
        )
        require(
            str(pins[code]["source_id"]) in json.dumps(known[code]),
            f"Composition profile drift: {code}",
        )
    for code in ["LIME_JUICE", "TURMERIC_GROUND", "VEGETABLE_BROTH"]:
        require(pins[code]["version"] is None, f"Invented Composition: {code}")
    variants = {}
    for v in d["rice-variant-matrix.json"]["variants"]:
        rows = v["inputs"]
        exact_forms = all(r["form_compatible"] and r["food_code"] in pins for r in rows)
        composition = all(
            r["food_code"] in pins and pins[r["food_code"]]["version"] is not None
            for r in rows
        )
        mass = all(r["input_g"] is not None and r["mass_authority"] for r in rows)
        kitchen = v["kitchen_status"] == "PUBLISHED_BASE"
        rice_oz = next(
            x["oz25"]
            for x in d["source-facts.json"]["rice"]["rice_choices"]
            if x["id"] == v["rice"]
        )
        process = (
            rice_oz == d["source-facts.json"]["rice"]["method"]["step3_rice_oz_per_pan"]
            and v["seasoning"] == "NONE"
        )
        market = v["id"] == "BASE_WATER_REGULAR" and all(
            default_gate(x) == "PASS" for x in cf["market"]["R1-13"]
        )
        gates = dict(
            food_form=exact_forms,
            composition=composition,
            exact_input_mass=mass,
            process_compatible=process,
            kitchen_scope=kitchen,
            ru_availability=market,
            russian_display=all(
                bool(re.search(r"[А-Яа-яЁё]", r["name_ru"])) for r in rows
            ),
            rights=v["rights"] == "ACCEPT",
        )
        variants[v["id"]] = gates
    substitutions = {}
    expected_pairs = {
        "WATER_BROTH": ["BASE_WATER_REGULAR", "BROTH_REGULAR"],
        "REGULAR_PARBOILED": ["BASE_WATER_REGULAR", "WATER_PARBOILED"],
        "REGULAR_MEDIUM": ["BASE_WATER_REGULAR", "WATER_MEDIUM"],
        "SEASONING": ["BASE_CILANTRO_LIME", "BASE_TURMERIC"],
    }
    paths = d["rice-variant-matrix.json"]["substitutions"]
    require(
        {p["id"] for p in paths} == set(expected_pairs), "Substitution path inventory"
    )
    for path in paths:
        require(
            path["branches"] == expected_pairs[path["id"]]
            and path["source_operator"] == "OR",
            "Substitution needs both complete source branches",
        )
        usable = all(all(variants[branch].values()) for branch in path["branches"])
        require(
            path["status"] == ("VERIFIED" if usable else "NOT_ESTABLISHED"),
            "Incomplete substitution branch promoted",
        )
        substitutions[path["id"]] = usable
    egg = dict(frozen["candidate_gates"]["R1-23"])
    egg = {k: v == "PASS" for k, v in egg.items()}
    egg.update(food_form_composition=True, exact_input_mass=True)
    egg["rights"] = (
        d["ep-ap-and-egg-decision.json"]["rights"] == "ACCEPT" and egg["rights"]
    )
    egg["market_default"] = all(
        default_gate(x) == "PASS" for x in cf["market"]["R1-23"]
    )
    base = variants[d["rice-variant-matrix.json"]["preferred_base"]]
    require(
        d["rice-variant-matrix.json"]["preferred_base"] == "BASE_WATER_REGULAR",
        "Unexpected preferred source branch",
    )
    rice = dict(
        rights=base["rights"],
        kitchen_scope=base["kitchen_scope"],
        food_form_composition=base["food_form"] and base["composition"],
        exact_input_mass=base["exact_input_mass"],
        ru_familiarity=frozen["candidate_gates"]["R1-13"]["ru_familiarity"] == "PASS",
        market_default=base["ru_availability"],
        source_template_scope=True,
        ordered_process=base["process_compatible"],
        russian_display=base["russian_display"],
        transformation_dependencies=True,
    )
    individuals = {
        "R1-21": {
            k: v == "PASS" for k, v in frozen["candidate_gates"]["R1-21"].items()
        },
        "R1-23": egg,
        "R1-13": rice,
    }
    ready = sorted(k for k, gates in individuals.items() if all(gates.values()))
    collective = dict(
        family_count=len(ready) == 3,
        required_roles=bool(ready),
        optional_role=bool(
            d["optional-role-decision.json"]["optional_component_providers"]
        ),
        verified_substitution=any(substitutions.values()) and "R1-13" in ready,
        compatibility=all(individuals[c]["food_form_composition"] for c in ready),
        deterministic_quantities=all(individuals[c]["exact_input_mass"] for c in ready),
        ordered_process=all(individuals[c]["ordered_process"] for c in ready),
    )
    complete = all(collective.values())
    a, b = "R1-23" in ready, "R1-13" in ready
    outcome = (
        "D"
        if complete
        else "C"
        if a and b
        else "A"
        if a
        else "B"
        if b
        else "NO_ADVANCE"
    )
    return dict(
        operation="RECIPE-ASSEMBLY-A-R2",
        outcome=outcome,
        individually_ready=ready,
        individually_ready_count=len(ready),
        required_family_count=3,
        candidate_gates=individuals,
        rice_variant_gates=variants,
        verified_substitutions=substitutions,
        collective_feature_gates=collective,
        selected_final_three=ready if complete else [],
        assembly_a="BLOCKED",
        evidence_ready_final_three=complete,
        implementation_authorized=False,
        assembly_b="NOT STARTED",
        pr7="NOT STARTED",
        migration="0029_food_composition_core",
    )


PIN_QUERY = """
SELECT f.canonical_code,f.canonical_name,c.version,c.input_state,c.kind,
       p.source_id,p.source_version,p.source_name,
       p.source_data_type,p.basis_grams,p.estimated
FROM food_ingredients f
LEFT JOIN food_composition_versions c ON c.food_ingredient_id=f.id
LEFT JOIN food_nutrition_profiles p ON p.id=c.profile_id
WHERE f.canonical_code IN ('EGG','GARLIC','RICE_BROWN','VEGETABLE_BROTH',
 'TURMERIC_GROUND','CILANTRO','LIME_JUICE','SALT','WATER')
ORDER BY f.canonical_code
"""


def database_audit(d):
    require(
        os.environ.get("AI_ENABLED") == "false", "DB audit requires AI_ENABLED=false"
    )
    sys.path[:0] = [str(ROOT / "backend"), str(ROOT / "scripts")]
    from app.db.config import DatabaseConfig
    from audit_pr6_close import measure, encode as accepted_encode

    with TemporaryDirectory(prefix="assembly-r2-") as directory:
        config = DatabaseConfig(path=Path(directory) / "accepted.sqlite")
        reports = measure(config)
        for name in ["food-readiness.json", "recipe-readiness.json"]:
            require(
                accepted_encode(reports[name])
                == (ROOT / "data/curation/pr6-close" / name).read_text(),
                f"Accepted report drift: {name}",
            )
        with sqlite3.connect(config.path) as db:
            db.row_factory = sqlite3.Row
            pins = [dict(x) for x in db.execute(PIN_QUERY)]
            expected_pins = d["composition-pins.json"]["foods"]
            differences = [
                f"{expected['canonical_code']}.{key}"
                for actual, expected in zip(pins, expected_pins, strict=True)
                for key in expected
                if actual[key] != expected[key]
            ]
            require(
                not differences, f"Disposable DB Composition pins differ: {differences}"
            )
            require(
                db.execute("SELECT COUNT(*) FROM food_ingredients").fetchone()[0]
                == 185,
                "Food count drift",
            )
            require(
                db.execute("SELECT COUNT(*) FROM food_composition_versions").fetchone()[
                    0
                ]
                == 63,
                "Composition count drift",
            )
            require(
                db.execute("SELECT COUNT(*) FROM nutrition_vector_seals").fetchone()[0]
                == 188,
                "Seal count drift",
            )
        closure = reports["closure-evidence.json"]
        frozen = read(R1 / "baseline-verification.json")
        for field in [
            "migration_head",
            "historical_replay",
            "deferred_forms_absent",
            "yield_rows",
        ]:
            require(closure[field] == frozen[field], f"Closure drift: {field}")
        require(
            closure["migration_head"] == "0029_food_composition_core"
            and len(closure["estimate_usages_non_executable"]) == 40,
            "Migration/estimate drift",
        )
    print(
        "Disposable accepted DB: PASS; 185 foods / 63 compositions / 188 seals / 40 estimates / migration 0029"
    )


def adversarial(d):
    def field(file, key, value):
        return lambda x: x[file].__setitem__(key, value)

    cases = [
        (
            "AP as EP",
            field("ep-ap-and-egg-decision.json", "mass_basis", "AP"),
            "AP cannot",
        ),
        (
            "universal piece mass",
            field("ep-ap-and-egg-decision.json", "piece_mass_g", "49.8951607"),
            "piece inference",
        ),
        (
            "mixed F00400 revision",
            field("ep-ap-and-egg-decision.json", "system", "AFRS 1993"),
            "Mixed F00400",
        ),
        (
            "wrong Decimal constant",
            field("ep-ap-and-egg-decision.json", "lb_to_g", "453.6"),
            "Decimal egg",
        ),
        (
            "cross-food garlic",
            field("garlic-mass-review.json", "food_code", "TURKEY_GROUND"),
            "Cross-food",
        ),
        (
            "estimate garlic",
            field("garlic-mass-review.json", "estimated", True),
            "Estimate garlic",
        ),
        (
            "generic density",
            field("garlic-mass-review.json", "universal_density_g_ml", "1.2"),
            "density",
        ),
        (
            "alternative as optional",
            field("optional-role-decision.json", "eligible_optional_role", True),
            "Alternative relabeled",
        ),
        (
            "household egg scaling",
            field("ep-ap-and-egg-decision.json", "servings", 4),
            "household",
        ),
        (
            "hosting as rights",
            field("rice-rights-review.json", "hosting_is_authorship", True),
            "rights acceptance",
        ),
        (
            "OR as kitchen verification",
            lambda x: x["rice-variant-matrix.json"]["variants"][1].__setitem__(
                "kitchen_status", "PUBLISHED_BASE"
            ),
            "alternative kitchen",
        ),
        (
            "one branch missing Composition",
            lambda x: x["rice-variant-matrix.json"]["substitutions"][0].__setitem__(
                "status", "VERIFIED"
            ),
            "Incomplete substitution",
        ),
        (
            "omit replacement branch",
            lambda x: x["rice-variant-matrix.json"]["substitutions"][0].__setitem__(
                "branches", ["BASE_WATER_REGULAR"]
            ),
            "both complete",
        ),
        (
            "household rice scaling",
            lambda x: x["rice-variant-matrix.json"]["variants"][0].__setitem__(
                "household_kitchen_verified", True
            ),
            "household rice",
        ),
        (
            "invented broth Composition",
            lambda x: next(
                p
                for p in x["composition-pins.json"]["foods"]
                if p["canonical_code"] == "VEGETABLE_BROTH"
            ).__setitem__("version", 1),
            "Invented Composition",
        ),
    ]
    for name, mutate, reason in cases:
        copy = deepcopy(d)
        mutate(copy)
        # Round-trip recomputes a semantic payload hash, rather than failing on the old package hash.
        payload = encode(copy)
        require(
            hashlib.sha256(payload.encode()).digest()
            != hashlib.sha256(encode(d).encode()).digest(),
            "Ineffective mutant",
        )
        copy = json.loads(
            payload, parse_float=reject_float, parse_constant=reject_float
        )
        try:
            derive(copy)
        except ValueError as error:
            require(reason in str(error), f"Wrong rejection for {name}: {error}")
        else:
            raise ValueError(f"Adversarial case accepted: {name}")
    result = derive(d)
    for key, value in [
        ("selected_final_three", ["R1-21", "R1-23", "R1-13"]),
        ("evidence_ready_final_three", True),
        ("individually_ready_count", 3),
    ]:
        copy = deepcopy(result)
        copy[key] = value
        require(copy != derive(d), f"False final-three state accepted: {key}")
    try:
        json.loads('{"mass": 1.25}', parse_float=reject_float)
    except ValueError:
        pass
    else:
        raise ValueError("Float accepted")
    # Positive control: safe exclusion after an explicit DEFER removes rights readiness.
    copy = deepcopy(d)
    copy["rice-rights-review.json"]["disposition"] = "DEFER"
    for variant in copy["rice-variant-matrix.json"]["variants"]:
        variant["rights"] = "DEFER"
    require(not derive(copy)["candidate_gates"]["R1-13"]["rights"], "DEFER ignored")
    print(
        f"Adversarial semantic audit: PASS; {len(cases) + 4} rejected cases + DEFER positive control"
    )


def local_links():
    files = [PACKAGE / "README.md"] + [ROOT / p for p in ALLOWED if p.endswith(".md")]
    checked = 0
    for file in files:
        for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", file.read_text()):
            if re.match(r"[a-z]+://", target):
                continue
            target = target.strip("<>")
            name, _, anchor = target.partition("#")
            path = (file.parent / name).resolve() if name else file
            require(path.exists(), f"Broken local link: {file}: {target}")
            if anchor and path.suffix == ".md":
                headings = re.findall(r"^#+\s+(.+)$", path.read_text(), re.M)
                slugs = {
                    re.sub(r"[^\w\- ]", "", h.lower().replace("`", "")).replace(
                        " ", "-"
                    )
                    for h in headings
                }
                require(anchor in slugs, f"Broken local anchor: {file}: {target}")
            checked += 1
    print(f"Local links/anchors: PASS; {checked}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", action="store_true")
    parser.add_argument("--adversarial", action="store_true")
    parser.add_argument("--source-dir", type=Path)
    parser.add_argument(
        "--derive",
        action="store_true",
        help="Print derived JSON only; read-only, no file writes",
    )
    args = parser.parse_args()
    docs = {p.name: read(p) for p in PACKAGE.glob("*.json")}
    if args.derive:
        print(encode(derive(docs)), end="")
        return
    scope_audit(docs)
    package_audit(docs, args.source_dir)
    result = derive(docs)
    require(
        result == docs["final-readiness.json"],
        "Reported final readiness differs from derived gates",
    )
    if args.database:
        database_audit(docs)
    if args.adversarial:
        adversarial(docs)
    local_links()
    print(
        f"R2 Outcome {result['outcome']}: individually ready {result['individually_ready_count']}/3; selected {len(result['selected_final_three'])}; Assembly A BLOCKED; implementation unauthorized"
    )


if __name__ == "__main__":
    main()
