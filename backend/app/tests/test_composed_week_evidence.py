"""Actual read-only source/role/physical/Nutrition evidence from persisted 0044.

Synthetic fixtures exercise the tool, not independent clinical or kitchen proof.
"""

import json
import sqlite3
import subprocess
import sys
from datetime import UTC, datetime
from decimal import Decimal
from hashlib import sha256
from types import SimpleNamespace
from uuid import uuid4

import pytest
from app.domain.recipe_nutrition_v2 import NUTRIENT_CODES
from app.persistence.sqlalchemy_core.shopping_uow import SqlAlchemyShoppingReadScope
from app.services.recipe_nutrition_v2 import RecipeNutritionV2UnavailableError
from app.tests.persistence.test_meal_plan_composition_persistence import (
    _compose,
    _setup,
    _write,
)
from app.tests.persistence.test_meal_plan_full_week_composition import _week_21_42
from app.tests.persistence.test_shopping_composition_v1b import (
    _compose_with_leftover_obligation,
)

from scripts.composed_week_evidence import (
    NO_GO,
    SCHEMA,
    _nutrition_observation,
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
            assert (
                component["nutrition"]["unavailable_reason"]
                == "MISSING_COMPOSITION_BINDINGS"
            )
            assert component["nutrition"]["available_nutrients"] == 0
            assert component["nutrition"]["total_nutrients"] == 54
            assert len(component["nutrition"]["unknown_codes"]) == 54
        assert result["composition_events"] == 1
        assert len(result["non_composition_events"]) == 6
        assert result["summary"]["non_composition_events"] == 6
        assert result["summary"]["non_composition_by_kind"] == {"COOK_RECIPE": 6}
        assert result["summary"]["all_plan_events_accounted"] is True
        assert all(
            event["detailed_evidence_assessment"] == "NOT_IN_SCOPE"
            and event["shopping_source_replay"] == "INCLUDED"
            and event["recipe_version_id"] is not None
            and len(event["member_servings"]) == 1
            for event in result["non_composition_events"]
        )
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
        assert result["composition_events"] == 1
        assert len(result["non_composition_events"]) == 20
        assert result["summary"]["non_composition_by_kind"] == {"COOK_RECIPE": 20}
        assert result["summary"]["all_plan_events_accounted"] is True
        assert sum(
            len(event["member_servings"]) for event in result["non_composition_events"]
        ) == 41
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


def test_inventory_lists_nonrecipe_leftover_as_unassessed_weekly_obligation(tmp_path):
    config, engine, home, saved, _diagnostic = _compose_with_leftover_obligation(
        tmp_path
    )
    try:
        before = sha256(config.path.read_bytes()).hexdigest()
        result = inventory_from_database(
            database_path=config.path,
            household_id=home.id,
            plan_id=saved.shopping_list.meal_plan_id,
            captured_at=CAPTURED,
        )
        assert result["verdict"] == NO_GO
        assert result["plan_events"] == 7
        assert result["shopping_status"] == "INCOMPLETE"
        assert result["summary"]["non_composition_events"] == 6
        assert result["summary"]["non_composition_by_kind"] == {
            "COOK_RECIPE": 5,
            "LEFTOVER": 1,
        }
        leftover = next(
            event
            for event in result["non_composition_events"]
            if event["source_kind"] == "LEFTOVER"
        )
        assert leftover["recipe_version_id"] is None
        assert leftover["source_reference_present"] is True
        assert leftover["detailed_evidence_assessment"] == "NOT_IN_SCOPE"
        assert leftover["shopping_source_replay"] == "INCLUDED"
        assert sha256(config.path.read_bytes()).hexdigest() == before
    finally:
        engine.dispose()


@pytest.mark.parametrize(
    ("row_count", "bound_count", "prepared", "reason"),
    [
        (1, 0, False, "MISSING_COMPOSITION_BINDINGS"),
        (2, 1, False, "PARTIAL_COMPOSITION_BINDINGS"),
        (1, 1, True, "CONFLICTING_AUTHORITIES"),
        (1, 0, True, "PREPARED_AUTHORITY_ONLY"),
        (1, 1, False, "BOUND_AUTHORITY_INVALID_OR_INAPPLICABLE"),
    ],
)
def test_nutrition_unavailable_reason_is_derived_from_authoritative_read_state(
    row_count, bound_count, prepared, reason
):
    """Do not parse human error messages or mistake corrupt authority for absent."""
    version_id = uuid4()
    ingredient_ids = tuple(uuid4() for _ in range(row_count))
    required = tuple(
        SimpleNamespace(id=ingredient_id, optional=False)
        for ingredient_id in ingredient_ids
    )
    bound_ids = frozenset(ingredient_ids[:bound_count])
    scope = SimpleNamespace(
        versions=SimpleNamespace(
            get_detail=lambda _version: SimpleNamespace(ingredients=required)
        ),
        bindings=SimpleNamespace(
            get=lambda ingredient_id: object() if ingredient_id in bound_ids else None
        ),
        prepared=SimpleNamespace(
            get_authority=lambda _version: object() if prepared else None
        ),
    )

    def fail_calculation(_scope, _version_id):
        raise RecipeNutritionV2UnavailableError("message must not be parsed")

    result = _nutrition_observation(
        scope, SimpleNamespace(calculate_in_scope=fail_calculation), version_id
    )
    assert result["status"] == "UNAVAILABLE"
    assert result["unavailable_reason"] == reason
    assert result["available_nutrients"] == 0
    assert len(result["unknown_codes"]) == 54


def test_nutrition_unexpected_source_corruption_does_not_get_silenced():
    def corrupt(_scope, _version_id):
        raise RuntimeError("unexpected repository/decoder corruption")

    with pytest.raises(RuntimeError, match="corruption"):
        _nutrition_observation(
            SimpleNamespace(),
            SimpleNamespace(calculate_in_scope=corrupt),
            uuid4(),
        )


@pytest.mark.parametrize(
    ("has_prepared", "status", "reason"),
    [
        (False, "COMPLETE", None),
        (True, "UNAVAILABLE", "CONFLICTING_AUTHORITIES"),
    ],
)
def test_nutrition_observation_rejects_conflict_even_after_successful_v2_calculation(
    has_prepared, status, reason
):
    """Composition V2's success alone cannot override competing prepared authority."""
    version_id = uuid4()
    ingredient_id = uuid4()
    scope = SimpleNamespace(
        versions=SimpleNamespace(
            get_detail=lambda _version: SimpleNamespace(
                ingredients=(SimpleNamespace(id=ingredient_id, optional=False),)
            )
        ),
        bindings=SimpleNamespace(get=lambda _ingredient: object()),
        prepared=SimpleNamespace(
            get_authority=lambda _version: object() if has_prepared else None
        ),
    )
    result = SimpleNamespace(
        status="COMPLETE",
        per_base_serving=tuple(
            SimpleNamespace(code=code, amount=Decimal("1")) for code in NUTRIENT_CODES
        ),
    )
    service = SimpleNamespace(calculate_in_scope=lambda _scope, _version: result)
    observed = _nutrition_observation(scope, service, version_id)
    assert observed["status"] == status
    assert observed["unavailable_reason"] == reason
    assert observed["available_nutrients"] == (0 if has_prepared else 54)
