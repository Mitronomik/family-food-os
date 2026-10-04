#!/usr/bin/env python3
"""Validate the frozen R3-C post-R3B Contract Gate package deterministically."""

from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import json
import re
import sys
import zipfile
from collections import Counter
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

PACKAGE_REL = Path("data/curation/r3c-post-r3b-catalogue-gate")
EXPECTED_BASE = "90c4f0ebab693b01ec5b4cf7b93b67feeaf0ddb4"
EXPECTED_CODES = (
    "SCHOOL2022_54_21M_BOILED_CHICKEN",
    "SCHOOL2022_54_3M_LAZY_CABBAGE_ROLLS",
    "SCHOOL2022_54_26M_POTATO_BEEF_CASSEROLE",
    "SCHOOL2022_54_1M_BOILED_BEEF_STROGANOFF",
    "SCHOOL2022_54_30M_BEEF_RICE_QUENELLES",
    "SCHOOL2022_54_20M_BOILED_BEEF",
    "SCHOOL2022_54_15R_SALMON_IN_MILK",
    "SCHOOL2022_54_17R_SALMON_TOMATO_VEGETABLES",
)
EXPECTED_MILK_UNAFFECTED = frozenset(
    {
        "HARD_BOILED_EGG",
        "SCHOOL2022_54_1T_COTTAGE_CHEESE_CASSEROLE",
        "SAD28_SANDWICH_CHEESE_20_10",
    }
)
EXPECTED_IDENTITY = "ATLANTIC_SALMON_FILLET_RAW"

RECIPES_MEMBER = "corpus-work/packages/school2022/normalized/recipes.jsonl"
ROWS_MEMBER = "corpus-work/packages/school2022/normalized/published_rows.jsonl"
RECONCILIATION_MEMBER = (
    "corpus-work/packages/school2022/normalized/"
    "published_nutrient_reconciliation.jsonl"
)

CURRENT_RUNTIME_BATCHES = (
    {
        "name": "R1-H",
        "module": "backend/app/seed/r1h_school2022_main.py",
        "constant": "RECIPE_CODES",
        "package": (
            "data/curation/r1g-catalogue-capacity-expansion/"
            "prepared-publication-specs.json"
        ),
        "activation_marker": "activate_prepared_recipe",
    },
    {
        "name": "R2",
        "module": "backend/app/seed/r2_breakfast_capacity.py",
        "constant": "RECIPE_CODES",
        "package": "data/curation/r2-breakfast-capacity/publication-specs.json",
        "activation_marker": "activate_prepared_recipe",
    },
    {
        "name": "R2-B",
        "module": "backend/app/seed/r2b_fish_main_diversity.py",
        "constant": "RECIPE_CODES",
        "package": "data/curation/r2b-fish-main-diversity/publication-specs.json",
        "activation_marker": "activate_prepared_recipe",
    },
    {
        "name": "R2-C",
        "module": "backend/app/seed/r2c_breakfast_grain_diversity.py",
        "constant": "RECIPE_CODES",
        "package": "data/curation/r2c-breakfast-grain-diversity/publication-specs.json",
        "activation_marker": "activate_prepared_recipe",
    },
    {
        "name": "R2-E",
        "module": "backend/app/seed/r2e_cottage_casserole.py",
        "constant": "CASSEROLE_RECIPE_CODE",
        "package": "data/curation/r2e-cottage-casserole/publication-specs.json",
        "activation_marker": "activate_prepared_recipe",
    },
    {
        "name": "R2-F",
        "module": "backend/app/seed/r2f_cheese_sandwich.py",
        "constant": "CHEESE_SANDWICH_RECIPE_CODE",
        "package": "data/curation/r2f-sandwich-resilience/publication-specs.json",
        "activation_marker": "activate_prepared_recipe",
    },
    {
        "name": "R3-A",
        "module": "backend/app/seed/r3a_school2022_main_batch.py",
        "constant": "RECIPE_CODES",
        "package": "data/curation/r3a-school2022-main-batch/publication-specs.json",
        "activation_marker": "activate_prepared_recipe_batch",
    },
    {
        "name": "R3-B",
        "module": "backend/app/seed/r3b_school2022_breakfast_batch.py",
        "constant": "RECIPE_CODES",
        "package": "data/curation/r3b-school2022-breakfast-batch/publication-specs.json",
        "activation_marker": "activate_prepared_recipe_batch",
    },
)

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
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


def canonical_sha256(value: Any) -> str:
    raw = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def positive_decimal(value: object, label: str) -> Decimal:
    require(isinstance(value, str) and value, f"{label} must be text")
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise ValidationError(f"{label} must be Decimal") from exc
    require(parsed.is_finite() and parsed > 0, f"{label} must be positive")
    return parsed


