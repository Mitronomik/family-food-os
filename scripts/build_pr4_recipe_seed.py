"""Compile the accepted PR4-DATA2 corpus into the deterministic Recipe seed.

This is an offline curation compiler. It performs no network access and never
parses source websites at runtime. Recipe identities, ingredient selections,
servings, metadata, equipment, rights review and accepted source hashes come
from the merged PR4-DATA2 evidence. Ordered directions come from the reviewed
PR4 runtime-step curation file.
"""

from __future__ import annotations

import json
import re
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA2 = ROOT / "data/curation/pr4-data2"
CORPUS = DATA2 / "recipe-corpus.json"
COVERAGE = DATA2 / "draft-ingredient-coverage.json"
STEP_CURATION = ROOT / "data/curation/pr4-runtime/recipe-steps.json"
OUTPUT = ROOT / "data/seed/recipes"
VERIFIED_AT = "2026-09-05T16:06:13+00:00"
SOURCE_NAME = "USDA_FNS"
EXPECTED_RECIPE_COUNT = 30
EXPECTED_INGREDIENT_ROWS = 189
EXPECTED_EQUIPMENT_ROWS = 86
EXPECTED_FOOD_INGREDIENT_CODES = 81
EXPECTED_STEP_ROWS = 169

HISTORICAL_RETRIEVED_AT = {
    "CACFP6-CORN-EDAMAME-BLEND": "2026-09-04T04:35:40.896467+00:00",
    "CACFP6-TABBOULEH": "2026-09-04T04:35:52.082224+00:00",
    "CACFP6-CREAMY-COLESLAW": "2026-09-04T04:34:53.373753+00:00",
}

FRACTIONS = {
    "¼": Decimal("0.25"),
    "½": Decimal("0.5"),
    "¾": Decimal("0.75"),
    "⅓": Decimal("0.333333333333"),
    "⅔": Decimal("0.666666666667"),
    "⅛": Decimal("0.125"),
    "⅜": Decimal("0.375"),
    "⅝": Decimal("0.625"),
    "⅞": Decimal("0.875"),
    "⅕": Decimal("0.2"),
    "⅖": Decimal("0.4"),
    "⅗": Decimal("0.6"),
    "⅘": Decimal("0.8"),
    "⅙": Decimal("0.166666666667"),
    "⅚": Decimal("0.833333333333"),
}
NUMBER = r"(?:\d+(?:\.\d+)?(?:\s*[¼½¾⅓⅔⅛⅜⅝⅞⅕⅖⅗⅘⅙⅚])?|[¼½¾⅓⅔⅛⅜⅝⅞⅕⅖⅗⅘⅙⅚]|\d+\s*/\s*\d+)"
OUNCE_GRAMS = Decimal("28.349523125")
POUND_GRAMS = Decimal("453.59237")
VOLUME_ML = {
    "tsp": Decimal(5),
    "teaspoon": Decimal(5),
    "teaspoons": Decimal(5),
    "tbsp": Decimal(15),
    "tablespoon": Decimal(15),
    "tablespoons": Decimal(15),
    "cup": Decimal(240),
    "cups": Decimal(240),
    "qt": Decimal(960),
    "quart": Decimal(960),
    "quarts": Decimal(960),
}


def _json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"Expected object in {path}")
    return value


def _decimal_text(value: Decimal) -> str:
    return format(value.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP), "f")


def _number(raw: str) -> Decimal:
    value = raw.strip()
    if "/" in value:
        numerator, denominator = value.replace(" ", "").split("/", 1)
        return Decimal(numerator) / Decimal(denominator)
    for glyph, fraction in FRACTIONS.items():
        if glyph in value:
            whole = value.replace(glyph, "").strip()
            return (Decimal(whole) if whole else Decimal(0)) + fraction
    return Decimal(value)


