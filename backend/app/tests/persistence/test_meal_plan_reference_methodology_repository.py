from dataclasses import replace
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

import pytest

from app.db.config import DatabaseConfig
from app.db.migrations import apply_migrations
from app.domain.households import Household, HouseholdMember
from app.domain.meal_patterns import MealRole
from app.domain.meal_plans import (
    HouseholdMealEvent,
    MealPlan,
    MealPlanDetail,
    MealPlanMemberReferenceMethodologyPin,
    MealPlanMemberSelection,
    MealPlanStatus,
    MealSourceKind,
    MemberMealPatternOpportunitySnapshot,
    MemberMealPatternSelection,
    MemberMealPatternSelectionDetail,
    MemberMealPatternSourceKind,
    Serving,
)
from app.domain.reference_methodology import MemberReferenceMethodologySelection
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
from app.persistence.sqlalchemy_core.household_uow import SqlAlchemyHouseholdUnitOfWork
from app.persistence.sqlalchemy_core.meal_plan_uow import (
    SqlAlchemyMealPlanReadScope,
    SqlAlchemyMealPlanUnitOfWork,
)
from app.persistence.sqlalchemy_core.reference_methodology_uow import (
    SqlAlchemyReferenceMethodologyUnitOfWork,
)
from app.services.meal_plan_contracts import MealPlanPersistenceConflictError


NOW = datetime(2026, 9, 23, 10, 0, tzinfo=timezone.utc)
WEEK_START = date(2026, 9, 14)


@pytest.fixture
def database(tmp_path):
    config = DatabaseConfig(path=tmp_path / "step6b-persistence.sqlite")
    apply_migrations(config)
    engine = create_sqlite_engine(config)
    try:
        yield config, engine
    finally:
        engine.dispose()


def _household():
    return Household(
        uuid4(),
        "Home",
        "Europe/Moscow",
        None,
        None,
        None,
        NOW,
        NOW,
    )


def _member(household_id):
    return HouseholdMember(
        uuid4(),
        household_id,
        "Anna",
        True,
        date(1990, 5, 20),
        "female",
        Decimal("168"),
        Decimal("62"),
        "moderate",
        "maintain",
        NOW,
        NOW,
    )


def _seed(engine, home, person):
    with SqlAlchemyHouseholdUnitOfWork(engine) as scope:
        scope.households.add_household(home)
        scope.members.add_member(person)
        scope.commit()


def _pattern(home, person):
    selection = MemberMealPatternSelection(
        uuid4(),
        home.id,
        person.id,
        1,
        MemberMealPatternSourceKind.CUSTOM,
        None,
        None,
        False,
        NOW,
        None,
        NOW,
    )
    return MemberMealPatternSelectionDetail(
        selection,
        tuple(
            MemberMealPatternOpportunitySnapshot(
                selection.id, weekday, 1, MealRole.DINNER
            )
            for weekday in range(1, 8)
        ),
    )


def _reference(home, person):
    return MemberReferenceMethodologySelection(
        id=uuid4(),
        household_id=home.id,
        member_id=person.id,
        version_number=1,
        nutrition_config_version="FAMILY_FOOD_NUTRITION_V1",
        group_reference_methodology_version=None,
        accepted_local_date=date(2026, 9, 23),
        household_timezone_at_acceptance=home.timezone,
        member_updated_at_at_acceptance=person.updated_at,
        household_updated_at_at_acceptance=home.updated_at,
        acceptance_request_id=uuid4(),
        accepted_at=NOW,
        supersedes_selection_id=None,
        created_at=NOW,
    )


