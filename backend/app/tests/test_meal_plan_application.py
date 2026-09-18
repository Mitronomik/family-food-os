from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from app.domain.households import Household, HouseholdMember
from app.domain.meal_patterns import (
    MealPatternLifecycle,
    MealPatternOpportunity,
    MealPatternProgram,
    MealPatternProgramDetail,
    MealPatternProgramVersion,
    MealPatternReviewStatus,
    MealPatternScope,
    MealRole,
)
from app.domain.meal_plans import MealSourceKind, MemberMealPatternSourceKind
from app.services.meal_plans import MealEventDraft, MealPlanService, MealPlanValidationError

NOW = datetime(2026, 9, 17, 12, 0, tzinfo=timezone.utc)
WEEK_START = date(2026, 9, 14)


class SelectionRepo:
    def __init__(self):
        self.details = {}

    def add_detail(self, detail):
        self.details[detail.selection.id] = detail

    def get_detail(self, household_id, selection_id):
        detail = self.details.get(selection_id)
        if detail is None or detail.selection.household_id != household_id:
            return None
        return detail

    def get_current(self, household_id, member_id):
        values = [
            item
            for item in self.details.values()
            if item.selection.household_id == household_id
            and item.selection.member_id == member_id
        ]
        return max(values, key=lambda item: item.selection.version_number, default=None)

    def list_history(self, household_id, member_id):
        current = [
            item.selection
            for item in self.details.values()
            if item.selection.household_id == household_id
            and item.selection.member_id == member_id
        ]
        return sorted(current, key=lambda item: item.version_number)


class PlanRepo:
    def __init__(self):
        self.details = {}

    def add_detail(self, detail):
        self.details[detail.plan.id] = detail

    def get_detail(self, household_id, plan_id):
        detail = self.details.get(plan_id)
        if detail is None or detail.plan.household_id != household_id:
            return None
        return detail

    def get_current(self, household_id, week_start):
        values = [
            item
            for item in self.details.values()
            if item.plan.household_id == household_id
            and item.plan.week_start == week_start
        ]
        return max(values, key=lambda item: item.plan.revision_number, default=None)

    def list_history(self, household_id, week_start):
        values = [
            item.plan
            for item in self.details.values()
            if item.plan.household_id == household_id
            and item.plan.week_start == week_start
        ]
        return sorted(values, key=lambda item: item.revision_number)


class MealPlanScope:
    def __init__(self, selections, plans):
        self.selections = selections
        self.plans = plans
        self.committed = False

    def __enter__(self):
        return self

    def commit(self):
        self.committed = True

    def rollback(self):
        pass

    def __exit__(self, *args):
        return None


class HouseholdRepo:
    def __init__(self, household):
        self.household = household

    def get_household(self, household_id):
        return self.household if household_id == self.household.id else None


class MemberRepo:
    def __init__(self, members):
        self.members = {item.id: item for item in members}

    def get_member(self, household_id, member_id):
        member = self.members.get(member_id)
        if member is None or member.household_id != household_id:
            return None
        return member

    def list_members(self, household_id):
        return [item for item in self.members.values() if item.household_id == household_id]


class HouseholdScope:
    def __init__(self, household, members):
        self.households = HouseholdRepo(household)
        self.members = MemberRepo(members)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None


class PatternVersionRepo:
    def __init__(self, detail=None):
        self.detail = detail

    def get_detail(self, version_id):
        if self.detail is not None and self.detail.version.id == version_id:
            return self.detail
        return None


class PatternScope:
    def __init__(self, detail=None):
        self.versions = PatternVersionRepo(detail)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None


def _household():
    return Household(
        id=uuid4(),
        name="Home",
        timezone="Europe/Moscow",
        city="Saint Petersburg",
        default_weekly_budget=Decimal("10000"),
        default_cooking_profile="standard",
        created_at=NOW,
        updated_at=NOW,
    )


def _member(household_id, *, birth_date=date(1990, 5, 20)):
    return HouseholdMember(
        id=uuid4(),
        household_id=household_id,
        name="Anna",
        active=True,
        birth_date=birth_date,
        sex="female",
        height_cm=Decimal("168"),
        weight_kg=Decimal("62"),
        activity_level="moderate",
        goal="maintain",
        created_at=NOW,
        updated_at=NOW,
    )


