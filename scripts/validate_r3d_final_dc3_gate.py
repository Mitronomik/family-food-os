"""Validate the R3-D final DC3 Contract Gate against repository/source truth."""

from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import json
import re
import sys
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any

PACKAGE_REL = Path("data/curation/r3d-final-dc3-batch-gate")
R3C_PACKAGE_REL = Path("data/curation/r3c-post-r3b-catalogue-gate")
ACCEPTED_BASE = "1c82f34b960621aed3e1c43780270f8048edfe0f"
MR_BUNDLE_REL = Path("data/seed/ru_normative_recipe_corpus/mr_2_4_0162_19.bundle.json")
MR_BUNDLE_GIT_BLOB_SHA = "9210458b9ad81aa3650eccad7935519f8d375432"
MR_RAW_BYTES_SHA256 = "973acb53eee7a04c76853dff80988a0f9b70e704495b715639cd8a34a747293e"
MR_RAW_TEXT_SHA256 = "b5a05ffb36d34cd7bd82de71b55319d72ac850064302bf228e1e1ad19fd02062"
SCHOOL_ARCHIVE_SHA256 = "c0d90020798b2998e841328b9081f06f8197efda084b852aa8457fd41a5ce8ea"
SCHOOL_PDF_SHA256 = "c9264cf521ae699fb30a964d5668caec8f31ff1efc1f13a3dd055df40ebafb5d"
SCHOOL_PDF_PATH = "corpus-work/packages/school2022/raw/source.pdf"

FISH_CODES = frozenset(
    {
        "COD_FILLET_RAW",
        "PINK_SALMON_FILLET_RAW",
        "POLLOCK_FILLET_RAW",
        "ATLANTIC_SALMON_FILLET_RAW",
    }
)
CHICKEN_CODES = frozenset(
    {
        "CHICKEN_CATEGORY_2_RAW",
        "CHICKEN_BREAST",
        "CHICKEN_CATEGORY_1_WHOLE_RAW",
    }
)
BEEF_CODE = "BEEF_CATEGORY_1_RAW"
MILK_CODE = "MILK_2_5"
ASCII_WORD_RE = re.compile(r"[A-Za-z]{2,}")


class ValidationError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValidationError(f"could not read JSON: {path}") from exc
    require(isinstance(value, dict), f"JSON root must be object: {path}")
    return value


def git_blob_sha(raw: bytes) -> str:
    return hashlib.sha1(f"blob {len(raw)}\0".encode() + raw).hexdigest()


def normalize_number(value: object) -> str:
    return str(value).strip().replace(",", ".")


def simple_constant(path: Path, name: str) -> object:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    values: dict[str, object] = {}
    for _ in range(5):
        changed = False
        for node in tree.body:
            target = None
            value = None
            if isinstance(node, ast.Assign) and len(node.targets) == 1:
                target, value = node.targets[0], node.value
            elif isinstance(node, ast.AnnAssign):
                target, value = node.target, node.value
            if not isinstance(target, ast.Name) or value is None:
                continue

            def resolve(item: ast.AST) -> object | None:
                if isinstance(item, ast.Constant) and isinstance(item.value, (str, int)):
                    return item.value
                if isinstance(item, ast.Name):
                    return values.get(item.id)
                if isinstance(item, (ast.Tuple, ast.List)):
                    resolved = [resolve(child) for child in item.elts]
                    if any(child is None for child in resolved):
                        return None
                    return tuple(resolved)
                return None

            resolved = resolve(value)
            if resolved is not None and values.get(target.id) != resolved:
                values[target.id] = resolved
                changed = True
        if not changed:
            break
    require(name in values, f"{path}: missing constant {name}")
    return values[name]


