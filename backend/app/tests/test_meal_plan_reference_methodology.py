from dataclasses import replace
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

import pytest

from app.db.config import DatabaseConfig
from app.db.migrations import apply_migrations
from app.domain.households import Household, HouseholdMember
from app.domain.meal_patterns import MealRole
from app.domain.meal_plans import MealSourceKind, MemberMealPatternSourceKind
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
from app.persistence.sqlalchemy_core.household_uow import (
    SqlAlchemyHouseholdReadScope,
    SqlAlchemyHouseholdUnitOfWork,
)
from app.persistence.sqlalchemy_core.meal_pattern_uow import (
    SqlAlchemyMealPatternCatalogueReadScope,
)
from app.persistence.sqlalchemy_core.meal_plan_uow import (
    SqlAlchemyMealPlanReadScope,
    SqlAlchemyMealPlanUnitOfWork,
)
from app.persistence.sqlalchemy_core.reference_methodology_uow import (
    SqlAlchemyReferenceMethodologyReadScope,
    SqlAlchemyReferenceMethodologyUnitOfWork,
)
from app.seed.russian_reference_table_step5 import russian_reference_table_provider
from app.services.meal_plans import MealEventDraft, MealPlanService, MealPlanValidationError
from app.services.reference_methodology import (
    BASELINE_NUTRITION_CONFIG_VERSION,
    RUSSIAN_GROUP_REFERENCE_VERSION,
    ReferenceMethodologyService,
)


BASE = datetime(2026, 9, 23, 9, 0, tzinfo=timezone.utc)
WEEK_START = date(2026, 9, 14)


@pytest.fixture
def runtime(tmp_path):
    config = DatabaseConfig(path=tmp_path / "step6b.sqlite")
    apply_migrations(config)
    engine = create_sqlite_engine(config)
    try:
        yield config, engine
    finally:
        engine.dispose()


def _household():
    return Household(
        id=uuid4(),
        name="Home",
        timezone="Europe/Moscow",
        city=None,
        default_weekly_budget=None,
        default_cooking_profile=None,
        created_at=BASE,
        updated_at=BASE,
    )


def _member(
    household_id,
    *,
    name="Anna",
    birth_date=date(1990, 5, 20),
    weight=Decimal("62"),
):
    return HouseholdMember(
        id=uuid4(),
        household_id=household_id,
        name=name,
        active=True,
        birth_date=birth_date,
        sex="female",
        height_cm=Decimal("168"),
        weight_kg=weight,
        activity_level="moderate",
        goal="maintain",
        created_at=BASE,
        updated_at=BASE,
    )


def _seed(engine, household, *members):
    with SqlAlchemyHouseholdUnitOfWork(engine) as scope:
        scope.households.add_household(household)
        for member in members:
            scope.members.add_member(member)
        scope.commit()


def _reference_service(engine):
    return ReferenceMethodologyService(
        write_scope_factory=lambda: SqlAlchemyReferenceMethodologyUnitOfWork(engine),
        read_scope_factory=lambda: SqlAlchemyReferenceMethodologyReadScope(engine),
        russian_reference_tables=russian_reference_table_provider,
        clock=lambda: BASE + timedelta(hours=1),
    )


def _meal_service(engine, *, clock=None):
    return MealPlanService(
        write_scope_factory=lambda: SqlAlchemyMealPlanUnitOfWork(engine),
        read_scope_factory=lambda: SqlAlchemyMealPlanReadScope(engine),
        household_read_scope_factory=lambda: SqlAlchemyHouseholdReadScope(engine),
        pattern_read_scope_factory=lambda: SqlAlchemyMealPatternCatalogueReadScope(
            engine
        ),
        russian_reference_tables=russian_reference_table_provider,
        clock=clock or (lambda: BASE + timedelta(hours=2)),
    )


def _pattern(service, household_id, member_id):
    return service.accept_member_pattern(
        household_id=household_id,
        member_id=member_id,
        source_kind=MemberMealPatternSourceKind.CUSTOM,
        schedule={weekday: (MealRole.DINNER,) for weekday in range(1, 8)},
    )


