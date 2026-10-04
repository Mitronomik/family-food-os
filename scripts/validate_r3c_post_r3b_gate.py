#!/usr/bin/env python3
"""Validate the frozen R3-C post-R3B Contract Gate package deterministically."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import zipfile
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
EXPECTED_MILK_UNAFFECTED = (
    "HARD_BOILED_EGG",
    "SCHOOL2022_54_1T_COTTAGE_CHEESE_CASSEROLE",
    "SAD28_SANDWICH_CHEESE_20_10",
)
EXPECTED_IDENTITY = "ATLANTIC_SALMON_FILLET_RAW"

RECIPES_MEMBER = "corpus-work/packages/school2022/normalized/recipes.jsonl"
ROWS_MEMBER = "corpus-work/packages/school2022/normalized/published_rows.jsonl"
RECONCILIATION_MEMBER = (
    "corpus-work/packages/school2022/normalized/"
    "published_nutrient_reconciliation.jsonl"
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


def validate_repo_package(repo_root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    package = repo_root / PACKAGE_REL
    frozen = load_json(package / "frozen-batch.json")
    summary = load_json(package / "summary.json")

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

    ingredient_rows = 0
    for row in selected:
        code = row["canonical_code"]
        require(row.get("meal_type_code") == "main", f"{code}: meal_type != main")
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
            require(
                isinstance(ingredient.get("food_code"), str)
                and ingredient["food_code"].strip(),
                f"{code}: ingredient food_code missing",
            )
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

    identities = frozen.get("new_identity_only_foods")
    require(isinstance(identities, list) and len(identities) == 1, "identity count != 1")
    identity = identities[0]
    require(identity.get("canonical_code") == EXPECTED_IDENTITY, "identity changed")
    require(identity.get("nutrition_profile") is None, "Nutrition authority leaked")
    require(identity.get("composition_authority") is None, "Composition authority leaked")

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

    current = summary.get("current_repository_truth")
    require(isinstance(current, dict), "current repository truth missing")
    require(
        current.get("active_exact_energy_by_meal_type")
        == {"breakfast": 17, "main": 15, "sandwich": 1},
        "current meal-type counts changed",
    )
    require(current.get("dc3_active_exact_energy_count") == 33, "current count != 33")
    require(current.get("planner_supported_exact_energy_count") == 33, "Planner count != 33")
    require(current.get("breakfast_compatible_count") == 18, "breakfast-compatible != 18")

    resilience = summary.get("hard_exclusion_resilience")
    require(isinstance(resilience, dict), "exclusion analysis missing")
    milk = resilience.get("MILK_2_5")
    require(isinstance(milk, dict), "MILK_2_5 proof missing")
    require(
        tuple(milk.get("unaffected_breakfast_compatible_codes", ()))
        == EXPECTED_MILK_UNAFFECTED,
        "MILK_2_5 unaffected set changed",
    )
    require(
        milk.get("unaffected_count") == 3 and milk.get("capacity") == 9,
        "MILK_2_5 3/capacity-9 proof changed",
    )

    beef = resilience.get("main_dependency_analysis")
    require(isinstance(beef, dict), "MAIN dependency analysis missing")
    require(beef.get("BEEF_CATEGORY_1_RAW_current_count") == 7, "exact beef count != 7")
    require(beef.get("current_main_count") == 15, "current MAIN count != 15")
    require(
        beef.get("unaffected_after_exact_beef_exclusion") == 8,
        "exact beef exclusion must leave 8 MAIN",
    )
    require(
        beef.get("capacity_after_exact_beef_exclusion") == 24,
        "exact beef exclusion capacity must be 24",
    )

    baseline = summary.get("data_corpus_baseline")
    require(isinstance(baseline, dict), "baseline summary missing")
    require(baseline.get("current_usable_exact_energy") == 33, "baseline current != 33")
    require(baseline.get("gap_to_50") == 17, "baseline gap != 17")
    require(baseline.get("dc4_ready") is False, "DC4 must remain blocked")

    r3c = summary.get("r3c")
    require(isinstance(r3c, dict), "R3-C summary missing")
    require(r3c.get("selected_count") == 8, "summary selected count != 8")
    require(tuple(r3c.get("selected_recipe_codes", ())) == EXPECTED_CODES, "summary set changed")
    require(r3c.get("new_identity_only_foods") == [EXPECTED_IDENTITY], "summary identity changed")

    projected = summary.get("projected_after_future_runtime")
    require(isinstance(projected, dict), "projection missing")
    require(
        projected.get("active_exact_energy_by_meal_type")
        == {"breakfast": 17, "main": 23, "sandwich": 1},
        "projected meal-type counts changed",
    )
    require(projected.get("active_exact_energy_count") == 41, "projection count != 41")
    require(projected.get("gap_to_50_usable") == 9, "projection gap != 9")
    require(projected.get("dc4_ready_after") is False, "projected DC4 must be false")

    return frozen, {
        "selected_recipes": 8,
        "ingredient_rows": ingredient_rows,
        "deferred_or_rejected": len(deferred),
        "current_exact_energy": 33,
        "projected_exact_energy": 41,
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
                    f"source ingredient mapping mismatch: {source_id}: {expected}",
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

            reconciliation = reconciliations.get(
                f"{source_id}:reconcile:energy_kcal"
            )
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
    except (ValidationError, KeyError, zipfile.BadZipFile) as exc:
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