def load_r3c_validator(repo_root: Path):
    path = repo_root / "scripts/validate_r3c_post_r3b_gate.py"
    spec = importlib.util.spec_from_file_location("r3c_gate_validator", path)
    require(spec is not None and spec.loader is not None, "could not load R3-C validator")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def recipe_ingredient_codes(
    code: str,
    row: dict[str, Any],
) -> tuple[str, ...]:
    direct = row.get("ingredient_codes")
    if isinstance(direct, (tuple, list)) and all(
        isinstance(item, str) and item for item in direct
    ):
        return tuple(direct)

    frozen = row.get("ingredients")
    if isinstance(frozen, list):
        codes = tuple(
            item.get("food_code")
            for item in frozen
            if isinstance(item, dict)
        )
        if len(codes) == len(frozen) and all(
            isinstance(item, str) and item for item in codes
        ):
            return codes

    raise ValidationError(
        f"recipe ingredient-code shape unavailable: {code}"
    )


def derive_current_truth(
    repo_root: Path,
) -> tuple[dict[str, Any], set[str], dict[str, dict[str, Any]]]:
    r3c_validator = load_r3c_validator(repo_root)
    pre, food_codes, recipes = r3c_validator._derive_current_repository_truth(repo_root)

    require(pre["exact_energy_recipe_count"] == 33, "pre-R3C exact-energy count drifted")
    r3c = load_json(repo_root / R3C_PACKAGE_REL / "frozen-batch.json")
    runtime_codes = simple_constant(
        repo_root / "backend/app/seed/r3c_school2022_main_batch.py",
        "RECIPE_CODES",
    )
    require(isinstance(runtime_codes, tuple), "R3-C runtime RECIPE_CODES shape changed")
    frozen_codes = tuple(row["canonical_code"] for row in r3c["selected"])
    require(runtime_codes == frozen_codes, "merged R3-C runtime/frozen set drifted")

    for row in r3c["selected"]:
        code = row["canonical_code"]
        require(code not in recipes, f"duplicate exact-energy code: {code}")
        recipes[code] = {
            "canonical_code": code,
            "meal_type_code": row["meal_type_code"],
            "ingredient_codes": tuple(i["food_code"] for i in row["ingredients"]),
        }
    for identity in r3c["new_identity_only_foods"]:
        food_codes.add(identity["canonical_code"])

    planner_compatibility, max_repetitions = r3c_validator._planner_contract(repo_root)
    supported = frozenset().union(*planner_compatibility.values())
    require(
        all(row["meal_type_code"] in supported for row in recipes.values()),
        "current exact-energy recipe has Planner-unsupported meal type",
    )

    meal_counts = Counter(row["meal_type_code"] for row in recipes.values())
    breakfast_types = planner_compatibility["BREAKFAST"]
    breakfast = {
        code
        for code, row in recipes.items()
        if row["meal_type_code"] in breakfast_types
    }
    milk_dependent = {
        code
        for code in breakfast
        if MILK_CODE in recipe_ingredient_codes(code, recipes[code])
    }
    milk_unaffected = breakfast - milk_dependent

    main = {
        code: row
        for code, row in recipes.items()
        if row["meal_type_code"] == "main"
    }

    def has_any(row: dict[str, Any], codes: frozenset[str]) -> bool:
        return bool(set(recipe_ingredient_codes(row["canonical_code"], row)) & codes)

    beef = {code for code, row in main.items() if BEEF_CODE in recipe_ingredient_codes(code, row)}
    fish = {code for code, row in main.items() if has_any(row, FISH_CODES)}
    chicken = {code for code, row in main.items() if has_any(row, CHICKEN_CODES)}
    meat_free = set(main) - beef - fish - chicken

    require(len(recipes) == 41, "current exact-energy total must be 41")
    require(
        dict(sorted(meal_counts.items()))
        == {"breakfast": 17, "main": 23, "sandwich": 1},
        "current post-R3C meal counts drifted",
    )
    require(len(breakfast) == 18, "breakfast-compatible count must be 18")
    require(
        len(milk_dependent) == 15,
        "MILK_2_5 dependent breakfast count must be 15; "
        f"derived={len(milk_dependent)} codes={sorted(milk_dependent)}",
    )
    require(
        len(milk_unaffected) == 3,
        "MILK_2_5 unaffected set must contain 3; "
        f"derived={len(milk_unaffected)} codes={sorted(milk_unaffected)}",
    )
    require(len(beef) == 12, "current exact beef MAIN count must be 12")
    require(len(fish) == 9, "current fish MAIN count must be 9")
    require(len(chicken) == 2, "current chicken MAIN count must be 2")
    require(len(meat_free) == 0, "current meat-free MAIN count must be 0")

    return (
        {
            "exact_energy_count": len(recipes),
            "meal_counts": dict(sorted(meal_counts.items())),
            "breakfast_compatible_count": len(breakfast),
            "max_recipe_repetitions": max_repetitions,
            "milk_dependent_count": len(milk_dependent),
            "milk_unaffected_codes": sorted(milk_unaffected),
            "milk_unaffected_count": len(milk_unaffected),
            "milk_unaffected_capacity": len(milk_unaffected) * max_repetitions,
            "main_count": len(main),
            "beef_main_count": len(beef),
            "fish_main_count": len(fish),
            "chicken_main_count": len(chicken),
            "meat_free_main_count": len(meat_free),
            "beef_or_fish_count": len(beef | fish),
            "accepted_food_code_count": len(food_codes),
            "supported_meal_types": sorted(supported),
        },
        food_codes,
        recipes,
    )


