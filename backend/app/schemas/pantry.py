"""Explicit Pantry HTTP contracts; exact quantities serialize as strings."""

from datetime import date, datetime
from decimal import Decimal
import re
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, BeforeValidator, ConfigDict, StrictBool, UUID4

from app.domain.pantry import PantryLocation, PantryMovementType
from app.domain.units import UnitCode


def _exact_input(value):
    if isinstance(value, (float, bool)):
        raise ValueError(
            "Quantity must be a decimal string or integer; float is not allowed."
        )
    return value


def _calendar_input(value):
    if value is not None and not (
        type(value) is date
        or isinstance(value, str)
        and re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value)
    ):
        raise ValueError("Use an ISO calendar date (YYYY-MM-DD) or null.")
    return value


DecimalInput = Annotated[Decimal | int | str, BeforeValidator(_exact_input)]
CalendarDate = Annotated[date, BeforeValidator(_calendar_input)]


class PantryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PantryCreateRequest(PantryRequest):
    food_ingredient_id: UUID4
    quantity: DecimalInput
    unit: UnitCode
    location: PantryLocation = PantryLocation.PANTRY
    estimated: StrictBool = False
    purchased_on: CalendarDate | None = None
    opened_on: CalendarDate | None = None
    expires_on: CalendarDate | None = None


class PantryMetadataRequest(PantryRequest):
    location: PantryLocation | None = None
    estimated: StrictBool | None = None
    purchased_on: CalendarDate | None = None
    opened_on: CalendarDate | None = None
    expires_on: CalendarDate | None = None


class PantryQuantityRequest(PantryRequest):
    quantity: DecimalInput
    unit: UnitCode


class PantryConsumeRequest(PantryQuantityRequest):
    food_ingredient_id: UUID4


class PantryAdjustRequest(PantryRequest):
    target_quantity: DecimalInput
    unit: UnitCode


class PantryItemResponse(BaseModel):
    id: UUID
    household_id: UUID
    food_ingredient_id: UUID
    quantity: str
    unit: UnitCode
    location: PantryLocation
    estimated: bool
    purchased_on: date | None
    opened_on: date | None
    expires_on: date | None
    created_at: datetime
    updated_at: datetime


class PantryItemsResponse(BaseModel):
    items: list[PantryItemResponse]


class PantryMovementResponse(BaseModel):
    id: UUID
    household_id: UUID
    pantry_item_id: UUID
    movement_type: PantryMovementType
    quantity: str
    unit: UnitCode
    occurred_at: datetime
    created_at: datetime


class PantryConsumptionResponse(BaseModel):
    movements: list[PantryMovementResponse]