def _normalize_quantity(
    row: dict[str, object],
) -> tuple[str, str, str, bool, str | None]:
    source = str(row["source_text"])
    quantity_text = str(row.get("quantity_text") or source)
    selection = str(row["selection"])
    optional = selection != "SELECTED_REQUIRED"

    if selection == "SELECTED_CONDITIONAL":
        return (
            "30.000000",
            "ml",
            "Conditional source range is 1–2 tablespoons (15–30 ml) only if vegetables start to brown; quantity stores the source-explicit upper bound for deterministic planning.",
            True,
            "Use only if vegetables start to brown; source permits 1–2 tablespoons of water.",
        )

    weight = re.search(
        rf"(?P<number>{NUMBER})\s*(?P<unit>lb|lbs|pounds?|oz|ounces?)\b",
        source,
        re.IGNORECASE,
    )
    if weight:
        amount = _number(weight.group("number"))
        unit = weight.group("unit").casefold()
        total = amount * (
            POUND_GRAMS if unit.startswith(("lb", "pound")) else OUNCE_GRAMS
        )
        if unit.startswith(("lb", "pound")):
            tail = source[weight.end() :]
            ounces = re.match(
                rf"\s*(?P<number>{NUMBER})\s*(?:oz|ounces?)\b", tail, re.IGNORECASE
            )
            if ounces:
                total += _number(ounces.group("number")) * OUNCE_GRAMS
        return (
            _decimal_text(total),
            "g",
            "Converted source avoirdupois weight to grams using exact pound/ounce constants.",
            optional,
            None,
        )

    for candidate in (quantity_text, source):
        matches = list(
            re.finditer(
                rf"(?P<number>{NUMBER})\s*(?P<unit>tsp|teaspoons?|tbsp|tablespoons?|cups?|qt|quarts?)\b",
                candidate,
                re.IGNORECASE,
            )
        )
        if matches:
            values = [
                _number(match.group("number"))
                * VOLUME_ML[match.group("unit").casefold()]
                for match in matches
            ]
            total = (
                sum(values, Decimal(0))
                if (" plus " in candidate.casefold() or " and " in candidate.casefold())
                else values[0]
            )
            return (
                _decimal_text(total),
                "ml",
                "Converted source US recipe volume using 1 cup=240 ml, 1 Tbsp=15 ml, 1 tsp=5 ml, 1 qt=960 ml.",
                optional,
                None,
            )

    for candidate in (quantity_text, source):
        count = re.search(
            rf"(?<!\d)(?P<number>{NUMBER})\s*(?:slices?|eggs?|apples?|bananas?|peaches?|pears?|potatoes?|carrots?|tomatoes?|cucumbers?|peppers?|cloves?|fillets?|chops?|pieces?|bunch|medium|large|small)?\b",
            candidate,
            re.IGNORECASE,
        )
        if count:
            return (
                _decimal_text(_number(count.group("number"))),
                "pcs",
                "Preserved the source count without a food-specific mass conversion.",
                optional,
                None,
            )
    raise ValueError(f"Cannot normalize selected source quantity: {source!r}")


def _minutes(value: object) -> int | None:
    if value is None:
        return None
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    if isinstance(value, str):
        minute = re.fullmatch(r"\s*(\d+)\s*minutes?\s*", value, re.IGNORECASE)
        if minute:
            return int(minute.group(1))
        hour = re.fullmatch(r"\s*(\d+)\s*hours?\s*", value, re.IGNORECASE)
        if hour:
            return int(hour.group(1)) * 60
    return None


def _time_fields(
    recipe: dict[str, object],
) -> tuple[int | None, int | None, int | None]:
    facts = recipe.get("source_times") or {}
    if not isinstance(facts, dict):
        return None, None, None
    prep = facts.get("prep_minutes")
    cook = facts.get("cook_minutes")
    total = facts.get("total_minutes")
    if prep is None:
        prep = _minutes(facts.get("preparation"))
    if cook is None:
        cook = _minutes(facts.get("cooking"))
    if total is None:
        total = _minutes(facts.get("total"))
    return (
        prep if isinstance(prep, int) else None,
        cook if isinstance(cook, int) else None,
        total if isinstance(total, int) else None,
    )


def _canonical_code(source_id: str) -> str:
    return re.sub(r"[^A-Z0-9]+", "_", source_id.upper()).strip("_")


