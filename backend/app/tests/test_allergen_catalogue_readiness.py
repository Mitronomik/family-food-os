"""Full FoodIngredient catalogue allergen readiness, source-safe admission preflight."""

import copy
import json
import sqlite3
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
    assert summary["food_ingredients_unknown"] == len(report["unresolved_queue"])
    assert summary["active_food_ingredients_unknown"] == len(
        report["active_unresolved_queue"]
    )
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
    # No random seed UUIDs may enter semantic lineage or the report hash.
    for food in report["foods"]:
        for historical in food["historical_recipe_versions"]:
            assert set(historical) == {"recipe_code", "version_number"}
            assert historical["recipe_code"] in food["historical_recipe_codes"]
            assert isinstance(historical["version_number"], int)
    assert report["semantic_sha256"] == _digest(
        {key: value for key, value in report.items() if key != "semantic_sha256"}
    )


def test_actual_source_recipe_dependencies_follow_current_review_data(report):
    """The audit must remain valid AFTER real ingredient reviews are published."""
    foods = {food["canonical_code"]: food for food in report["foods"]}
    for code in ACTUAL_FOOD_BLOCKERS:
        food = foods[code]
        assert food["status"] in (
            "UNKNOWN",
            "RECORDED_REVIEWED_WITH_CODES",
            "RECORDED_REVIEWED_EMPTY_SET",
        )
        if food["status"] == "UNKNOWN":
            assert food["recorded_allergen_codes"] == []
        assert food["review_provenance_in_db"] == "NOT_STORED"
    soup = "MR2019_1_2A_VEGETARIAN_CABBAGE_SOUP"
    goulash = "SCHOOL2022_54_2M_BEEF_GOULASH"
    recipes = {row["recipe_code"]: row for row in report["active_recipes"]}
    assert {soup, goulash} <= set(recipes)
    assert soup in foods["CABBAGE_GREEN"]["active_recipe_codes"]
    assert goulash in foods["BEEF_CATEGORY_1_RAW"]["active_recipe_codes"]
    assert soup in foods["WATER"]["active_recipe_codes"]
    assert goulash in foods["WATER"]["active_recipe_codes"]
    for code in (soup, goulash):
        missing = recipes[code]["missing_food_codes"]
        assert missing == sorted(
            food["canonical_code"]
            for food in report["foods"]
            if code in food["active_recipe_codes"]
            and (not food["is_active"] or food["status"] == "UNKNOWN")
        )
        assert recipes[code]["allergen_readiness"] == (
            "BLOCKED" if missing else "RECORDED_REVIEW_COMPLETE"
        )
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
        "taxonomy_code": "TEST_ONLY_UNACCEPTED_TAXONOMY",
        "taxonomy_version": "test-v1",
        "reviewed_at": "2026-11-23T08:00:00+00:00",
        "source_sha256": "1" * 64,
        "review_reference": "TEST_ONLY_NOT_AN_APPROVED_REVIEW",
        "applicability": "TEST_ONLY_EXACT_CANONICAL_FOOD_FORM",
    }


def test_proposed_review_does_not_silently_publish_or_clear_allergens(report):
    food = report["foods"][0]
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
    assert food["status"] == report["foods"][0]["status"]


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
    food = report["foods"][0]
    entry = _entry(food)
    change(entry)
    with pytest.raises(AllergenReadinessBlocked):
        validate_review_proposals(
            report, {"schema": PACKAGE_SCHEMA, "entries": [entry]}
        )


def test_proposed_review_must_pin_actual_source_hash_and_applicability(report):
    food = report["foods"][0]
    entry = _entry(
        food,
        review_state="REVIEWED_EMPTY_SET",
        evidence=_source_evidence(),
    )
    for field, bad in [
        ("source_sha256", "not-a-real-sha"),
        ("source_version", ""),
        ("taxonomy_code", ""),
        ("taxonomy_version", ""),
        ("reviewed_at", "2026-11-23T08:00:00"),
        ("reviewed_at", "not-a-date"),
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
    food = report["foods"][0]
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


@pytest.mark.parametrize("bad_codes", [[["MILK"]], [{"code": "MILK"}], [12], [None]])
def test_malformed_allergen_codes_fail_closed_without_type_error(report, bad_codes):
    entry = _entry(report["foods"][0], codes=bad_codes)
    with pytest.raises(AllergenReadinessBlocked, match="нормализованным"):
        validate_review_proposals(
            report, {"schema": PACKAGE_SCHEMA, "entries": [entry]}
        )


def test_existing_sqlite_is_opened_at_driver_level_read_only(tmp_path, monkeypatch):
    """Even a buggy later inventory write must fail for an explicit database."""
    database = tmp_path / "existing.sqlite"
    with sqlite3.connect(database) as connection:
        connection.execute("CREATE TABLE sentinel (value INTEGER)")
        connection.execute("INSERT INTO sentinel VALUES (1)")

    from sqlalchemy import text
    from sqlalchemy.exc import OperationalError

    import scripts.audit_food_allergen_readiness as module

    def probe(engine):
        with engine.connect() as connection:
            assert connection.scalar(text("SELECT value FROM sentinel")) == 1
            with pytest.raises(OperationalError, match="readonly|read-only"):
                connection.execute(text("INSERT INTO sentinel VALUES (2)"))
        return {"read_only": True}

    monkeypatch.setattr(module, "inventory_from_engine", probe)
    assert audit_catalogue(sqlite_path=database) == {"read_only": True}
    with sqlite3.connect(database) as connection:
        assert connection.execute("SELECT value FROM sentinel").fetchall() == [(1,)]


def test_inactive_unknown_food_remains_in_full_review_backlog(tmp_path):
    from app.db.config import DatabaseConfig
    from app.seed.dc4_a3_russian_step_corrections import (
        seed_dc4_a3_russian_step_corrections,
    )

    database = tmp_path / "catalogue.sqlite"
    seed_dc4_a3_russian_step_corrections(DatabaseConfig(path=database))
    with sqlite3.connect(database) as connection:
        connection.execute(
            "UPDATE food_ingredients SET is_active = 0 WHERE canonical_code = ?",
            ("WATER",),
        )
    report = audit_catalogue(sqlite_path=database)
    food = next(row for row in report["foods"] if row["canonical_code"] == "WATER")
    assert food["is_active"] is False
    assert food["status"] == "UNKNOWN"
    assert "WATER" in {row["canonical_code"] for row in report["unresolved_queue"]}
    assert "WATER" not in {
        row["canonical_code"] for row in report["active_unresolved_queue"]
    }
    assert report["summary"]["food_ingredients_unknown"] == len(
        report["unresolved_queue"]
    )
    assert report["summary"]["active_food_ingredients_unknown"] == len(
        report["active_unresolved_queue"]
    )
    assert len(report["unresolved_queue"]) == len(report["active_unresolved_queue"]) + 1
