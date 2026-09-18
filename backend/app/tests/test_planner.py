from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import UUID

from app.domain.food_recipes import MealTypeCode
from app.domain.meal_patterns import MealRole
from app.domain.meal_plans import (
    MemberMealPatternOpportunitySnapshot,
    MemberMealPatternSelection,
    MemberMealPatternSelectionDetail,
    MemberMealPatternSourceKind,
)
from app.domain.nutrition import NutritionStatus
from app.domain.planner import (
    MemberPlannerConstraints,
    PlannerCandidate,
    PlannerConfig,
    PlannerFailure,
    PlannerFailureCode,
    PlannerRequest,
    PlannerSuccess,
    generate_week,
)
from app.services.planner import PlannerService, RecommenderRequest, recommend_patterns


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
    assert all(
        "MEMBER_EXCLUDED_INGREDIENT" in {code.value for code in item.rejection_codes}
        for item in excluded_traces
        if len(
            next(
                event
                for event in result.events
                if event.local_date == item.local_date
                and event.position == item.position
            ).participant_member_ids
        )
        == 2
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


def test_application_facade_never_writes_an_infeasible_partial_plan() -> None:
    class NeverCalledMealPlans:
        def create_plan_revision(self, **kwargs):
            raise AssertionError(f"partial write attempted: {kwargs}")

    invalid = PlannerRequest(uid(1), date(2026, 9, 14), (), ())
    result, persisted = PlannerService(NeverCalledMealPlans()).generate(invalid)  # type: ignore[arg-type]
    assert isinstance(result, PlannerFailure)
    assert persisted is None
