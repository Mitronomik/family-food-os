"""Offline DATA2 evidence checks; no network, database or production imports.

Research integrity is deliberately separate from final-corpus acceptance.
The default command fails closed unless the final successor exists and passes.
"""

from __future__ import annotations

import argparse
import ast
from collections import Counter
import csv
from datetime import date
import hashlib
import json
from io import StringIO
from pathlib import Path
import re
import subprocess
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT / "data/curation/pr4-data2"
CHAINS = ("PYATEROCHKA", "PEREKRESTOK", "LENTA", "OKEY", "MAGNIT")
CHAIN_NAMES = {
    "Пятёрочка": "PYATEROCHKA",
    "Перекрёсток": "PEREKRESTOK",
    "Лента": "LENTA",
    "О'КЕЙ": "OKEY",
    "Магнит": "MAGNIT",
}
OBSERVATION_FILES = (
    "research-x5-v2.json",
    "research-x5-v3.json",
    "research-lenta-okey-v2.json",
    "research-lenta-okey-v3.json",
    "research-lenta-okey-v4.json",
    "research-lenta-okey-v5.json",
    "research-lenta-okey-v6.json",
    "research-lenta-okey-v7.json",
    "research-lenta-okey-v8.json",
    "research-lenta-okey-v9.json",
    "research-magnit-v2.json",
    "research-panel-v3.json",
    "research-correction-market.json",
)
FORBIDDEN = {
    "CACFP6-VEGETABLE-FRITTATA-BITES",
    "CACFP6-CAULIFLOWER-RICE",
}
CSV_FIELDS = (
    "source_recipe_id",
    "source_ingredient_text",
    "normalized_concept",
    "existing_food_ingredient_code",
    "resolution_status",
    "missing_reason",
)
SELECTED = {"SELECTED_REQUIRED", "SELECTED_OPTIONAL", "SELECTED_CONDITIONAL"}
PR4_HEAD = "cd2285802c94735e0c9015042f9f4c0b52d68b85"
PR4_ENUM_SHA256 = "86e61513ea1ae4373c1624d47e01e4bedf993ad6ccd433f0093d125da60a6552"
SOURCE_FACT_FIELDS = (
    "recipe_name",
    "source_servings",
    "source_url",
    "source_sha256",
    "meal_type_code",
    "curation_role",
    "meal_anchor",
    "substantial_one_bowl",
    "pure_side_dish",
    "primary_protein_family",
    "protein_evidence_codes",
    "role_evidence",
    "diversity_contribution",
    "source_times",
    "equipment",
    "source_limits",
)
HANDBACK_METADATA_FIELDS = (
    "source_collection",
    "source_section",
    "source_attribution",
    "rights_review",
    "source_artifact",
    "source_quality_flags",
    "checked_at",
    "ordinary_equipment_assessment",
    "selection",
)
PROTEIN_PATTERNS = {
    "POULTRY": r"(?:CHICKEN|TURKEY)_(?!BROTH)[A-Z0-9_]+",
    "FISH": r"(?:COD|SALMON|TUNA|TILAPIA)_[A-Z0-9_]+",
    "MEAT": r"(?:BEEF|PORK)_(?!BROTH)[A-Z0-9_]+",
    "EGG": r"EGG(?:_WHITE)?",
    "LEGUME_TOFU": r"(?:TOFU|LENTILS|CHICKPEAS)_[A-Z0-9_]+|(?:WHITE|BLACK|KIDNEY|PINTO)_BEANS_[A-Z0-9_]+|BLACK_EYED_PEAS_DRY|GREEN_PEAS_CANNED|EDAMAME_FROZEN",
    "GRAIN_VEGETABLE": r"(?:RICE|OATS|PASTA)_[A-Z0-9_]+|BUCKWHEAT|MILLET|BULGUR|QUINOA",
}
# These are curation consistency rules, not a parallel runtime enum.
CURATION_ROLE_COMPATIBILITY = {
    "BREAKFAST": {"breakfast"},
    "MAIN_DISH": {"main"},
    "SIDE_DISH": {"side", "salad"},
    "SALAD": {"salad"},
    "SANDWICH": {"sandwich"},
    "SOUP": {"main", "other"},
    "DESSERT": {"other"},
    "SNACK": {"other"},
    "CONDIMENT": {"other"},
}


def pr4_meal_type_codes(directory: Path = DIRECTORY, root: Path = ROOT) -> set[str]:
    """Parse a pinned, verbatim runtime declaration without importing runtime.

    Git-object comparison is an additional check when the reviewed PR exists
    locally. A shallow/offline main checkout remains reproducible from the
    integrity-pinned excerpt. No network or changing-branch lookup is performed.
    """
    document = read_json(directory / "pr4-meal-type-contract.json")
    source = document["enum_source"]
    if (
        document.get("source_head") != PR4_HEAD
        or document.get("source_path") != "backend/app/domain/food_recipes.py"
        or hashlib.sha256(source.encode()).hexdigest() != PR4_ENUM_SHA256
        or document.get("enum_source_sha256") != PR4_ENUM_SHA256
    ):
        raise ValueError("PR4 MealTypeCode pinned source integrity failed")
    classes = [n for n in ast.parse(source).body if isinstance(n, ast.ClassDef)]
    if len(classes) != 1 or classes[0].name != "MealTypeCode":
        raise ValueError("PR4 MealTypeCode declaration missing")
    values = {
        node.value.value
        for node in classes[0].body
        if isinstance(node, ast.Assign)
        and isinstance(node.value, ast.Constant)
        and isinstance(node.value.value, str)
    }
    result = subprocess.run(
        ["git", "show", f"{PR4_HEAD}:{document['source_path']}"],
        cwd=root,
        capture_output=True,
        check=False,
    )
    if result.returncode == 0:
        full_source = result.stdout.decode()
        node = next(
            n
            for n in ast.parse(full_source).body
            if isinstance(n, ast.ClassDef) and n.name == "MealTypeCode"
        )
        if ast.get_source_segment(full_source, node) + "\n" != source or hashlib.sha256(
            result.stdout
        ).hexdigest() != document.get("source_blob_sha256"):
            raise ValueError("PR4 MealTypeCode differs from reviewed Git source")
    return values


def diversity_counts(recipes: list[dict]) -> dict:
    anchors = [r for r in recipes if r.get("meal_anchor") is True]
    return {
        "meal_types": dict(
            sorted(Counter(r.get("meal_type_code") for r in recipes).items())
        ),
        "curation_roles": dict(
            sorted(Counter(r.get("curation_role") for r in recipes).items())
        ),
        "meal_anchors": len(anchors),
        "substantial_one_bowl_meals": sum(
            r.get("substantial_one_bowl") is True for r in recipes
        ),
        "primary_protein_families": dict(
            sorted(
                Counter(
                    r["primary_protein_family"]
                    for r in anchors
                    if r.get("primary_protein_family")
                ).items()
            )
        ),
        "pure_side_dishes": sum(r.get("pure_side_dish") is True for r in recipes),
    }


