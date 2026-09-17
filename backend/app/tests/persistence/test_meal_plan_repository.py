import sqlite3
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
    MealPlanMemberSelection,
    MealPlanStatus,
    MealSourceKind,
    MemberMealPatternOpportunitySnapshot,
    MemberMealPatternSelection,
    MemberMealPatternSelectionDetail,
    MemberMealPatternSourceKind,
    Serving,
)
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
from app.persistence.sqlalchemy_core.household_uow import SqlAlchemyHouseholdUnitOfWork
from app.persistence.sqlalchemy_core.meal_plan_uow import (
    SqlAlchemyMealPlanReadScope,
    SqlAlchemyMealPlanUnitOfWork,
)
from app.services.meal_plan_contracts import MealPlanPersistenceConflictError

NOW = datetime(2026, 9, 17, 12, 0, tzinfo=timezone.utc)
WEEK_START = date(2026, 9, 14)


@pytest.fixture
def meal_plan_engine(tmp_path):
    config = DatabaseConfig(path=tmp_path / "meal-plan.sqlite")
    apply_migrations(config)
    engine = create_sqlite_engine(config)
    try:
        yield config, engine
    finally:
        engine.dispose()


def _household(name="Home"):
    return Household(
        id=uuid4(),
        name=name,
        timezone="Europe/Moscow",
        city="Saint Petersburg",
        default_weekly_budget=Decimal("12000.00"),
        default_cooking_profile="standard",
        created_at=NOW,
        updated_at=NOW,
    )


def _member(household_id, name="Anna"):
    return HouseholdMember(
        id=uuid4(),
        household_id=household_id,
        name=name,
        active=True,
        birth_date=date(1990, 5, 20),
        sex="female",
        height_cm=Decimal("168.0"),
        weight_kg=Decimal("62.000"),
        activity_level="moderate",
        goal="maintain",
        created_at=NOW,
        updated_at=NOW,
    )


def _seed_household(engine, household, *members):
    with SqlAlchemyHouseholdUnitOfWork(engine) as scope:
        scope.households.add_household(household)
        for member in members:
            scope.members.add_member(member)
        scope.commit()


def _selection(household_id, member_id, *, version=1, supersedes=None):
    selection = MemberMealPatternSelection(
        id=uuid4(),
        household_id=household_id,
        member_id=member_id,
        version_number=version,
        source_kind=MemberMealPatternSourceKind.CUSTOM,
        program_version_id=None,
        recommender_version=None,
        has_user_overrides=False,
        accepted_at=NOW + timedelta(minutes=version),
        supersedes_selection_id=supersedes,
        created_at=NOW + timedelta(minutes=version),
    )
    opportunities = tuple(
        MemberMealPatternOpportunitySnapshot(
            selection_id=selection.id,
            weekday=weekday,
            position=1,
            role=MealRole.DINNER,
        )
        for weekday in range(1, 8)
    )
    return MemberMealPatternSelectionDetail(selection, opportunities)


def _plan(household_id, member_id, selection_id, *, revision=1, supersedes=None):
    plan = MealPlan(
        id=uuid4(),
        household_id=household_id,
        week_start=WEEK_START,
        revision_number=revision,
        status=MealPlanStatus.CONFIRMED,
        config_version="manual-v1",
        supersedes_plan_id=supersedes,
        created_at=NOW + timedelta(hours=revision),
    )
    events = []
    servings = []
    for offset in range(7):
        event = HouseholdMealEvent(
            id=uuid4(),
            plan_id=plan.id,
            local_date=WEEK_START + timedelta(days=offset),
            position=1,
            role=MealRole.DINNER,
            source_kind=MealSourceKind.EAT_OUT,
            recipe_version_id=None,
            source_reference="manual schedule",
            created_at=plan.created_at,
        )
        events.append(event)
        servings.append(
            Serving(
                id=uuid4(),
                event_id=event.id,
                member_id=member_id,
                portion_servings=Decimal("1.250000"),
                created_at=plan.created_at,
            )
        )
    return MealPlanDetail(
        plan=plan,
        member_selections=(
            MealPlanMemberSelection(plan.id, member_id, selection_id),
        ),
        events=tuple(events),
        servings=tuple(servings),
    )


def test_selection_roundtrip_current_and_history(meal_plan_engine):
    _, engine = meal_plan_engine
    household = _household()
    member = _member(household.id)
    _seed_household(engine, household, member)
    first = _selection(household.id, member.id)
    second = _selection(
        household.id,
        member.id,
        version=2,
        supersedes=first.selection.id,
    )

    with SqlAlchemyMealPlanUnitOfWork(engine) as scope:
        scope.selections.add_detail(first)
        scope.selections.add_detail(second)
        scope.commit()

    with SqlAlchemyMealPlanReadScope(engine) as scope:
        assert scope.selections.get_detail(household.id, first.selection.id) == first
        assert scope.selections.get_current(household.id, member.id) == second
        assert scope.selections.list_history(household.id, member.id) == [
            first.selection,
            second.selection,
        ]