def require_sha(value: object, label: str) -> None:
    require(
        isinstance(value, str) and SHA256_RE.fullmatch(value) is not None,
        f"{label} must be lowercase SHA-256",
    )


def _simple_constants(path: Path) -> dict[str, object]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    values: dict[str, object] = {}

    def resolve(node: ast.AST) -> object | None:
        if isinstance(node, ast.Constant) and isinstance(node.value, (str, int)):
            return node.value
        if isinstance(node, ast.Name):
            return values.get(node.id)
        if isinstance(node, (ast.Tuple, ast.List)):
            items = [resolve(item) for item in node.elts]
            if any(item is None for item in items):
                return None
            return tuple(items)
        return None

    pending = [
        node
        for node in tree.body
        if isinstance(node, (ast.Assign, ast.AnnAssign))
    ]
    for _ in range(4):
        changed = False
        for node in pending:
            target = (
                node.targets[0]
                if isinstance(node, ast.Assign) and len(node.targets) == 1
                else node.target
                if isinstance(node, ast.AnnAssign)
                else None
            )
            value_node = node.value
            if not isinstance(target, ast.Name) or value_node is None:
                continue
            resolved = resolve(value_node)
            if resolved is not None and values.get(target.id) != resolved:
                values[target.id] = resolved
                changed = True
        if not changed:
            break
    return values


def _runtime_codes(module_path: Path, constant: str) -> tuple[str, ...]:
    values = _simple_constants(module_path)
    require(constant in values, f"{module_path}: missing {constant}")
    raw = values[constant]
    if isinstance(raw, str):
        return (raw,)
    require(
        isinstance(raw, tuple) and all(isinstance(item, str) for item in raw),
        f"{module_path}: {constant} is not a string/tuple of strings",
    )
    return tuple(raw)


def _recipe_record_from_payload(row: dict[str, Any]) -> dict[str, Any]:
    trusted = row.get("trusted_recipe_seed")
    if isinstance(trusted, dict):
        return trusted
    return row