def diversity_errors(
    recipes: list[dict], source_rows: list[dict], allowed: set[str]
) -> list[str]:
    """Bounded factual guards, not a general semantic or nutrition validator."""
    errors = []
    for recipe in recipes:
        recipe_id = recipe["recipe_source_id"]
        codes = {
            r["existing_food_ingredient_code"]
            for r in source_rows
            if r["source_recipe_id"] == recipe_id
        }
        if recipe.get("meal_type_code") not in allowed or "meal_type" in recipe:
            errors.append(
                f"Canonical meal_type_code violates PR4 contract: {recipe_id}"
            )
        compatible = CURATION_ROLE_COMPATIBILITY.get(recipe.get("curation_role"))
        if (
            compatible is not None and recipe.get("meal_type_code") not in compatible
        ) or (
            recipe.get("meal_type_code") == "breakfast"
            and recipe.get("curation_role") != "BREAKFAST"
        ):
            errors.append(f"Curation role contradicts canonical meal type: {recipe_id}")
        role_evidence = recipe.get("role_evidence")
        if not nonempty_text(recipe.get("curation_role")) or not (
            nonempty_text(role_evidence)
            or isinstance(role_evidence, dict)
            and all(
                nonempty_text(role_evidence.get(key))
                for key in ("source_words", "source_section", "curator_rationale")
            )
        ):
            errors.append(f"Missing reviewed curation role evidence: {recipe_id}")
        if any(
            type(recipe.get(k)) is not bool
            for k in ("meal_anchor", "substantial_one_bowl", "pure_side_dish")
        ):
            errors.append(f"Diversity flags must be explicit booleans: {recipe_id}")
        anchor = recipe.get("meal_anchor") is True
        family = recipe.get("primary_protein_family")
        evidence = recipe.get("protein_evidence_codes", [])
        if not isinstance(evidence, list) or not set(evidence) <= codes:
            errors.append(
                f"Protein evidence is not selected ingredient evidence: {recipe_id}"
            )
            evidence = []
        if family is not None and (
            family not in PROTEIN_PATTERNS
            or not evidence
            or any(
                not re.fullmatch(PROTEIN_PATTERNS[family], code) for code in evidence
            )
        ):
            errors.append(
                f"Primary protein family contradicts selected codes: {recipe_id}"
            )
        if anchor and (
            family is None
            or recipe.get("pure_side_dish") is True
            or recipe.get("meal_type_code")
            not in {"breakfast", "main", "sandwich", "salad"}
            or recipe.get("curation_role")
            in {"SIDE_DISH", "DESSERT", "SNACK", "CONDIMENT"}
        ):
            errors.append(f"Unsupported meal-anchor claim: {recipe_id}")
        if recipe.get("substantial_one_bowl") is True and not (
            recipe.get("curation_role") == "SOUP" or anchor
        ):
            errors.append(f"Unsupported soup/substantial one-bowl claim: {recipe_id}")
        if (
            recipe.get("meal_type_code") == "side"
            or recipe.get("curation_role") == "SIDE_DISH"
        ) and recipe.get("pure_side_dish") is not True:
            errors.append(
                f"Source side role cannot be hidden from side count: {recipe_id}"
            )
        if recipe.get("pure_side_dish") is True and recipe.get(
            "meal_type_code"
        ) not in {"side", "salad"}:
            errors.append(
                f"Pure-side role contradicts canonical meal type: {recipe_id}"
            )
        # Positive diversity descriptions must not name absent protein foods.
        # This deliberately narrow vocabulary catches the known corruption class;
        # provenance and reviewed role checks remain necessary for other claims.
        claims = str(recipe.get("diversity_contribution", "")).lower()
        for words, pattern in (
            (r"\bpork\b|\bswine\b", r"PORK_.*"),
            (r"\bbeef\b", r"BEEF_(?!BROTH).*"),
            (r"\bchicken\b", r"CHICKEN_(?!BROTH).*"),
            (r"\bturkey\b", r"TURKEY_.*"),
            (r"\bpoultry\b", PROTEIN_PATTERNS["POULTRY"]),
            (r"\bfish\b|\bcod\b|\bsalmon\b|\btuna\b", PROTEIN_PATTERNS["FISH"]),
            (r"\beggs?\b", PROTEIN_PATTERNS["EGG"]),
            (r"\btofu\b", r"TOFU_.*"),
        ):
            if re.search(words, claims) and not any(
                re.fullmatch(pattern, code) for code in codes
            ):
                errors.append(
                    f"Diversity protein claim contradicts selected codes: {recipe_id}"
                )
        if recipe_id == "CACFP6-LOCAL-HARVEST-BAKE" and (
            recipe.get("meal_type_code") != "side"
            or recipe.get("curation_role") != "SIDE_DISH"
            or anchor
            or recipe.get("pure_side_dish") is not True
            or family is not None
            or any(
                re.fullmatch(PROTEIN_PATTERNS[f], code)
                for f in ("MEAT", "POULTRY", "FISH")
                for code in codes
            )
            or re.search(r"\bpork\b|\bmain\b", claims)
        ):
            errors.append("Local Harvest Bake is a vegetable side, not a pork main")
    counts = diversity_counts(recipes)
    for condition, message in (
        (counts["meal_anchors"] >= 8, "Diversity requires >=8 meal anchors"),
        (
            counts["meal_types"].get("breakfast", 0) >= 3,
            "Diversity requires >=3 breakfasts",
        ),
        (
            counts["substantial_one_bowl_meals"] >= 2,
            "Diversity requires >=2 soups/substantial one-bowl meals",
        ),
        (
            len(counts["primary_protein_families"]) >= 3,
            "Diversity requires >=3 primary protein families",
        ),
        (counts["pure_side_dishes"] <= 12, "Diversity requires <=12 pure side dishes"),
    ):
        if not condition:
            errors.append(message)
    return errors


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def classify_market(chains: set[str], ordinary_retail_plausibility: bool) -> str:
    """Call only with evidence reviewed for the SAME purchase concept/form."""
    if not chains <= set(CHAINS):
        raise ValueError("Non-panel retailer cannot qualify a core ingredient")
    if len(chains) >= 3:
        return "RU_MASS_MARKET"
    if chains and ordinary_retail_plausibility:
        return "RU_AVAILABLE"
    return "SPECIALTY_OR_UNCLEAR"


def reviewable_url(value: object) -> bool:
    if not isinstance(value, str):
        return False
    try:
        parsed = urlparse(value)
    except ValueError:
        return False
    return parsed.scheme == "https" and bool(parsed.hostname) and not parsed.username


