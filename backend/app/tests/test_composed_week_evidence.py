"""Actual read-only source/role/physical/Nutrition evidence from persisted 0044.

Synthetic fixtures exercise the tool, not independent clinical or kitchen proof.
"""

import json
import sqlite3
import subprocess
import sys
from datetime import UTC, datetime
from hashlib import sha256
from uuid import uuid4

import pytest
from app.persistence.sqlalchemy_core.shopping_uow import SqlAlchemyShoppingReadScope
from app.tests.persistence.test_meal_plan_composition_persistence import (
    _compose,
    _setup,
    _write,
)
from app.tests.persistence.test_meal_plan_full_week_composition import _week_21_42

from scripts.composed_week_evidence import (
    NO_GO,
    SCHEMA,
    build_inventory,
    inventory_from_database,
)
from scripts.composed_week_preview import ComposedWeekPreviewBlocked

CAPTURED = datetime(2026, 11, 16, 12, tzinfo=UTC)


def _week(tmp_path):
    config, engine, home, people, old, recipes, selections = _setup(tmp_path)
    composed = _compose(old, people, recipes, selections)
    _write(engine, composed, people)
    return config, engine, home, composed


def test_persisted_composed_week_inventory_reports_real_gaps_without_invention(
    tmp_path,
):
    config, engine, home, composed = _week(tmp_path)
    try:
        original = sha256(config.path.read_bytes()).hexdigest()
        result = inventory_from_database(
            database_path=config.path,
            household_id=home.id,
            plan_id=composed.plan.id,
            captured_at=CAPTURED,
        )
        assert result["schema"] == SCHEMA
        assert result["verdict"] == NO_GO
        assert result["scope"] == "INTERNAL_READ_ONLY_EVIDENCE"
        assert result["plan_events"] == 7
        assert result["revision"] == composed.plan.revision_number
        assert len(result["shopping_source_fingerprint"]) == 64
        assert result["shopping_status"] == "COMPLETE"
        assert result["shopping_price_status"] == "UNKNOWN"
        assert len(result["components"]) == 3
        assert [c["course_kind"] for c in result["components"]] == [
            "FIRST",
            "SECOND",
            "DESSERT",
        ]
        assert [c["member_servings"][0]["factor"] for c in result["components"]] == [
            "1.000000",
            "1.000000",
            "0.500000",
        ]
        for component in result["components"]:
            source = component["source_rights"]
            assert source["recorded_status"] == "VERIFIED_METADATA"
            assert source["independent_source_review"] == "NOT_PERFORMED"
            assert len(source["source_document_sha256"]) == 64
            assert component["role_structure"]["structure_replayed"] is True
            assert len(component["role_structure"]["rule_sha256"]) == 64
            assert component["role_structure"]["course_suitability"] == "UNKNOWN"
            assert component["physical"]["member_final_edible_mass_g"] is None
            assert component["physical"]["status"] == "UNKNOWN"
            assert component["physical"]["output_evidence"] == "MISSING_SOURCE_OUTPUT"
            assert component["nutrition"]["status"] == "UNAVAILABLE"
            assert component["nutrition"]["available_nutrients"] == 0
            assert component["nutrition"]["total_nutrients"] == 54
            assert len(component["nutrition"]["unknown_codes"]) == 54
        assert result["summary"]["source_metadata_blocked"] == 0
        assert result["summary"]["nutrition_v2_unavailable_or_partial"] == 3
        assert result["summary"]["consumer_activation"] == "BLOCKED"
        assert sha256(config.path.read_bytes()).hexdigest() == original
        with sqlite3.connect(config.path) as db:
            assert db.execute("SELECT count(*) FROM shopping_lists").fetchone() == (0,)
    finally:
        engine.dispose()


