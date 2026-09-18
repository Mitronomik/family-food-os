from datetime import date, datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.domain.errors import DomainValidationError
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
    calculate_meal_plan_nutrition,
    validate_complete_plan,
)
from app.domain.nutrition import NutritionStatus, NutritionValues

NOW = datetime(2026, 9, 17, 12, 0, tzinfo=timezone.utc)
WEEK_START = date(2026, 9, 14)


def _selection_detail(*, household_id, member_id, roles, source_kind="CUSTOM"):
    selection_id = uuid4()
    program_version_id = uuid4() if source_kind == "PROGRAM" else None
    selection = MemberMealPatternSelection(
        id=selection_id,
        household_id=household_id,
        member_id=member_id,
        version_number=1,
        source_kind=MemberMealPatternSourceKind(source_kind),
        program_version_id=program_version_id,
        recommender_version=None,
        has_user_overrides=False,
        accepted_at=NOW,
        supersedes_selection_id=None,
        created_at=NOW,
    )
    opportunities = tuple(
        MemberMealPatternOpportunitySnapshot(
            selection_id=selection_id,
            weekday=weekday,
            position=position,
            role=role,
        )
        for weekday in range(1, 8)
        for position, role in enumerate(roles, start=1)
    )
    return MemberMealPatternSelectionDetail(selection, opportunities)


@pytest.mark.parametrize(
    "roles",
    [
        (MealRole.DINNER,),
        (MealRole.BREAKFAST, MealRole.DINNER),
        (MealRole.BREAKFAST, MealRole.LUNCH, MealRole.DINNER),
        (
            MealRole.BREAKFAST,
            MealRole.SNACK,
            MealRole.LUNCH,
            MealRole.SNACK,
            MealRole.DINNER,
        ),
        (
            MealRole.BREAKFAST,
            MealRole.SNACK,
            MealRole.LUNCH,
            MealRole.SNACK,
            MealRole.DINNER,
            MealRole.SNACK,
        ),
    ],
)
def test_selection_snapshot_supports_initial_one_to_six_opportunities(roles):
    detail = _selection_detail(
        household_id=uuid4(), member_id=uuid4(), roles=roles
    )
    assert detail.roles_for_weekday(1) == roles
    assert detail.roles_for_weekday(7) == roles


def test_selection_snapshot_rejects_seven_opportunities_at_product_boundary():
    roles = (MealRole.SNACK,) * 7
    with pytest.raises(DomainValidationError):
        _selection_detail(household_id=uuid4(), member_id=uuid4(), roles=roles)


def test_program_and_custom_selection_reference_invariants():
    household_id = uuid4()
    member_id = uuid4()
    MemberMealPatternSelection(
        id=uuid4(),
        household_id=household_id,
        member_id=member_id,
        version_number=1,
        source_kind=MemberMealPatternSourceKind.PROGRAM,
        program_version_id=uuid4(),
        recommender_version="meal-pattern-v1",
        has_user_overrides=True,
        accepted_at=NOW,
        supersedes_selection_id=None,
        created_at=NOW,
    )
    with pytest.raises(DomainValidationError):
        MemberMealPatternSelection(
            id=uuid4(),
            household_id=household_id,
            member_id=member_id,
            version_number=1,
            source_kind=MemberMealPatternSourceKind.CUSTOM,
            program_version_id=uuid4(),
            recommender_version=None,
            has_user_overrides=False,
            accepted_at=NOW,
            supersedes_selection_id=None,
            created_at=NOW,
        )


def test_meal_source_requires_recipe_only_for_cook_recipe():
    plan_id = uuid4()
    recipe_version_id = uuid4()
    event = HouseholdMealEvent(
        id=uuid4(),
        plan_id=plan_id,
        local_date=WEEK_START,
        position=1,
        role=MealRole.DINNER,
        source_kind=MealSourceKind.COOK_RECIPE,
        recipe_version_id=recipe_version_id,
        source_reference=None,
        created_at=NOW,
    )
    assert event.recipe_version_id == recipe_version_id

    HouseholdMealEvent(
        id=uuid4(),
        plan_id=plan_id,
        local_date=WEEK_START,
        position=2,
        role=MealRole.OTHER,
        source_kind=MealSourceKind.EAT_OUT,
        recipe_version_id=None,
        source_reference="семейный ужин вне дома",
        created_at=NOW,
    )

    with pytest.raises(DomainValidationError):
        HouseholdMealEvent(
            id=uuid4(),
            plan_id=plan_id,
            local_date=WEEK_START,
            position=1,
            role=MealRole.DINNER,
            source_kind=MealSourceKind.COOK_RECIPE,
            recipe_version_id=None,
            source_reference=None,
            created_at=NOW,
        )

    with pytest.raises(DomainValidationError):
        HouseholdMealEvent(
            id=uuid4(),
            plan_id=plan_id,
            local_date=WEEK_START,
            position=1,
            role=MealRole.DINNER,
            source_kind=MealSourceKind.ORDER_OUT,
            recipe_version_id=recipe_version_id,
            source_reference="manual",
            created_at=NOW,
        )