def parse_mr_12_plus(card: dict[str, Any]) -> tuple[dict[str, list[str]], str]:
    raw = card["raw_card_text"]
    lines = [line.strip() for line in raw.splitlines() if line.strip()]
    try:
        start = lines.index("12 лет и старше") + 1
        end = lines.index("Выход готовой продукции", start)
    except ValueError as exc:
        raise ValidationError(
            f"MR card table markers missing: {card['source_card_code']}"
        ) from exc

    rows: dict[str, list[str]] = {}
    index = start
    while index < end:
        require(index + 3 < end + 1, f"MR ingredient row truncated: {card['source_card_code']}")
        label = lines[index]
        values = lines[index + 1 : index + 4]
        require(len(values) == 3, f"MR ingredient quantities missing: {label}")
        rows.setdefault(label, []).append(normalize_number(values[2]))
        index += 4
    require(index == end, f"MR ingredient table shape changed: {card['source_card_code']}")

    output_values = lines[end + 1 : end + 4]
    require(len(output_values) == 3, f"MR output row missing: {card['source_card_code']}")
    return rows, normalize_number(output_values[2])


def verify_mr_nutrition_row(card: dict[str, Any], frozen: dict[str, Any]) -> None:
    raw_lines = [line.strip() for line in card["raw_card_text"].splitlines() if line.strip()]
    try:
        start = next(
            i for i, line in enumerate(raw_lines) if line.startswith("Сведения о пищевой")
        )
    except StopIteration as exc:
        raise ValidationError(
            f"MR nutrition section missing: {card['source_card_code']}"
        ) from exc
    expected = [
        frozen["source_output_g"],
        frozen["source_nutrition_row"]["protein_g"],
        frozen["source_nutrition_row"]["fat_g"],
        frozen["source_nutrition_row"]["carbohydrate_g"],
        frozen["energy_kcal"],
    ]
    normalized = [normalize_number(line) for line in raw_lines[start:]]
    found = any(
        normalized[i : i + 5] == expected
        for i in range(0, max(0, len(normalized) - 4))
    )
    require(found, f"MR 12+ output/macros/ENERGY row mismatch: {card['source_card_code']}")


