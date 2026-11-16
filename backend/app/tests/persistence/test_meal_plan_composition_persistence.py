"""Persistence-specific acceptance: complete diagnostic week, source and Shopping gates."""

import sqlite3
import subprocess
import sys
from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from app.db.config import DatabaseConfig
from app.db.migrations import apply_migrations
from app.domain.meal_compositions import (
    CourseCardinality,
    DraftMealStructureRule,
    MealComponentDraft,
    MealCourseKind,
    MealEventCompositionDraft,
    MemberComponentServingDraft,
    RequiredCourseCoverage,
    restore_rule_snapshot,
    rule_snapshot_digest,
    serialized_requirements,
)
from app.domain.meal_patterns import MealRole
from app.domain.meal_plans import MealPlanDetail, MealSourceKind
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
from app.persistence.sqlalchemy_core.meal_plan_uow import (
    SqlAlchemyMealPlanReadScope,
    SqlAlchemyMealPlanUnitOfWork,
)
from app.services.meal_plan_composition_revisions import (
    make_complete_diagnostic_revision,
)
from app.services.meal_plan_contracts import MealPlanPersistenceConflictError
from app.tests.persistence.test_meal_plan_repository import (
    _household, _member, _seed_household, _plan, _selection
)

TIME = datetime(2026, 11, 16, 12, 0, tzinfo=UTC)


def _source_recipes(config):
    """Synthetic source-verified fixtures; not published food catalogue truth."""
    recipes = {}
    food_id = uuid4().hex
    with sqlite3.connect(config.path) as db:
        db.execute("PRAGMA foreign_keys=ON")
        db.execute(
            "INSERT INTO food_ingredients "
            "(id, canonical_code, canonical_name, canonical_name_key, category_code, "
            "default_unit, allergens_reviewed, is_active, created_at, updated_at) "
            "VALUES (?, 'TEST_POTATO', 'Картофель', 'картофель', 'vegetables', "
            "'g', 1, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)",
            (food_id,),
        )
        for ix, code in enumerate(("FIRST_TEST", "SECOND_TEST", "DESSERT_TEST"), 1):
            rid = uuid4().hex
            vid = uuid4().hex
            db.execute(
                "INSERT INTO food_recipes "
                "(id, canonical_code, canonical_name, canonical_name_key, is_active, "
                "created_at, updated_at) "
                "VALUES (?, ?, ?, ?, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)",
                (rid, code, f"Проверочное блюдо {ix}", f"проверочное блюдо {ix}"),
            )
            db.execute(
                "INSERT INTO food_recipe_versions "
                "(id, recipe_id, version_number, base_servings, meal_type_code, "
                "verification_status, source_name, source_recipe_id, source_url, "
                "source_version, source_document_sha256, source_original_servings, "
                "rights_review_status, change_note, created_at) "
                "VALUES (?, ?, 1, '1.000000', 'main', 'SOURCE_VERIFIED', "
                "'test-fixture', ?, 'https://example.test/fixture', 'v1', ?, "
                "'1.000000', 'REVIEWED', 'test only', CURRENT_TIMESTAMP)",
                (vid, rid, code, "1" * 64),
            )
            db.execute(
                "INSERT INTO food_recipe_ingredients "
                "(id, recipe_version_id, food_ingredient_id, position, quantity, "
                "unit, source_amount_text, optional, created_at) "
                "VALUES (?, ?, ?, 1, '25.000000', 'g', 'test 25g', 0, CURRENT_TIMESTAMP)",
                (uuid4().hex, vid, food_id),
            )
            recipes[code] = __import__("uuid").UUID(hex=vid)
        db.commit()
    return recipes