def _events(*members):
    return [
        MealEventDraft(
            local_date=WEEK_START + timedelta(days=offset),
            position=1,
            role=MealRole.DINNER,
            source_kind=MealSourceKind.EAT_OUT,
            source_reference="manual",
            servings={member.id: Decimal("1") for member in members},
        )
        for offset in range(7)
    ]


def _baseline_reference(service, household_id, member_id):
    return service.accept_member_selection(
        household_id=household_id,
        member_id=member_id,
        acceptance_request_id=uuid4(),
        expected_current_selection_id=None,
        nutrition_config_version=BASELINE_NUTRITION_CONFIG_VERSION,
        group_reference_methodology_version=None,
    )


def test_legacy_zero_pin_and_complete_reference_pin_roundtrip(runtime):
    _, engine = runtime
    household = _household()
    member = _member(household.id)
    _seed(engine, household, member)
    meal_service = _meal_service(engine)
    pattern = _pattern(meal_service, household.id, member.id)
    reference = _baseline_reference(
        _reference_service(engine), household.id, member.id
    )

    legacy = meal_service.create_plan_revision(
        household_id=household.id,
        week_start=WEEK_START,
        member_selection_ids={member.id: pattern.selection.id},
        events=_events(member),
    )
    assert legacy.reference_methodology_pins == ()

    pinned = meal_service.create_plan_revision(
        household_id=household.id,
        week_start=WEEK_START,
        member_selection_ids={member.id: pattern.selection.id},
        reference_methodology_selection_ids={member.id: reference.id},
        events=_events(member),
    )
    assert pinned.plan.revision_number == 2
    assert len(pinned.reference_methodology_pins) == 1
    pin = pinned.reference_methodology_pins[0]
    assert pin.reference_methodology_selection_id == reference.id
    assert pin.birth_date == member.birth_date
    assert pin.sex == member.sex
    assert pin.height_cm == member.height_cm
    assert pin.weight_kg == member.weight_kg
    assert pin.activity_level == member.activity_level
    assert pin.goal == member.goal
    assert pin.member_updated_at == member.updated_at
    assert meal_service.get_plan(household.id, pinned.plan.id) == pinned


def test_reference_pin_set_must_be_complete_and_member_scoped(runtime):
    _, engine = runtime
    household = _household()
    first = _member(household.id, name="Anna")
    second = _member(household.id, name="Boris")
    _seed(engine, household, first, second)
    meals = _meal_service(engine)
    first_pattern = _pattern(meals, household.id, first.id)
    second_pattern = _pattern(meals, household.id, second.id)
    refs = _reference_service(engine)
    first_ref = _baseline_reference(refs, household.id, first.id)
    second_ref = _baseline_reference(refs, household.id, second.id)
    selections = {
        first.id: first_pattern.selection.id,
        second.id: second_pattern.selection.id,
    }

    with pytest.raises(MealPlanValidationError, match="cover all"):
        meals.create_plan_revision(
            household_id=household.id,
            week_start=WEEK_START,
            member_selection_ids=selections,
            reference_methodology_selection_ids={first.id: first_ref.id},
            events=_events(first, second),
        )

    with pytest.raises(MealPlanValidationError, match="accepted supported"):
        meals.create_plan_revision(
            household_id=household.id,
            week_start=WEEK_START,
            member_selection_ids=selections,
            reference_methodology_selection_ids={
                first.id: second_ref.id,
                second.id: first_ref.id,
            },
            events=_events(first, second),
        )


def test_russian_selection_is_revalidated_at_plan_week_start(runtime):
    _, engine = runtime
    household = _household()
    member = _member(
        household.id,
        birth_date=date(2007, 9, 15),
    )
    _seed(engine, household, member)
    meals = _meal_service(engine)
    pattern = _pattern(meals, household.id, member.id)
    refs = _reference_service(engine)
    russian = refs.accept_member_selection(
        household_id=household.id,
        member_id=member.id,
        acceptance_request_id=uuid4(),
        expected_current_selection_id=None,
        nutrition_config_version=BASELINE_NUTRITION_CONFIG_VERSION,
        group_reference_methodology_version=RUSSIAN_GROUP_REFERENCE_VERSION,
    )

    with pytest.raises(MealPlanValidationError, match="week_start"):
        meals.create_plan_revision(
            household_id=household.id,
            week_start=WEEK_START,
            member_selection_ids={member.id: pattern.selection.id},
            reference_methodology_selection_ids={member.id: russian.id},
            events=_events(member),
        )


