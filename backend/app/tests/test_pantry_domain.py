from dataclasses import FrozenInstanceError
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid1, uuid4

import pytest

from app.domain.errors import DomainIssueCode, DomainValidationError
from app.domain.pantry import (
    MAX_QUANTITY,
    PantryItem,
    PantryLocation,
    PantryMovement,
    normalize_quantity,
    update_item_metadata,
    validate_ingredient_unit,
)
from app.tests.test_food_ingredient_domain import ingredient

NOW = datetime(2026, 9, 6, 12, tzinfo=timezone.utc)


def item(**overrides):
    values = dict(
        id=uuid4(),
        household_id=uuid4(),
        food_ingredient_id=uuid4(),
        quantity="10",
        unit="pcs",
        location="PANTRY",
        estimated=False,
        purchased_on=None,
        opened_on=None,
        expires_on=None,
        created_at=NOW,
        updated_at=NOW,
    )
    values.update(overrides)
    return PantryItem(**values)


def movement(**overrides):
    values = dict(
        id=uuid4(),
        household_id=uuid4(),
        pantry_item_id=uuid4(),
        movement_type="ADD",
        quantity="10",
        unit="pcs",
        occurred_at=NOW,
        created_at=NOW,
    )
    values.update(overrides)
    return PantryMovement(**values)


@pytest.mark.parametrize(
    "factory,field",
    [
        (item, "id"),
        (item, "household_id"),
        (item, "food_ingredient_id"),
        (movement, "id"),
        (movement, "household_id"),
        (movement, "pantry_item_id"),
    ],
)
@pytest.mark.parametrize("bad_id", [uuid1(), "not-a-uuid", str(uuid4()), 1])
def test_all_identity_fields_require_uuid4(factory, field, bad_id):
    with pytest.raises(DomainValidationError) as error:
        factory(**{field: bad_id})
    assert error.value.issue.code == DomainIssueCode.INVALID_IDENTIFIER
    assert error.value.issue.field == field


@pytest.mark.parametrize(
    "value,expected",
    [
        ("1.2345", "1.235"),
        ("1.2344", "1.234"),
        (" 1,25 ", "1.250"),
        (2, "2.000"),
        (Decimal("0.001"), "0.001"),
        (MAX_QUANTITY, "999999999999.999"),
    ],
)
def test_quantities_parse_exact_decimal_with_documented_precision(value, expected):
    assert normalize_quantity(value) == Decimal(expected)


@pytest.mark.parametrize(
    "value",
    [
        "NaN",
        "sNaN",
        "Infinity",
        "-Infinity",
        "-0.00001",
        "-1",
        "",
        "eggs",
        "1e999999",
        "1000000000000",
        None,
        True,
        1.2,
    ],
)
def test_invalid_quantities_produce_stable_domain_errors(value):
    with pytest.raises(DomainValidationError) as error:
        item(quantity=value)
    assert error.value.issue.field == "quantity"


@pytest.mark.parametrize("value", ["0", "0.0004", "-1"])
def test_initial_quantity_and_movements_must_be_positive(value):
    with pytest.raises(DomainValidationError):
        normalize_quantity(value, positive=True)
    with pytest.raises(DomainValidationError):
        movement(quantity=value)


def test_zero_current_balance_is_a_valid_durable_item():
    assert item(quantity="0").quantity == Decimal("0.000")


@pytest.mark.parametrize("unit", ["g", "ml", "pcs"])
def test_all_canonical_units_preserve_fractional_accounting_precision(unit):
    assert item(unit=unit, quantity="0.125").quantity == Decimal("0.125")
    assert movement(unit=unit, quantity="0.125").quantity == Decimal("0.125")
    assert validate_ingredient_unit(ingredient(default_unit=unit), unit) == unit


@pytest.mark.parametrize("unit", ["kg", "l", "%", "pack", None])
def test_units_cannot_be_packages_or_conversion_shortcuts(unit):
    with pytest.raises(DomainValidationError):
        item(unit=unit)
    with pytest.raises(DomainValidationError):
        movement(unit=unit)