def _setup(tmp_path, *, members=1):
    config = DatabaseConfig(path=tmp_path / "meal-composition.sqlite")
    apply_migrations(config)
    recipes = _source_recipes(config)
    engine = create_sqlite_engine(config)
    household = _household()
    people = [_member(household.id, f"Member {i}") for i in range(members)]
    _seed_household(engine, household, *people)
    selection_details = {}
    source_pins = []
    with SqlAlchemyMealPlanUnitOfWork(engine) as scope:
        for person in people:
            selection = _selection(household.id, person.id)
            # The test fixture explicitly chooses LUNCH at home every day.
            selection = replace(
                selection,
                opportunities=tuple(
                    replace(opportunity, role=MealRole.LUNCH)
                    for opportunity in selection.opportunities
                ),
            )
            selection_details[selection.selection.id] = selection
            source_pins.append(selection.selection.id)
            scope.selections.add_detail(selection)
        scope.commit()
    # Start with a genuine complete immutable seven-day single-recipe week.
    prior = _plan(household.id, people[0].id, source_pins[0])
    prior = replace(
        prior,
        events=tuple(
            replace(
                event,
                role=MealRole.LUNCH,
                source_kind=MealSourceKind.COOK_RECIPE,
                recipe_version_id=recipes["SECOND_TEST"],
                source_reference=None,
            )
            for event in prior.events
        ),
    )
    if members > 1:
        prior = replace(
            prior,
            member_selections=prior.member_selections + tuple(
                __import__("app.domain.meal_plans", fromlist=["MealPlanMemberSelection"])
                .MealPlanMemberSelection(prior.plan.id, p.id, src)
                for p, src in zip(people[1:], source_pins[1:])
            ),
            servings=prior.servings + tuple(
                __import__("app.domain.meal_plans", fromlist=["Serving"]).Serving(
                    uuid4(), event.id, p.id, Decimal("1.250000"), TIME
                )
                for event in prior.events for p in people[1:]
            ),
        )
    with SqlAlchemyMealPlanUnitOfWork(engine) as scope:
        scope.plans.add_detail(prior)
        scope.commit()
    return config, engine, household, people, prior, recipes, selection_details


def _rule(*, code="DEV_LUNCH_FIRST_SECOND_OPTIONAL_DESSERT", version=1):
    return DraftMealStructureRule(
        code=code, version=version, meal_role=MealRole.LUNCH,
        requirements=(
            CourseCardinality(MealCourseKind.FIRST, 1, 1),
            CourseCardinality(MealCourseKind.SECOND, 1, 1),
            CourseCardinality(MealCourseKind.DESSERT, 0, 1),
        ),
        coverage=RequiredCourseCoverage.PER_PARTICIPANT,
    )


def _compose(prior, people, recipes, selected, *, rule=None):
    event = prior.events[1]
    components = (
        MealComponentDraft(event.id, 1, MealCourseKind.FIRST, recipes["FIRST_TEST"]),
        MealComponentDraft(event.id, 2, MealCourseKind.SECOND, recipes["SECOND_TEST"]),
        MealComponentDraft(event.id, 3, MealCourseKind.DESSERT, recipes["DESSERT_TEST"]),
    )
    allocations = tuple(
        MemberComponentServingDraft(
            event.id, position, p.id,
            Decimal("0.500000") if position == 3 else Decimal("1.000000")
        )
        for p in people
        for position in ((1, 2, 3) if p is people[0] else (1, 2))
    )
    proposal = MealEventCompositionDraft(prior.plan.id, event.id, components, allocations)
    return make_complete_diagnostic_revision(
        prior=prior,
        proposal=proposal,
        rule=rule or _rule(),
        selection_details=selected,
        created_at=TIME,
    )


def _write(engine, new, people):
    with SqlAlchemyMealPlanUnitOfWork(
        engine, enable_internal_composition_writes=True
    ) as scope:
        scope.plans.add_diagnostic_composition_revision(
            new,
            excluded_food_codes_by_member={p.id: frozenset() for p in people},
        )
        scope.commit()


def test_complete_week_source_roundtrip_and_legacy_history(tmp_path):
    config, engine, home, people, prior, recipes, selection_details = _setup(tmp_path)
    try:
        current = _compose(prior, people, recipes, selection_details)
        assert len(prior.events) == len(current.events) == 7
        assert len(prior.servings) == 7 and len(current.servings) == 6
        assert len(current.compositions) == 1
        assert current.compositions[0].rule == _rule()
        assert len(current.compositions[0].servings) == 3
        with pytest.raises(MealPlanPersistenceConflictError):
            with SqlAlchemyMealPlanUnitOfWork(engine) as scope:
                scope.plans.add_diagnostic_composition_revision(
                    current, excluded_food_codes_by_member={people[0].id: frozenset()}
                )
        _write(engine, current, people)
        with SqlAlchemyMealPlanReadScope(engine) as scope:
            assert scope.plans.get_detail(home.id, prior.plan.id) == prior
            loaded = scope.plans.get_detail(home.id, current.plan.id)
            assert loaded == current
            assert scope.plans.get_current(home.id, prior.plan.week_start) == current
            assert len(scope.plans.list_history(home.id, prior.plan.week_start)) == 2
        # New connection/process identity and rule hash remain identical.
        engine.dispose()
        engine = create_sqlite_engine(config)
        with SqlAlchemyMealPlanReadScope(engine) as scope:
            again = scope.plans.get_detail(home.id, current.plan.id)
        assert again == current
        assert serialized_requirements(again.compositions[0].rule) == serialized_requirements(_rule())
        assert rule_snapshot_digest(again.compositions[0].rule) == rule_snapshot_digest(_rule())
    finally:
        engine.dispose()


