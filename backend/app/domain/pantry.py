"""Household stock buckets and immutable, unsigned movement facts."""

from dataclasses import dataclass, replace
from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Mapping
from uuid import UUID

from app.domain.decimal_utils import parse_decimal, quantize_decimal
from app.domain.errors import DomainIssue, DomainIssueCode, DomainValidationError
from app.domain.food_ingredients import FoodIngredient, normalize_utc_instant
from app.domain.units import UnitCode

QUANTITY_QUANT = Decimal("0.001")
MAX_QUANTITY = Decimal("999999999999.999")
METADATA_FIELDS = frozenset(
    {"location", "estimated", "purchased_on", "opened_on", "expires_on"}
)


class PantryLocation(StrEnum):
    PANTRY = "PANTRY"
    FRIDGE = "FRIDGE"
    FREEZER = "FREEZER"


class PantryMovementType(StrEnum):
    ADD = "ADD"
    CONSUMPTION = "CONSUMPTION"
    WASTE = "WASTE"
    ADJUSTMENT_IN = "ADJUSTMENT_IN"
    ADJUSTMENT_OUT = "ADJUSTMENT_OUT"

    @property
    def direction(self) -> int:
        return 1 if self in {self.ADD, self.ADJUSTMENT_IN} else -1


def invalid(
    field: str, value: object, message: str, code=DomainIssueCode.VALUE_OUT_OF_RANGE
):
    return DomainValidationError(
        DomainIssue(
            code=code,
            message=message,
            field=field,
            value=str(value),
            next_action="Supply a valid Pantry value.",
        )
    )


def validate_uuid(value: object, *, field: str) -> UUID:
    if not isinstance(value, UUID) or value.version != 4:
        raise invalid(
            field,
            value,
            "Identifier must be UUIDv4.",
            DomainIssueCode.INVALID_IDENTIFIER,
        )
    return value


def normalize_unit(value: object) -> UnitCode:
    try:
        unit = UnitCode(value)
    except (TypeError, ValueError) as exc:
        raise invalid(
            "unit", value, "Use g, ml or pcs.", DomainIssueCode.INVALID_UNIT
        ) from exc
    if unit not in {UnitCode.GRAM, UnitCode.MILLILITER, UnitCode.PIECE}:
        raise invalid("unit", value, "Use g, ml or pcs.", DomainIssueCode.INVALID_UNIT)
    return unit


def normalize_quantity(value: object, *, positive: bool = False) -> Decimal:
    parsed = parse_decimal(value, field="quantity")
    if parsed < 0 or parsed > MAX_QUANTITY:
        raise invalid(
            "quantity", value, f"Quantity must be between 0 and {MAX_QUANTITY}."
        )
    quantity = quantize_decimal(parsed, QUANTITY_QUANT, field="quantity")
    if positive and quantity <= 0:
        raise invalid(
            "quantity", value, "Quantity must be positive at 0.001 precision."
        )
    return quantity if quantity else Decimal("0.000")


def normalize_date(value: object, *, field: str) -> date | None:
    if value is not None and (
        not isinstance(value, date) or isinstance(value, datetime)
    ):
        raise invalid(
            field,
            value,
            "Supply a calendar date or null.",
            DomainIssueCode.INVALID_DATE,
        )
    return value


def validate_ingredient_unit(ingredient: FoodIngredient, unit: object) -> UnitCode:
    normalized = normalize_unit(unit)
    if normalized != ingredient.default_unit:
        raise invalid(
            "unit",
            unit,
            "Unit must equal FoodIngredient.default_unit; conversions are not supported.",
            DomainIssueCode.INVALID_UNIT,
        )
    return normalized


def _enum(enum_type, value, field):
    try:
        return enum_type(value)
    except (TypeError, ValueError) as exc:
        raise invalid(field, value, f"Invalid {field}.") from exc


@dataclass(frozen=True)
class PantryItem:
    id: UUID
    household_id: UUID
    food_ingredient_id: UUID
    quantity: Decimal
    unit: UnitCode
    location: PantryLocation
    estimated: bool
    purchased_on: date | None
    opened_on: date | None
    expires_on: date | None
    created_at: datetime
    updated_at: datetime

    def __post_init__(self) -> None:
        for field in ("id", "household_id", "food_ingredient_id"):
            validate_uuid(getattr(self, field), field=field)
        object.__setattr__(self, "quantity", normalize_quantity(self.quantity))
        object.__setattr__(self, "unit", normalize_unit(self.unit))
        object.__setattr__(
            self, "location", _enum(PantryLocation, self.location, "location")
        )
        if type(self.estimated) is not bool:
            raise invalid(
                "estimated",
                self.estimated,
                "Estimated must be boolean.",
                DomainIssueCode.INVALID_BOOLEAN,
            )
        for field in ("purchased_on", "opened_on", "expires_on"):
            normalize_date(getattr(self, field), field=field)
        for field in ("created_at", "updated_at"):
            object.__setattr__(
                self, field, normalize_utc_instant(getattr(self, field), field=field)
            )
        if self.updated_at < self.created_at:
            raise invalid(
                "updated_at",
                self.updated_at,
                "Update must not precede creation.",
                DomainIssueCode.INVALID_DATE,
            )


@dataclass(frozen=True)
class PantryMovement:
    id: UUID
    household_id: UUID
    pantry_item_id: UUID
    movement_type: PantryMovementType
    quantity: Decimal
    unit: UnitCode
    occurred_at: datetime
    created_at: datetime

    def __post_init__(self) -> None:
        for field in ("id", "household_id", "pantry_item_id"):
            validate_uuid(getattr(self, field), field=field)
        object.__setattr__(
            self, "quantity", normalize_quantity(self.quantity, positive=True)
        )
        object.__setattr__(self, "unit", normalize_unit(self.unit))
        object.__setattr__(
            self,
            "movement_type",
            _enum(PantryMovementType, self.movement_type, "movement_type"),
        )
        for field in ("occurred_at", "created_at"):
            object.__setattr__(
                self, field, normalize_utc_instant(getattr(self, field), field=field)
            )


def update_item_metadata(
    item: PantryItem, changes: Mapping[str, object], *, updated_at: datetime
) -> PantryItem:
    if not changes or set(changes) - METADATA_FIELDS:
        raise invalid("changes", sorted(changes), "Supply only Pantry metadata fields.")
    return replace(item, **changes, updated_at=updated_at)