def nonempty_text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def form_qualified_chains(
    code: str, purchase_concept: str, matches: list[dict], observations: dict[str, dict]
) -> set[str]:
    """Require explicit form review; code equality alone never qualifies evidence.

    This validates the review record, not culinary equivalence. A reviewer must
    document the source/observed form comparison; software cannot infer it.
    """
    chains = set()
    for match in matches:
        observation = observations.get(match.get("observation_id"))
        if (
            not observation
            or observation["status"] != "AVAILABLE"
            or observation["food_ingredient_code"] != code
            or match.get("purchase_concept") != purchase_concept
            or match.get("form_match_reviewed") is not True
            or not nonempty_text(match.get("rationale"))
        ):
            raise ValueError("Evidence lacks reviewed same-code AND same-form match")
        chains.add(observation["retailer_chain"])
    return chains


def normalized_observations(directory: Path = DIRECTORY) -> list[dict]:
    records = []
    for filename in OBSERVATION_FILES:
        path = directory / filename
        if not path.exists():
            continue
        for index, raw in enumerate(read_json(path)["observations"], 1):
            chain = raw.get("retailer_chain", raw.get("retailer"))
            records.append(
                {
                    "observation_id": f"{filename}:{index}",
                    "food_ingredient_code": raw.get(
                        "food_ingredient_code", raw.get("code")
                    ),
                    "retailer_chain": CHAIN_NAMES.get(chain, chain),
                    "region": raw["region"],
                    "checked_at": raw["checked_at"],
                    "evidence_url": raw.get("evidence_url", raw.get("url")),
                    "region_evidence_url": raw.get("region_evidence_url"),
                    "observed_product_wording": raw.get(
                        "observed_product_wording", raw.get("wording")
                    ),
                    "purchase_concept": raw.get("purchase_concept"),
                    "evidence_method": raw.get("evidence_method", raw.get("method")),
                    "status": raw["status"],
                    "notes": raw["notes"],
                    "stock_claim": raw.get("stock_claim", False),
                }
            )
    return records


def build_matrix(directory: Path = DIRECTORY) -> dict:
    """Deduplicate evidence, preserving every raw ID and form-specific claim.

    The first raw ID is the deterministic representative. Mixed availability
    claims remain UNCERTAIN here: one product can establish generic curry yet
    fail to establish mild Indian curry. Explicit form joins use raw records,
    not this conservative group summary.
    """
    raw_observations = normalized_observations(directory)
    groups = {}
    for observation in raw_observations:
        key = (
            observation["food_ingredient_code"],
            observation["retailer_chain"],
            observation["evidence_url"],
        )
        groups.setdefault(key, []).append(observation)
    observations = []
    for sources in groups.values():
        statuses = sorted({source["status"] for source in sources})
        observations.append(
            {
                **sources[0],
                "source_observation_ids": [s["observation_id"] for s in sources],
                "aliases": [s["observation_id"] for s in sources[1:]],
                "source_observations": sources,
                "source_statuses": statuses,
                "status": statuses[0] if len(statuses) == 1 else "UNCERTAIN",
                "status_basis": (
                    "All raw observations agree; inspect each source form."
                    if len(statuses) == 1
                    else "Mixed form-specific claims; summary is conservative, "
                    "raw evidence requires explicit source-form review."
                ),
            }
        )
    return {
        "schema_version": 1,
        "status": "RESEARCH_EVIDENCE_NOT_ACCEPTED_CORPUS",
        "method": (
            "Current official product/category plus official SPB/LO chain presence; "
            "no momentary stock claim. AVAILABLE applies only to the observed "
            "product wording, not every source form sharing a FoodIngredient code. "
            "Recipe-specific form matches are in original-corpus-market-review.json. "
            "Missing observations and access failures are UNCERTAIN, not absence. "
            "Exact code/chain/URL duplicates count once; all original IDs, "
            "notes and claims remain in source_observations. Mixed form claims "
            "have an UNCERTAIN summary, never a universal code-level clearance."
        ),
        "baseline_chains": list(CHAINS),
        "observations": observations,
        "counts": {
            "raw_observations": len(raw_observations),
            "observations": len(observations),
            "duplicate_observations": len(raw_observations) - len(observations),
            "available": sum(o["status"] == "AVAILABLE" for o in observations),
            "uncertain": sum(o["status"] == "UNCERTAIN" for o in observations),
            "available_by_chain": {
                chain: sum(
                    o["retailer_chain"] == chain and o["status"] == "AVAILABLE"
                    for o in observations
                )
                for chain in CHAINS
            },
        },
    }


def selected_source_rows(directory: Path = DIRECTORY) -> list[dict]:
    """Flatten reviewed source rows, not compact candidate ingredient summaries."""
    document = read_json(directory / "draft-ingredient-coverage.json")
    rows = []
    source_ids = [r["source_recipe_id"] for r in document["recipes"]]
    if len(source_ids) != len(set(source_ids)):
        raise ValueError("Duplicate source recipe in ingredient audit")
    for recipe in document["recipes"]:
        if recipe.get("unresolved_issues"):
            raise ValueError("Source ingredient audit has unresolved issues")
        if [s["position"] for s in recipe["rows"]] != list(
            range(1, len(recipe["rows"]) + 1)
        ):
            raise ValueError("Source ingredient audit order is not contiguous")
        for source in recipe["rows"]:
            if source["selection"] not in SELECTED | {
                "OMITTED_OPTIONAL",
                "OMITTED_VARIANT",
            }:
                raise ValueError("Unknown source ingredient selection decision")
            if source["selection"] not in SELECTED:
                if source["selected_codes"]:
                    raise ValueError("Omitted source row cannot carry selected codes")
                continue
            if not source["selected_codes"]:
                raise ValueError("Selected source row has no resolved food concept")
            for code in source["selected_codes"]:
                if not nonempty_text(source["quantity_text"]) or (
                    code != "WATER"
                    and not re.search(r"[0-9¼½¾⅛⅜⅝⅞]", source["quantity_text"])
                ):
                    raise ValueError(
                        "Selected food row lacks an explicit source quantity"
                    )
                rows.append(
                    {
                        "source_recipe_id": recipe["source_recipe_id"],
                        "source_ingredient_text": source["source_text"],
                        "normalized_concept": code.lower(),
                        "existing_food_ingredient_code": code,
                        "resolution_status": "RESOLVED_EXISTING",
                        "missing_reason": "",
                        "source_position": source["position"],
                        "source_quantity_text": source["quantity_text"],
                        "ingredient_selection": source["selection"],
                        "normalization_reason": source["normalization_reason"],
                    }
                )
    return rows