def test_inventory_is_deterministic_in_fresh_python_process(tmp_path):
    config, engine, home, composed = _week(tmp_path)
    try:
        expected = inventory_from_database(
            database_path=config.path,
            household_id=home.id,
            plan_id=composed.plan.id,
            captured_at=CAPTURED,
        )
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "scripts.composed_week_evidence",
                "--sqlite",
                str(config.path),
                "--household",
                str(home.id),
                "--plan",
                str(composed.plan.id),
                "--captured-at",
                CAPTURED.isoformat(),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        assert json.loads(completed.stdout) == expected
        assert "NO_GO_TO_CONSUMER_COMPOSED_MEALS" in completed.stdout
    finally:
        engine.dispose()


def test_inventory_reads_complete_21_event_heterogeneous_household_without_phantoms(
    tmp_path,
):
    config, engine, home, people, old, recipes, selections = _week_21_42(tmp_path)
    try:
        composed = _compose(old, people[:1], recipes, selections, target_index=4)
        _write(engine, composed, people)
        result = inventory_from_database(
            database_path=config.path,
            household_id=home.id,
            plan_id=composed.plan.id,
            captured_at=CAPTURED,
        )
        assert result["plan_events"] == 21
        assert len(result["components"]) == 3
        assert {
            s["member_id"]
            for component in result["components"]
            for s in component["member_servings"]
        } == {str(people[0].id)}
        assert result["verdict"] == NO_GO
        assert result["shopping_status"] == "COMPLETE"
    finally:
        engine.dispose()


def test_inventory_rejects_other_household_missing_plan_and_missing_database(tmp_path):
    config, engine, home, composed = _week(tmp_path)
    try:
        for member_home, plan_id in (
            (uuid4(), composed.plan.id),
            (home.id, uuid4()),
        ):
            with pytest.raises(ComposedWeekPreviewBlocked):
                inventory_from_database(
                    database_path=config.path,
                    household_id=member_home,
                    plan_id=plan_id,
                    captured_at=CAPTURED,
                )
        absent = tmp_path / "not-a-database.sqlite"
        with pytest.raises(ComposedWeekPreviewBlocked, match="не найдена"):
            inventory_from_database(
                database_path=absent,
                household_id=home.id,
                plan_id=composed.plan.id,
                captured_at=CAPTURED,
            )
        assert not absent.exists()
    finally:
        engine.dispose()


def test_inventory_never_promotes_complete_nutrition_without_physical_role_sources(
    tmp_path,
):
    config, engine, home, composed = _week(tmp_path)
    try:
        original = inventory_from_database(
            database_path=config.path,
            household_id=home.id,
            plan_id=composed.plan.id,
            captured_at=CAPTURED,
        )
        with SqlAlchemyShoppingReadScope(engine) as scope:
            plan = scope.plans.get_detail(home.id, composed.plan.id)
            versions = {
                part.recipe_version_id
                for comp in plan.compositions
                for part in comp.components
            }
            recipes = {vid: scope.recipes.get_detail(vid) for vid in versions}
            food_ids = {
                i.food_ingredient_id
                for detail in recipes.values()
                for i in detail.ingredients
            }
            foods = {fid: scope.foods.get(fid) for fid in food_ids}
        # Deliberately fabricated *test-only* coverage, never persisted or used
        # as Nutrition truth: even 54/54 doesn't confer role/portion authority.
        complete = {
            vid: {
                "status": "COMPLETE",
                "available_nutrients": 54,
                "total_nutrients": 54,
                "unknown_codes": [],
            }
            for vid in recipes
        }
        preview = {
            "status": "DIAGNOSTIC_ONLY",
            "week_start": original["week_start"],
            "revision": original["revision"],
            "source_fingerprint": original["shopping_source_fingerprint"],
            "shopping_status": original["shopping_status"],
            "price_status": original["shopping_price_status"],
        }
        audited = build_inventory(
            plan=plan,
            recipes=recipes,
            foods=foods,
            preview=preview,
            nutrition=complete,
        )
        assert audited["summary"]["nutrition_v2_unavailable_or_partial"] == 0
        assert audited["summary"]["physical_portions"] == "NOT_PROVEN"
        assert audited["summary"]["course_suitability"] == "UNKNOWN"
        assert audited["verdict"] == NO_GO
    finally:
        engine.dispose()