def test_complete_manual_week_supports_heterogeneous_schedules_and_shared_servings():
    household_id = uuid4()
    member_a = uuid4()
    member_b = uuid4()
    selection_a = _selection_detail(
        household_id=household_id,
        member_id=member_a,
        roles=(MealRole.DINNER,),
    )
    selection_b = _selection_detail(
        household_id=household_id,
        member_id=member_b,
        roles=(MealRole.BREAKFAST, MealRole.DINNER),
    )
    plan = MealPlan(
        id=uuid4(),
        household_id=household_id,
        week_start=WEEK_START,
        revision_number=1,
        status=MealPlanStatus.CONFIRMED,
        config_version="manual-v1",
        supersedes_plan_id=None,
        created_at=NOW,
    )
    pins = (
        MealPlanMemberSelection(plan.id, member_a, selection_a.selection.id),
        MealPlanMemberSelection(plan.id, member_b, selection_b.selection.id),
    )
    events = []
    servings = []
    recipe_version_id = uuid4()
    for offset in range(7):
        local_date = WEEK_START.fromordinal(WEEK_START.toordinal() + offset)
        breakfast = HouseholdMealEvent(
            id=uuid4(),
            plan_id=plan.id,
            local_date=local_date,
            position=1,
            role=MealRole.BREAKFAST,
            source_kind=MealSourceKind.COOK_RECIPE,
            recipe_version_id=recipe_version_id,
            source_reference=None,
            created_at=NOW,
        )
        dinner = HouseholdMealEvent(
            id=uuid4(),
            plan_id=plan.id,
            local_date=local_date,
            position=2,
            role=MealRole.DINNER,
            source_kind=MealSourceKind.COOK_RECIPE,
            recipe_version_id=recipe_version_id,
            source_reference=None,
            created_at=NOW,
        )
        events.extend((breakfast, dinner))
        servings.extend(
            (
                Serving(uuid4(), breakfast.id, member_b, Decimal("1.0"), NOW),
                Serving(uuid4(), dinner.id, member_a, Decimal("1.25"), NOW),
                Serving(uuid4(), dinner.id, member_b, Decimal("0.75"), NOW),
            )
        )
    detail = MealPlanDetail(plan, pins, tuple(events), tuple(servings))
    validate_complete_plan(
        detail,
        {
            selection_a.selection.id: selection_a,
            selection_b.selection.id: selection_b,
        },
    )
    dinner = next(event for event in events if event.local_date == WEEK_START and event.role is MealRole.DINNER)
    dinner_servings = [item for item in servings if item.event_id == dinner.id]
    assert {item.portion_servings for item in dinner_servings} == {
        Decimal("1.250000"),
        Decimal("0.750000"),
    }


def test_meal_plan_detail_rejects_duplicate_member_serving_for_event():
    household_id = uuid4()
    member_id = uuid4()
    selection = _selection_detail(
        household_id=household_id,
        member_id=member_id,
        roles=(MealRole.DINNER,),
    )
    plan = MealPlan(
        uuid4(),
        household_id,
        WEEK_START,
        1,
        MealPlanStatus.DRAFT,
        "manual-v1",
        None,
        NOW,
    )
    event = HouseholdMealEvent(
        uuid4(),
        plan.id,
        WEEK_START,
        1,
        MealRole.DINNER,
        MealSourceKind.EAT_OUT,
        None,
        "manual",
        NOW,
    )
    pin = MealPlanMemberSelection(plan.id, member_id, selection.selection.id)
    with pytest.raises(DomainValidationError):
        MealPlanDetail(
            plan,
            (pin,),
            (event,),
            (
                Serving(uuid4(), event.id, member_id, Decimal("1"), NOW),
                Serving(uuid4(), event.id, member_id, Decimal("2"), NOW),
            ),
        )