def build_final_evidence(directory: Path = DIRECTORY) -> dict[str, str]:
    """Return deterministic final artifacts; fail on missing/ambiguous form review.

    This is an offline serializer of explicit reviews, not a source/rights or
    form-equivalence inference engine. It never writes files or production data.
    """
    source_rows = selected_source_rows(directory)
    forms = read_json(directory / "draft-purchase-form-review.json")["rows"]
    observations = {o["observation_id"]: o for o in normalized_observations(directory)}
    reviews = []
    selected_forms = {}
    for line, source in enumerate(source_rows, 2):
        code = source["existing_food_ingredient_code"]
        review = {
            "coverage_line": line,
            "source_recipe_id": source["source_recipe_id"],
            "food_ingredient_code": code,
            "source_position": source["source_position"],
            "source_quantity_text": source["source_quantity_text"],
            "ingredient_selection": source["ingredient_selection"],
            "normalization_reason": source["normalization_reason"],
            "review_status": "REVIEWED",
        }
        if code == "WATER":
            review.update(
                purchase_concept="Household preparation/cooking water",
                evidence_matches=[],
                market_classification="HOUSEHOLD_WATER",
                retention_reason="Explicit source cooking/preparation water; no "
                "retailer purchase requirement. Preserve source amount/condition.",
            )
            reviews.append(review)
            continue
        matches = [
            form
            for form in forms
            if form["food_ingredient_code"] == code
            and source["source_recipe_id"] in form["recipe_ids"]
        ]
        if len(matches) != 1:
            raise ValueError(f"Missing/ambiguous source-form review at CSV line {line}")
        form = matches[0]
        evidence = [
            {
                "observation_id": ref,
                "purchase_concept": form["purchase_form"],
                "form_match_reviewed": True,
                "rationale": form["review_notes"]
                + " Source normalization: "
                + source["normalization_reason"],
            }
            for ref in form["qualifying_refs"]
        ]
        chains = form_qualified_chains(
            code, form["purchase_form"], evidence, observations
        )
        ordinary = nonempty_text(form.get("ordinary_retail_plausibility"))
        classification = classify_market(chains, ordinary)
        if (
            classification == "SPECIALTY_OR_UNCLEAR"
            or classification != form["classification"]
        ):
            raise ValueError(f"Uncleared source purchase form at CSV line {line}")
        if not nonempty_text(form.get("retention_reason")):
            raise ValueError("Missing source-form retention rationale")
        review.update(
            purchase_form_review_id=form["review_id"],
            purchase_concept=form["purchase_form"],
            evidence_matches=evidence,
            ordinary_retail_plausibility=ordinary,
            ordinary_retail_rationale=form["ordinary_retail_plausibility"],
            market_classification=classification,
            retention_reason=form["retention_reason"],
            chain_review={
                chain: {"status": entry["status"], "basis": entry["note"]}
                for chain, entry in form["five_chain_review"].items()
            },
        )
        selected_forms[form["review_id"]] = form
        reviews.append(review)
    output = StringIO(newline="")
    writer = csv.DictWriter(
        output, fieldnames=CSV_FIELDS, extrasaction="ignore", lineterminator="\n"
    )
    writer.writeheader()
    writer.writerows(source_rows)
    union = sorted({r["existing_food_ingredient_code"] for r in source_rows})
    purchase = {"schema_version": 1, "status": "REVIEWED", "rows": reviews}
    matrix = build_matrix(directory)
    matrix["final_source_forms"] = list(selected_forms.values())
    matrix["final_source_form_classification_counts"] = dict(
        sorted(Counter(f["classification"] for f in selected_forms.values()).items())
    )
    matrix["final_coverage_classification_counts"] = dict(
        sorted(Counter(r["market_classification"] for r in reviews).items())
    )
    matrix["final_scope_note"] = (
        "Explicit reviewed source-form and five-chain records "
        "for final coverage; raw observations remain research evidence, not universal "
        "code-level clearance. No live stock or production retailer integration."
    )
    return {
        "ingredient-coverage.csv": output.getvalue(),
        "mvp0-food-ingredient-codes.txt": "\n".join(union) + "\n",
        "purchase-form-review.json": json.dumps(purchase, ensure_ascii=False, indent=2)
        + "\n",
        "retailer-evidence-matrix.json": json.dumps(
            matrix, ensure_ascii=False, indent=2
        )
        + "\n",
    }


