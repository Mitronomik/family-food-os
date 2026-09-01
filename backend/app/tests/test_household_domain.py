from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

import pytest

from app.domain.errors import DomainIssueCode, DomainValidationError
from app.domain.households import (
    Household,
    HouseholdMember,
    update_household,
    update_household_member,
)

NOW = datetime(2026, 9, 1, 10, 0, tzinfo=timezone.utc)


def household(**overrides):
    values = {
        "id": uuid4(),
        "name": " Family Home ",
        "timezone": "Europe/Moscow",
        "city": " Saint Petersburg ",
        "default_weekly_budget": "12000.005",
        "default_cooking_profile": " easy week ",
        "created_at": NOW,
        "updated_at": NOW,
    }
    values.update(overrides)
    return Household(**values)


def member(household_id, **overrides):
    values = {
        "id": uuid4(),
        "household_id": household_id,
        "name": " Anna ",
        "active": True,
        "birth_date": date(1990, 5, 20),
        "sex": " female ",
        "height_cm": "168.24",
        "weight_kg": "62.3456",
        "activity_level": " moderate ",
        "goal": " maintain ",
        "created_at": NOW,
        "updated_at": NOW,
    }
    values.update(overrides)
    return HouseholdMember(**values)


def test_valid_household_normalizes_foundation_values():
    value = household()

    assert value.name == "Family Home"
    assert value.city == "Saint Petersburg"
    assert value.default_weekly_budget == Decimal("12000.01")
    assert value.default_cooking_profile == "easy week"


def test_household_normalizes_aware_instants_to_utc():
    source = datetime(2026, 9, 1, 13, 0, tzinfo=timezone(timedelta(hours=3)))

    value = household(created_at=source, updated_at=source)

    assert value.created_at == NOW
    assert value.created_at.tzinfo is timezone.utc


@pytest.mark.parametrize("name", ["", "   ", None])
def test_household_rejects_empty_name(name):
    with pytest.raises(DomainValidationError) as exc_info:
        household(name=name)

    assert exc_info.value.issue.code == DomainIssueCode.REQUIRED_FIELD
    assert exc_info.value.issue.field == "name"


def test_household_rejects_invalid_timezone():
    with pytest.raises(DomainValidationError) as exc_info:
        household(timezone="Mars/Olympus_Mons")

    assert exc_info.value.issue.code == DomainIssueCode.INVALID_TIMEZONE
    assert exc_info.value.issue.field == "timezone"


def test_household_rejects_negative_budget_and_float_budget():
    with pytest.raises(DomainValidationError) as negative:
        household(default_weekly_budget="-0.01")
    assert negative.value.issue.code == DomainIssueCode.NEGATIVE_MONEY

    with pytest.raises(DomainValidationError) as floating:
        household(default_weekly_budget=10.5)
    assert floating.value.issue.code == DomainIssueCode.FLOAT_NOT_ALLOWED


def test_valid_member_uses_explicit_measurement_units_and_birth_date():
    household_id = uuid4()

    value = member(household_id)

    assert value.household_id == household_id
    assert value.height_cm == Decimal("168.2")
    assert value.weight_kg == Decimal("62.346")
    assert value.birth_date == date(1990, 5, 20)
    assert value.activity_level == "moderate"


@pytest.mark.parametrize(
    ("field", "value", "code"),
    [
        ("height_cm", "0", DomainIssueCode.NON_POSITIVE_MEASUREMENT),
        ("height_cm", "301", DomainIssueCode.MEASUREMENT_OUT_OF_RANGE),
        ("weight_kg", "-1", DomainIssueCode.NON_POSITIVE_MEASUREMENT),
        ("weight_kg", "1001", DomainIssueCode.MEASUREMENT_OUT_OF_RANGE),
    ],
)
def test_member_rejects_invalid_physical_measurements(field, value, code):
    with pytest.raises(DomainValidationError) as exc_info:
        member(uuid4(), **{field: value})

    assert exc_info.value.issue.code == code
    assert exc_info.value.issue.field == field


def test_member_rejects_future_birth_date_and_empty_profile_codes():
    with pytest.raises(DomainValidationError) as future:
        member(uuid4(), birth_date=date.today() + timedelta(days=1))
    assert future.value.issue.code == DomainIssueCode.INVALID_DATE

    with pytest.raises(DomainValidationError) as activity:
        member(uuid4(), activity_level=" ")
    assert activity.value.issue.field == "activity_level"

    with pytest.raises(DomainValidationError) as goal:
        member(uuid4(), goal=" ")
    assert goal.value.issue.field == "goal"


def test_patch_functions_preserve_identity_and_validate_changes():
    original = household()
    changed_at = NOW + timedelta(hours=1)

    changed = update_household(
        original,
        {"name": "New Home", "city": None, "default_weekly_budget": "9000"},
        updated_at=changed_at,
    )

    assert changed.id == original.id
    assert changed.created_at == original.created_at
    assert changed.updated_at == changed_at
    assert changed.name == "New Home"
    assert changed.city is None
    assert changed.default_weekly_budget == Decimal("9000.00")

    original_member = member(original.id)
    changed_member = update_household_member(
        original_member,
        {"active": False, "weight_kg": None},
        updated_at=changed_at,
    )
    assert changed_member.household_id == original.id
    assert changed_member.active is False
    assert changed_member.weight_kg is None


def test_domain_instants_must_be_timezone_aware():
    with pytest.raises(DomainValidationError, match="timezone-aware"):
        household(created_at=datetime(2026, 9, 1, 10, 0))