def test_serving_nutrition_scales_recipe_truth_and_non_recipe_stays_unknown():
    household_id = uuid4()
    member_id = uuid4()
    selection = _selection_detail(
        household_id=household_id,
        member_id=member_id,
        roles=(MealRole.DINNER,),
    )
    plan = MealPlan(
        uuid4(),
        household_id,
        WEEK_START,
        1,
        MealPlanStatus.DRAFT,
        "manual-v1",
        None,
        NOW,
    )
    recipe_version_id = uuid4()
    cooked = HouseholdMealEvent(
        uuid4(),
        plan.id,
        WEEK_START,
        1,
        MealRole.DINNER,
        MealSourceKind.COOK_RECIPE,
        recipe_version_id,
        None,
        NOW,
    )
    eating_out = HouseholdMealEvent(
        uuid4(),
        plan.id,
        date(2026, 9, 15),
        1,
        MealRole.DINNER,
        MealSourceKind.EAT_OUT,
        None,
        "manual",
        NOW,
    )
    servings = (
        Serving(uuid4(), cooked.id, member_id, Decimal("1.5"), NOW),
        Serving(uuid4(), eating_out.id, member_id, Decimal("1"), NOW),
    )
    detail = MealPlanDetail(
        plan,
        (MealPlanMemberSelection(plan.id, member_id, selection.selection.id),),
        (cooked, eating_out),
        servings,
    )
    recipe_nutrition = SimpleNamespace(
        version=SimpleNamespace(id=recipe_version_id),
        per_base_serving=NutritionValues(
            kcal=Decimal("400"),
            protein_g=Decimal("30"),
            fat_g=Decimal("10"),
            carbohydrates_g=Decimal("50"),
            fiber_g=Decimal("5"),
        ),
        status=NutritionStatus.COMPLETE,
    )
    result = calculate_meal_plan_nutrition(
        detail, {recipe_version_id: recipe_nutrition}
    )
    cooked_result = next(item for item in result.servings if item.event.id == cooked.id)
    assert cooked_result.values.kcal == Decimal("600.000000")
    assert cooked_result.values.protein_g == Decimal("45.000000")
    external_result = next(
        item for item in result.servings if item.event.id == eating_out.id
    )
    assert external_result.status is NutritionStatus.INCOMPLETE
    assert external_result.values.kcal is None
    assert result.member_weeks[0].status is NutritionStatus.INCOMPLETE
    assert result.member_weeks[0].values.kcal is None


def test_serving_nutrition_rejects_mismatched_recipe_version_truth():
    household_id = uuid4()
    member_id = uuid4()
    selection = _selection_detail(
        household_id=household_id,
        member_id=member_id,
        roles=(MealRole.DINNER,),
    )
    plan = MealPlan(
        uuid4(),
        household_id,
        WEEK_START,
        1,
        MealPlanStatus.DRAFT,
        "manual-v1",
        None,
        NOW,
    )
    recipe_version_id = uuid4()
    event = HouseholdMealEvent(
        uuid4(),
        plan.id,
        WEEK_START,
        1,
        MealRole.DINNER,
        MealSourceKind.COOK_RECIPE,
        recipe_version_id,
        None,
        NOW,
    )
    detail = MealPlanDetail(
        plan,
        (MealPlanMemberSelection(plan.id, member_id, selection.selection.id),),
        (event,),
        (Serving(uuid4(), event.id, member_id, Decimal("1"), NOW),),
    )
    mismatched = SimpleNamespace(
        version=SimpleNamespace(id=uuid4()),
        per_base_serving=NutritionValues(
            kcal=Decimal("400"),
            protein_g=Decimal("30"),
            fat_g=Decimal("10"),
            carbohydrates_g=Decimal("50"),
            fiber_g=Decimal("5"),
        ),
        status=NutritionStatus.COMPLETE,
    )

    with pytest.raises(DomainValidationError, match="Recipe nutrition must match"):
        calculate_meal_plan_nutrition(
            detail,
            {recipe_version_id: mismatched},
        )
