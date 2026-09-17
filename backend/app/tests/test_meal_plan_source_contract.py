from datetime import date, datetime, timezone
from uuid import uuid4

import pytest

from app.domain.errors import DomainValidationError
from app.domain.meal_patterns import MealRole
from app.domain.meal_plans import HouseholdMealEvent, MealSourceKind

NOW = datetime(2026, 9, 17, 12, 0, tzinfo=timezone.utc)


@pytest.mark.parametrize(
    "source_kind",
    [
        MealSourceKind.ASSEMBLY,
        MealSourceKind.LEFTOVER,
        MealSourceKind.PREPARED,
        MealSourceKind.READY_MEAL,
        MealSourceKind.ORDER_OUT,
        MealSourceKind.EAT_OUT,
    ],
)
def test_non_recipe_sources_are_representable_without_fake_recipe(source_kind):
    event = HouseholdMealEvent(
        id=uuid4(),
        plan_id=uuid4(),
        local_date=date(2026, 9, 17),
        position=1,
        role=MealRole.OTHER,
        source_kind=source_kind,
        recipe_version_id=None,
        source_reference="manual-fixed-source",
        created_at=NOW,
    )
    assert event.recipe_version_id is None


def test_non_recipe_source_rejects_recipe_reference():
    with pytest.raises(DomainValidationError):
        HouseholdMealEvent(
            id=uuid4(),
            plan_id=uuid4(),
            local_date=date(2026, 9, 17),
            position=1,
            role=MealRole.DINNER,
            source_kind=MealSourceKind.LEFTOVER,
            recipe_version_id=uuid4(),
            source_reference="manual",
            created_at=NOW,
        )
