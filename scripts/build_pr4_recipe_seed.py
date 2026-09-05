#!/usr/bin/env python3
"""Build the bounded PR4 seed from reviewed local USDA source documents.

This is a curation tool, not a runtime ingestion path. It requires the exact PDFs
named by ``data/curation/pr4/recipe-corpus.json`` to be present in ``--source-dir``.
"""

from __future__ import annotations

import argparse
import csv
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "data/curation/pr4/recipe-corpus.json"
COVERAGE = ROOT / "data/curation/pr4/ingredient-coverage.csv"
OUTPUT = ROOT / "data/seed/recipes"
RETRIEVED_AT = "2026-09-04T00:00:00+00:00"
SOURCE_NAME = "USDA_FNS"
RIGHTS_EVIDENCE_URL = "https://www.ars.usda.gov/ott/templates-agreements/"
RIGHTS_BASIS = (
    "Reviewed each source card as an identified USDA Food and Nutrition Service "
    "work produced by the stated USDA recipe project. USDA ARS copyright guidance "
    "states that United States Government employee official-duty works are public "
    "domain in the United States under 17 U.S.C. 105. No third-party copyright "
    "notice was present on the reviewed card; retain USDA attribution."
)

FRACTIONS = {
    "¼": Decimal("0.25"),
    "½": Decimal("0.5"),
    "¾": Decimal("0.75"),
    "⅐": Decimal("0.142857142857"),
    "⅑": Decimal("0.111111111111"),
    "⅒": Decimal("0.1"),
    "⅓": Decimal("0.333333333333"),
    "⅔": Decimal("0.666666666667"),
    "⅕": Decimal("0.2"),
    "⅖": Decimal("0.4"),
    "⅗": Decimal("0.6"),
    "⅘": Decimal("0.8"),
    "⅙": Decimal("0.166666666667"),
    "⅚": Decimal("0.833333333333"),
    "⅛": Decimal("0.125"),
    "⅜": Decimal("0.375"),
    "⅝": Decimal("0.625"),
    "⅞": Decimal("0.875"),
}
NUMBER = r"(?:\d+(?:\.\d+)?(?:\s+[\u00bc-\u00be\u2150-\u215e])?|[\u00bc-\u00be\u2150-\u215e]|\d+\s*/\s*\d+)"
OUNCE_GRAMS = Decimal("28.349523125")
POUND_GRAMS = Decimal("453.59237")
VOLUME_ML = {
    "tsp": Decimal("5"),
    "teaspoon": Decimal("5"),
    "teaspoons": Decimal("5"),
    "tbsp": Decimal("15"),
    "tablespoon": Decimal("15"),
    "tablespoons": Decimal("15"),
    "cup": Decimal("240"),
    "cups": Decimal("240"),
    "qt": Decimal("960"),
    "quart": Decimal("960"),
    "quarts": Decimal("960"),
}


def decimal_text(value: Decimal) -> str:
    value = value.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)
    return format(value, "f")


def parse_number(raw: str) -> Decimal:
    value = raw.strip()
    if "/" in value:
        numerator, denominator = value.replace(" ", "").split("/", 1)
        return Decimal(numerator) / Decimal(denominator)
    for glyph, fraction in FRACTIONS.items():
        if glyph in value:
            whole = value.replace(glyph, "").strip()
            return (Decimal(whole) if whole else Decimal(0)) + fraction
    return Decimal(value)


def selected_branch(text: str) -> tuple[str, str | None]:
    lowered = text.casefold()
    if " or " not in lowered:
        return text, None
    if "(juice selected)" in lowered:
        return text.split(" OR ", 1)[1], (
            "Selected the source-authorized lime juice alternative recorded by PR4-DATA."
        )
    if any(
        token in lowered
        for token in (
            "(fresh selected)",
            "(ancho selected)",
            "(canned selected)",
            "cranberries selected",
        )
    ):
        return text.split(" OR ", 1)[0], (
            "Selected the source-authorized first alternative recorded by PR4-DATA."
        )
    if "cranberries selected" in lowered:
        return text.rsplit(" or ", 1)[0], (
            "Selected the source-authorized dried cranberry alternative recorded by PR4-DATA."
        )
    if "black selected" in lowered:
        return text, (
            "Selected the source-authorized black pepper alternative recorded by PR4-DATA."
        )
    return text, None