def test_old_plan_snapshot_survives_member_change_and_new_revision(runtime):
    _, engine = runtime
    household = _household()
    member = _member(household.id, weight=Decimal("62"))
    _seed(engine, household, member)
    refs = _reference_service(engine)
    reference = _baseline_reference(refs, household.id, member.id)
    first_service = _meal_service(engine)
    pattern = _pattern(first_service, household.id, member.id)
    first = first_service.create_plan_revision(
        household_id=household.id,
        week_start=WEEK_START,
        member_selection_ids={member.id: pattern.selection.id},
        reference_methodology_selection_ids={member.id: reference.id},
        events=_events(member),
    )

    changed = replace(
        member,
        weight_kg=Decimal("64"),
        updated_at=BASE + timedelta(hours=3),
    )
    with SqlAlchemyHouseholdUnitOfWork(engine) as scope:
        scope.members.update_member(changed)
        scope.commit()

    second_service = _meal_service(
        engine, clock=lambda: BASE + timedelta(hours=4)
    )
    second = second_service.create_plan_revision(
        household_id=household.id,
        week_start=WEEK_START,
        member_selection_ids={member.id: pattern.selection.id},
        reference_methodology_selection_ids={member.id: reference.id},
        events=_events(changed),
    )

    loaded_first = second_service.get_plan(household.id, first.plan.id)
    assert loaded_first.reference_methodology_pins[0].weight_kg == Decimal("62")
    assert second.reference_methodology_pins[0].weight_kg == Decimal("64")
    assert second.plan.supersedes_plan_id == first.plan.id


def test_new_reference_selection_can_be_pinned_by_revision_two_without_rewriting_one(
    runtime,
):
    _, engine = runtime
    household = _household()
    member = _member(household.id)
    _seed(engine, household, member)
    references = _reference_service(engine)
    first_reference = _baseline_reference(references, household.id, member.id)
    meals = _meal_service(engine)
    pattern = _pattern(meals, household.id, member.id)

    first_plan = meals.create_plan_revision(
        household_id=household.id,
        week_start=WEEK_START,
        member_selection_ids={member.id: pattern.selection.id},
        reference_methodology_selection_ids={member.id: first_reference.id},
        events=_events(member),
    )
    second_reference = references.accept_member_selection(
        household_id=household.id,
        member_id=member.id,
        acceptance_request_id=uuid4(),
        expected_current_selection_id=first_reference.id,
        nutrition_config_version=BASELINE_NUTRITION_CONFIG_VERSION,
        group_reference_methodology_version=RUSSIAN_GROUP_REFERENCE_VERSION,
    )
    second_plan = meals.create_plan_revision(
        household_id=household.id,
        week_start=WEEK_START,
        member_selection_ids={member.id: pattern.selection.id},
        reference_methodology_selection_ids={member.id: second_reference.id},
        events=_events(member),
    )

    reloaded_first = meals.get_plan(household.id, first_plan.plan.id)
    assert (
        reloaded_first.reference_methodology_pins[0]
        .reference_methodology_selection_id
        == first_reference.id
    )
    assert (
        second_plan.reference_methodology_pins[0]
        .reference_methodology_selection_id
        == second_reference.id
    )
    assert second_plan.plan.supersedes_plan_id == first_plan.plan.id


def test_reference_selection_from_another_household_is_rejected(runtime):
    _, engine = runtime
    home = _household()
    member = _member(home.id)
    foreign_home = _household()
    foreign_member = _member(foreign_home.id)
    _seed(engine, home, member)
    _seed(engine, foreign_home, foreign_member)

    meals = _meal_service(engine)
    pattern = _pattern(meals, home.id, member.id)
    foreign_reference = _baseline_reference(
        _reference_service(engine),
        foreign_home.id,
        foreign_member.id,
    )

    with pytest.raises(MealPlanValidationError, match="accepted supported"):
        meals.create_plan_revision(
            household_id=home.id,
            week_start=WEEK_START,
            member_selection_ids={member.id: pattern.selection.id},
            reference_methodology_selection_ids={
                member.id: foreign_reference.id
            },
            events=_events(member),
        )