def test_plan_roundtrip_current_and_history(meal_plan_engine):
    _, engine = meal_plan_engine
    household = _household()
    member = _member(household.id)
    _seed_household(engine, household, member)
    selection = _selection(household.id, member.id)
    with SqlAlchemyMealPlanUnitOfWork(engine) as scope:
        scope.selections.add_detail(selection)
        scope.commit()

    first = _plan(household.id, member.id, selection.selection.id)
    second = _plan(
        household.id,
        member.id,
        selection.selection.id,
        revision=2,
        supersedes=first.plan.id,
    )
    with SqlAlchemyMealPlanUnitOfWork(engine) as scope:
        scope.plans.add_detail(first)
        scope.plans.add_detail(second)
        scope.commit()

    with SqlAlchemyMealPlanReadScope(engine) as scope:
        assert scope.plans.get_detail(household.id, first.plan.id) == first
        assert scope.plans.get_current(household.id, WEEK_START) == second
        assert scope.plans.list_history(household.id, WEEK_START) == [
            first.plan,
            second.plan,
        ]


def test_cross_household_selection_is_rejected(meal_plan_engine):
    _, engine = meal_plan_engine
    first = _household("First")
    second = _household("Second")
    member = _member(first.id)
    _seed_household(engine, first, member)
    _seed_household(engine, second)
    wrong = _selection(second.id, member.id)

    with pytest.raises(MealPlanPersistenceConflictError):
        with SqlAlchemyMealPlanUnitOfWork(engine) as scope:
            scope.selections.add_detail(wrong)
            scope.commit()


def test_uncommitted_plan_rolls_back(meal_plan_engine):
    _, engine = meal_plan_engine
    household = _household()
    member = _member(household.id)
    _seed_household(engine, household, member)
    selection = _selection(household.id, member.id)
    with SqlAlchemyMealPlanUnitOfWork(engine) as scope:
        scope.selections.add_detail(selection)
        scope.commit()
    plan = _plan(household.id, member.id, selection.selection.id)

    with SqlAlchemyMealPlanUnitOfWork(engine) as scope:
        scope.plans.add_detail(plan)

    with SqlAlchemyMealPlanReadScope(engine) as scope:
        assert scope.plans.get_detail(household.id, plan.plan.id) is None


def test_append_only_triggers_reject_history_mutation(meal_plan_engine):
    config, engine = meal_plan_engine
    household = _household()
    member = _member(household.id)
    _seed_household(engine, household, member)
    selection = _selection(household.id, member.id)
    with SqlAlchemyMealPlanUnitOfWork(engine) as scope:
        scope.selections.add_detail(selection)
        scope.commit()

    with sqlite3.connect(config.path) as connection:
        with pytest.raises(sqlite3.IntegrityError, match="immutable"):
            connection.execute(
                "UPDATE member_meal_pattern_selections SET version_number = 99 WHERE id = ?",
                (selection.selection.id.hex,),
            )

def test_selection_and_plan_revision_chains_reject_gaps(meal_plan_engine):
    _, engine = meal_plan_engine
    household = _household()
    member = _member(household.id)
    _seed_household(engine, household, member)
    first_selection = _selection(household.id, member.id)
    with SqlAlchemyMealPlanUnitOfWork(engine) as scope:
        scope.selections.add_detail(first_selection)
        scope.commit()

    missing_link = _selection(household.id, member.id, version=2)
    with pytest.raises(MealPlanPersistenceConflictError, match="require the previous selection"):
        with SqlAlchemyMealPlanUnitOfWork(engine) as scope:
            scope.selections.add_detail(missing_link)
            scope.commit()

    skipped_selection = _selection(
        household.id,
        member.id,
        version=3,
        supersedes=first_selection.selection.id,
    )
    with pytest.raises(MealPlanPersistenceConflictError, match="immediately previous selection"):
        with SqlAlchemyMealPlanUnitOfWork(engine) as scope:
            scope.selections.add_detail(skipped_selection)
            scope.commit()

    first_plan = _plan(household.id, member.id, first_selection.selection.id)
    with SqlAlchemyMealPlanUnitOfWork(engine) as scope:
        scope.plans.add_detail(first_plan)
        scope.commit()

    missing_plan_link = _plan(
        household.id,
        member.id,
        first_selection.selection.id,
        revision=2,
    )
    with pytest.raises(MealPlanPersistenceConflictError, match="require the previous plan"):
        with SqlAlchemyMealPlanUnitOfWork(engine) as scope:
            scope.plans.add_detail(missing_plan_link)
            scope.commit()

    skipped_plan = _plan(
        household.id,
        member.id,
        first_selection.selection.id,
        revision=3,
        supersedes=first_plan.plan.id,
    )
    with pytest.raises(MealPlanPersistenceConflictError, match="immediately previous MealPlan"):
        with SqlAlchemyMealPlanUnitOfWork(engine) as scope:
            scope.plans.add_detail(skipped_plan)
            scope.commit()