def normalize_ingredient(source_text: str) -> tuple[str, str, str | None, bool]:
    text = re.sub(r"^Pico de Gallo:\s*", "", source_text)
    text, branch_note = selected_branch(text)
    optional = "(optional)" in source_text.casefold()

    lb_match = re.search(
        rf"(?P<lb>{NUMBER})\s*lb(?:\s*(?P<oz>{NUMBER})\s*oz)?", text, re.IGNORECASE
    )
    if lb_match:
        pounds = parse_number(lb_match.group("lb"))
        ounces = (
            parse_number(lb_match.group("oz")) if lb_match.group("oz") else Decimal(0)
        )
        quantity = pounds * POUND_GRAMS + ounces * OUNCE_GRAMS
        note = "Converted source avoirdupois pounds/ounces to grams exactly."
        return decimal_text(quantity), "g", _notes(note, branch_note), optional

    oz_match = re.search(rf"(?P<oz>{NUMBER})\s*oz\b", text, re.IGNORECASE)
    if oz_match:
        ounces = parse_number(oz_match.group("oz"))
        each_match = re.search(
            rf"^(?P<count>{NUMBER})\s+.*?{NUMBER}\s*oz\s+each", text, re.IGNORECASE
        )
        if each_match:
            ounces *= parse_number(each_match.group("count"))
        quantity = ounces * OUNCE_GRAMS
        note = "Converted source avoirdupois ounces to grams exactly."
        if each_match:
            note += " Multiplied the stated per-item weight by the stated item count."
        return decimal_text(quantity), "g", _notes(note, branch_note), optional

    volume_tokens = list(
        re.finditer(
            rf"(?P<number>{NUMBER})\s*(?P<unit>tsp|teaspoons?|Tbsp|tablespoons?|cups?|qt|quarts?)\b",
            text,
            re.IGNORECASE,
        )
    )
    if volume_tokens:
        # When alternatives remain, only the first measure is authoritative for
        # the selected concept. Semicolon-plus quantities are intentionally summed.
        relevant = volume_tokens
        if " or " in text.casefold() and branch_note is None:
            relevant = volume_tokens[:1]
        quantity = sum(
            (
                parse_number(match.group("number"))
                * VOLUME_ML[match.group("unit").casefold()]
            )
            for match in relevant
        )
        note = "Converted source US recipe volume using 1 cup=240 ml, 1 Tbsp=15 ml, 1 tsp=5 ml, 1 qt=960 ml."
        if len(relevant) > 1:
            note += " Summed the source quantities explicitly joined in the ingredient line."
        return decimal_text(quantity), "ml", _notes(note, branch_note), optional

    count_match = re.match(rf"(?P<count>{NUMBER})\b", text)
    if count_match:
        return (
            decimal_text(parse_number(count_match.group("count"))),
            "pcs",
            _notes(
                "Preserved the source count without a food-specific mass conversion.",
                branch_note,
            ),
            optional,
        )
    raise ValueError(f"Cannot normalize ingredient quantity: {source_text!r}")


def _notes(*values: str | None) -> str | None:
    present = [value for value in values if value]
    return " ".join(present) or None


def normalized_components(
    source_text: str,
) -> list[tuple[str, str, str | None, bool]]:
    parts = re.split(r";\s*plus\s+", source_text, maxsplit=1, flags=re.IGNORECASE)
    if len(parts) == 1:
        return [normalize_ingredient(source_text)]
    first, additional = parts
    first_value = normalize_ingredient(first)
    additional_value = normalize_ingredient(additional)
    return [
        (
            first_value[0],
            first_value[1],
            _notes(
                first_value[2],
                "Preserved the first component of the source's explicit semicolon-plus quantity.",
            ),
            first_value[3],
        ),
        (
            additional_value[0],
            additional_value[1],
            _notes(
                additional_value[2],
                "Preserved the explicitly added component of the source's semicolon-plus quantity.",
            ),
            additional_value[3],
        ),
    ]