def research_errors(directory: Path = DIRECTORY, root: Path = ROOT) -> list[str]:
    errors = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    for filename in OBSERVATION_FILES:
        require((directory / filename).is_file(), f"Missing research input: {filename}")
        if not (directory / filename).is_file():
            continue
        try:
            document = read_json(directory / filename)
            require(
                document.get("schema_version") in {1, 2},
                f"Unsupported research input schema version: {filename}",
            )
            records = document["observations"]
            if not isinstance(records, list) or not records:
                raise ValueError("observations must be a nonempty list")
            for record in records:
                if not isinstance(record, dict) or not all(
                    nonempty_text(record.get(key))
                    for key in ("region", "checked_at", "status", "notes")
                ):
                    raise ValueError("observation lacks required text fields")
        except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
            errors.append(f"Invalid research input {filename}: {exc}")
    if any(error.startswith("Invalid research input") for error in errors):
        return errors

    with (root / "data/seed/food_ingredients/ingredients.csv").open() as handle:
        codes = {row["canonical_code"] for row in csv.DictReader(handle)}
    with (root / "data/curation/pr4/ingredient-coverage.csv").open() as handle:
        coverage = list(csv.DictReader(handle))
    source_pairs = {
        (
            row["source_recipe_id"],
            row["existing_food_ingredient_code"],
            row["source_ingredient_text"],
        )
        for row in coverage
    }
    source_ids = {row["source_recipe_id"] for row in coverage}
    audit = read_json(directory / "research-candidates.json")
    recipes = audit["all_recipe_form_audit"]
    require(len(recipes) == 30, "Exactly 30 source audits required")
    require({r["recipe_source_id"] for r in recipes} == source_ids, "Audit source IDs")
    checks = [c for r in recipes for c in r["form_checks"]]
    require(len(checks) == 96, "Exactly 96 historical source/form rows required")
    require(
        len(
            {
                (r["recipe_source_id"], c["code"], c["source_text"])
                for r in recipes
                for c in r["form_checks"]
            }
        )
        == 96,
        "Duplicate historical form check",
    )
    classes = Counter(c["form_class"] for c in checks)
    require(dict(classes) == audit["form_class_counts"], "Form-class totals stale")
    for recipe in recipes:
        for check in recipe["form_checks"]:
            require(
                (recipe["recipe_source_id"], check["code"], check["source_text"])
                in source_pairs,
                f"Exact source text/code lost: {recipe['recipe_source_id']}",
            )
            require(
                check["form_class"]
                in {
                    "PURCHASE_FORM_CRITICAL",
                    "PREPARATION_ONLY_OR_NOT_RETAIL_FORM",
                },
                "Unknown form class",
            )
            require(
                bool(check["purchase_concept"] and check["collapse_reason"]),
                "Form rationale missing",
            )
    observations = normalized_observations(directory)
    ids = {o["observation_id"] for o in observations}
    require(len(ids) == len(observations), "Duplicate observation ID")
    for obs in observations:
        require(obs["food_ingredient_code"] in codes, "Unknown observation ingredient")
        require(obs["retailer_chain"] in CHAINS, "Unknown retailer chain")
        require(obs["status"] in {"AVAILABLE", "UNCERTAIN"}, "Unknown evidence status")
        require(
            bool(obs["observed_product_wording"] and obs["evidence_method"]),
            "Missing observation wording/method",
        )
        try:
            date.fromisoformat(obs["checked_at"])
        except (ValueError, TypeError):
            errors.append("Invalid check date")
        if obs["status"] == "AVAILABLE":
            for field in ("evidence_url", "region_evidence_url"):
                require(reviewable_url(obs[field]), f"Missing reviewable {field}")
        require(obs["stock_claim"] is False, "Curation must not imply momentary stock")
    equipment_document = read_json(directory / "source-equipment-audit.json")
    equipment = equipment_document["recipes"]
    require(len(equipment) == 30, "Exactly 30 equipment audits required")
    require(
        sum(len(r["equipment"]) for r in equipment) == 80,
        "Historical equipment count must remain 80",
    )
    require(
        equipment_document["counts"]
        == {
            "historical_sources": 30,
            "initial_equipment_rows": 80,
            "historical_icn_sources": 2,
            "conditional_equipment_rows": 4,
        },
        "Historical equipment count metadata stale",
    )
    require(
        sum(len(r["conditional_equipment"]) for r in equipment) == 4,
        "Historical conditional equipment count must remain 4",
    )
    require(
        {r["recipe_source_id"] for r in equipment} == source_ids, "Equipment source IDs"
    )
    for recipe in equipment:
        require(
            bool(re.fullmatch(r"[a-f0-9]{64}", recipe["source_sha256"])),
            "Missing source hash",
        )
        items = recipe["equipment"]
        require(
            [e["position"] for e in items] == list(range(1, len(items) + 1)),
            "Equipment order",
        )
        require(
            len({e["equipment_code"] for e in items}) == len(items),
            "Duplicate equipment",
        )
        require(
            all(e["evidence_snippet"] and e["source_page"] for e in items),
            "Equipment evidence",
        )
    candidates = []
    candidate_origins = {}
    for filename in (
        "candidate-review-v2.json",
        "candidate-review-v3.json",
        "candidate-review-v4.json",
        "candidate-review-v5.json",
    ):
        candidate_document = read_json(directory / filename)
        revisions = {
            item["candidate_id"]: item
            for item in candidate_document.get("supersedes", [])
        }
        for candidate in candidate_document["candidates"] + candidate_document.get(
            "backup_candidates", []
        ):
            candidate_id = candidate["candidate_id"]
            prior_file = candidate_origins.get(candidate_id)
            if prior_file is not None:
                revision = revisions.get(candidate_id, {})
                require(
                    revision.get("prior_file") == prior_file
                    and nonempty_text(revision.get("reason")),
                    "Duplicate candidate without explicit reviewed revision",
                )
            candidate_origins[candidate_id] = filename
            candidates.append(candidate)
        for screen in candidate_document.get("additional_negative_screens", []):
            require(
                reviewable_url(screen.get("source_url")),
                "Negative screen source missing",
            )
            require(bool(screen.get("reason")), "Negative screen reason missing")
    for candidate in candidates:
        require(
            set(candidate.get("selected_required_codes", [])) <= codes,
            "Candidate adds global ingredient",
        )
    review = read_json(directory / "original-corpus-market-review.json")["recipes"]
    by_id = {o["observation_id"]: o for o in observations}
    require(
        {r["recipe_source_id"] for r in review} == source_ids,
        "Market review source IDs",
    )
    for recipe in review:
        for code, refs in recipe["matching_evidence_by_code"].items():
            require(set(refs) <= ids, "Dangling market observation reference")
            require(
                all(
                    ref not in by_id
                    or (
                        by_id[ref]["status"] == "AVAILABLE"
                        and by_id[ref]["food_ingredient_code"] == code
                    )
                    for ref in refs
                ),
                "Market evidence must be AVAILABLE for the same code",
            )
        for check in recipe["critical_form_checks"]:
            refs = recipe["matching_evidence_by_code"].get(check["code"], [])
            require(
                not (set(refs) & set(check["excluded_code_only"])),
                "Excluded code-only form match reused",
            )
            require(
                not (check["reason"] and refs),
                "Unresolved critical form cannot be cleared by code-only evidence",
            )
            require(
                (check["status"] == "MATCHED") == bool(refs),
                "Critical form match status stale",
            )
    return errors


def corpus_counts(
    recipes: list[dict], source_rows: list[dict], directory: Path
) -> dict:
    draft = read_json(directory / "draft-ingredient-coverage.json")["recipes"]
    equipment = [item for recipe in recipes for item in recipe["equipment"]]
    decisions = Counter(r["selection"]["decision"] for r in recipes)
    with (ROOT / "data/seed/food_ingredients/ingredients.csv").open() as handle:
        global_codes = {r["canonical_code"] for r in csv.DictReader(handle)}
    return {
        "recipes": len(recipes),
        "retained": decisions["KEEP"],
        "replacements": decisions["REPLACE"],
        "source_ingredient_rows": sum(len(r["rows"]) for r in draft),
        "selected_ingredient_rows": len(source_rows),
        "distinct_food_ingredient_codes": len(
            {r["existing_food_ingredient_code"] for r in source_rows}
        ),
        "equipment_rows": len(equipment),
        "distinct_equipment_codes": len({e["equipment_code"] for e in equipment}),
        "unresolved_required_rows": sum(
            r["ingredient_selection"] == "SELECTED_REQUIRED"
            and r["resolution_status"] != "RESOLVED_EXISTING"
            for r in source_rows
        ),
        "new_food_ingredients": len(
            {r["existing_food_ingredient_code"] for r in source_rows} - global_codes
        ),
        **diversity_counts(recipes),
    }


