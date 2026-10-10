"""Explicit Russian-facing Shopping HTTP contracts (PR9-C).

Amounts are strings, not JSON numbers. Machine status identifiers remain stable,
while display messages are separately localized at the API boundary.
"""

from datetime import date, datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.domain.meal_plans import MealSourceKind
from app.domain.shopping_calculation import (
    ShoppingPriceStatus,
    ShoppingStatus,
    ShoppingUnresolvedReason,
)
from app.domain.units import UnitCode


class ShoppingGenerateRequest(BaseModel):
    """Empty command: all calculation inputs come from authoritative backend state."""

    model_config = ConfigDict(extra="forbid")


class ShoppingLifecycle(StrEnum):
    MISSING = "MISSING"
    CURRENT = "CURRENT"
    STALE = "STALE"


class ShoppingItemResponse(BaseModel):
    id: UUID
    shopping_list_id: UUID
    food_ingredient_id: UUID
    form_basis: str
    unit: UnitCode
    required_quantity: str
    pantry_available_quantity: str
    purchase_quantity: str
    ordinal: int


class ShoppingUnresolvedResponse(BaseModel):
    id: UUID
    shopping_list_id: UUID
    meal_event_id: UUID
    source_kind: MealSourceKind
    reason: ShoppingUnresolvedReason
    message: str
    ordinal: int


class ShoppingWarningResponse(BaseModel):
    code: str
    message: str
    pantry_item_id: UUID
    meal_event_id: UUID | None = None
    required_date: date | None = None


class ShoppingAllocationResponse(BaseModel):
    meal_event_id: UUID
    pantry_item_id: UUID
    food_ingredient_id: UUID
    quantity: str


class ShoppingDetailResponse(BaseModel):
    id: UUID
    household_id: UUID
    meal_plan_id: UUID
    source_plan_revision_number: int
    source_pantry_snapshot_hash: str
    as_of_date: date
    engine_version: str
    pantry_policy_version: str
    config_fingerprint: str
    source_fingerprint: str
    content_fingerprint: str
    status: ShoppingStatus
    status_message: str
    price_status: ShoppingPriceStatus
    price_status_message: str
    lifecycle: ShoppingLifecycle
    lifecycle_message: str
    stale_reason: str | None
    stale_reason_message: str | None
    supersedes_list_id: UUID | None
    created_at: datetime
    items: list[ShoppingItemResponse]
    unresolved: list[ShoppingUnresolvedResponse]
    warnings: list[ShoppingWarningResponse]
    allocations: list[ShoppingAllocationResponse]


class ShoppingCurrentResponse(BaseModel):
    lifecycle: ShoppingLifecycle
    lifecycle_message: str
    stale_reason: str | None
    stale_reason_message: str | None
    detail: ShoppingDetailResponse | None


class ShoppingHistoryResponse(BaseModel):
    shopping_lists: list[ShoppingDetailResponse]
