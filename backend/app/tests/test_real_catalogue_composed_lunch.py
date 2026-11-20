"""Real-source MealPlan research: correct blocker when canonical allergens are unreviewed."""

import json
import subprocess
import sys
from copy import deepcopy
from decimal import Decimal

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


def test_real_catalogue_lunch_source_gate_reports_real_unreviewed_foods(receipt):
    assert receipt["schema"] == SCHEMA
    assert receipt["scope"] == "ISOLATED_SYNTHETIC_MEMBER_REAL_CURATED_RECIPES"
    assert receipt["decision"] == "BLOCKED_UNREVIEWED_CANONICAL_FOOD_ALLERGENS"
    assert (
        receipt["source_pairing"] == "MANUAL_CROSS_SOURCE_RESEARCH_NOT_PUBLISHED_MENU"
    )
    assert receipt["core_ai_enabled"] is False
    e = receipt["evidence"]
    assert e["baseline_events"] == 7
    assert e["composed_event_count"] == 0
    assert e["shopping_status"] == "NOT_RUN_SOURCE_ADMISSION_BLOCKED"
    assert e["price_status"] == "UNKNOWN"
    assert [r["course"] for r in e["source_courses"]] == ["FIRST", "SECOND"]
    assert [r["recipe_code"] for r in e["source_courses"]] == [
        code for code, _kind in SOURCE_CODES
    ]
    assert all(
        len(r["source_document_sha256"]) == 64
        and r["source_recipe_id"]
        and r["portion_servings"] == "1.000000"
        for r in e["source_courses"]
    )
    assert Decimal(e["source_courses"][1]["source_original_servings"]) == 1
    assert Decimal(e["source_courses"][1]["source_output_g_raw"]) == 80
    assert len(e["blocking_ingredients"]) == 14
    assert e["unique_blocking_food_codes"] == sorted(
        {
            "BEEF_CATEGORY_1_RAW",
            "BUTTER_PEASANT_72_5_UNSALTED",
            "CABBAGE_GREEN",
            "CARROT",
            "FLOUR_WHEAT_HIGH_GRADE",
            "ONION_BULB_FRESH",
            "POTATO",
            "SALT_IODIZED",
            "TOMATO",
            "TOMATO_PUREE_PASTE",
            "VEGETABLE_OIL_REFINED_UNSPECIFIED",
            "WATER",
        }
    )
    assert all(
        item["recipe_code"] in [c for c, _ in SOURCE_CODES]
        and item["food_code"]
        and item["food_name_ru"]
        and isinstance(item["allergen_codes_observed"], list)
        and (not item["active"] or not item["allergens_reviewed"])
        for item in e["blocking_ingredients"]
    )
    assert receipt["semantic_sha256"] == _hash(e)


def test_real_source_blocker_does_not_suggest_unsafe_bypass_or_customer_readiness(
    receipt,
):
    assert receipt["limitations"] == {
        "reviewed_source_provenance": True,
        "canonical_allergen_review_complete": False,
        "course_suitability_independently_approved": False,
        "member_portion_mass_validated": False,
        "nutrition_fully_complete": False,
        "safe_prep_approved": False,
        "customer_activation": False,
        "no_production_data_modified": True,
    }


def test_semantic_fingerprint_detects_source_food_review_tampering(receipt):
    modified = deepcopy(receipt["evidence"])
    modified["blocking_ingredients"][0]["allergens_reviewed"] = True
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
    assert decoded["decision"] == "BLOCKED_UNREVIEWED_CANONICAL_FOOD_ALLERGENS"


def test_research_cli_cannot_accept_an_arbitrary_user_database_path(tmp_path):
    path = tmp_path / "must-not-create.sqlite"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "scripts.real_catalogue_composed_lunch",
            "--sqlite",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    assert not path.exists()