def reviewed_recipe_summaries(directory: Path = DIRECTORY) -> list[dict]:
    """Derive final recipe facts and summaries from reviews, never the manifest.

    The source consistency audit is the human-reviewed input; ingredient and
    market summaries are calculated from the source-row/form joins. Additional
    raw audit notes stay in the review artifact rather than leaking into runtime.
    """
    audited = read_json(directory / "source-consistency-audit.json")["recipes"]
    source_recipes = {
        r["source_recipe_id"]: r
        for r in read_json(directory / "draft-ingredient-coverage.json")["recipes"]
    }
    rows = selected_source_rows(directory)
    forms = json.loads(build_final_evidence(directory)["purchase-form-review.json"])[
        "rows"
    ]
    recipes = []
    for audit in audited:
        recipe_id = audit["recipe_source_id"]
        selected = [r for r in rows if r["source_recipe_id"] == recipe_id]
        reviewed = [r for r in forms if r["source_recipe_id"] == recipe_id]
        concepts = {
            (r["food_ingredient_code"], r.get("purchase_form_review_id")): r[
                "market_classification"
            ]
            for r in reviewed
            if r["ingredient_selection"] == "SELECTED_REQUIRED"
            and r["food_ingredient_code"] != "WATER"
        }
        categories = Counter(concepts.values())
        recipes.append(
            {
                "recipe_source_id": recipe_id,
                **{
                    field: audit[field]
                    for field in SOURCE_FACT_FIELDS + HANDBACK_METADATA_FIELDS
                },
                "source_ingredient_rows": len(source_recipes[recipe_id]["rows"]),
                "selected_ingredient_rows": len(selected),
                "distinct_food_ingredient_codes": sorted(
                    {r["existing_food_ingredient_code"] for r in selected}
                ),
                "market_summary": {
                    "required_concepts": len(concepts),
                    "RU_MASS_MARKET": categories["RU_MASS_MARKET"],
                    "RU_AVAILABLE": categories["RU_AVAILABLE"],
                    "SPECIALTY_OR_UNCLEAR": categories["SPECIALTY_OR_UNCLEAR"],
                    "household_water": len(
                        {
                            r["food_ingredient_code"]
                            for r in reviewed
                            if r["food_ingredient_code"] == "WATER"
                        }
                    ),
                },
            }
        )
    return recipes


def build_final_corpus(directory: Path = DIRECTORY) -> str:
    """Serialize only reviewed handback inputs; no network, database or writes."""
    document = read_json(directory / "source-consistency-audit.json")
    envelope = document["corpus_metadata"]
    if set(envelope) != {
        "schema_version",
        "status",
        "checked_at",
        "base_sha",
        "scope",
        "count_semantics",
    }:
        raise ValueError("Reviewed corpus envelope fields are incomplete or unexpected")
    recipes = reviewed_recipe_summaries(directory)
    corpus = {
        **envelope,
        "counts": corpus_counts(recipes, selected_source_rows(directory), directory),
        "recipes": recipes,
    }
    return json.dumps(corpus, ensure_ascii=False, indent=2) + "\n"


def source_consistency_errors(
    recipes: list[dict], source_rows: list[dict], directory: Path
) -> list[str]:
    """Compare final claims to the independently reviewed primary-source audit."""
    document = read_json(directory / "source-consistency-audit.json")
    audits = document["recipes"]
    ids = [r["recipe_source_id"] for r in audits]
    if (
        document.get("status") != "REVIEWED"
        or len(ids) != len(set(ids))
        or set(ids) != {r["recipe_source_id"] for r in recipes}
    ):
        return ["Source consistency audit must review exactly the final recipes"]
    by_id = {r["recipe_source_id"]: r for r in audits}
    errors = []
    for recipe in recipes:
        recipe_id = recipe["recipe_source_id"]
        audit = by_id[recipe_id]
        for field in SOURCE_FACT_FIELDS:
            if field not in audit or recipe.get(field) != audit[field]:
                errors.append(
                    f"Recipe differs from reviewed source fact {field}: {recipe_id}"
                )
        codes = sorted(
            {
                r["existing_food_ingredient_code"]
                for r in source_rows
                if r["source_recipe_id"] == recipe_id
            }
        )
        if audit.get("selected_ingredient_codes") != codes:
            errors.append(
                f"Source consistency selected concepts differ from ingredient audit: {recipe_id}"
            )
    return errors


def selection_errors(recipes: list[dict], directory: Path, root: Path) -> list[str]:
    decisions = read_json(directory / "replacement-decisions.json")
    with (root / "data/curation/pr4/ingredient-coverage.csv").open() as handle:
        original_ids = {r["source_recipe_id"] for r in csv.DictReader(handle)}
    kept = decisions["kept_source_ids"]
    replacements = decisions["replacements"]
    removed = [r["removed"] for r in replacements]
    added = [r["replacement"] for r in replacements]
    by_id = {r["recipe_source_id"]: r for r in recipes}
    if (
        len(kept) != len(set(kept))
        or len(removed) != len(set(removed))
        or len(added) != len(set(added))
        or set(kept) & set(removed)
        or set(kept) | set(removed) != original_ids
        or set(kept) | set(added) != set(by_id)
        or set(kept) & set(added)
        or any(not nonempty_text(r.get("reason")) for r in replacements)
    ):
        return [
            "Keep/replacement decisions must partition original and final corpus exactly"
        ]
    errors = []
    for recipe_id, recipe in by_id.items():
        expected = "KEEP" if recipe_id in kept else "REPLACE"
        if recipe.get("selection", {}).get("decision") != expected:
            errors.append(
                f"Recipe selection contradicts keep/replacement decision: {recipe_id}"
            )
    return errors


