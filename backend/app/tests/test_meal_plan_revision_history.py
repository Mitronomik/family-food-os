from datetime import date, datetime, timezone
from uuid import uuid4

from app.domain.meal_patterns import MealRole
from app.domain.meal_plans import (
    HouseholdMealEvent,
    MealPlan,
    MealPlanDetail,
    MealPlanMemberSelection,
    MealPlanStatus,
    MealSourceKind,
    Serving,
)
from decimal import Decimal

NOW = datetime(2026, 9, 17, 12, 0, tzinfo=timezone.utc)
WEEK_START = date(2026, 9, 14)


def test_old_revision_retains_original_selection_and_source_reference():
    household_id = uuid4()
    member_id = uuid4()
    old_selection_id = uuid4()
    new_selection_id = uuid4()
    old_plan = MealPlan(
        uuid4(), household_id, WEEK_START, 1, MealPlanStatus.CONFIRMED, "manual-v1", None, NOW
    )
    old_event = HouseholdMealEvent(
        uuid4(),
        old_plan.id,
        WEEK_START,
        1,
        MealRole.DINNER,
        MealSourceKind.EAT_OUT,
        None,
        "old-source",
        NOW,
    )
    old_detail = MealPlanDetail(
        old_plan,
        (MealPlanMemberSelection(old_plan.id, member_id, old_selection_id),),
        (old_event,),
        (Serving(uuid4(), old_event.id, member_id, Decimal("1"), NOW),),
    )

    new_plan = MealPlan(
        uuid4(),
        household_id,
        WEEK_START,
        2,
        MealPlanStatus.CONFIRMED,
        "manual-v1",
        old_plan.id,
        NOW,
    )
    new_event = HouseholdMealEvent(
        uuid4(),
        new_plan.id,
        WEEK_START,
        1,
        MealRole.DINNER,
        MealSourceKind.ORDER_OUT,
        None,
        "new-source",
        NOW,
    )
    new_detail = MealPlanDetail(
        new_plan,
        (MealPlanMemberSelection(new_plan.id, member_id, new_selection_id),),
        (new_event,),
        (Serving(uuid4(), new_event.id, member_id, Decimal("1"), NOW),),
    )

    assert old_detail.member_selections[0].selection_id == old_selection_id
    assert old_detail.events[0].source_kind is MealSourceKind.EAT_OUT
    assert old_detail.events[0].source_reference == "old-source"
    assert new_detail.plan.supersedes_plan_id == old_detail.plan.id
    assert new_detail.member_selections[0].selection_id == new_selection_id
