"""Real curated RecipeVersions in disposable composed MealPlan + Shopping V2."""

import json
import subprocess
import sys
from copy import deepcopy

import pytest

from scripts.real_catalogue_composed_lunch import (
    SCHEMA,
    SOURCE_CODES,
    _hash,
    build_research_proof,
)


@pytest.fixture(scope="module")
def receipt():
    return build_research_proof()


def test_seven_day_real_recipe_week_with_one_true_source_backed_composed_lunch(receipt):
    assert receipt["schema"] == SCHEMA
    assert receipt["scope"] == "ISOLATED_SYNTHETIC_MEMBER_REAL_CURATED_RECIPES"
    assert receipt["decision"] == "NO_GO_FOR_CONSUMER_OR_PHYSICAL_SERVING"
    assert receipt["source_pairing"] == "MANUAL_CROSS_SOURCE_RESEARCH_NOT_PUBLISHED_MENU"
    assert receipt["core_ai_enabled"] is False
    e = receipt["evidence"]
    assert e["event_count"] == 7
    assert e["composed_event_count"] == 1
    assert e["individual_component_servings"] == 2
    assert [r["course"] for r in e["source_courses"]] == ["FIRST", "SECOND"]
    assert [r["recipe_code"] for r in e["source_courses"]] == [
        code for code, _kind in SOURCE_CODES
    ]
    assert {r["source_name"] for r in e["source_courses"]} == {"MR2019", "ru-school2022"}
    assert all(
        len(r["source_document_sha256"]) == 64
        and r["source_recipe_id"]
        and r["portion_servings"] == "1.000000"
        for r in e["source_courses"]
    )
    assert e["source_courses"][1]["source_original_servings"] == "1"
    assert e["source_courses"][1]["source_output_g_raw"] == "80.000000"
    assert e["shopping_status"] == "COMPLETE"
    assert e["price_status"] == "UNKNOWN"
    assert e["shopping"]
    assert all(float(row["required"]) >= 0 and float(row["to_buy"]) >= 0 for row in e["shopping"])
    assert receipt["semantic_sha256"] == _hash(e)


def test_real_source_composed_week_does_not_claim_user_readiness(receipt):
    flags = receipt["limitations"]
    assert flags == {
        "reviewed_source_provenance": True,
        "course_suitability_independently_approved": False,
        "member_portion_mass_validated": False,
        "nutrition_fully_complete": False,
        "safe_prep_approved": False,
        "customer_activation": False,
        "no_production_data_modified": True,
    }


def test_semantic_fingerprint_detects_grocery_tampering(receipt):
    modified = deepcopy(receipt["evidence"])
    modified["shopping"][0]["to_buy"] = "999999"
    assert _hash(modified) != receipt["semantic_sha256"]


def test_fresh_process_receipt_matches_in_memory_source_identity(receipt):
    completed = subprocess.run(
        [sys.executable, "-m", "scripts.real_catalogue_composed_lunch"],
        check=True,
        capture_output=True,
        text=True,
    )
    assert completed.stderr == ""
    decoded = json.loads(completed.stdout)
    assert decoded["semantic_sha256"] == receipt["semantic_sha256"]
    assert decoded["evidence"] == receipt["evidence"]
    assert decoded["decision"] == "NO_GO_FOR_CONSUMER_OR_PHYSICAL_SERVING"