def metadata_errors(
    recipes: list[dict], source_rows: list[dict], reviews: list[dict], directory: Path
) -> list[str]:
    """Cross-check summaries/provenance against reviewed source artifacts."""
    errors = []
    draft = {
        r["source_recipe_id"]: r
        for r in read_json(directory / "draft-ingredient-coverage.json")["recipes"]
    }
    if set(draft) != {r["recipe_source_id"] for r in recipes}:
        errors.append("Ingredient source audit must cover exactly final recipes")
    registry = {
        (r["source_url"], r["sha256"])
        for r in read_json(directory / "source-downloads.json")["documents"]
    }
    registry.update(
        (r["source_url"], r["source_sha256"])
        for r in read_json(directory / "source-equipment-audit.json")["recipes"]
    )
    source_equipment = {
        r["recipe_source_id"]: r
        for r in read_json(directory / "source-equipment-audit.json")["recipes"]
    }
    source_equipment.update(
        {
            r["recipe_source_id"]: r
            for r in read_json(directory / "recipe-review-metadata.json")["recipes"]
        }
    )
    current_audit = directory / "source-consistency-audit.json"
    if current_audit.exists():
        # Final correction-pass review supersedes earlier equipment decisions.
        # Historical audit files remain unchanged and independently tested.
        source_equipment.update(
            {r["recipe_source_id"]: r for r in read_json(current_audit)["recipes"]}
        )
    for recipe in recipes:
        recipe_id = recipe["recipe_source_id"]
        selected = [r for r in source_rows if r["source_recipe_id"] == recipe_id]
        reviewed = [r for r in reviews if r["source_recipe_id"] == recipe_id]
        source = draft[recipe_id]
        if recipe.get("source_limits", []) != source.get("source_limitations", []):
            errors.append(f"Recipe omitted reviewed source limitations: {recipe_id}")
        if (
            recipe["source_url"] != source["source_url"]
            or (recipe["source_url"], recipe["source_sha256"]) not in registry
        ):
            errors.append(f"Source hash/URL is not the reviewed artifact: {recipe_id}")
        if (
            recipe.get("source_ingredient_rows") != len(source["rows"])
            or recipe.get("selected_ingredient_rows") != len(selected)
            or recipe.get("distinct_food_ingredient_codes")
            != sorted({r["existing_food_ingredient_code"] for r in selected})
        ):
            errors.append(
                f"Recipe ingredient summary disagrees with audit: {recipe_id}"
            )
        concepts = {
            (r["food_ingredient_code"], r.get("purchase_form_review_id")): r[
                "market_classification"
            ]
            for r in reviewed
            if r["ingredient_selection"] == "SELECTED_REQUIRED"
            and r["food_ingredient_code"] != "WATER"
        }
        categories = Counter(concepts.values())
        expected_summary = {
            "required_concepts": len(concepts),
            "RU_MASS_MARKET": categories["RU_MASS_MARKET"],
            "RU_AVAILABLE": categories["RU_AVAILABLE"],
            "SPECIALTY_OR_UNCLEAR": categories["SPECIALTY_OR_UNCLEAR"],
            "household_water": len(
                {
                    r["food_ingredient_code"]
                    for r in reviewed
                    if r["food_ingredient_code"] == "WATER"
                }
            ),
        }
        if recipe.get("market_summary") != expected_summary:
            errors.append(f"Recipe market summary disagrees with forms: {recipe_id}")
        equipment = recipe.get("equipment")
        if not isinstance(equipment, list) or not all(
            isinstance(item, dict) for item in equipment
        ):
            errors.append(f"Missing source-backed equipment audit: {recipe_id}")
        elif (
            [e.get("position") for e in equipment] != list(range(1, len(equipment) + 1))
            or len({e.get("equipment_code") for e in equipment}) != len(equipment)
            or any(
                not re.fullmatch(r"[A-Z][A-Z0-9_]*", str(e.get("equipment_code", "")))
                or not nonempty_text(e.get("evidence_snippet"))
                or not nonempty_text(e.get("source_section"))
                for e in equipment
            )
        ):
            errors.append(f"Equipment order/code/source evidence invalid: {recipe_id}")
        elif recipe_id not in source_equipment:
            errors.append(f"Equipment has no reviewed source audit: {recipe_id}")
        else:
            audit = source_equipment[recipe_id]
            expected = audit["equipment"]
            conditionals = audit.get("conditional_equipment", [])
            if [e["equipment_code"] for e in equipment[: len(expected)]] != [
                e["equipment_code"] for e in expected
            ]:
                errors.append(
                    f"Equipment differs from reviewed source order: {recipe_id}"
                )
            for item in equipment:
                matches = [
                    e
                    for e in expected + conditionals
                    if e["equipment_code"] == item["equipment_code"]
                    and e.get("evidence_snippet", e.get("source_words"))
                    == item["evidence_snippet"]
                ]
                if not matches or (
                    matches[0] in conditionals
                    and not nonempty_text(item.get("selection_reason"))
                ):
                    errors.append(f"Equipment not source-backed/selected: {recipe_id}")
        if (
            not nonempty_text(recipe.get("source_attribution"))
            or not nonempty_text(recipe.get("meal_type_code"))
            or not nonempty_text(recipe.get("diversity_contribution"))
            or not isinstance(recipe.get("source_times"), (dict, str))
            or not isinstance(recipe.get("selection"), dict)
            or recipe["selection"].get("decision") not in {"KEEP", "REPLACE"}
            or not nonempty_text(recipe["selection"].get("reason"))
        ):
            errors.append(f"Recipe source/selection metadata incomplete: {recipe_id}")
    return errors