def extract_text(pdf: Path) -> str:
    result = subprocess.run(
        ["pdftotext", "-raw", str(pdf), "-"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.replace("\f", "\n")


def parse_minutes(text: str, label: str) -> int | None:
    match = re.search(rf"{label} Time:\s*([^\n]+)", text, re.IGNORECASE)
    if not match:
        return None
    raw = match.group(1).strip()
    minute_match = re.search(r"(\d+)\s*minutes?", raw, re.IGNORECASE)
    if minute_match:
        return int(minute_match.group(1))
    if "hour" in raw.casefold():
        values = [parse_number(value) for value in re.findall(NUMBER, raw)]
        return int(max(values) * 60) if values else None
    return None


def parse_steps(text: str) -> list[str]:
    start = re.search(r"^Directions:?\s*$", text, re.MULTILINE)
    if not start:
        raise ValueError("Directions heading not found")
    body = text[start.end() :]
    lines = [line.strip() for line in body.splitlines()]
    steps: list[str] = []
    current: list[str] = []
    synthetic: list[str] | None = None
    expected_number = 1
    index = 0
    while index < len(lines):
        line = lines[index]
        index += 1
        if not line or line.casefold() == "directions continued":
            continue
        if re.match(
            r"^(?:Notes:?|Notes Section:?|Source:|NUTRITION INFORMATION|Variations?:?)",
            line,
            re.IGNORECASE,
        ):
            break
        if re.match(r"^Ingredients(?: continued)?:?$", line, re.IGNORECASE):
            continuation = next(
                (
                    offset
                    for offset in range(index, len(lines))
                    if lines[offset].casefold() == "directions continued"
                ),
                None,
            )
            terminal = next(
                (
                    offset
                    for offset in range(index, len(lines))
                    if re.match(
                        r"^(?:Notes:?|Notes Section:?|Source:)",
                        lines[offset],
                        re.IGNORECASE,
                    )
                ),
                len(lines),
            )
            if continuation is None or continuation > terminal:
                break
            index = continuation + 1
            continue
        stop_after_line = False
        if " Source:" in line:
            line = line.split(" Source:", 1)[0].strip()
            stop_after_line = True
        if (
            "Food and Nutrition Service | USDA" in line
            or line.startswith("United States Department of Agriculture")
            or "CACFP Home Childcare" in line
            or re.search(r"Page \d+ of \d+$", line)
        ):
            continue
        if line == "Pico de Gallo Recipe":
            if current:
                steps.append(" ".join(current))
                current = []
            synthetic = ["Prepare the source Pico de Gallo subrecipe:"]
            continue
        numbered = re.match(r"^(\d+)\s+(.*)$", line)
        if numbered and synthetic is None and int(numbered.group(1)) == expected_number:
            if current:
                steps.append(" ".join(current))
            current = [numbered.group(2)]
            expected_number += 1
            if stop_after_line:
                break
            continue
        if synthetic is not None:
            synthetic.append(line)
        elif current:
            current.append(line)
        if stop_after_line:
            break
    if current:
        steps.append(" ".join(current))
    if synthetic:
        steps.append(" ".join(synthetic))
    if not steps or any(not step.strip() for step in steps):
        raise ValueError("No complete directions parsed")
    return steps


def meal_type(record: dict[str, object]) -> str:
    collection = str(record["source_collection"])
    source_id = str(record["recipe_source_id"])
    if "Breakfasts" in collection:
        return "breakfast"
    if "Side Dishes" in collection or source_id == "CACFP6-CAULIFLOWER-RICE":
        return "side"
    if "Salads" in collection:
        return "salad"
    if "Sandwiches" in collection:
        return "sandwich"
    return "main"


def load_coverage() -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = {}
    with COVERAGE.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            grouped.setdefault(row["source_recipe_id"], []).append(row)
    return grouped


def build(source_dir: Path, output_dir: Path) -> None:
    corpus = json.loads(CORPUS.read_text(encoding="utf-8"))["recipes"]
    coverage = load_coverage()
    recipes = []
    manifest = []
    for source in corpus:
        source_id = source["recipe_source_id"]
        filename = unquote(Path(urlparse(source["source_url"]).path).name)
        pdf = source_dir / filename
        if not pdf.is_file():
            raise FileNotFoundError(f"Missing reviewed source document: {pdf}")
        content = pdf.read_bytes()
        if not content.startswith(b"%PDF"):
            raise ValueError(f"Reviewed source is not a PDF: {pdf}")
        digest = hashlib.sha256(content).hexdigest()
        raw_text = extract_text(pdf)
        ingredients = []
        for row in coverage[source_id]:
            code = row["existing_food_ingredient_code"]
            if not code:
                if row["normalized_concept"] == "authoritative_subrecipe_decomposition":
                    continue
                raise ValueError(f"Unresolved coverage row: {row}")
            for quantity, unit, note, optional in normalized_components(
                row["source_ingredient_text"]
            ):
                ingredients.append(
                    {
                        "food_ingredient_code": code,
                        "quantity": quantity,
                        "unit": unit,
                        "source_amount_text": row["source_ingredient_text"],
                        "normalization_note": note,
                        "prep_note": None,
                        "optional": optional,
                    }
                )
        source_version = f"sha256:{digest}"
        version = {
            "base_servings": "6.000000",
            "meal_type_code": meal_type(source),
            "prep_time_minutes": parse_minutes(raw_text, "Preparation"),
            "cook_time_minutes": parse_minutes(raw_text, "Cooking"),
            "total_time_minutes": None,
            "difficulty_code": None,
            "batch_friendly": None,
            "freezable": None,
            "storage_days_fridge": None,
            "storage_days_freezer": None,
            "verification_status": "SOURCE_VERIFIED",
            "verified_at": RETRIEVED_AT,
            "source_name": SOURCE_NAME,
            "source_recipe_id": source_id,
            "source_url": source["source_url"],
            "source_version": source_version,
            "source_retrieved_at": RETRIEVED_AT,
            "source_document_sha256": digest,
            "source_original_servings": "6.000000",
            "rights_review_status": "REVIEWED",
            "rights_basis": RIGHTS_BASIS,
            "change_note": "Initial verified transcription from the frozen PR4 USDA FNS corpus.",
            "ingredients": ingredients,
            "steps": parse_steps(raw_text),
            "equipment_codes": [],
        }
        recipes.append(
            {
                "canonical_code": source_id.removeprefix("CACFP6-").replace("-", "_"),
                "canonical_name": source["recipe_name"],
                "version": version,
            }
        )
        manifest.append(
            {
                "recipe_source_id": source_id,
                "source_name": SOURCE_NAME,
                "source_url": source["source_url"],
                "source_collection": source["source_collection"],
                "source_version": source_version,
                "source_original_servings": 6,
                "source_retrieved_at": RETRIEVED_AT,
                "source_document_sha256": digest,
                "rights_review_status": "REVIEWED",
                "rights_basis": RIGHTS_BASIS,
                "rights_evidence_url": RIGHTS_EVIDENCE_URL,
            }
        )
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "recipes.json").write_text(
        json.dumps(
            {"schema_version": 1, "recipes": recipes}, ensure_ascii=False, indent=2
        )
        + "\n",
        encoding="utf-8",
    )
    (output_dir / "source-manifest.json").write_text(
        json.dumps(
            {"schema_version": 1, "sources": manifest}, ensure_ascii=False, indent=2
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT)
    args = parser.parse_args()
    build(args.source_dir, args.output_dir)


if __name__ == "__main__":
    main()