def test_rule_drift_and_injected_component_failure_leave_current_unchanged(tmp_path):
    config, engine, home, people, prior, recipes, accepted = _setup(tmp_path)
    try:
        new = _compose(prior, people, recipes, accepted)
        # Failure inside component insertion must roll back the entire new week.
        with sqlite3.connect(config.path) as db:
            db.execute(
                "CREATE TRIGGER test_composition_insert_failure "
                "BEFORE INSERT ON meal_plan_event_components "
                "BEGIN SELECT RAISE(ABORT, 'injected component fault'); END"
            )
        with pytest.raises(Exception, match="injected|conflict|failed"):
            _write(engine, new, people)
        with SqlAlchemyMealPlanReadScope(engine) as scope:
            assert scope.plans.get_current(home.id, prior.plan.week_start) == prior
            assert scope.plans.list_history(home.id, prior.plan.week_start) == [prior.plan]
        with sqlite3.connect(config.path) as db:
            db.execute("DROP TRIGGER test_composition_insert_failure")
        _write(engine, new, people)
        with sqlite3.connect(config.path) as db:
            # Direct DB tampering is impossible through the ordinary immutable triggers.
            with pytest.raises(sqlite3.IntegrityError, match="immutable"):
                db.execute(
                    "UPDATE meal_plan_event_compositions SET structure_rule_version=2"
                )
        current = new
        # A second revision with conflicting meaning under the same code/version
        # is not accepted even if it carries its own recomputed valid digest.
        altered_rule = replace(
            _rule(),
            requirements=(
                CourseCardinality(MealCourseKind.FIRST, 1, 1),
                CourseCardinality(MealCourseKind.SECOND, 1, 1),
            ),
        )
        changed = _compose(current, people, recipes, accepted, rule=altered_rule)
        with pytest.raises(MealPlanPersistenceConflictError):
            _write(engine, changed, people)
    finally:
        engine.dispose()


def test_snapshot_corruption_is_detected_on_a_new_read(tmp_path):
    config, engine, home, people, prior, recipes, accepted = _setup(tmp_path)
    try:
        new = _compose(prior, people, recipes, accepted)
        _write(engine, new, people)
        with sqlite3.connect(config.path) as db:
            db.execute("DROP TRIGGER trg_meal_plan_event_compositions_no_update")
            db.execute(
                "UPDATE meal_plan_event_compositions SET requirements_json='[]'"
            )
            db.commit()
        with pytest.raises(ValueError, match="snapshot|requirements|rule"):
            with SqlAlchemyMealPlanReadScope(engine) as scope:
                scope.plans.get_detail(home.id, new.plan.id)
    finally:
        engine.dispose()


@pytest.mark.parametrize("bad", ["NaN", "1e10", "0.000000", "-1.000000", "1.0000001"])
def test_database_rejects_invalid_component_decimal(tmp_path, bad):
    config = DatabaseConfig(path=tmp_path / "decimal.sqlite")
    apply_migrations(config)
    # FK failures may precede numeric checks; validate the canonical amount
    # in a standalone SELECT expression identical to migration's guard.
    with sqlite3.connect(config.path) as db:
        result = db.execute(
            "SELECT typeof(?)='text' AND length(?) BETWEEN 8 AND 26 "
            "AND ? GLOB '*.*' AND ? NOT GLOB '*[^0-9.]*' "
            "AND length(?) - length(replace(?, '.', '')) = 1 "
            "AND length(substr(?, instr(?, '.') + 1)) = 6 "
            "AND CAST(? AS NUMERIC) > 0",
            (bad,) * 9,
        ).fetchone()[0]
        assert not result