def _package_recipe_records(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if isinstance(payload.get("recipes"), dict):
        result = {}
        for key, raw in payload["recipes"].items():
            require(isinstance(raw, dict), f"recipe payload not object: {key}")
            recipe = _recipe_record_from_payload(raw)
            code = recipe.get("canonical_code")
            require(code == key, f"recipe key/canonical_code mismatch: {key}")
            result[key] = recipe
        return result
    if isinstance(payload.get("recipe"), dict):
        recipe = _recipe_record_from_payload(payload["recipe"])
        code = recipe.get("canonical_code")
        require(isinstance(code, str) and code, "single recipe canonical_code missing")
        return {code: recipe}
    raise ValidationError("publication package has no recipe/recipes payload")


def _extract_r1f(repo_root: Path) -> dict[str, dict[str, Any]]:
    path = repo_root / "backend/app/seed/r1f_prepared_output.py"
    text = path.read_text(encoding="utf-8")
    require("activate_prepared_recipe" in text, "R1-F activation seam missing")
    constants = _simple_constants(path)
    tree = ast.parse(text, filename=str(path))

    def resolve_string(node: ast.AST) -> str:
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        if isinstance(node, ast.Name):
            value = constants.get(node.id)
            if isinstance(value, str):
                return value
        raise ValidationError("R1-F seed contains unresolved string expression")

    def keyword(call: ast.Call, name: str) -> ast.AST:
        for item in call.keywords:
            if item.arg == name:
                return item.value
        raise ValidationError(f"R1-F seed missing keyword: {name}")

    result: dict[str, dict[str, Any]] = {}
    for node in ast.walk(tree):
        if not (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "TrustedRecipeSeed"
        ):
            continue
        code = resolve_string(keyword(node, "canonical_code"))
        version_node = keyword(node, "version")
        require(
            isinstance(version_node, ast.Call)
            and isinstance(version_node.func, ast.Name)
            and version_node.func.id == "TrustedRecipeVersionSeed",
            f"R1-F {code}: version is not TrustedRecipeVersionSeed",
        )
        meal_type = resolve_string(keyword(version_node, "meal_type_code"))
        ingredients_node = keyword(version_node, "ingredients")
        require(
            isinstance(ingredients_node, (ast.Tuple, ast.List)),
            f"R1-F {code}: ingredients are not literal tuple/list",
        )
        ingredients = []
        for ingredient_node in ingredients_node.elts:
            require(
                isinstance(ingredient_node, ast.Call)
                and isinstance(ingredient_node.func, ast.Name)
                and ingredient_node.func.id == "TrustedRecipeIngredientSeed",
                f"R1-F {code}: ingredient seed shape changed",
            )
            ingredients.append(
                resolve_string(keyword(ingredient_node, "food_ingredient_code"))
            )
        result[code] = {
            "canonical_code": code,
            "meal_type_code": meal_type,
            "ingredient_codes": tuple(ingredients),
        }

    expected = {
        constants.get("EGG_RECIPE_CODE"),
        constants.get("CHICKEN_RECIPE_CODE"),
    }
    require(set(result) == expected, "R1-F exact recipe set changed")
    return result


def _load_current_exact_energy_catalogue(
    repo_root: Path,
) -> tuple[dict[str, dict[str, Any]], set[str]]:
    recipes = _extract_r1f(repo_root)
    accepted_food_codes = {
        ingredient
        for row in recipes.values()
        for ingredient in row["ingredient_codes"]
    }

    for batch in CURRENT_RUNTIME_BATCHES:
        module_path = repo_root / batch["module"]
        module_text = module_path.read_text(encoding="utf-8")
        require(
            batch["activation_marker"] in module_text,
            f"{batch['name']}: activation seam missing",
        )
        runtime_codes = _runtime_codes(module_path, batch["constant"])
        package = load_json(repo_root / batch["package"])
        package_recipes = _package_recipe_records(package)
        require(
            set(runtime_codes) == set(package_recipes),
            f"{batch['name']}: runtime/package recipe set mismatch",
        )
        for code in runtime_codes:
            require(code not in recipes, f"duplicate accepted exact-energy recipe: {code}")
            recipe = package_recipes[code]
            version = recipe.get("version")
            require(isinstance(version, dict), f"{batch['name']} {code}: version missing")
            require(
                version.get("verification_status") == "SOURCE_VERIFIED",
                f"{batch['name']} {code}: not SOURCE_VERIFIED",
            )
            meal_type = version.get("meal_type_code")
            require(isinstance(meal_type, str), f"{batch['name']} {code}: meal type missing")
            ingredient_rows = version.get("ingredients")
            require(
                isinstance(ingredient_rows, list) and ingredient_rows,
                f"{batch['name']} {code}: ingredient list missing",
            )
            ingredient_codes = tuple(
                row.get("food_ingredient_code")
                for row in ingredient_rows
                if isinstance(row, dict)
            )
            require(
                len(ingredient_codes) == len(ingredient_rows)
                and all(isinstance(item, str) and item for item in ingredient_codes),
                f"{batch['name']} {code}: ingredient mapping incomplete",
            )

            prepared = (
                package.get("recipe", {}).get("prepared_spec")
                if "recipe" in package
                else package_recipes[code]
                if "prepared_spec" in package_recipes[code]
                else package.get("recipes", {}).get(code, {}).get("prepared_spec")
            )
            if not isinstance(prepared, dict):
                raw = package.get("recipes", {}).get(code)
                if isinstance(raw, dict):
                    prepared = raw.get("prepared_spec")
            require(isinstance(prepared, dict), f"{batch['name']} {code}: prepared spec missing")
            require(
                prepared.get("recipe_code") == code,
                f"{batch['name']} {code}: prepared recipe_code mismatch",
            )
            available = prepared.get("expected_available_amounts")
            require(
                isinstance(available, list)
                and len(available) == 1
                and available[0][0] == "ENERGY_KCAL",
                f"{batch['name']} {code}: exact-energy authority missing",
            )

            recipes[code] = {
                "canonical_code": code,
                "meal_type_code": meal_type,
                "ingredient_codes": ingredient_codes,
            }
            accepted_food_codes.update(ingredient_codes)

    base_path = repo_root / "data/seed/food_ingredients/ingredients.csv"
    try:
        with base_path.open(encoding="utf-8", newline="") as handle:
            base_rows = list(csv.DictReader(handle))
    except (OSError, UnicodeError, csv.Error) as exc:
        raise ValidationError(f"could not read base food seed: {base_path}") from exc
    base_codes = {
        row.get("canonical_code", "").strip()
        for row in base_rows
        if row.get("canonical_code", "").strip()
    }
    require(base_codes, "base FoodIngredient universe is empty")
    accepted_food_codes.update(base_codes)
    return recipes, accepted_food_codes


def _planner_contract(repo_root: Path) -> tuple[dict[str, frozenset[str]], int]:
    food_types_path = repo_root / "backend/app/domain/food_recipes.py"
    food_tree = ast.parse(
        food_types_path.read_text(encoding="utf-8"),
        filename=str(food_types_path),
    )
    meal_values: dict[str, str] = {}
    for node in food_tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "MealTypeCode":
            for item in node.body:
                if (
                    isinstance(item, ast.Assign)
                    and len(item.targets) == 1
                    and isinstance(item.targets[0], ast.Name)
                    and isinstance(item.value, ast.Constant)
                    and isinstance(item.value.value, str)
                ):
                    meal_values[item.targets[0].id] = item.value.value
    require(meal_values, "MealTypeCode enum could not be derived")

    planner_path = repo_root / "backend/app/domain/planner.py"
    tree = ast.parse(
        planner_path.read_text(encoding="utf-8"),
        filename=str(planner_path),
    )
    compatibility: dict[str, frozenset[str]] | None = None
    max_repetitions: int | None = None

    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "PlannerConfig":
            for item in node.body:
                if (
                    isinstance(item, ast.AnnAssign)
                    and isinstance(item.target, ast.Name)
                    and item.target.id == "max_recipe_repetitions"
                    and isinstance(item.value, ast.Constant)
                    and isinstance(item.value.value, int)
                ):
                    max_repetitions = item.value.value

        target = None
        value = None
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target, value = node.targets[0], node.value
        elif isinstance(node, ast.AnnAssign):
            target, value = node.target, node.value
        if not (
            isinstance(target, ast.Name)
            and target.id == "ROLE_COMPATIBILITY_V1"
            and isinstance(value, ast.Dict)
        ):
            continue

        parsed: dict[str, frozenset[str]] = {}
        for key, raw_value in zip(value.keys, value.values, strict=True):
            require(
                isinstance(key, ast.Attribute)
                and isinstance(key.value, ast.Name)
                and key.value.id == "MealRole",
                "ROLE_COMPATIBILITY_V1 key shape changed",
            )
            require(
                isinstance(raw_value, ast.Call)
                and isinstance(raw_value.func, ast.Name)
                and raw_value.func.id == "frozenset"
                and len(raw_value.args) == 1
                and isinstance(raw_value.args[0], ast.Set),
                "ROLE_COMPATIBILITY_V1 value shape changed",
            )
            names = []
            for element in raw_value.args[0].elts:
                require(
                    isinstance(element, ast.Attribute)
                    and isinstance(element.value, ast.Name)
                    and element.value.id == "MealTypeCode",
                    "ROLE_COMPATIBILITY_V1 MealTypeCode shape changed",
                )
                require(
                    element.attr in meal_values,
                    f"unknown MealTypeCode in Planner contract: {element.attr}",
                )
                names.append(meal_values[element.attr])
            parsed[key.attr] = frozenset(names)
        compatibility = parsed

    require(compatibility is not None, "ROLE_COMPATIBILITY_V1 could not be derived")
    require(
        isinstance(max_repetitions, int) and max_repetitions > 0,
        "Planner max_recipe_repetitions could not be derived",
    )
    return compatibility, max_repetitions


def _derive_current_repository_truth(
    repo_root: Path,
) -> tuple[dict[str, Any], set[str], dict[str, dict[str, Any]]]:
    recipes, accepted_food_codes = _load_current_exact_energy_catalogue(repo_root)
    compatibility, max_repetitions = _planner_contract(repo_root)

    supported_meal_types = frozenset().union(*compatibility.values())
    require(
        all(row["meal_type_code"] in supported_meal_types for row in recipes.values()),
        "accepted exact-energy set contains Planner-unsupported meal type",
    )

    meal_counts = Counter(row["meal_type_code"] for row in recipes.values())
    breakfast_types = compatibility.get("BREAKFAST")
    require(breakfast_types is not None, "Planner BREAKFAST compatibility missing")
    breakfast_codes = {
        code
        for code, row in recipes.items()
        if row["meal_type_code"] in breakfast_types
    }
    milk_dependent_breakfast = {
        code
        for code in breakfast_codes
        if "MILK_2_5" in row_ingredients(recipes[code])
    }
    milk_unaffected = breakfast_codes - milk_dependent_breakfast

    main_codes = {
        code for code, row in recipes.items() if row["meal_type_code"] == "main"
    }
    beef_dependent_main = {
        code
        for code in main_codes
        if "BEEF_CATEGORY_1_RAW" in row_ingredients(recipes[code])
    }
    beef_unaffected_main = main_codes - beef_dependent_main

    exact_codes_sorted = sorted(recipes)
    return (
        {
            "exact_energy_recipe_count": len(recipes),
            "exact_energy_recipe_codes_sha256": sha256(
                "\n".join(exact_codes_sorted).encode("utf-8")
            ),
            "meal_type_counts": dict(sorted(meal_counts.items())),
            "breakfast_compatible_count": len(breakfast_codes),
            "milk_dependent_breakfast_count": len(milk_dependent_breakfast),
            "milk_unaffected_breakfast_codes": sorted(milk_unaffected),
            "milk_unaffected_breakfast_count": len(milk_unaffected),
            "milk_unaffected_breakfast_capacity": (
                len(milk_unaffected) * max_repetitions
            ),
            "main_count": len(main_codes),
            "beef_dependent_main_count": len(beef_dependent_main),
            "beef_unaffected_main_count": len(beef_unaffected_main),
            "beef_unaffected_main_capacity": (
                len(beef_unaffected_main) * max_repetitions
            ),
            "max_recipe_repetitions": max_repetitions,
            "planner_supported_meal_types": sorted(supported_meal_types),
            "breakfast_compatible_meal_types": sorted(breakfast_types),
            "accepted_food_code_count": len(accepted_food_codes),
        },
        accepted_food_codes,
        recipes,
    )


def row_ingredients(row: dict[str, Any]) -> frozenset[str]:
    return frozenset(row["ingredient_codes"])


def load_jsonl(archive: zipfile.ZipFile, member: str) -> list[dict[str, Any]]:
    try:
        text = archive.read(member).decode("utf-8")
    except (KeyError, UnicodeDecodeError) as exc:
        raise ValidationError(f"could not read archive member: {member}") from exc
    rows = []
    for number, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValidationError(f"invalid JSONL: {member}:{number}") from exc
        require(isinstance(row, dict), f"JSONL row must be object: {member}:{number}")
        rows.append(row)
    return rows


def validate_repo_package(
    repo_root: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    package = repo_root / PACKAGE_REL
    frozen = load_json(package / "frozen-batch.json")
    summary = load_json(package / "summary.json")
    derived, accepted_food_codes, current_recipes = _derive_current_repository_truth(
        repo_root
    )

    require(frozen.get("schema_version") == 1, "frozen schema changed")
    require(
        frozen.get("operation") == "R3C_POST_R3B_FROZEN_BATCH_CONTRACT",
        "frozen operation changed",
    )
    require(frozen.get("accepted_base") == EXPECTED_BASE, "accepted base changed")
    require(frozen.get("issue") == 153, "issue binding changed")
    require(frozen.get("status") == "FROZEN_FOR_GATE_REVIEW", "status changed")

    selected = frozen.get("selected")
    require(isinstance(selected, list) and len(selected) == 8, "expected 8 selected")
    codes = tuple(row.get("canonical_code") for row in selected)
    source_ids = tuple(row.get("source_recipe_id") for row in selected)
    require(codes == EXPECTED_CODES, "selected recipe set/order changed")
    require(len(set(codes)) == 8, "selected recipe codes are not unique")
    require(len(set(source_ids)) == 8, "selected source IDs are not unique")

    identities = frozen.get("new_identity_only_foods")
    require(isinstance(identities, list) and len(identities) == 1, "identity count != 1")
    identity = identities[0]
    require(identity.get("canonical_code") == EXPECTED_IDENTITY, "identity changed")
    require(identity.get("nutrition_profile") is None, "Nutrition authority leaked")
    require(identity.get("composition_authority") is None, "Composition authority leaked")
    new_identity_codes = {EXPECTED_IDENTITY}
    require(
        EXPECTED_IDENTITY not in accepted_food_codes,
        "new R3-C identity already exists in accepted current FoodIngredient universe",
    )

    compatibility, _ = _planner_contract(repo_root)
    supported_meal_types = frozenset().union(*compatibility.values())

    mapped_food_codes: set[str] = set()
    ingredient_rows = 0
    for row in selected:
        code = row["canonical_code"]
        meal_type = row.get("meal_type_code")
        require(meal_type == "main", f"{code}: meal_type != main")
        require(
            meal_type in supported_meal_types,
            f"{code}: meal_type unsupported by current ROLE_COMPATIBILITY_V1",
        )
        require(
            row.get("household_applicability") == "REVIEWED_PASS",
            f"{code}: household applicability not reviewed pass",
        )
        process = row.get("process_binding")
        require(
            isinstance(process, dict)
            and str(process.get("status", "")).startswith("PASS_"),
            f"{code}: process binding not PASS",
        )
        positive_decimal(row.get("source_output_g"), f"{code}.source_output_g")
        positive_decimal(row.get("energy_kcal"), f"{code}.energy_kcal")

        prepared = row.get("prepared_authority")
        require(isinstance(prepared, dict), f"{code}: prepared authority missing")
        require(
            prepared.get("authority_kind") == "PREPARED_OUTPUT_V1",
            f"{code}: authority kind changed",
        )
        require(
            prepared.get("calculation_version")
            == "RECIPE_PREPARED_OUTPUT_NUTRITION_V1",
            f"{code}: calculation version changed",
        )
        require(
            prepared.get("available") == {"ENERGY_KCAL": row.get("energy_kcal")},
            f"{code}: prepared ENERGY_KCAL mismatch",
        )

        for field in (
            "source_card_canonical_json_sha256",
            "source_process_text_sha256",
            "source_output_row_canonical_json_sha256",
            "energy_reconciliation_canonical_json_sha256",
        ):
            require_sha(row.get(field), f"{code}.{field}")

        ingredients = row.get("ingredients")
        require(isinstance(ingredients, list) and ingredients, f"{code}: no ingredients")
        ingredient_rows += len(ingredients)
        for ingredient in ingredients:
            require(
                isinstance(ingredient.get("source_label"), str)
                and ingredient["source_label"].strip(),
                f"{code}: ingredient source_label missing",
            )
            food_code = ingredient.get("food_code")
            require(
                isinstance(food_code, str) and food_code.strip(),
                f"{code}: ingredient food_code missing",
            )
            mapped_food_codes.add(food_code)
            positive_decimal(ingredient.get("gross_g"), f"{code}.ingredient.gross_g")
            positive_decimal(ingredient.get("net_g"), f"{code}.ingredient.net_g")

        steps = row.get("consumer_steps_ru")
        require(isinstance(steps, list) and steps, f"{code}: consumer steps missing")
        for step in steps:
            require(isinstance(step, str) and step.strip(), f"{code}: empty step")
            require(
                ASCII_WORD_RE.search(step) is None,
                f"{code}: consumer step contains internal English token",
            )

    missing_from_current = mapped_food_codes - accepted_food_codes
    require(
        missing_from_current == new_identity_codes,
        "selected ingredient mapping references unknown current FoodIngredient code(s): "
        f"{sorted(missing_from_current)}",
    )

    deferred = frozen.get("deferred_or_rejected")
    require(isinstance(deferred, list) and deferred, "deferred inventory missing")
    deferred_ids = {row.get("source_recipe_id") for row in deferred}
    require(not (set(source_ids) & deferred_ids), "selected/deferred overlap")

    source = frozen.get("source")
    require(isinstance(source, dict), "source receipt missing")
    require_sha(source.get("source_archive_sha256"), "archive hash")
    require_sha(source.get("source_pdf_sha256"), "PDF hash")
    require(source.get("source_archive_size_bytes") == 206692075, "archive size changed")
    require(source.get("source_pdf_size_bytes") == 4102547, "PDF size changed")

    require(
        derived["exact_energy_recipe_count"] == 33,
        "derived current exact-energy recipe count != 33",
    )
    require(
        derived["meal_type_counts"]
        == {"breakfast": 17, "main": 15, "sandwich": 1},
        "derived current meal-type counts changed",
    )
    require(
        derived["breakfast_compatible_count"] == 18,
        "derived breakfast-compatible count != 18",
    )
    require(
        derived["milk_unaffected_breakfast_count"] == 3
        and derived["milk_unaffected_breakfast_capacity"] == 9,
        "derived MILK_2_5 unaffected 3/capacity-9 proof changed",
    )
    require(
        frozenset(derived["milk_unaffected_breakfast_codes"])
        == EXPECTED_MILK_UNAFFECTED,
        "derived MILK_2_5 unaffected set changed",
    )
    require(
        derived["beef_dependent_main_count"] == 7
        and derived["main_count"] == 15
        and derived["beef_unaffected_main_count"] == 8
        and derived["beef_unaffected_main_capacity"] == 24,
        "derived exact-beef exclusion proof changed",
    )

    current = summary.get("current_repository_truth")
    require(isinstance(current, dict), "current repository truth missing")
    require(
        current.get("active_exact_energy_by_meal_type")
        == derived["meal_type_counts"],
        "summary current meal-type counts differ from repository-derived truth",
    )
    require(
        current.get("dc3_active_exact_energy_count")
        == derived["exact_energy_recipe_count"],
        "summary current count differs from repository-derived truth",
    )
    require(
        current.get("planner_supported_exact_energy_count")
        == derived["exact_energy_recipe_count"],
        "summary Planner count differs from repository-derived truth",
    )
    require(
        current.get("breakfast_compatible_count")
        == derived["breakfast_compatible_count"],
        "summary breakfast-compatible count differs from Planner contract",
    )
    require(
        current.get("max_recipe_repetitions") == derived["max_recipe_repetitions"],
        "summary repetition limit differs from PlannerConfig",
    )

    resilience = summary.get("hard_exclusion_resilience")
    require(isinstance(resilience, dict), "exclusion analysis missing")
    milk = resilience.get("MILK_2_5")
    require(isinstance(milk, dict), "MILK_2_5 proof missing")
    require(
        milk.get("dependent_breakfast_count")
        == derived["milk_dependent_breakfast_count"],
        "summary MILK_2_5 dependent count differs from repository truth",
    )
    require(
        frozenset(milk.get("unaffected_breakfast_compatible_codes", ()))
        == frozenset(derived["milk_unaffected_breakfast_codes"]),
        "summary MILK_2_5 unaffected set differs from repository truth",
    )
    require(
        milk.get("unaffected_count") == derived["milk_unaffected_breakfast_count"]
        and milk.get("capacity") == derived["milk_unaffected_breakfast_capacity"],
        "summary MILK_2_5 capacity differs from repository truth",
    )

    beef = resilience.get("main_dependency_analysis")
    require(isinstance(beef, dict), "MAIN dependency analysis missing")
    require(
        beef.get("BEEF_CATEGORY_1_RAW_current_count")
        == derived["beef_dependent_main_count"],
        "summary exact-beef count differs from repository truth",
    )
    require(
        beef.get("current_main_count") == derived["main_count"],
        "summary MAIN count differs from repository truth",
    )
    require(
        beef.get("unaffected_after_exact_beef_exclusion")
        == derived["beef_unaffected_main_count"],
        "summary exact-beef unaffected count differs from repository truth",
    )
    require(
        beef.get("capacity_after_exact_beef_exclusion")
        == derived["beef_unaffected_main_capacity"],
        "summary exact-beef capacity differs from repository truth",
    )

    baseline = summary.get("data_corpus_baseline")
    require(isinstance(baseline, dict), "baseline summary missing")
    require(
        baseline.get("current_usable_exact_energy")
        == derived["exact_energy_recipe_count"],
        "baseline current count differs from repository truth",
    )
    require(
        baseline.get("gap_to_50") == 50 - derived["exact_energy_recipe_count"],
        "baseline gap differs from repository truth",
    )
    require(baseline.get("dc4_ready") is False, "DC4 must remain blocked")

    r3c = summary.get("r3c")
    require(isinstance(r3c, dict), "R3-C summary missing")
    require(r3c.get("selected_count") == 8, "summary selected count != 8")
    require(tuple(r3c.get("selected_recipe_codes", ())) == EXPECTED_CODES, "summary set changed")
    require(r3c.get("new_identity_only_foods") == [EXPECTED_IDENTITY], "summary identity changed")

    projected = summary.get("projected_after_future_runtime")
    require(isinstance(projected, dict), "projection missing")
    projected_meal_counts = dict(derived["meal_type_counts"])
    projected_meal_counts["main"] += len(selected)
    projected_count = derived["exact_energy_recipe_count"] + len(selected)
    require(
        projected.get("active_exact_energy_by_meal_type") == projected_meal_counts,
        "projected meal-type counts are not derived from current repository truth",
    )
    require(
        projected.get("active_exact_energy_count") == projected_count,
        "projected exact-energy count is not derived from current repository truth",
    )
    require(
        projected.get("gap_to_50_usable") == 50 - projected_count,
        "projected gap-to-50 is not derived from current repository truth",
    )
    require(projected.get("dc4_ready_after") is False, "projected DC4 must be false")

    return frozen, {
        "selected_recipes": 8,
        "ingredient_rows": ingredient_rows,
        "deferred_or_rejected": len(deferred),
        "accepted_food_code_count": derived["accepted_food_code_count"],
        "current_exact_energy": derived["exact_energy_recipe_count"],
        "current_exact_energy_codes_sha256": derived[
            "exact_energy_recipe_codes_sha256"
        ],
        "current_meal_type_counts": derived["meal_type_counts"],
        "breakfast_compatible": derived["breakfast_compatible_count"],
        "milk_dependent_breakfast": derived["milk_dependent_breakfast_count"],
        "milk_unaffected_breakfast": derived["milk_unaffected_breakfast_count"],
        "beef_dependent_main": derived["beef_dependent_main_count"],
        "beef_unaffected_main": derived["beef_unaffected_main_count"],
        "projected_exact_energy": projected_count,
        "planner_supported_meal_types": derived["planner_supported_meal_types"],
        "breakfast_compatible_meal_types": derived[
            "breakfast_compatible_meal_types"
        ],
        "current_exact_energy_recipe_codes": sorted(current_recipes),
    }


def validate_source_archive(
    archive_path: Path, frozen: dict[str, Any]
) -> dict[str, Any]:
    require(archive_path.is_file(), f"source archive missing: {archive_path}")
    source = frozen["source"]
    archive_raw = archive_path.read_bytes()
    require(len(archive_raw) == source["source_archive_size_bytes"], "archive size mismatch")
    require(sha256(archive_raw) == source["source_archive_sha256"], "archive hash mismatch")

    with zipfile.ZipFile(archive_path) as archive:
        pdf_raw = archive.read(source["source_pdf_archive_path"])
        require(len(pdf_raw) == source["source_pdf_size_bytes"], "PDF size mismatch")
        require(sha256(pdf_raw) == source["source_pdf_sha256"], "PDF hash mismatch")

        recipes = {row.get("id"): row for row in load_jsonl(archive, RECIPES_MEMBER)}
        rows = load_jsonl(archive, ROWS_MEMBER)
        reconciliations = {
            row.get("id"): row for row in load_jsonl(archive, RECONCILIATION_MEMBER)
        }

        hash_checks = 0
        mapped_rows = 0
        for selected in frozen["selected"]:
            source_id = selected["source_recipe_id"]
            recipe = recipes.get(source_id)
            require(recipe is not None, f"source recipe missing: {source_id}")
            require(
                canonical_sha256(recipe)
                == selected["source_card_canonical_json_sha256"],
                f"source-card hash mismatch: {source_id}",
            )
            hash_checks += 1

            process_text = recipe.get("payload", {}).get("process_text")
            require(isinstance(process_text, str), f"process text missing: {source_id}")
            require(
                sha256(process_text.encode("utf-8"))
                == selected["source_process_text_sha256"],
                f"process hash mismatch: {source_id}",
            )
            hash_checks += 1

            quantity_rows = [
                row
                for row in rows
                if row.get("payload", {}).get("recipe_id") == source_id
                and row.get("payload", {}).get("role") == "ingredient_or_intermediate"
                and row.get("payload", {})
                .get("quantities", {})
                .get("net_mass_g", {})
                .get("resolved_quantity")
                is not None
            ]
            require(
                len(quantity_rows) == len(selected["ingredients"]),
                f"ingredient-row count mismatch: {source_id}",
            )
            available = {
                (
                    row["payload"].get("source_label"),
                    row["payload"]["quantities"]
                    .get("gross_mass_g", {})
                    .get("resolved_quantity"),
                    row["payload"]["quantities"]["net_mass_g"]["resolved_quantity"],
                )
                for row in quantity_rows
            }
            for ingredient in selected["ingredients"]:
                expected = (
                    ingredient["source_label"],
                    ingredient["gross_g"],
                    ingredient["net_g"],
                )
                require(
                    expected in available,
                    f"source ingredient row mismatch: {source_id}: {expected}",
                )
                mapped_rows += 1

            output_rows = [
                row
                for row in rows
                if row.get("payload", {}).get("recipe_id") == source_id
                and row.get("payload", {}).get("role") == "output"
                and row.get("payload", {})
                .get("values", {})
                .get("energy_kcal", {})
                .get("value")
                is not None
            ]
            require(len(output_rows) == 1, f"quantified output row count != 1: {source_id}")
            output_row = output_rows[0]
            require(
                canonical_sha256(output_row)
                == selected["source_output_row_canonical_json_sha256"],
                f"output-row hash mismatch: {source_id}",
            )
            hash_checks += 1
            payload = output_row["payload"]
            require(
                payload["quantities"]["net_mass_g"]["resolved_quantity"]
                == selected["source_output_g"],
                f"output mass mismatch: {source_id}",
            )
            require(
                payload["values"]["energy_kcal"]["value"] == selected["energy_kcal"],
                f"output ENERGY_KCAL mismatch: {source_id}",
            )

            reconciliation = reconciliations.get(f"{source_id}:reconcile:energy_kcal")
            require(reconciliation is not None, f"energy reconciliation missing: {source_id}")
            require(
                canonical_sha256(reconciliation)
                == selected["energy_reconciliation_canonical_json_sha256"],
                f"energy reconciliation hash mismatch: {source_id}",
            )
            hash_checks += 1
            require(
                reconciliation.get("payload", {}).get("published_output")
                == selected["energy_kcal"],
                f"reconciled ENERGY_KCAL mismatch: {source_id}",
            )

    require(hash_checks == 32, "expected 32/32 frozen source hashes")
    return {
        "archive_bytes": len(archive_raw),
        "archive_sha256": source["source_archive_sha256"],
        "pdf_bytes": source["source_pdf_size_bytes"],
        "pdf_sha256": source["source_pdf_sha256"],
        "frozen_source_hashes": "32/32",
        "source_ingredient_rows": mapped_rows,
    }


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
    )
    mode = result.add_mutually_exclusive_group(required=True)
    mode.add_argument("--source-archive", type=Path)
    mode.add_argument("--repo-only", action="store_true")
    result.add_argument("--json", action="store_true")
    return result


def main() -> int:
    args = parser().parse_args()
    try:
        frozen, stats = validate_repo_package(args.repo_root.resolve())
        result: dict[str, Any] = {"status": "PASS", "repo_checks": "PASS", **stats}
        if args.source_archive is not None:
            result["source_archive_checks"] = "PASS"
            result.update(validate_source_archive(args.source_archive.resolve(), frozen))
        else:
            result["source_archive_checks"] = "NOT_RUN"
            result["source_archive_note"] = (
                "rerun with --source-archive to recompute ZIP/PDF and all 32 hashes"
            )
    except (ValidationError, KeyError, OSError, SyntaxError, zipfile.BadZipFile) as exc:
        payload = {"status": "FAIL", "error": str(exc)}
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        else:
            print(f"R3-C gate validator: FAIL: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    else:
        print("R3-C gate validator: PASS")
        for key, value in result.items():
            if key != "status":
                print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
