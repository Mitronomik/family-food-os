from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import UUID

import pytest

from app.domain.food_recipes import MealTypeCode
from app.domain.meal_patterns import MealRole
from app.domain.meal_plans import (
    HouseholdMealEvent,
    MealPlan,
    MealPlanDetail,
    MealPlanMemberSelection,
    MealPlanStatus,
    MemberMealPatternOpportunitySnapshot,
    MemberMealPatternSelection,
    MemberMealPatternSelectionDetail,
    MemberMealPatternSourceKind,
    MealSourceKind,
    Serving,
    validate_complete_plan,
)
from app.domain.nutrition import NutritionStatus
from app.domain.planner import (
    MemberPlannerConstraints,
    PlannerCandidate,
    PlannerConfig,
    PlannerFailure,
    PlannerFailureCode,
    PlannerRequest,
    PlannerRejectionCode,
    PlannerSuccess,
    FixedPlannerEvent,
    generate_week,
)
from app.services.planner import RecommenderRequest, recommend_patterns


def uid(number: int) -> UUID:
    return UUID(f"00000000-0000-4000-8000-{number:012d}")


def selection(
    member_id: UUID, roles: tuple[MealRole, ...]
) -> MemberMealPatternSelectionDetail:
    now = datetime(2026, 9, 18, tzinfo=timezone.utc)
    selection_id = uid(1000 + int(member_id.hex[-2:], 16))
    selected = MemberMealPatternSelection(
        selection_id,
        uid(1),
        member_id,
        1,
        MemberMealPatternSourceKind.CUSTOM,
        None,
        None,
        False,
        now,
        None,
        now,
    )
    opportunities = tuple(
        MemberMealPatternOpportunitySnapshot(selection_id, weekday, position, role)
        for weekday in range(1, 8)
        for position, role in enumerate(roles, start=1)
    )
    return MemberMealPatternSelectionDetail(selected, opportunities)


def candidate(
    number: int,
    meal_type: MealTypeCode,
    *,
    ingredients: frozenset[UUID] = frozenset(),
    kcal: str = "500",
    verified: bool = True,
) -> PlannerCandidate:
    return PlannerCandidate(
        uid(number),
        meal_type,
        ingredients,
        Decimal(kcal),
        NutritionStatus.COMPLETE,
        verified,
        30,
        False,
    )


def request(*, excluded: frozenset[UUID] = frozenset()) -> PlannerRequest:
    first, second = uid(2), uid(3)
    return PlannerRequest(
        uid(1),
        date(2026, 9, 14),
        (
            MemberPlannerConstraints(
                first,
                selection(first, (MealRole.BREAKFAST, MealRole.DINNER)),
                Decimal("2000"),
                excluded,
            ),
            MemberPlannerConstraints(
                second, selection(second, (MealRole.DINNER,)), Decimal("2500")
            ),
        ),
        (
            candidate(10, MealTypeCode.BREAKFAST),
            candidate(15, MealTypeCode.BREAKFAST),
            candidate(16, MealTypeCode.BREAKFAST),
            candidate(11, MealTypeCode.MAIN, ingredients=frozenset({uid(50)})),
            candidate(12, MealTypeCode.MAIN),
            candidate(13, MealTypeCode.MAIN),
            candidate(14, MealTypeCode.MAIN),
        ),
    )


def test_complete_heterogeneous_week_is_deterministic_and_weekly_normalized() -> None:
    first = generate_week(request())
    second = generate_week(request())
    assert isinstance(first, PlannerSuccess)
    assert first == second
    assert first.trace.fingerprint == second.trace.fingerprint
    assert len(first.events) == 14
    assert {len(event.participant_member_ids) for event in first.events} == {1, 2}
    assert all(
        event.portions and all(portion > 0 for _, portion in event.portions)
        for event in first.events
    )


def test_hard_exclusion_precedes_sharedness_and_is_explained() -> None:
    result = generate_week(request(excluded=frozenset({uid(50)})))
    assert isinstance(result, PlannerSuccess)
    excluded_traces = [
        item for item in result.trace.candidates if item.recipe_version_id == uid(11)
    ]
    assert excluded_traces
    assert any(
        "MEMBER_EXCLUDED_INGREDIENT" in {code.value for code in item.rejection_codes}
        for item in excluded_traces
    )


def test_infeasible_week_returns_bounded_failure_without_partial_success() -> None:
    value = request()
    result = generate_week(
        PlannerRequest(
            value.household_id,
            value.week_start,
            value.members,
            (candidate(10, MealTypeCode.BREAKFAST),),
        )
    )
    assert isinstance(result, PlannerFailure)
    assert result.code is PlannerFailureCode.NO_ELIGIBLE_CANDIDATE
    assert any(item.rejection_codes for item in result.trace.candidates)


def test_max_repetitions_is_a_hard_filter() -> None:
    value = request()
    result = generate_week(value, PlannerConfig(max_recipe_repetitions=1))
    assert isinstance(result, PlannerFailure)
    assert any(
        "MAX_REPETITIONS" in {code.value for code in item.rejection_codes}
        for item in result.trace.candidates
    )


def test_recommender_fails_safe_for_medical_request() -> None:
    result = recommend_patterns(
        RecommenderRequest(age_years=35, medical_or_therapeutic_request=True), ()
    )
    assert result.ranked_program_version_ids == ()
    assert result.unsupported_reason == "MEDICAL_OR_THERAPEUTIC_REQUEST_UNSUPPORTED"
    assert result.requires_user_acceptance is True


