"""Immutable, household-owned Shopping snapshot types (PR9-B).

A ShoppingList is an auditable derived artifact, never Pantry consumption.
"""

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from app.domain.meal_plans import MealSourceKind
from app.domain.shopping_calculation import (
    ShoppingPriceStatus,
    ShoppingStatus,
    ShoppingUnresolvedReason,
)
from app.domain.units import UnitCode


@dataclass(frozen=True)
class ShoppingList:
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
    price_status: ShoppingPriceStatus
    provenance_json: str
    supersedes_list_id: UUID | None
    created_at: datetime

    def __post_init__(self) -> None:
        for name in ("id", "household_id", "meal_plan_id"):
            uid = getattr(self, name)
            if not isinstance(uid, UUID) or uid.version != 4:
                raise ValueError(f"{name} must be UUIDv4")
        if self.source_plan_revision_number <= 0:
            raise ValueError("source_plan_revision_number must be positive")
        for field in (
            "source_pantry_snapshot_hash",
            "config_fingerprint",
            "source_fingerprint",
            "content_fingerprint",
        ):
            value = getattr(self, field)
            if len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value):
                raise ValueError(f"{field} must be lowercase SHA-256")
        if not isinstance(self.as_of_date, date) or isinstance(
            self.as_of_date, datetime
        ):
            raise TypeError("as_of_date must be date")
        if not self.engine_version or not self.pantry_policy_version:
            raise ValueError("Shopping engine/policy identity is required")
        if not self.provenance_json:
            raise ValueError("Shopping provenance is required")
        if self.created_at.tzinfo is None or self.created_at.utcoffset() is None:
            raise ValueError("created_at must be timezone-aware")
        object.__setattr__(self, "status", ShoppingStatus(self.status))
        object.__setattr__(self, "price_status", ShoppingPriceStatus(self.price_status))


@dataclass(frozen=True)
class ShoppingListItem:
    id: UUID
    shopping_list_id: UUID
    household_id: UUID
    food_ingredient_id: UUID
    form_basis: str
    unit: UnitCode
    required_quantity: Decimal
    pantry_available_quantity: Decimal
    purchase_quantity: Decimal
    ordinal: int


@dataclass(frozen=True)
class ShoppingUnresolvedObligation:
    id: UUID
    shopping_list_id: UUID
    household_id: UUID
    meal_event_id: UUID
    source_kind: MealSourceKind
    reason: ShoppingUnresolvedReason
    ordinal: int


@dataclass(frozen=True)
class ShoppingListDetail:
    shopping_list: ShoppingList
    items: tuple[ShoppingListItem, ...]
    unresolved: tuple[ShoppingUnresolvedObligation, ...]


@dataclass(frozen=True)
class ShoppingCurrent:
    detail: ShoppingListDetail | None
    stale: bool
    reason: str | None