def validate_selected_source(
    repo_root: Path,
    frozen: dict[str, Any],
) -> dict[str, Any]:
    bundle_path = repo_root / MR_BUNDLE_REL
    raw = bundle_path.read_bytes()
    require(git_blob_sha(raw) == MR_BUNDLE_GIT_BLOB_SHA, "MR bundle Git blob drifted")
    bundle = json.loads(raw)
    require(isinstance(bundle, dict), "MR bundle root changed")
    document = bundle.get("document")
    cards = bundle.get("cards")
    require(isinstance(document, dict) and isinstance(cards, list), "MR bundle shape changed")
    require(document.get("raw_bytes_sha256") == MR_RAW_BYTES_SHA256, "MR raw bytes receipt drifted")
    require(document.get("raw_text_sha256") == MR_RAW_TEXT_SHA256, "MR raw text receipt drifted")
    require(document.get("publication_policy") == "NORMATIVE_BASE_RECIPE_APPROVED", "MR publication policy drifted")

    by_key = {
        (card.get("source_section_code"), card.get("source_card_code")): card
        for card in cards
        if isinstance(card, dict)
    }
    selected = frozen["selected"]
    for row in selected:
        key = (row["source_section_code"], row["source_card_code"])
        card = by_key.get(key)
        require(card is not None, f"selected MR card missing: {key}")
        raw_card = card.get("raw_card_text")
        require(isinstance(raw_card, str) and raw_card, f"raw card missing: {key}")
        recomputed = hashlib.sha256(raw_card.encode("utf-8")).hexdigest()
        require(recomputed == card.get("raw_card_sha256"), f"MR card self-hash mismatch: {key}")
        require(recomputed == row["source_card_raw_sha256"], f"frozen MR card hash mismatch: {key}")
        rows, output = parse_mr_12_plus(card)
        require(output == row["source_output_g"], f"MR output mismatch: {key}")
        for ingredient in row["ingredients"]:
            values = rows.get(ingredient["source_label"])
            require(values is not None, f"MR source label missing: {key}: {ingredient['source_label']}")
            require(
                ingredient["quantity_g"] in values,
                f"MR source quantity mismatch: {key}: {ingredient['source_label']}",
            )
        verify_mr_nutrition_row(card, row)
        technology = card.get("technology_text_ru")
        require(isinstance(technology, str) and technology.strip(), f"MR technology missing: {key}")

    return {
        "mr_bundle_git_blob_sha": MR_BUNDLE_GIT_BLOB_SHA,
        "mr_selected_cards_verified": len(selected),
        "mr_raw_card_hashes": f"{len(selected)}/{len(selected)}",
        "mr_output_energy_rows": f"{len(selected)}/{len(selected)}",
    }