def _program(*, min_age=19, max_age=None):
    program = MealPatternProgram(uuid4(), "REGULAR_THREE_MEALS", NOW)
    version = MealPatternProgramVersion(
        id=uuid4(),
        program_id=program.id,
        version_number=1,
        lifecycle=MealPatternLifecycle.PUBLISHED,
        scope=MealPatternScope.WELLNESS_SCHEDULE,
        display_name_ru="Три приёма пищи",
        explanation_ru="Регулярный режим на день.",
        min_age_years=min_age,
        max_age_years=max_age,
        review_status=MealPatternReviewStatus.REVIEWED,
        reviewed_at=NOW,
        published_at=NOW,
        created_from_version_id=None,
        change_note="initial",
        created_at=NOW,
    )
    return MealPatternProgramDetail(
        program=program,
        version=version,
        opportunities=(
            MealPatternOpportunity(version.id, 1, MealRole.BREAKFAST),
            MealPatternOpportunity(version.id, 2, MealRole.LUNCH),
            MealPatternOpportunity(version.id, 3, MealRole.DINNER),
        ),
        tags=(),
        evidence=(),
    )


def _service(household, members, pattern=None):
    selections = SelectionRepo()
    plans = PlanRepo()
    ids = iter(uuid4() for _ in range(200))
    return (
        MealPlanService(
            lambda: MealPlanScope(selections, plans),
            lambda: MealPlanScope(selections, plans),
            lambda: HouseholdScope(household, members),
            lambda: PatternScope(pattern),
            id_factory=lambda: next(ids),
            clock=lambda: NOW,
        ),
        selections,
        plans,
    )


def test_program_selection_expands_catalogue_template_to_seven_days():
    household = _household()
    member = _member(household.id)
    program = _program()
    service, _, _ = _service(household, [member], program)

    detail = service.accept_member_pattern(
        household_id=household.id,
        member_id=member.id,
        source_kind=MemberMealPatternSourceKind.PROGRAM,
        program_version_id=program.version.id,
    )

    assert detail.selection.program_version_id == program.version.id
    assert detail.roles_for_weekday(1) == (
        MealRole.BREAKFAST,
        MealRole.LUNCH,
        MealRole.DINNER,
    )
    assert detail.roles_for_weekday(7) == detail.roles_for_weekday(1)


def test_child_cannot_accept_adult_program_but_can_use_custom():
    household = _household()
    child = _member(household.id, birth_date=date(2018, 1, 1))
    adult_program = _program(min_age=19)
    service, _, _ = _service(household, [child], adult_program)

    with pytest.raises(MealPlanValidationError):
        service.accept_member_pattern(
            household_id=household.id,
            member_id=child.id,
            source_kind=MemberMealPatternSourceKind.PROGRAM,
            program_version_id=adult_program.version.id,
        )

    custom = service.accept_member_pattern(
        household_id=household.id,
        member_id=child.id,
        source_kind=MemberMealPatternSourceKind.CUSTOM,
        schedule={weekday: (MealRole.DINNER,) for weekday in range(1, 8)},
    )
    assert custom.selection.source_kind is MemberMealPatternSourceKind.CUSTOM


def test_selection_versions_advance_and_preserve_superseded_history():
    household = _household()
    member = _member(household.id)
    service, _, _ = _service(household, [member])

    first = service.accept_member_pattern(
        household_id=household.id,
        member_id=member.id,
        source_kind=MemberMealPatternSourceKind.CUSTOM,
        schedule={weekday: (MealRole.DINNER,) for weekday in range(1, 8)},
    )
    second = service.accept_member_pattern(
        household_id=household.id,
        member_id=member.id,
        source_kind=MemberMealPatternSourceKind.CUSTOM,
        schedule={
            weekday: (MealRole.BREAKFAST, MealRole.DINNER)
            for weekday in range(1, 8)
        },
    )

    assert second.selection.version_number == 2
    assert second.selection.supersedes_selection_id == first.selection.id


