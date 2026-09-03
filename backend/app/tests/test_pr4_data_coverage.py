import csv
import json

from app.db.config import REPOSITORY_ROOT
from app.seed.food_ingredients import load_seed_entries


CURATION_DIRECTORY = REPOSITORY_ROOT / "data" / "curation" / "pr4"
CORPUS_PATH = CURATION_DIRECTORY / "recipe-corpus.json"
COVERAGE_PATH = CURATION_DIRECTORY / "ingredient-coverage.csv"
MVP0_MANIFEST_PATH = CURATION_DIRECTORY / "mvp0-food-ingredient-codes.txt"
STRUCTURAL_CONCEPT = "authoritative_subrecipe_decomposition"


def _corpus_records() -> list[dict[str, object]]:
    with CORPUS_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)["recipes"]


def _coverage_rows() -> list[dict[str, str]]:
    with COVERAGE_PATH.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _manifest_codes() -> list[str]:
    return MVP0_MANIFEST_PATH.read_text(encoding="utf-8").splitlines()


def test_pr4_corpus_is_exactly_thirty_reviewable_six_serving_usda_sources():
    records = _corpus_records()
    recipe_ids = [record["recipe_source_id"] for record in records]

    assert len(records) == len(set(recipe_ids)) == 30
    assert all(record["source_servings"] == 6 for record in records)
    assert all(
        str(record["source_url"]).startswith(
            (
                "https://fns-prod.azureedge.us/",
                "https://theicn.org/cnrb/pdfs/cacfp/family-child-care-homes/",
            )
        )
        for record in records
    )
    assert "CACFP6-ROASTED-POTATO-TURKEY-HASH" not in recipe_ids
    assert "CACFP6-BROWN-RICE-PILAF" not in recipe_ids
    assert "CACFP6-VEGETABLE-FRITTATA-BITES" in recipe_ids
    assert "CACFP6-CAULIFLOWER-RICE" in recipe_ids


def test_pr4_matrix_has_no_dropped_or_unresolved_source_ingredients():
    recipe_ids = {record["recipe_source_id"] for record in _corpus_records()}
    rows = _coverage_rows()

    assert len(rows) == 363
    assert {row["source_recipe_id"] for row in rows} == recipe_ids
    assert all(row["source_ingredient_text"].strip() for row in rows)
    assert all(row["normalized_concept"].strip() for row in rows)
    assert all(row["resolution_status"] == "RESOLVED_EXISTING" for row in rows)
    assert all(
        row["existing_food_ingredient_code"].strip()
        for row in rows
        if row["normalized_concept"] != STRUCTURAL_CONCEPT
    )
    assert sum(row["normalized_concept"] == STRUCTURAL_CONCEPT for row in rows) == 1

    concepts_to_codes: dict[str, set[str]] = {}
    for row in rows:
        if row["normalized_concept"] != STRUCTURAL_CONCEPT:
            concepts_to_codes.setdefault(row["normalized_concept"], set()).add(
                row["existing_food_ingredient_code"]
            )
    assert all(len(codes) == 1 for codes in concepts_to_codes.values())


def test_mvp0_manifest_is_the_exact_bounded_catalogue_subset():
    rows = _coverage_rows()
    manifest_codes = _manifest_codes()
    matrix_codes = {
        row["existing_food_ingredient_code"]
        for row in rows
        if row["normalized_concept"] != STRUCTURAL_CONCEPT
    }

    assert manifest_codes == sorted(set(manifest_codes))
    assert len(manifest_codes) == 119
    assert len(manifest_codes) <= 120
    assert set(manifest_codes) == matrix_codes


def test_pr4_data_additions_are_corpus_bounded_and_have_fdc_provenance():
    entries = load_seed_entries()
    entries_by_code = {entry.canonical_code: entry for entry in entries}
    manifest_codes = set(_manifest_codes())
    additions = {
        code: entry
        for code, entry in entries_by_code.items()
        if entry.nutrition.verified_at.isoformat().startswith("2026-09-04")
    }

    assert len(entries) == 183
    assert len(additions) == 83
    assert set(additions) <= manifest_codes <= set(entries_by_code)
    assert len(manifest_codes - set(additions)) == 36
    assert (
        sum(
            entry.nutrition.source_data_type == "Foundation"
            for entry in additions.values()
        )
        == 15
    )
    assert (
        sum(
            entry.nutrition.source_data_type == "SR Legacy"
            for entry in additions.values()
        )
        == 68
    )
    assert all(
        entry.nutrition.source_name == "USDA_FDC" for entry in additions.values()
    )
    assert all(
        entry.nutrition.source_version
        == (
            "2026-04-30"
            if entry.nutrition.source_data_type == "Foundation"
            else "2018-04"
        )
        for entry in additions.values()
    )