def validate_gate(repo_root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    package = repo_root / PACKAGE_REL
    frozen = load_json(package / "frozen-batch.json")
    audit = load_json(package / "candidate-audit.json")
    summary = load_json(package / "summary.json")
    source_receipt = load_json(package / "source-verification.json")

    require(frozen.get("schema_version") == 1, "frozen schema changed")
    require(frozen.get("operation") == "R3D_FINAL_DC3_FROZEN_BATCH_CONTRACT", "frozen operation changed")
    require(frozen.get("accepted_base") == ACCEPTED_BASE, "accepted base changed")
    require(frozen.get("issue") == 157, "issue binding changed")
    require(frozen.get("status") == "PREFLIGHT_FROZEN_FOR_GATE", "gate status changed")

    current, current_food_codes, current_recipes = derive_current_truth(repo_root)
    selected = frozen.get("selected")
    require(isinstance(selected, list) and len(selected) == 10, "R3-D selected_count must be 10")
    codes = tuple(row.get("canonical_code") for row in selected)
    source_keys = tuple((row.get("source_section_code"), row.get("source_card_code")) for row in selected)
    require(len(set(codes)) == len(codes), "selected canonical codes are not unique")
    require(len(set(source_keys)) == len(source_keys), "selected source cards are not unique")
    require(all(code not in current_recipes for code in codes), "selected recipe already exists in current exact-energy set")

    identities = frozen.get("new_identity_only_foods")
    require(isinstance(identities, list) and len(identities) == 10, "expected 10 identity-only foods")
    identity_codes = {row["canonical_code"] for row in identities}
    require(not identity_codes & current_food_codes, "R3-D identity-only code already exists")
    for row in identities:
        require(row.get("nutrition_profile") is None, f"Nutrition authority leaked: {row['canonical_code']}")
        require(row.get("nutrient_vector_authority") is None, f"NutrientVector authority leaked: {row['canonical_code']}")
        require(row.get("composition_authority") is None, f"Composition authority leaked: {row['canonical_code']}")

    compatibility, max_repetitions = load_r3c_validator(repo_root)._planner_contract(repo_root)
    supported = frozenset().union(*compatibility.values())
    selected_food_codes: set[str] = set()
    for row in selected:
        require(row.get("meal_type_code") == "main", f"selected meal type is not main: {row.get('canonical_code')}")
        require(row["meal_type_code"] in supported, f"Planner does not support selected meal type: {row['canonical_code']}")
        require(row.get("source_variant") == "12_PLUS", f"source variant drifted: {row['canonical_code']}")
        require(row.get("source_output_g") and row.get("energy_kcal"), f"output/energy missing: {row['canonical_code']}")
        steps = row.get("consumer_steps_ru")
        require(isinstance(steps, list) and steps, f"consumer steps missing: {row['canonical_code']}")
        require(
            all(isinstance(step, str) and step.strip() and ASCII_WORD_RE.search(step) is None for step in steps),
            f"consumer step contains non-Russian engineering token: {row['canonical_code']}",
        )
        binding = row.get("process_binding")
        require(
            isinstance(binding, dict) and str(binding.get("status", "")).startswith("PASS_"),
            f"process binding not PASS: {row['canonical_code']}",
        )
        ingredients = row.get("ingredients")
        require(isinstance(ingredients, list) and ingredients, f"ingredients missing: {row['canonical_code']}")
        for ingredient in ingredients:
            food_code = ingredient.get("food_code")
            require(isinstance(food_code, str) and food_code, f"food mapping missing: {row['canonical_code']}")
            selected_food_codes.add(food_code)

    missing = selected_food_codes - current_food_codes
    require(missing == identity_codes, f"R3-D mapping completeness mismatch; missing={sorted(missing)}")
    require(identity_codes <= selected_food_codes, "unused new identity-only food")

    audit_rows = audit.get("reviewed_not_selected")
    require(isinstance(audit_rows, list) and audit_rows, "candidate audit missing")
    rejected_keys = {
        (row.get("source"), row.get("card"))
        for row in audit_rows
    }
    require(
        not any(("RU_MR_2_4_0162_19", f"APPENDIX_5_CARD_{card}") in rejected_keys for _, card in source_keys),
        "selected/reviewed-not-selected source overlap",
    )
    require(audit.get("decision", {}).get("milk_free_breakfast_result") == "NO_NEW_SOURCE_CLEAN_CANDIDATE", "milk-free breakfast disposition changed")

    source_stats = validate_selected_source(repo_root, frozen)

    selected_beef = sum(
        1 for row in selected if BEEF_CODE in {i["food_code"] for i in row["ingredients"]}
    )
    selected_fish = sum(
        1 for row in selected if set(i["food_code"] for i in row["ingredients"]) & FISH_CODES
    )
    selected_chicken = sum(
        1 for row in selected if set(i["food_code"] for i in row["ingredients"]) & CHICKEN_CODES
    )
    selected_meat_free = len(selected) - selected_beef - selected_fish - selected_chicken
    require(
        (selected_meat_free, selected_chicken, selected_beef, selected_fish)
        == (6, 2, 2, 0),
        "R3-D product mix drifted",
    )

    projected_total = current["exact_energy_count"] + len(selected)
    projected_main = current["main_count"] + len(selected)
    projected_beef = current["beef_main_count"] + selected_beef
    projected_fish = current["fish_main_count"] + selected_fish
    projected_chicken = current["chicken_main_count"] + selected_chicken
    projected_meat_free = current["meat_free_main_count"] + selected_meat_free
    projected_beef_unaffected = projected_main - projected_beef

    require(projected_total == 51, "projected usable total must be 51")
    require(projected_total >= 50, "R3-D does not cross lower usable baseline")
    require(projected_main == 33, "projected MAIN count must be 33")
    require(projected_beef == 14, "projected beef MAIN count must be 14")
    require(projected_fish == 9, "projected fish MAIN count must be 9")
    require(projected_chicken == 4, "projected chicken MAIN count must be 4")
    require(projected_meat_free == 6, "projected meat-free MAIN count must be 6")
    require(projected_beef_unaffected == 19, "projected exact-beef unaffected MAIN must be 19")
    require(projected_beef_unaffected * max_repetitions == 57, "projected exact-beef capacity must be 57")

    expected_milk = {
        "HARD_BOILED_EGG",
        "SCHOOL2022_54_1T_COTTAGE_CHEESE_CASSEROLE",
        "SAD28_SANDWICH_CHEESE_20_10",
    }
    require(set(current["milk_unaffected_codes"]) == expected_milk, "MILK_2_5 unaffected set drifted")
    require(current["milk_unaffected_capacity"] == 9, "MILK_2_5 capacity drifted")

    current_summary = summary.get("current_repository_truth")
    projected_summary = summary.get("projected_after_future_runtime")
    r3d_summary = summary.get("r3d")
    require(isinstance(current_summary, dict) and isinstance(projected_summary, dict) and isinstance(r3d_summary, dict), "summary sections missing")
    require(current_summary.get("active_exact_energy_count") == current["exact_energy_count"], "summary current total is self-inconsistent")
    require(current_summary.get("by_meal_type") == current["meal_counts"], "summary current meal counts differ from repo truth")
    require(current_summary.get("breakfast_compatible_count") == current["breakfast_compatible_count"], "summary breakfast compatibility differs from repo truth")
    require(current_summary.get("gap_to_50") == 50 - current["exact_energy_count"], "summary current gap differs from repo truth")
    require(r3d_summary.get("selected_count") == len(selected), "summary selected count mismatch")
    require(projected_summary.get("active_exact_energy_count") == projected_total, "summary projection total mismatch")
    require(projected_summary.get("by_meal_type") == {"breakfast": 17, "main": 33, "sandwich": 1}, "summary projected meal counts mismatch")
    require(projected_summary.get("gap_to_50") == 0, "summary projected gap-to-50 mismatch")
    require(projected_summary.get("dc4_next_planned_operation") is True, "DC4 handoff must be next planned operation")
    require(projected_summary.get("no_further_discretionary_dc3_expansion") is True, "further discretionary DC3 must be false")

    require(source_receipt.get("selected_source", {}).get("selected_card_count") == len(selected), "source receipt selected count mismatch")
    require(source_receipt.get("school2022_gap_audit", {}).get("result") == "NO_SOURCE_CLEAN_IN_SCOPE_MILK_FREE_BREAKFAST", "School2022 gap receipt changed")

    return frozen, {
        "status": "PASS",
        "current_exact_energy": current["exact_energy_count"],
        "current_meal_counts": current["meal_counts"],
        "current_food_code_count": current["accepted_food_code_count"],
        "current_breakfast_compatible": current["breakfast_compatible_count"],
        "current_milk_unaffected": current["milk_unaffected_count"],
        "current_milk_capacity": current["milk_unaffected_capacity"],
        "current_beef_main": current["beef_main_count"],
        "current_fish_main": current["fish_main_count"],
        "selected_count": len(selected),
        "new_identity_only_count": len(identities),
        "selected_mix": {
            "meat_free": selected_meat_free,
            "chicken": selected_chicken,
            "beef": selected_beef,
            "fish": selected_fish,
        },
        "projected_exact_energy": projected_total,
        "projected_main": projected_main,
        "projected_beef_main": projected_beef,
        "projected_fish_main": projected_fish,
        "projected_chicken_main": projected_chicken,
        "projected_meat_free_main": projected_meat_free,
        "projected_beef_unaffected": projected_beef_unaffected,
        "projected_beef_capacity": projected_beef_unaffected * max_repetitions,
        "gap_to_50": 50 - projected_total,
        "dc4_next": True,
        **source_stats,
    }


def verify_school_archive(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == SCHOOL_ARCHIVE_SHA256, "School archive SHA-256 mismatch")
    with zipfile.ZipFile(path) as archive:
        pdf = archive.read(SCHOOL_PDF_PATH)
        require(hashlib.sha256(pdf).hexdigest() == SCHOOL_PDF_SHA256, "School PDF SHA-256 mismatch")
        recipes = [
            json.loads(line)
            for line in archive.read(
                "corpus-work/packages/school2022/normalized/recipes.jsonl"
            ).decode("utf-8").splitlines()
            if line.strip()
        ]
        rows = [
            json.loads(line)
            for line in archive.read(
                "corpus-work/packages/school2022/normalized/published_rows.jsonl"
            ).decode("utf-8").splitlines()
            if line.strip()
        ]
    by_id = {row["id"]: row for row in recipes}

    def quantified_labels(recipe_id: str) -> set[str]:
        return {
            row["payload"]["source_label"]
            for row in rows
            if row.get("payload", {}).get("recipe_id") == recipe_id
            and row.get("payload", {}).get("role") == "ingredient_or_intermediate"
            and row.get("payload", {}).get("quantities", {}).get("net_mass_g", {}).get("resolved_quantity") is not None
        }

    r3t = by_id["ru-school2022:recipe:54-3т"]["payload"]
    require("сахар-песок" in quantified_labels("ru-school2022:recipe:54-3т"), "54-3т sugar row missing")
    require("сахар" not in r3t["process_text"].casefold(), "54-3т sugar unexpectedly placed")

    for card in ("54-4т", "54-6т"):
        rid = f"ru-school2022:recipe:{card}"
        payload = by_id[rid]["payload"]
        labels = quantified_labels(rid)
        require("ванилин" in labels, f"{card} vanillin row missing")
        require("горячей воде" in payload["process_text"].casefold(), f"{card} hot-water process missing")
        require("вода" not in labels, f"{card} unexpectedly has quantified water")

    r5t = by_id["ru-school2022:recipe:54-5т"]["payload"]
    labels5 = quantified_labels("ru-school2022:recipe:54-5т")
    require("масло подсолнечное" in labels5, "54-5т sunflower-oil row missing")
    require("сливочным маслом" in r5t["process_text"].casefold(), "54-5т butter process conflict missing")

    r7t = by_id["ru-school2022:recipe:54-7т"]["payload"]
    require(r7t.get("specialized_medical_scope") is True, "54-7т medical scope flag changed")

    return {
        "school_archive_checks": "PASS",
        "school_archive_bytes": len(raw),
        "school_archive_sha256": SCHOOL_ARCHIVE_SHA256,
        "school_pdf_bytes": len(pdf),
        "school_pdf_sha256": SCHOOL_PDF_SHA256,
        "milk_free_breakfast_blockers_verified": 5,
    }


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
    )
    result.add_argument("--school-archive", type=Path)
    result.add_argument("--json", action="store_true")
    return result


def main() -> int:
    args = parser().parse_args()
    try:
        _, result = validate_gate(args.repo_root.resolve())
        if args.school_archive is not None:
            result.update(verify_school_archive(args.school_archive.resolve()))
        else:
            result["school_archive_checks"] = "NOT_RUN"
            result["school_archive_note"] = (
                "selected R3-D recipes use the repo-retained MR bundle; "
                "supply --school-archive only to reproduce the rejected milk-free "
                "School2022 candidate audit"
            )
    except (ValidationError, KeyError, OSError, SyntaxError, ValueError, zipfile.BadZipFile) as exc:
        payload = {"status": "FAIL", "error": str(exc)}
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        else:
            print(f"R3-D gate validator: FAIL: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    else:
        print("R3-D gate validator: PASS")
        for key, value in result.items():
            print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
