"""Read-only R3 research audit. Passing audit is not evidence-ready Assembly A.

--database replays accepted seeds only in a disposable database, AI disabled.
--source-dir checks the two full primary downloads against retained observations.
--adversarial tests semantic guards with an explicitly synthetic positive control.
No source search, production write, recipe publication or migration is performed.
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
PACKAGE = ROOT / "data/curation/recipe-assembly-a-r3"
BASE = "f2b6bc9015a1b892bb533b5d322d981d5a1782bd"
R2_HEAD = "5da808134e7fe7171ece0cc6d34a4b04db5e461f"
FIXED = ["R1-21", "R1-23"]
LB = Decimal("453.59237")
OZ = Decimal("28.349523125")
ALLOWED = {
    "scripts/audit_recipe_assembly_a_r3.py",
    "state/current-focus.md",
    "state/progress.md",
    "state/handoff.md",
    "docs/family-food/master-roadmap.md",
    "docs/family-food/food-composition-and-assembly.md",
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


def check_scope_names(names):
    for name in names - {".DS_Store"}:
        require(
            name in ALLOWED or name.startswith("data/curation/recipe-assembly-a-r3/"),
            f"Out of scope: {name}",
        )


def check_frozen(expected, actual):
    require(expected == actual, "Frozen R1/R2 evidence changed")


def scope_audit(d):
    b = d["baseline.json"]
    require(b["accepted_base"] == BASE, "Incorrect base")
    require(git("rev-parse", "origin/main") == BASE, "Fetched main differs")
    require(git("merge-base", BASE, "HEAD") == BASE, "Base not ancestor")
    require(git("merge-base", R2_HEAD, BASE) == R2_HEAD, "R2 not merged")
    require(
        git("rev-parse", "--abbrev-ref", "HEAD") == "codex/recipe-assembly-a-r3",
        "Wrong branch",
    )
    receipt = d["pr33-receipt.json"]
    require(
        receipt["number"] == 33
        and receipt["merged"] is True
        and receipt["state"] == "closed"
        and receipt["merge_commit_sha"] == BASE
        and receipt["head_sha"] == R2_HEAD
        and receipt["base_ref"] == "main",
        "PR33 merge receipt mismatch",
    )
    for key, expected in {
        "pr6": "COMPLETE",
        "pr33": "MERGED",
        "r1": "COMPLETE AS BLOCKED RESEARCH",
        "r2": "COMPLETE AS BLOCKED RESEARCH",
        "fixed_members": FIXED,
        "individual_ready_count": 2,
        "selected_final_three": [],
        "optional_role": "OPEN",
        "verified_substitution": "OPEN",
        "assembly_a": "BLOCKED",
        "assembly_b": "NOT STARTED",
        "pr7": "NOT STARTED",
        "migration": "0029_food_composition_core",
    }.items():
        require(b[key] == expected, f"Accepted baseline drift: {key}")
    frozen = {
        str(p.relative_to(ROOT)): digest(p)
        for name in ["recipe-assembly-a-r1", "recipe-assembly-a-r2"]
        for p in (ROOT / "data/curation" / name).rglob("*")
        if p.is_file()
    }
    check_frozen(b["frozen_packages_sha256"], frozen)
    for name, expected in {**frozen, **b["accepted_input_sha256"]}.items():
        original = subprocess.check_output(["git", "show", f"{BASE}:{name}"], cwd=ROOT)
        require(hashlib.sha256(original).hexdigest() == expected, f"Base hash: {name}")
        require(digest(ROOT / name) == expected, f"Accepted input changed: {name}")
    for name, tree in b["frozen_production_trees"].items():
        require(git("rev-parse", f"{BASE}:{name}") == tree, f"Production tree: {name}")
    names = set(git("diff", "--name-only", BASE).splitlines())
    names |= set(git("ls-files", "--others", "--exclude-standard").splitlines())
    check_scope_names(names)
    require(
        ".DS_Store" not in git("diff", "--cached", "--name-only").splitlines(),
        "Unrelated .DS_Store staged",
    )
    print("Exact base / merged PR33 / frozen R1+R2 / production scope: PASS")


def package_audit(d, source_dir):
    actual = {
        str(p.relative_to(PACKAGE)): digest(p)
        for p in PACKAGE.rglob("*")
        if p.is_file() and p.name != "checksums.json"
    }
    require(actual == d["checksums.json"]["files"], "Package hashes/inventory differ")
    require(
        not any(
            isinstance(n, ast.Constant) and isinstance(n.value, float)
            for n in ast.walk(ast.parse(Path(__file__).read_text()))
        ),
        "Float literal in auditor",
    )
    text = pdf_text(PACKAGE / "sources/afrs-prefilter.pdf")
    require(
        text == (PACKAGE / "sources/afrs-prefilter.txt").read_text(), "PDF text drift"
    )
    compact = " ".join(text.split())
    for token in [
        "No.M 504 00",
        "No.N 502 00",
        "Q-G. VEGETABLES No. 5",
        "No.Q 069 01",
        "No.O 007 01",
        "TURKEY,GROUND,90% LEAN,RAW",
        "walnuts (optional)",
        "fresh green pepper or tomato (optional)",
        "If desired, add cinnamon and nutmeg",
        "TOMATOES,CANNED,DICED,DRAINED",
    ]:
        require(token in compact, f"Primary source fact absent: {token}")
    sources = d["source-manifest.json"]["sources"]
    afrs = sources[0]
    require(
        afrs["version"] == "June 2003"
        and afrs["pages"] == [1214, 1329, 1457, 1612, 1345]
        and afrs["original_sha256"]
        == "2f6795b5fc39b167fb2913bfccb720948dd257f6a90ca3fa7e228d7fb87ec090",
        "Mixed AFRS lineage",
    )
    if source_dir:
        for source in sources:
            if source["original_filename"]:
                path = source_dir / source["original_filename"]
                require(
                    digest(path) == source["original_sha256"]
                    and path.stat().st_size == source["original_bytes"],
                    f"Original source hash/size: {source['id']}",
                )
        full = pdf_text(source_dir / "afrs-full.pdf").split("\f")
        for index, page in enumerate(afrs["pages"]):
            require(
                " ".join(full[page - 1].split())
                == " ".join(text.split("\f")[index].split()),
                f"AFRS excerpt lineage differs: {page}",
            )
        fries = pdf_text(source_dir / "sweet-fries.pdf").split("\f")[10]
        for token in ["4 medium sweet potatoes", "canola or olive oil", "Optional"]:
            require(token.lower() in fries.lower(), f"SDSU observation: {token}")
    print("Source/package SHA-256 / primary excerpt lineage / no floats: PASS")


def russian(text):
    return (
        isinstance(text, str)
        and bool(re.search(r"[А-Яа-яЁё]", text))
        and not re.search(r"[A-Za-z]", text)
    )


def composition_ok(code, inventory):
    p = inventory.get(code, {})
    return (
        p.get("version") is not None
        and p.get("input_state") == "INPUT"
        and p.get("kind") == "ATOMIC"
        and p.get("source_id") is not None
        and p.get("source_version") is not None
        and p.get("source_name") == "USDA_FDC"
        and p.get("estimated") is not True
    )


def exact_mass(q):
    require(
        isinstance(q, dict)
        and all(isinstance(q.get(k), str) for k in ["grams", "lb", "oz"]),
        "Missing exact mass",
    )
    require(
        q["authority"] == "DIRECT_SOURCE_WEIGHT", "Estimate/density/piece inference"
    )
    require(q["estimated"] is False, "Estimate mass authority")
    require(q["mass_basis"] in {"EP", "SOURCE_INGREDIENT_WEIGHT"}, "AP is not EP")
    require(q.get("piece_mass_g") is None, "Universal piece mass")
    require(q.get("density_g_ml") is None, "Generic density")
    grams = Decimal(q["lb"]) * LB + Decimal(q["oz"]) * OZ
    require(grams.is_finite() and grams > 0, "Invalid grams")
    require(Decimal(q["grams"]) == grams, "Decimal conversion mismatch")
    return True


def validate_variant(v, inventory, source):
    """Fail-closed contract for a complete branch, also exercised non-vacuously.

    Synthetic positive control supplies test-only source records. The real R3
    funnel has no complete branch; it cannot acquire readiness from this fixture.
    Source records describe reviewed applicability, never inferred category ORs.
    """
    require(
        v["inventory_complete"]
        and v["roles"]
        and any(not r["optional"] for r in v["roles"]),
        "Incomplete branch",
    )
    require(v["id"] in source["tested_variant_ids"], "Variant lacks kitchen evidence")
    require(v["family_id"] == source["family_id"], "Family grouping without provenance")
    require(v["batch"] == source["tested_batch"], "Household scaling without evidence")
    require(v["rights"] == "ACCEPT", "Rights deferred")
    require(v["ru_familiarity"] == "RU_RECIPE_FAMILIAR", "Familiarity unreviewed")
    require(
        v["steps_ru"] and all(map(russian, v["steps_ru"])), "Russian process absent"
    )
    require(russian(v["name_ru"]) and russian(v["restriction_ru"]), "English display")
    for role in v["roles"]:
        require(composition_ok(role["food_code"], inventory), "Missing Composition")
        require(role["form_compatible"], "Food form mismatch")
        require(exact_mass(role["quantity"]), "Missing exact mass")
        require(russian(role["name_ru"]), "English display")
        require(
            role["market_class"] in {"RU_COMMON", "RU_AVAILABLE"}
            and role["default_suitability_reviewed"],
            "SPECIALTY_OR_UNCLEAR or unreviewed default",
        )
        if role["optional"]:
            require(role["semantics"] == "OPTIONAL", "Alternative relabeled optional")
            require(
                role["component_kind"] == "FOOD_COMPONENT", "Optional processing medium"
            )
            require(
                role["id"] in source["optional_role_ids"],
                "Omission lacks source support",
            )
    return True


def validate_substitution(path, inventory, source):
    require(len(path["branches"]) == 2, "One-sided substitution")
    require(path["rule_id"] in source["replacement_rule_ids"], "Inferred substitution")
    require(path["basis"] == "EXPLICIT_SOURCE_REPLACEMENT", "Inferred substitution")
    require(russian(path["explanation_ru"]), "English substitution display")
    for branch in path["branches"]:
        validate_variant(branch, inventory, source)
    return True


def derive(d):
    inventory = {p["canonical_code"]: p for p in d["catalogue-inventory.json"]}
    require(len(inventory) == 185, "Food inventory count")
    require(
        sum(composition_ok(c, inventory) for c in inventory) == 63, "Composition count"
    )
    funnel = d["candidate-funnel.json"]
    candidates = funnel["candidates"]
    require(
        [c["id"] for c in candidates] == [f"R3-{i:02}" for i in range(1, 13)]
        and funnel["serious_count"] == len(candidates) == funnel["serious_limit"] == 12,
        "Funnel boundary/identity drift",
    )
    require(
        sum(c["deep_reviewed"] for c in candidates) == funnel["deep_count"] == 0
        and funnel["deep_limit"] == 5
        and funnel["closed"] is True,
        "Unreviewed deep candidate or enlarged funnel",
    )
    quantities = d["quantity-authority.json"]
    require(
        Decimal(quantities["lb_to_g"]) == LB and Decimal(quantities["oz_to_g"]) == OZ,
        "Wrong mass constant",
    )
    require(
        quantities["universal_piece_mass_g"] is None
        and quantities["generic_density"] is None
        and quantities["production_mass_rows_changed"] is False,
        "Quantity authority broadened",
    )
    source_weights = {
        "R3-01:WALNUTS": ("2.125", "0"),
        "R3-02:GREEN_PEPPER": ("2", "0"),
        "R3-02:TOMATO": ("2", "0"),
        "R3-03:BUTTER_OR_MARGARINE": ("1", "0"),
        "R3-04:CINNAMON": ("0", "0.5"),
        "R3-04:NUTMEG": ("0", "0.25"),
        "R3-06:GREEN_PEPPER": ("0", "2.5"),
        "R3-06:DRESSING_OR_MAYONNAISE": ("0", "14"),
        "R3-07:TOASTED_ALMONDS": ("0", "2"),
        "R3-08:WALNUTS": ("0", "3.25"),
    }
    require(
        {q["id"]: (q["lb"], q["oz"]) for q in quantities["observations"]}
        == source_weights,
        "Reviewed source weight observation drift",
    )
    for q in quantities["observations"]:
        exact_mass(q)
        require(q["production_publish"] is False, "Research mass published")
    qids = {q["id"] for q in quantities["observations"]}
    expected_optional = [
        "OPTIONAL",
        "OPTIONAL",
        "OPTIONAL",
        "OPTIONAL_GROUP",
        "ABSENT",
        "OPTIONAL",
        "OPTIONAL",
        "OPTIONAL",
        "OPTIONAL_GROUP",
        "OPTIONAL",
        "OPTIONAL_GROUP",
        "OPTIONAL",
    ]
    evidence = {}
    for filename, key in [
        ("source-observations.json", "observations"),
        ("composition-readiness.json", "witnesses"),
        ("kitchen-verification.json", "candidates"),
        ("optional-role.json", "roles"),
        ("substitution-matrix.json", "paths"),
        ("compatibility.json", "candidates"),
        ("ru-familiarity.json", "candidates"),
        ("market-evidence.json", "candidates"),
    ]:
        rows = d[filename][key]
        require(
            [r["candidate_id"] for r in rows] == [c["id"] for c in candidates], filename
        )
        evidence[filename] = {r["candidate_id"]: r for r in rows}
    failures = {}
    for c in candidates:
        cid = c["id"]
        require(c["required_witnesses"], "No decisive prefilter witness")
        require(
            c["required_witnesses"]
            == evidence["composition-readiness.json"][cid]["required_witnesses"],
            "Composition witness drift",
        )
        blockers = []
        for w in c["required_witnesses"]:
            if not composition_ok(w["food_code"], inventory):
                blockers.append("MISSING_COMPOSITION")
            if not w["form_compatible"]:
                blockers.append("FOOD_FORM_UNRESOLVED")
        mass = c.get("required_mass_witness")
        if mass and mass["authority"] == "UNRESOLVED_PIECE" and mass["grams"] is None:
            blockers.append("REQUIRED_EXACT_MASS_UNRESOLVED")
        require(blockers, f"No independently verified decisive blocker: {cid}")
        # No promotion from partial evidence; a real full review is a different payload.
        require(
            c["stage"] == "PREFILTER_REJECTED"
            and c["required_inventory_complete"] is False
            and c["household_scaling_verified"] is False,
            f"False full review: {cid}",
        )
        failures[cid] = sorted(set(blockers))
        optional = evidence["optional-role.json"][cid]
        require(
            optional["semantics"] == expected_optional[int(cid[-2:]) - 1],
            "Source optional/alternative semantics changed",
        )
        require(
            set(optional["quantity_refs"]) <= qids, "Unknown optional mass reference"
        )
        require(
            optional["full_component_review"] == "NOT_ESTABLISHED",
            "False optional closure",
        )
        if optional["semantics"] != "ABSENT":
            require(
                optional["semantics"] in {"OPTIONAL", "OPTIONAL_GROUP"},
                "Alternative as optional",
            )
            require(
                optional["component_kind"] == "FOOD_COMPONENT",
                "Processing medium as food",
            )
        path = evidence["substitution-matrix.json"][cid]
        require(path["status"] == "NOT_ESTABLISHED", "False substitution closure")
        if path["source_rule"] == "EXPLICIT_REPLACEMENT":
            require(len(path["branches"]) == 2, "One-sided substitution")
        else:
            require(
                path["source_rule"] == "ABSENT" and not path["branches"],
                "Inferred substitution",
            )
        for branch in path["branches"]:
            require(
                branch["complete_recipe_review"] is False
                and branch["composition_complete"] is False
                and branch["kitchen_status"] == "NOT_ESTABLISHED",
                "Shared base blocker bypassed in substitution",
            )
        kitchen = evidence["kitchen-verification.json"][cid]
        require(
            kitchen["base_variant_status"] == "NOT_REVIEWED"
            and kitchen["substituted_variant_status"] == "NOT_ESTABLISHED"
            and kitchen["household_scaling_verified"] is False,
            "Unreviewed kitchen applicability",
        )
        for filename in ["ru-familiarity.json", "market-evidence.json"]:
            require(
                evidence[filename][cid]["decision"] == "NOT_REVIEWED", "False RU review"
            )
    source_ids = {s["id"] for s in d["source-manifest.json"]["sources"]}
    rights = d["rights-review.json"]["reviews"]
    require({r["source_id"] for r in rights} == source_ids, "Rights coverage")
    for r in rights:
        require(
            r["disposition"] == ("ACCEPT" if r["source_id"] == "AFRS-2003" else "DEFER")
            and r["authorship_is_hosting"] is False
            and r["government_funding_is_federal_authorship"] is False
            and r["publication_approved"] is False,
            "Unsupported rights promotion",
        )
    market = d["market-evidence.json"]
    for key in [
        "new_commodity_exception",
        "mechanical_three_of_five",
        "ru_available_implies_rare",
    ]:
        require(market[key] is False, "Corrected market policy drift")
    # Accepted R2 supplies fixed member gates, unchanged; do not re-evaluate their recipes.
    fixed = read(ROOT / "data/curation/recipe-assembly-a-r2/final-readiness.json")
    require(fixed["individually_ready"] == FIXED, "Frozen membership drift")
    for member in FIXED:
        require(
            all(fixed["candidate_gates"][member].values()),
            "Fixed individual gate drift",
        )
    require(not fixed["evidence_ready_final_three"], "Accepted R2 final state drift")
    gates = {
        name: "PASS" if passed else "OPEN"
        for name, passed in fixed["collective_feature_gates"].items()
    }
    for name, key in [
        ("kitchen_verification", "kitchen_scope"),
        ("ru_familiarity", "ru_familiarity"),
        ("russian_display", "russian_display"),
    ]:
        gates[name] = (
            "PASS" if all(fixed["candidate_gates"][m][key] for m in FIXED) else "OPEN"
        )
    gates["family_count"] = "PASS" if len(FIXED) == 3 else "OPEN"
    complete = len(FIXED) == 3 and all(value == "PASS" for value in gates.values())
    return dict(
        operation="RECIPE-ASSEMBLY-A-R3",
        status="READY" if complete else "BLOCKED",
        fixed_members=FIXED,
        third_candidate=None,
        individual_ready_count=len(FIXED),
        candidate_individual_gates={cid: False for cid in failures},
        decisive_prefilter_blockers=failures,
        collective_gates=gates,
        gate_scope_ru="Пройденные критерии относятся только к двум принятым семействам в неизменном объёме; полного набора из трёх семейств нет.",
        evidence_ready_final_three=complete,
        selected_final_three=FIXED if complete else [],
        implementation_authorized=False,
        assembly_a="BLOCKED",
        assembly_b="NOT STARTED",
        pr7="NOT STARTED",
        migration="0029_food_composition_core",
        status_ru="Исследование заблокировано: готовы два семейства из трёх; необязательная роль и проверенная замена в готовом третьем семействе не установлены.",
    )


def russian_audit(d):
    def walk(value, key=""):
        if isinstance(value, dict):
            for k, v in value.items():
                walk(v, k)
        elif isinstance(value, list):
            for item in value:
                walk(item, key)
        elif key.endswith("_ru") and value:
            require(russian(value), f"English user-facing display: {key}")

    for doc in d.values():
        walk(doc)
    print(
        "Russian display / optional semantics / substitution completeness / RU policy: PASS"
    )


def database_audit(d):
    require(os.environ.get("AI_ENABLED") == "false", "AI_ENABLED=false required")
    sys.path[:0] = [str(ROOT / "backend"), str(ROOT / "scripts")]
    from app.db.config import DatabaseConfig
    from audit_pr6_close import measure, encode as accepted_encode

    with TemporaryDirectory(prefix="assembly-r3-") as directory:
        config = DatabaseConfig(path=Path(directory) / "accepted.sqlite")
        reports = measure(config)
        for name in ["food-readiness.json", "recipe-readiness.json"]:
            require(
                accepted_encode(reports[name])
                == (ROOT / "data/curation/pr6-close" / name).read_text(),
                f"Accepted replay drift: {name}",
            )
        with sqlite3.connect(config.path) as db:
            db.row_factory = sqlite3.Row
            require(
                [dict(r) for r in db.execute(PIN_QUERY)]
                == d["catalogue-inventory.json"],
                "Exact Composition/profile pins differ",
            )
            require(
                db.execute("SELECT COUNT(*) FROM nutrition_vector_seals").fetchone()[0]
                == 188,
                "Seal drift",
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
            require(closure[key] == accepted[key], f"Accepted closure drift: {key}")
        require(
            closure["migration_head"] == "0029_food_composition_core"
            and len(closure["estimate_usages_non_executable"]) == 40,
            "Migration or estimate drift",
        )
    print(
        "Disposable accepted DB replay / 185 foods / 63 Composition pins / 188 seals / 40 estimates / 0029: PASS"
    )


def adversarial(d):
    inventory = {p["canonical_code"]: p for p in d["catalogue-inventory.json"]}
    # Not donor 13: artificial contract unit data, no real source or nutrition claim.
    quantity = dict(
        authority="DIRECT_SOURCE_WEIGHT",
        estimated=False,
        mass_basis="EP",
        lb="1",
        oz="0",
        grams="453.59237",
    )
    role = dict(
        id="optional",
        food_code="TOMATO",
        name_ru="Томат",
        form_compatible=True,
        quantity=quantity,
        optional=True,
        semantics="OPTIONAL",
        component_kind="FOOD_COMPONENT",
        market_class="RU_AVAILABLE",
        default_suitability_reviewed=True,
    )
    source = dict(
        family_id="SYNTHETIC",
        tested_variant_ids=["a", "b"],
        tested_batch=100,
        optional_role_ids=["optional"],
        replacement_rule_ids=["explicit"],
    )
    variant = dict(
        id="a",
        family_id="SYNTHETIC",
        inventory_complete=True,
        roles=[role],
        batch=100,
        rights="ACCEPT",
        ru_familiarity="RU_RECIPE_FAMILIAR",
        steps_ru=["Добавить подготовленный компонент."],
        name_ru="Искусственный проверочный пример",
        restriction_ru="Только проверка логики аудитора.",
    )
    required = deepcopy(role)
    required.update(id="required", food_code="WATER", name_ru="Вода", optional=False)
    variant["roles"].append(required)
    other = deepcopy(variant)
    other["id"] = "b"
    path = dict(
        branches=[variant, other],
        rule_id="explicit",
        basis="EXPLICIT_SOURCE_REPLACEMENT",
        explanation_ru="Искусственное правило для проверки валидатора.",
    )
    validate_substitution(path, inventory, source)

    def role_set(key, value):
        return lambda p: p["branches"][1]["roles"][0].__setitem__(key, value)

    def mass_set(key, value):
        return lambda p: p["branches"][1]["roles"][0]["quantity"].__setitem__(
            key, value
        )

    def branch_set(key, value):
        return lambda p: p["branches"][1].__setitem__(key, value)

    cases = [
        ("Missing Composition", role_set("food_code", "BROCCOLI")),
        ("Decimal conversion", mass_set("grams", "0")),
        ("Missing exact mass", mass_set("grams", None)),
        (
            "Alternative relabeled",
            role_set("semantics", "ALTERNATIVE_REQUIRED_VARIANT"),
        ),
        ("Optional processing", role_set("component_kind", "PROCESSING_MEDIUM")),
        ("One-sided", lambda p: p.__setitem__("branches", p["branches"][:1])),
        (
            "Inferred substitution",
            lambda p: p.__setitem__("basis", "CATEGORY_SIMILARITY"),
        ),
        ("kitchen evidence", branch_set("id", "untested")),
        ("Family grouping", branch_set("family_id", "UNRELATED")),
        ("Estimate/density/piece", mass_set("authority", "ESTIMATE")),
        ("Estimate mass", mass_set("estimated", True)),
        ("Generic density", mass_set("density_g_ml", "1")),
        ("Universal piece", mass_set("piece_mass_g", "50")),
        ("AP is not EP", mass_set("mass_basis", "AP")),
        ("SPECIALTY_OR_UNCLEAR", role_set("market_class", "SPECIALTY_OR_UNCLEAR")),
        ("English display", role_set("name_ru", "Tomato")),
        ("Household scaling", branch_set("batch", 4)),
        ("Rights deferred", branch_set("rights", "DEFER")),
        ("Incomplete branch", branch_set("inventory_complete", False)),
        ("Food form", role_set("form_compatible", False)),
    ]
    for reason, mutate in cases:
        mutant = deepcopy(path)
        mutate(mutant)
        try:
            validate_substitution(mutant, inventory, source)
        except ValueError as error:
            require(reason in str(error), f"Wrong rejection: {reason}: {error}")
        else:
            raise ValueError(f"Adversarial case accepted: {reason}")
    for name in [
        "backend/app/recipes/template.py",
        "backend/app/db/migrations/0030_recipe_template_catalogue.py",
        "data/seed/recipe_templates.json",
        "data/curation/recipe-assembly-a-r1/final-three.json",
        "data/curation/recipe-assembly-a-r2/final-readiness.json",
    ]:
        try:
            check_scope_names({name})
        except ValueError:
            pass
        else:
            raise ValueError(f"Forbidden scope accepted: {name}")
    try:
        check_frozen({"file": "accepted"}, {"file": "mutated"})
    except ValueError:
        pass
    else:
        raise ValueError("Frozen mutation accepted")
    for key, value in [
        ("evidence_ready_final_three", True),
        ("individual_ready_count", 3),
        ("third_candidate", "R3-02"),
    ]:
        false_result = deepcopy(derive(d))
        false_result[key] = value
        try:
            check_report(false_result, derive(d))
        except ValueError:
            pass
        else:
            raise ValueError("False final-three READY accepted")
    try:
        json.loads('{"mass": 1.25}', parse_float=reject_float)
    except ValueError:
        pass
    else:
        raise ValueError("Float accepted")
    print(
        f"Adversarial audit: PASS; {len(cases) + 10} negative cases + complete synthetic positive control (not a donor)"
    )


def check_report(reported, derived):
    require(reported == derived, "Reported final-three differs from derivation")


def local_links():
    count = 0
    for file in [PACKAGE / "README.md"] + [
        ROOT / p for p in sorted(ALLOWED) if p.endswith(".md")
    ]:
        for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", file.read_text()):
            if re.match(r"[a-z]+://", target):
                continue
            name, _, anchor = target.strip("<>").partition("#")
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
                require(anchor in slugs, f"Broken anchor: {file}: {target}")
            count += 1
    print(f"Local links/anchors: PASS; {count}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", action="store_true")
    parser.add_argument("--source-dir", type=Path)
    parser.add_argument("--adversarial", action="store_true")
    parser.add_argument(
        "--derive", action="store_true", help="Print derived JSON; no writes"
    )
    args = parser.parse_args()
    docs = {p.name: read(p) for p in PACKAGE.glob("*.json")}
    if args.derive:
        print(encode(derive(docs)), end="")
        return
    scope_audit(docs)
    package_audit(docs, args.source_dir)
    result = derive(docs)
    check_report(docs["final-three.json"], result)
    russian_audit(docs)
    if args.database:
        database_audit(docs)
    if args.adversarial:
        adversarial(docs)
    local_links()
    print(
        "R3 BLOCKED; individually ready 2/3; third candidate none; optional/substitution OPEN; implementation unauthorized"
    )


if __name__ == "__main__":
    main()