def _detail(home, person, pattern, reference, *, bad_recipe=False):
    plan = MealPlan(
        uuid4(),
        home.id,
        WEEK_START,
        1,
        MealPlanStatus.CONFIRMED,
        "manual-v1",
        None,
        NOW + timedelta(hours=1),
    )
    events = []
    servings = []
    for offset in range(7):
        event = HouseholdMealEvent(
            uuid4(),
            plan.id,
            WEEK_START + timedelta(days=offset),
            1,
            MealRole.DINNER,
            MealSourceKind.COOK_RECIPE if bad_recipe else MealSourceKind.EAT_OUT,
            uuid4() if bad_recipe else None,
            None if bad_recipe else "manual",
            plan.created_at,
        )
        events.append(event)
        servings.append(
            Serving(
                uuid4(),
                event.id,
                person.id,
                Decimal("1"),
                plan.created_at,
            )
        )
    return MealPlanDetail(
        plan=plan,
        member_selections=(
            MealPlanMemberSelection(plan.id, person.id, pattern.selection.id),
        ),
        events=tuple(events),
        servings=tuple(servings),
        reference_methodology_pins=(
            MealPlanMemberReferenceMethodologyPin(
                plan.id,
                person.id,
                reference.id,
                person.birth_date,
                person.sex,
                person.height_cm,
                person.weight_kg,
                person.activity_level,
                person.goal,
                person.updated_at,
            ),
        ),
    )


def _seed_selections(engine, pattern, reference):
    with SqlAlchemyMealPlanUnitOfWork(engine) as scope:
        scope.selections.add_detail(pattern)
        scope.commit()
    with SqlAlchemyReferenceMethodologyUnitOfWork(engine) as scope:
        scope.selections.add(reference)
        scope.commit()


def test_reference_pin_roundtrip_and_legacy_zero_pin(database):
    _, engine = database
    home = _household()
    person = _member(home.id)
    _seed(engine, home, person)
    pattern = _pattern(home, person)
    reference = _reference(home, person)
    _seed_selections(engine, pattern, reference)
    detail = _detail(home, person, pattern, reference)

    with SqlAlchemyMealPlanUnitOfWork(engine) as scope:
        scope.plans.add_detail(detail)
        scope.commit()

    with SqlAlchemyMealPlanReadScope(engine) as scope:
        assert scope.plans.get_detail(home.id, detail.plan.id) == detail


def test_repository_rejects_non_authoritative_member_snapshot(database):
    _, engine = database
    home = _household()
    person = _member(home.id)
    _seed(engine, home, person)
    pattern = _pattern(home, person)
    reference = _reference(home, person)
    _seed_selections(engine, pattern, reference)
    detail = _detail(home, person, pattern, reference)
    bad_pin = replace(
        detail.reference_methodology_pins[0],
        weight_kg=Decimal("63"),
    )
    detail = replace(detail, reference_methodology_pins=(bad_pin,))

    with pytest.raises(MealPlanPersistenceConflictError, match="snapshot"):
        with SqlAlchemyMealPlanUnitOfWork(engine) as scope:
            scope.plans.add_detail(detail)


def test_failure_after_reference_pin_insert_rolls_back_entire_plan(database):
    _, engine = database
    home = _household()
    person = _member(home.id)
    _seed(engine, home, person)
    pattern = _pattern(home, person)
    reference = _reference(home, person)
    _seed_selections(engine, pattern, reference)
    detail = _detail(home, person, pattern, reference, bad_recipe=True)

    with pytest.raises(MealPlanPersistenceConflictError):
        with SqlAlchemyMealPlanUnitOfWork(engine) as scope:
            scope.plans.add_detail(detail)
            scope.commit()

    with SqlAlchemyMealPlanReadScope(engine) as scope:
        assert scope.plans.get_detail(home.id, detail.plan.id) is None


def test_real_sqlite_concurrent_member_change_conflicts_before_plan_write(database):
    _, engine = database
    home = _household()
    person = _member(home.id)
    _seed(engine, home, person)

    with SqlAlchemyMealPlanUnitOfWork(engine) as plan_scope:
        accepted = plan_scope.members.get_member(home.id, person.id)
        assert accepted is not None

        with SqlAlchemyHouseholdUnitOfWork(engine) as concurrent_scope:
            concurrent_scope._scope.adapter_connection.exec_driver_sql(
                "PRAGMA busy_timeout = 50"
            )
            concurrent_scope.members.update_member(
                replace(
                    person,
                    goal="lose_weight",
                    updated_at=NOW + timedelta(minutes=1),
                )
            )
            plan_scope._scope.adapter_connection.exec_driver_sql(
                "PRAGMA busy_timeout = 50"
            )
            with pytest.raises(
                MealPlanPersistenceConflictError,
                match="concurrently being changed",
            ):
                plan_scope.guard_member_state(
                    household_id=home.id,
                    member_id=person.id,
                    member_updated_at=accepted.updated_at,
                )
