"""Driver-independent Household Pantry persistence contracts."""

from datetime import date, datetime
from decimal import Decimal
from types import TracebackType
from typing import Protocol, Self
from uuid import UUID

from app.domain.pantry import PantryItem, PantryLocation, PantryMovement
from app.services.food_ingredient_contracts import FoodIngredientRepository
from app.services.household_contracts import HouseholdRepository


class PantryItemRepository(Protocol):
    def add(self, item: PantryItem) -> None: ...
    def get(self, household_id: UUID, item_id: UUID) -> PantryItem | None: ...
    def list_items(
        self,
        household_id: UUID,
        *,
        food_ingredient_id: UUID | None = None,
        location: PantryLocation | None = None,
        include_empty: bool = False,
    ) -> list[PantryItem]: ...
    def list_available_for_ingredient_fefo(
        self, household_id: UUID, food_ingredient_id: UUID
    ) -> list[PantryItem]: ...
    def list_expiring(
        self, household_id: UUID, on_or_before: date
    ) -> list[PantryItem]: ...
    def update_metadata(self, item: PantryItem) -> None: ...
    def increase_quantity(
        self,
        household_id: UUID,
        item_id: UUID,
        amount: Decimal,
        *,
        expected_quantity: Decimal,
        updated_at: datetime,
    ) -> bool: ...
    def decrease_quantity_if_sufficient(
        self,
        household_id: UUID,
        item_id: UUID,
        amount: Decimal,
        *,
        expected_quantity: Decimal,
        updated_at: datetime,
    ) -> bool: ...


class PantryMovementRepository(Protocol):
    def add(self, movement: PantryMovement) -> None: ...
    def list_for_item(
        self, household_id: UUID, item_id: UUID
    ) -> list[PantryMovement]: ...


class PantryReadScope(Protocol):
    items: PantryItemRepository
    movements: PantryMovementRepository
    households: HouseholdRepository
    food_ingredients: FoodIngredientRepository

    def __enter__(self) -> Self: ...
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None: ...


class PantryUnitOfWork(PantryReadScope, Protocol):
    def commit(self) -> None: ...
    def rollback(self) -> None: ...


class PantryPersistenceError(RuntimeError):
    """A stable Pantry adapter failure."""


class PantryPersistenceConflictError(PantryPersistenceError):
    """Persisted state changed or conflicts with a Pantry command."""