def final_errors(directory: Path = DIRECTORY, root: Path = ROOT) -> list[str]:
    """Validate a final successor, never merely the existence of draft files.

    Final corpus recipes need source hashes and a reviewed rights record with
    basis/evidence URL. Final coverage uses the historical CSV column names.
    Purchase-form review rows key to CSV line numbers (header is line 1) and
    carry explicit reviewed evidence matches consumed by form_qualified_chains.
    Offline checks validate evidence integrity, not the truth of a human review.
    """
    corpus_path = directory / "recipe-corpus.json"
    if not corpus_path.exists():
        return ["No accepted DATA2 successor: exact final 30 and union not established"]
    errors = []
    try:
        corpus = read_json(corpus_path)
        recipes = corpus["recipes"]
        if not isinstance(recipes, list) or not all(
            isinstance(r, dict) for r in recipes
        ):
            raise ValueError("recipes must be a list of objects")
        ids = [r["recipe_source_id"] for r in recipes]
        if not all(nonempty_text(recipe_id) for recipe_id in ids):
            raise ValueError("recipe IDs must be nonempty strings")
    except (OSError, ValueError, TypeError, KeyError) as exc:
        return [f"Invalid final corpus schema: {exc}"]
    if len(ids) != 30 or len(set(ids)) != 30:
        errors.append("Exactly 30 unique recipes required")
    if FORBIDDEN & set(ids):
        errors.append("Forbidden ICN recipe in successor")
    if corpus.get("status") != "READY_FOR_REVIEW":
        errors.append("Successor is not fully reviewed")
    if corpus.get("schema_version") != 1:
        errors.append("Unsupported final corpus schema")
    for recipe in recipes:
        rights = recipe.get("rights_review")
        if not isinstance(rights, dict) or not (
            rights.get("status") == "REVIEWED"
            and nonempty_text(rights.get("basis"))
            and reviewable_url(rights.get("evidence_url"))
        ):
            errors.append(
                f"Missing source-specific reviewed rights: {recipe['recipe_source_id']}"
            )
        if not (
            reviewable_url(recipe.get("source_url"))
            and nonempty_text(recipe.get("recipe_name"))
            and nonempty_text(recipe.get("source_collection"))
            and re.fullmatch(r"[a-f0-9]{64}", str(recipe.get("source_sha256", "")))
            and type(recipe.get("source_servings")) is int
            and recipe["source_servings"] > 0
        ):
            errors.append(
                f"Incomplete final source provenance: {recipe['recipe_source_id']}"
            )
    # A final successor must carry its own row-level resolved coverage and
    # form-qualified matrix. Research-only files cannot satisfy these gates.
    for filename in (
        "ingredient-coverage.csv",
        "mvp0-food-ingredient-codes.txt",
        "purchase-form-review.json",
        "retailer-evidence-matrix.json",
    ):
        if not (directory / filename).exists():
            errors.append(f"Missing final evidence: {filename}")
    if errors:
        return errors
    try:
        with (root / "data/seed/food_ingredients/ingredients.csv").open() as handle:
            global_codes = {row["canonical_code"] for row in csv.DictReader(handle)}
        with (directory / "ingredient-coverage.csv").open() as handle:
            reader = csv.DictReader(handle)
            coverage = list(reader)
            if reader.fieldnames != list(CSV_FIELDS):
                errors.append("Final coverage columns differ from source contract")
        expected_sources = selected_source_rows(directory)
        expected_coverage = [
            {key: row[key] for key in CSV_FIELDS} for row in expected_sources
        ]
        if coverage != expected_coverage:
            errors.append(
                "Final coverage differs from exact selected source audit rows/order"
            )
        if not coverage or {r["source_recipe_id"] for r in coverage} != set(ids):
            errors.append("Final coverage must cover exactly the final 30 recipe IDs")
        food_rows = {}
        for line, row in enumerate(coverage, 2):
            if (
                row["resolution_status"] != "RESOLVED_EXISTING"
                or not row["source_ingredient_text"].strip()
                or row["missing_reason"]
            ):
                errors.append(f"Unresolved or empty final source row: {line}")
            code = row["existing_food_ingredient_code"]
            if code not in global_codes:
                errors.append(f"Final row adds/omits global ingredient: {line}")
            food_rows[line] = row
        union = {r["existing_food_ingredient_code"] for r in food_rows.values()}
        manifest = (
            (directory / "mvp0-food-ingredient-codes.txt").read_text().splitlines()
        )
        if not 80 <= len(union) <= 120 or manifest != sorted(union):
            errors.append("Final manifest must be the exact sorted union 80..120")
        document = read_json(directory / "purchase-form-review.json")
        reviews = document["rows"]
        if document.get("schema_version") != 1 or document.get("status") != "REVIEWED":
            errors.append("Final purchase-form review is not reviewed schema 1")
        lines = [r["coverage_line"] for r in reviews]
        if len(lines) != len(set(lines)) or set(lines) != set(food_rows):
            errors.append(
                "Final purchase-form review must cover each food row exactly once"
            )
        observations = {
            o["observation_id"]: o for o in normalized_observations(directory)
        }
        for filename, expected in build_final_evidence(directory).items():
            if (directory / filename).read_text(encoding="utf-8") != expected:
                errors.append(
                    f"Final artifact not reproducible from reviews: {filename}"
                )
        for review in reviews:
            if type(review.get("coverage_line")) is not int:
                errors.append("Final coverage line must be an integer")
                continue
            row = food_rows.get(review["coverage_line"])
            if (
                not row
                or review.get("source_recipe_id") != row["source_recipe_id"]
                or review.get("food_ingredient_code")
                != row["existing_food_ingredient_code"]
            ):
                errors.append("Final source-row review identity mismatch")
                continue
            expected_source = expected_sources[review["coverage_line"] - 2]
            if any(
                review.get(key) != expected_source[key]
                for key in (
                    "source_position",
                    "source_quantity_text",
                    "ingredient_selection",
                    "normalization_reason",
                )
            ):
                errors.append("Final review lost source quantity/optionality crosswalk")
            if review.get("review_status") != "REVIEWED" or not review.get(
                "purchase_concept"
            ):
                errors.append("Final source purchase concept not reviewed")
            code = review["food_ingredient_code"]
            if (
                code == "WATER"
                and review.get("market_classification") == "HOUSEHOLD_WATER"
                and review.get("retention_reason")
            ):
                continue
            chains = form_qualified_chains(
                code,
                review["purchase_concept"],
                review["evidence_matches"],
                observations,
            )
            classification = classify_market(
                chains, review.get("ordinary_retail_plausibility") is True
            )
            if classification == "SPECIALTY_OR_UNCLEAR" or classification != review.get(
                "market_classification"
            ):
                errors.append("Final source row fails market classification")
            if (
                classification == "RU_AVAILABLE"
                and not str(review.get("retention_reason", "")).strip()
            ):
                errors.append("RU_AVAILABLE needs a specific retention reason")
            panel = review.get("chain_review", {})
            if set(panel) != set(CHAINS) or any(
                not isinstance(v, dict)
                or v.get("status") not in {"AVAILABLE", "UNCERTAIN", "NOT_FOUND"}
                or not v.get("basis")
                for v in panel.values()
            ):
                errors.append("Final source row lacks the full five-chain audit")
            elif {
                chain
                for chain, value in panel.items()
                if value["status"] == "AVAILABLE"
            } != chains:
                errors.append(
                    "Five-chain positives disagree with form-qualified evidence"
                )
        errors.extend(metadata_errors(recipes, expected_sources, reviews, directory))
        errors.extend(
            diversity_errors(
                recipes, expected_sources, pr4_meal_type_codes(directory, root)
            )
        )
        errors.extend(source_consistency_errors(recipes, expected_sources, directory))
        errors.extend(selection_errors(recipes, directory, root))
        if corpus.get("counts") != corpus_counts(recipes, expected_sources, directory):
            errors.append("Final corpus counts disagree with reviewed rows/equipment")
        if corpus_path.read_text(encoding="utf-8") != build_final_corpus(directory):
            errors.append(
                "Final corpus not reproducible from reviewed source artifacts"
            )
    except (
        OSError,
        ValueError,
        TypeError,
        KeyError,
        AttributeError,
        IndexError,
    ) as exc:
        errors.append(f"Invalid final evidence schema/review: {exc}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--research", action="store_true", help="Research integrity ONLY"
    )
    parser.add_argument(
        "--matrix", action="store_true", help="Print deterministic research matrix JSON"
    )
    parser.add_argument(
        "--final-evidence",
        action="store_true",
        help="Serialize explicit source/form reviews as artifact-name/content JSON; not rights acceptance",
    )
    parser.add_argument(
        "--final-corpus",
        action="store_true",
        help="Serialize recipe corpus from reviewed source facts and exact source/form joins",
    )
    args = parser.parse_args()
    if args.final_corpus:
        print(build_final_corpus(), end="")
        return 0
    if args.final_evidence:
        print(json.dumps(build_final_evidence(), ensure_ascii=False))
        return 0
    if args.matrix:
        print(json.dumps(build_matrix(), ensure_ascii=False, indent=2))
        return 0
    errors = research_errors()
    if not args.research:
        errors.extend(final_errors())
    for error in errors:
        print(f"FAIL: {error}")
    if not errors:
        print(
            "PASS: research integrity only"
            if args.research
            else "PASS: final DATA2 gates"
        )
    return bool(errors)


if __name__ == "__main__":
    raise SystemExit(main())