@pytest.mark.parametrize("unit", ["ml", "pcs"])
def test_ingredient_default_unit_mismatch_is_rejected(unit):
    with pytest.raises(DomainValidationError) as error:
        validate_ingredient_unit(ingredient(default_unit="g"), unit)
    assert error.value.issue.code == DomainIssueCode.INVALID_UNIT


@pytest.mark.parametrize("location", list(PantryLocation))
def test_each_household_storage_location_is_accepted(location):
    assert item(location=location).location is location


@pytest.mark.parametrize("location", ["warehouse", "pantry", "", None])
def test_unknown_location_is_rejected(location):
    with pytest.raises(DomainValidationError):
        item(location=location)


@pytest.mark.parametrize("estimated", [0, 1, "false", None])
def test_estimation_state_is_strict_boolean(estimated):
    with pytest.raises(DomainValidationError):
        item(estimated=estimated)


@pytest.mark.parametrize("field", ["purchased_on", "opened_on", "expires_on"])
@pytest.mark.parametrize("value", ["2026-09-06", NOW, 20260906])
def test_metadata_dates_are_calendar_dates_not_instants_or_strings(field, value):
    with pytest.raises(DomainValidationError) as error:
        item(**{field: value})
    assert error.value.issue.code == DomainIssueCode.INVALID_DATE


def test_metadata_preserves_explicit_dates_and_does_not_invent_missing_dates():
    value = item(purchased_on=date(2026, 9, 1), expires_on=date(2026, 9, 5))
    assert value.purchased_on == date(2026, 9, 1)
    assert value.opened_on is None
    assert value.expires_on == date(2026, 9, 5)


@pytest.mark.parametrize(
    "factory,field",
    [
        (item, "created_at"),
        (item, "updated_at"),
        (movement, "occurred_at"),
        (movement, "created_at"),
    ],
)
def test_true_events_reject_naive_instants_and_normalize_offsets(factory, field):
    with pytest.raises(DomainValidationError):
        factory(**{field: NOW.replace(tzinfo=None)})
    offset = NOW.astimezone(timezone(timedelta(hours=3)))
    actual = factory(**{field: offset})
    assert getattr(actual, field) == NOW
    assert getattr(actual, field).tzinfo is timezone.utc


def test_updated_at_cannot_precede_creation():
    with pytest.raises(DomainValidationError):
        item(updated_at=NOW - timedelta(seconds=1))


@pytest.mark.parametrize(
    "kind,sign",
    [
        ("ADD", 1),
        ("ADJUSTMENT_IN", 1),
        ("CONSUMPTION", -1),
        ("WASTE", -1),
        ("ADJUSTMENT_OUT", -1),
    ],
)
def test_movement_direction_is_derived_and_quantity_unsigned(kind, sign):
    value = movement(movement_type=kind)
    assert value.movement_type.direction == sign
    assert value.quantity > 0
    with pytest.raises(FrozenInstanceError):
        value.quantity = Decimal("1")


def test_unknown_movement_type_is_rejected():
    with pytest.raises(DomainValidationError):
        movement(movement_type="RETURN_TO_SUPPLIER")


@pytest.mark.parametrize(
    "changes",
    [
        {},
        {"quantity": "1"},
        {"unit": "g"},
        {"food_ingredient_id": uuid4()},
        {"household_id": uuid4()},
        {"id": uuid4()},
        {"created_at": NOW},
        {"location": "FRIDGE", "quantity": "1"},
    ],
)
def test_metadata_updates_cannot_modify_quantity_or_identity(changes):
    original = item()
    with pytest.raises(DomainValidationError):
        update_item_metadata(original, changes, updated_at=NOW)
    assert original.quantity == Decimal("10.000")


def test_metadata_update_returns_new_validated_item_and_can_clear_dates():
    original = item(expires_on=date(2026, 9, 10))
    changed = update_item_metadata(
        original,
        {"location": "FREEZER", "estimated": True, "expires_on": None},
        updated_at=NOW + timedelta(seconds=1),
    )
    assert changed.id == original.id
    assert changed.quantity == original.quantity
    assert changed.location == PantryLocation.FREEZER
    assert changed.estimated is True
    assert changed.expires_on is None
    assert original.expires_on == date(2026, 9, 10)