def build(output_dir: Path = OUTPUT) -> None:
    corpus_rows = _json(CORPUS)["recipes"]
    coverage_payload = _json(COVERAGE)
    coverage_rows = coverage_payload["recipes"]
    step_payload = _json(STEP_CURATION)
    step_rows = step_payload["recipes"]
    if not all(
        isinstance(value, list) for value in (corpus_rows, coverage_rows, step_rows)
    ):
        raise ValueError("PR4 curation inputs must contain recipe lists")
    if (
        len(corpus_rows) != EXPECTED_RECIPE_COUNT
        or len(step_rows) != EXPECTED_RECIPE_COUNT
    ):
        raise ValueError("PR4 requires exactly 30 accepted recipes and step records")

    coverage_by_id = {row["source_recipe_id"]: row for row in coverage_rows}
    steps_by_id = {row["recipe_source_id"]: row for row in step_rows}
    accepted_codes = set(coverage_payload["selected_existing_codes"])
    if len(accepted_codes) != EXPECTED_FOOD_INGREDIENT_CODES:
        raise ValueError("Accepted DATA2 FoodIngredient manifest must contain 81 codes")

    recipes: list[dict[str, object]] = []
    sources: list[dict[str, object]] = []
    used_codes: set[str] = set()
    ingredient_count = equipment_count = step_count = 0

    for recipe in corpus_rows:
        source_id = recipe["recipe_source_id"]
        coverage = coverage_by_id[source_id]
        step_record = steps_by_id[source_id]
        if step_record["accepted_data2_sha256"] != recipe["source_sha256"]:
            raise ValueError(f"Step curation hash mismatch for {source_id}")

        ingredients: list[dict[str, object]] = []
        for row in coverage["rows"]:
            if not str(row["selection"]).startswith("SELECTED"):
                continue
            selected_codes = row["selected_codes"]
            if not isinstance(selected_codes, list) or len(selected_codes) != 1:
                raise ValueError(
                    f"Selected source row must resolve to one FoodIngredient: {source_id}"
                )
            code = str(selected_codes[0])
            quantity, unit, normalization_note, optional, prep_note = (
                _normalize_quantity(row)
            )
            ingredients.append(
                {
                    "food_ingredient_code": code,
                    "quantity": quantity,
                    "unit": unit,
                    "source_amount_text": row["source_text"],
                    "normalization_note": normalization_note,
                    "prep_note": prep_note,
                    "optional": optional,
                }
            )
            used_codes.add(code)

        steps = step_record["steps"]
        if (
            not isinstance(steps, list)
            or not steps
            or any(not isinstance(step, str) or not step.strip() for step in steps)
        ):
            raise ValueError(f"Missing ordered source-derived steps for {source_id}")
        equipment = [
            str(item["equipment_code"]).lower() for item in recipe["equipment"]
        ]
        prep_minutes, cook_minutes, total_minutes = _time_fields(recipe)
        source_hash = str(recipe["source_sha256"])
        source_retrieved_at = HISTORICAL_RETRIEVED_AT.get(str(source_id))
        rights = recipe["rights_review"]

        version = {
            "base_servings": _decimal_text(Decimal(str(recipe["source_servings"]))),
            "meal_type_code": recipe["meal_type_code"],
            "prep_time_minutes": prep_minutes,
            "cook_time_minutes": cook_minutes,
            "total_time_minutes": total_minutes,
            "difficulty_code": None,
            "batch_friendly": None,
            "freezable": None,
            "storage_days_fridge": None,
            "storage_days_freezer": None,
            "verification_status": "SOURCE_VERIFIED",
            "verified_at": VERIFIED_AT,
            "source_name": SOURCE_NAME,
            "source_recipe_id": source_id,
            "source_url": recipe["source_url"],
            "source_version": f"sha256:{source_hash}",
            "source_retrieved_at": source_retrieved_at,
            "source_document_sha256": source_hash,
            "source_original_servings": _decimal_text(
                Decimal(str(recipe["source_servings"]))
            ),
            "rights_review_status": "REVIEWED",
            "rights_basis": rights["basis"],
            "change_note": "Initial production version compiled from accepted PR4-DATA2 curation and reviewed source-derived steps.",
            "ingredients": ingredients,
            "steps": steps,
            "equipment_codes": equipment,
        }
        recipes.append(
            {
                "canonical_code": _canonical_code(str(source_id)),
                "canonical_name": recipe["recipe_name"],
                "version": version,
            }
        )
        sources.append(
            {
                "recipe_source_id": source_id,
                "source_name": SOURCE_NAME,
                "source_url": recipe["source_url"],
                "source_version": f"sha256:{source_hash}",
                "source_original_servings": recipe["source_servings"],
                "source_retrieved_at": source_retrieved_at,
                "accepted_data2_sha256": source_hash,
                "source_document_sha256": source_hash,
                "rights_review_status": "REVIEWED",
                "rights_basis": rights["basis"],
                "rights_evidence_urls": rights.get("evidence_urls", []),
                "source_attribution": recipe.get("source_attribution"),
                "retrieval_method": (
                    "RECOVERED_HISTORICAL_COMPLETION"
                    if source_retrieved_at is not None
                    else "ACCEPTED_DATA2_REVIEW_EVIDENCE"
                ),
                "comparison_result": "ACCEPTED_DATA2_ARTIFACT",
                "step_extraction_source_sha256": step_record[
                    "extraction_source_sha256"
                ],
                "step_comparison_result": step_record["comparison_result"],
            }
        )
        ingredient_count += len(ingredients)
        equipment_count += len(equipment)
        step_count += len(steps)

    if ingredient_count != EXPECTED_INGREDIENT_ROWS:
        raise ValueError(
            f"Expected 189 selected RecipeIngredient rows, got {ingredient_count}"
        )
    if equipment_count != EXPECTED_EQUIPMENT_ROWS:
        raise ValueError(f"Expected 86 RecipeEquipment rows, got {equipment_count}")
    if step_count != EXPECTED_STEP_ROWS:
        raise ValueError(f"Expected 169 RecipeStep rows, got {step_count}")
    if used_codes != accepted_codes:
        raise ValueError(
            "Production RecipeIngredient FoodIngredient set differs from accepted DATA2 manifest"
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "recipes.json").write_text(
        json.dumps(
            {"schema_version": 2, "recipes": recipes}, ensure_ascii=False, indent=2
        )
        + "\n",
        encoding="utf-8",
    )
    (output_dir / "source-manifest.json").write_text(
        json.dumps(
            {
                "schema_version": 2,
                "accepted_data2_checked_at": "2026-09-05",
                "sources": sources,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    build()
