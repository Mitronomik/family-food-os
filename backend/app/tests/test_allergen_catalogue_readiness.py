"""Full FoodIngredient catalogue allergen readiness, source-safe admission preflight."""

import copy
import json
import subprocess
import sys

import pytest

from scripts.audit_food_allergen_readiness import (
    PACKAGE_SCHEMA,
    SCHEMA,
    AllergenReadinessBlocked,
    _digest,
    audit_catalogue,
    validate_review_proposals,
)

ACTUAL_FOOD_BLOCKERS = {
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


@pytest.fixture(scope="module")
def report():
    return audit_catalogue()


def test_full_catalogue_is_not_truncated_to_list_active_limit(report):
    assert report["schema"] == SCHEMA
    assert report["scope"] == "ALL_CANONICAL_FOOD_INGREDIENTS_AND_ALL_RECIPE_VERSIONS"
    summary = report["summary"]
    assert summary["food_ingredients_total"] == len(report["foods"])
    assert summary["food_ingredients_active"] == sum(
        food["is_active"] for food in report["foods"]
    )
    assert summary["food_ingredients_unknown"] == sum(
        food["status"] == "UNKNOWN" for food in report["foods"]
    )
    assert summary["active_food_ingredients_unknown"] == len(report["unresolved_queue"])
    assert summary["recipes_active_total"] == len(report["active_recipes"])
    assert summary["active_recipes_blocked_for_composition"] == sum(
        row["allergen_readiness"] == "BLOCKED" for row in report["active_recipes"]
    )
    assert all(
        code in {food["canonical_code"] for food in report["foods"]}
        for code in ACTUAL_FOOD_BLOCKERS
    )
    assert report["foods"] == sorted(
        report["foods"], key=lambda food: food["canonical_code"]
    )
    assert report["semantic_sha256"] == _digest(
        {key: value for key, value in report.items() if key != "semantic_sha256"}
    )


def test_actual_source_recipe_dependencies_expose_all_unreviewed_foods(report):
    foods = {food["canonical_code"]: food for food in report["foods"]}
    for code in ACTUAL_FOOD_BLOCKERS:
        assert foods[code]["status"] == "UNKNOWN"
        assert foods[code]["recorded_allergen_codes"] == []
        assert foods[code]["review_provenance_in_db"] == "NOT_STORED"
    soup = "MR2019_1_2A_VEGETARIAN_CABBAGE_SOUP"
    goulash = "SCHOOL2022_54_2M_BEEF_GOULASH"
    recipes = {r["recipe_code"]: r for r in report["active_recipes"]}
    assert {soup, goulash} <= set(recipes)
    assert recipes[soup]["allergen_readiness"] == "BLOCKED"
    assert recipes[goulash]["allergen_readiness"] == "BLOCKED"
    assert "CABBAGE_GREEN" in recipes[soup]["missing_food_codes"]
    assert "BEEF_CATEGORY_1_RAW" in recipes[goulash]["missing_food_codes"]
    assert soup in foods["WATER"]["active_recipe_codes"]
    assert goulash in foods["WATER"]["active_recipe_codes"]
    assert report["limitations"]["family_admission_granted"] is False
    assert report["limitations"]["review_source_provenance_verified"] is False
    assert report["limitations"]["ready_for_bulk_publication"] is False


def _entry(food, *, review_state="UNKNOWN", codes=None, evidence=None):
    data = {
        "canonical_code": food["canonical_code"],
        "canonical_name_ru": food["canonical_name_ru"],
        "category_code": food["category_code"],
        "default_unit": food["default_unit"],
        "review_state": review_state,
        "allergen_codes": [] if codes is None else codes,
    }
    if evidence is not None:
        data["evidence"] = evidence
    return data


def _source_evidence():
    # Structurally complete test-only input, NOT a verified real source.
    return {
        "source_name": "TEST_ONLY_UNTRUSTED_SOURCE",
        "source_locator": "https://example.invalid/reference",
        "source_version": "test-v1",
        "source_sha256": "1" * 64,
        "review_reference": "TEST_ONLY_NOT_AN_APPROVED_REVIEW",
        "applicability": "TEST_ONLY_EXACT_CANONICAL_FOOD_FORM",
    }


def test_proposed_review_does_not_silently_publish_or_clear_allergens(report):
    food = next(x for x in report["foods"] if x["status"] == "UNKNOWN")
    for state, codes in [
        ("UNKNOWN", []),
        ("REVIEWED_EMPTY_SET", []),
        ("REVIEWED_WITH_CODES", ["MILK"]),
    ]:
        entry = _entry(
            food,
            review_state=state,
            codes=codes,
            evidence=_source_evidence() if state != "UNKNOWN" else None,
        )
        proposal = {"schema": PACKAGE_SCHEMA, "entries": [entry]}
        preview = validate_review_proposals(report, proposal)
        assert preview["status"] == "STRUCTURALLY_CHECKED_NOT_APPROVED"
        assert preview["publication_performed"] is False
        assert preview["mutation_performed"] is False
        assert preview["entries"][0]["publication"] == "NOT_AUTHORIZED_REVIEW_ONLY"
    assert food["status"] == "UNKNOWN"


@pytest.mark.parametrize(
    "change",
    [
        lambda row: row.update(canonical_code="UNKNOWN_UNPUBLISHED_FOOD"),
        lambda row: row.update(default_unit="pcs"),
        lambda row: row.update(canonical_name_ru="Другое сырьё"),
        lambda row: row.update(review_state="REVIEWED_EMPTY_SET"),
        lambda row: row.update(
            review_state="REVIEWED_WITH_CODES", allergen_codes=["MILK"]
        ),
        lambda row: row.update(
            review_state="REVIEWED_WITH_CODES", allergen_codes=["milk"]
        ),
        lambda row: row.update(
            review_state="REVIEWED_WITH_CODES", allergen_codes=["MILK", "MILK"]
        ),
    ],
)
def test_unsupported_or_unreviewed_source_cannot_pass_proposal_gate(report, change):
    food = next(x for x in report["foods"] if x["status"] == "UNKNOWN")
    entry = _entry(food)
    change(entry)
    with pytest.raises(AllergenReadinessBlocked):
        validate_review_proposals(
            report, {"schema": PACKAGE_SCHEMA, "entries": [entry]}
        )


def test_proposed_review_must_pin_actual_source_hash_and_applicability(report):
    food = next(x for x in report["foods"] if x["status"] == "UNKNOWN")
    entry = _entry(
        food,
        review_state="REVIEWED_EMPTY_SET",
        evidence=_source_evidence(),
    )
    for field, bad in [
        ("source_sha256", "not-a-real-sha"),
        ("source_version", ""),
        ("review_reference", ""),
        ("applicability", ""),
        ("source_locator", "file:///etc/passwd"),
    ]:
        bad_entry = copy.deepcopy(entry)
        bad_entry["evidence"][field] = bad
        with pytest.raises(AllergenReadinessBlocked):
            validate_review_proposals(
                report, {"schema": PACKAGE_SCHEMA, "entries": [bad_entry]}
            )


def test_duplicate_entries_are_rejected_without_any_publication(report):
    food = next(x for x in report["foods"] if x["status"] == "UNKNOWN")
    entry = _entry(food)
    with pytest.raises(AllergenReadinessBlocked, match="Повторяющийся"):
        validate_review_proposals(
            report, {"schema": PACKAGE_SCHEMA, "entries": [entry, entry]}
        )


def test_cli_reproduces_exact_semantic_report_in_fresh_process(report):
    process = subprocess.run(
        [sys.executable, "-m", "scripts.audit_food_allergen_readiness"],
        check=True,
        capture_output=True,
        text=True,
    )
    assert json.loads(process.stdout) == report
    assert process.stderr == ""


def test_missing_input_database_must_not_create_sqlite(tmp_path):
    missing = tmp_path / "must-not-create.sqlite"
    with pytest.raises(AllergenReadinessBlocked, match="уже существовать"):
        audit_catalogue(sqlite_path=missing)
    assert not missing.exists()