@pytest.mark.parametrize(
    "changes,error",
    [
        ({"preference_weight": 1.0}, TypeError),
        ({"pantry_weight": Decimal("NaN")}, ValueError),
        ({"time_weight": Decimal("Infinity")}, ValueError),
        ({"repetition_weight": Decimal("-1")}, ValueError),
        ({"max_recipe_repetitions": 0}, ValueError),
        ({"max_recipe_repetitions": True}, ValueError),
        ({"version": ""}, ValueError),
        ({"compatibility_version": "bad version"}, ValueError),
    ],
)
def test_planner_config_rejects_invalid_values(changes, error) -> None:
    with pytest.raises(error):
        PlannerConfig(**changes)


def test_recent_history_penalty_changes_selection_deterministically() -> None:
    value = request()
    configured = PlannerConfig(max_recipe_repetitions=20)
    without = generate_week(value, configured)
    with_history = generate_week(
        PlannerRequest(
            value.household_id,
            value.week_start,
            value.members,
            value.candidates,
            recent_plan_ids=(uid(90),),
            recent_recipe_version_ids=(uid(10),),
        ),
        configured,
    )
    assert isinstance(without, PlannerSuccess)
    assert isinstance(with_history, PlannerSuccess)
    assert without.events[0].recipe_version_id == uid(10)
    assert with_history.events[0].recipe_version_id == uid(15)
    assert with_history.trace.recent_plan_ids == (uid(90),)
    assert with_history.trace.recent_recipe_usage == ((uid(10), 1),)


def test_prior_week_uses_do_not_consume_current_week_hard_cap() -> None:
    member_id = uid(2)
    value = PlannerRequest(
        uid(1),
        date(2026, 9, 14),
        (
            MemberPlannerConstraints(
                member_id, selection(member_id, (MealRole.DINNER,)), Decimal("2000")
            ),
        ),
        (candidate(11, MealTypeCode.MAIN),),
        recent_recipe_version_ids=(uid(11), uid(11), uid(11)),
    )
    result = generate_week(value, PlannerConfig(max_recipe_repetitions=7))
    assert isinstance(result, PlannerSuccess)
    assert len(result.events) == 7
    assert result.trace.recent_recipe_usage == ((uid(11), 3),)
    assert all(
        PlannerRejectionCode.MAX_REPETITIONS not in item.rejection_codes
        for item in result.trace.candidates
    )


def test_incompatible_members_split_and_subset_fixed_event_is_preserved() -> None:
    first, second = uid(2), uid(3)
    members = (
        MemberPlannerConstraints(
            first,
            selection(first, (MealRole.DINNER,)),
            Decimal("2000"),
            frozenset({uid(51)}),
        ),
        MemberPlannerConstraints(
            second,
            selection(second, (MealRole.DINNER,)),
            Decimal("2200"),
            frozenset({uid(50)}),
        ),
    )
    candidates = (
        candidate(11, MealTypeCode.MAIN, ingredients=frozenset({uid(50)})),
        candidate(12, MealTypeCode.MAIN, ingredients=frozenset({uid(51)})),
    )
    fixed = FixedPlannerEvent(
        date(2026, 9, 14),
        MealRole.DINNER,
        1,
        MealSourceKind.EAT_OUT,
        "решение пользователя",
        frozenset({first}),
        ((first, Decimal("1")),),
    )
    result = generate_week(
        PlannerRequest(
            uid(1), date(2026, 9, 14), members, candidates, fixed_events=(fixed,)
        ),
        PlannerConfig(max_recipe_repetitions=10),
    )
    assert isinstance(result, PlannerSuccess)
    monday = [event for event in result.events if event.local_date == date(2026, 9, 14)]
    assert [event.source_kind for event in monday] == [
        MealSourceKind.EAT_OUT,
        MealSourceKind.COOK_RECIPE,
    ]
    assert monday[0].participant_member_ids == (first,)
    assert monday[1].participant_member_ids == (second,)
    tuesday = [
        event for event in result.events if event.local_date == date(2026, 9, 15)
    ]
    assert len(tuesday) == 2
    assert {event.participant_member_ids for event in tuesday} == {(first,), (second,)}
    selected = [item for item in result.trace.candidates if item.selected]
    assert selected and all(not item.rejection_codes for item in selected)
    assert any(item.excluded_member_ids for item in selected)
    repeated = generate_week(
        PlannerRequest(
            uid(1), date(2026, 9, 14), members, candidates, fixed_events=(fixed,)
        ),
        PlannerConfig(max_recipe_repetitions=10),
    )
    assert isinstance(repeated, PlannerSuccess)
    assert repeated.events == result.events
    assert repeated.trace.fingerprint == result.trace.fingerprint

    now = datetime(2026, 9, 18, tzinfo=timezone.utc)
    plan_id = uid(500)
    domain_events = []
    servings = []
    for index, event in enumerate(result.events, start=1):
        event_id = uid(500 + index)
        domain_events.append(
            HouseholdMealEvent(
                event_id,
                plan_id,
                event.local_date,
                event.position,
                event.role,
                event.source_kind,
                event.recipe_version_id,
                event.source_reference,
                now,
            )
        )
        servings.extend(
            Serving(uid(700 + len(servings)), event_id, member_id, portion, now)
            for member_id, portion in event.portions
        )
    detail = MealPlanDetail(
        MealPlan(
            plan_id,
            uid(1),
            date(2026, 9, 14),
            1,
            MealPlanStatus.CONFIRMED,
            "planner-v0.2",
            None,
            now,
        ),
        tuple(
            MealPlanMemberSelection(
                plan_id, member.member_id, member.selection.selection.id
            )
            for member in members
        ),
        tuple(domain_events),
        tuple(servings),
    )
    validate_complete_plan(
        detail, {member.selection.selection.id: member.selection for member in members}
    )