def test_manual_week_creates_revision_and_shared_event_servings():
    household = _household()
    first_member = _member(household.id)
    second_member = _member(household.id)
    service, _, _ = _service(household, [first_member, second_member])
    first_selection = service.accept_member_pattern(
        household_id=household.id,
        member_id=first_member.id,
        source_kind=MemberMealPatternSourceKind.CUSTOM,
        schedule={weekday: (MealRole.DINNER,) for weekday in range(1, 8)},
    )
    second_selection = service.accept_member_pattern(
        household_id=household.id,
        member_id=second_member.id,
        source_kind=MemberMealPatternSourceKind.CUSTOM,
        schedule={weekday: (MealRole.DINNER,) for weekday in range(1, 8)},
    )
    events = [
        MealEventDraft(
            local_date=date.fromordinal(WEEK_START.toordinal() + offset),
            position=1,
            role=MealRole.DINNER,
            source_kind=MealSourceKind.EAT_OUT,
            source_reference="manual",
            servings={
                first_member.id: Decimal("1.25"),
                second_member.id: Decimal("0.75"),
            },
        )
        for offset in range(7)
    ]

    detail = service.create_plan_revision(
        household_id=household.id,
        week_start=WEEK_START,
        member_selection_ids={
            first_member.id: first_selection.selection.id,
            second_member.id: second_selection.selection.id,
        },
        events=events,
    )

    assert detail.plan.revision_number == 1
    first_event_servings = [
        item for item in detail.servings if item.event_id == detail.events[0].id
    ]
    assert {item.portion_servings for item in first_event_servings} == {
        Decimal("1.250000"),
        Decimal("0.750000"),
    }

    revised = service.create_plan_revision(
        household_id=household.id,
        week_start=WEEK_START,
        member_selection_ids={
            first_member.id: first_selection.selection.id,
            second_member.id: second_selection.selection.id,
        },
        events=events,
    )
    assert revised.plan.revision_number == 2
    assert revised.plan.supersedes_plan_id == detail.plan.id


def test_program_override_requires_truthful_flag_and_preserves_day_specific_snapshot():
    household = _household()
    member = _member(household.id)
    program = _program()
    service, _, _ = _service(household, [member], program)
    override = {
        weekday: (
            (MealRole.BREAKFAST, MealRole.DINNER)
            if weekday == 1
            else (MealRole.BREAKFAST, MealRole.LUNCH, MealRole.DINNER)
        )
        for weekday in range(1, 8)
    }

    with pytest.raises(MealPlanValidationError, match="has_user_overrides=True"):
        service.accept_member_pattern(
            household_id=household.id,
            member_id=member.id,
            source_kind=MemberMealPatternSourceKind.PROGRAM,
            program_version_id=program.version.id,
            schedule=override,
        )

    detail = service.accept_member_pattern(
        household_id=household.id,
        member_id=member.id,
        source_kind=MemberMealPatternSourceKind.PROGRAM,
        program_version_id=program.version.id,
        schedule=override,
        has_user_overrides=True,
    )

    assert detail.selection.program_version_id == program.version.id
    assert detail.selection.has_user_overrides is True
    assert detail.roles_for_weekday(1) == (
        MealRole.BREAKFAST,
        MealRole.DINNER,
    )
    assert detail.roles_for_weekday(2) == (
        MealRole.BREAKFAST,
        MealRole.LUNCH,
        MealRole.DINNER,
    )


def test_member_pattern_history_read_is_household_scoped():
    household = _household()
    member = _member(household.id)
    service, _, _ = _service(household, [member])

    first = service.accept_member_pattern(
        household_id=household.id,
        member_id=member.id,
        source_kind=MemberMealPatternSourceKind.CUSTOM,
        schedule={weekday: (MealRole.DINNER,) for weekday in range(1, 8)},
    )
    second = service.accept_member_pattern(
        household_id=household.id,
        member_id=member.id,
        source_kind=MemberMealPatternSourceKind.CUSTOM,
        schedule={
            weekday: (MealRole.BREAKFAST, MealRole.DINNER)
            for weekday in range(1, 8)
        },
    )

    assert service.get_member_pattern_history(household.id, member.id) == (
        first.selection,
        second.selection,
    )
    assert service.get_member_pattern_history(uuid4(), member.id) == ()


def test_complete_manual_week_supports_three_member_household():
    household = _household()
    members = [_member(household.id) for _ in range(3)]
    service, _, _ = _service(household, members)
    selections = [
        service.accept_member_pattern(
            household_id=household.id,
            member_id=member.id,
            source_kind=MemberMealPatternSourceKind.CUSTOM,
            schedule={weekday: (MealRole.DINNER,) for weekday in range(1, 8)},
        )
        for member in members
    ]
    events = [
        MealEventDraft(
            local_date=date.fromordinal(WEEK_START.toordinal() + offset),
            position=1,
            role=MealRole.DINNER,
            source_kind=MealSourceKind.EAT_OUT,
            source_reference="manual",
            servings={
                members[0].id: Decimal("1.25"),
                members[1].id: Decimal("1.00"),
                members[2].id: Decimal("0.75"),
            },
        )
        for offset in range(7)
    ]

    detail = service.create_plan_revision(
        household_id=household.id,
        week_start=WEEK_START,
        member_selection_ids={
            member.id: selection.selection.id
            for member, selection in zip(members, selections, strict=True)
        },
        events=events,
    )

    assert len(detail.member_selections) == 3
    first_event_servings = [
        serving
        for serving in detail.servings
        if serving.event_id == detail.events[0].id
    ]
    assert len(first_event_servings) == 3
