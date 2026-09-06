"""Household-scoped Pantry storage with exact compare-and-swap balances."""

from dataclasses import asdict
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import insert, select, update
from sqlalchemy.engine import Connection
from sqlalchemy.exc import IntegrityError, OperationalError, ResourceClosedError

from app.domain.pantry import (
    PantryItem,
    PantryLocation,
    PantryMovement,
    normalize_quantity,
)
from app.persistence.sqlalchemy_core.pantry_tables import (
    pantry_items_table as items,
    pantry_movements_table as movements,
)
from app.services.pantry_contracts import (
    PantryPersistenceConflictError,
    PantryPersistenceError,
)


def _fefo_order():
    return (
        items.c.expires_on.is_(None),
        items.c.expires_on,
        items.c.purchased_on.is_(None),
        items.c.purchased_on,
        items.c.created_at,
        items.c.id,
    )


class SqlAlchemyPantryItemRepository:
    def __init__(self, connection: Connection) -> None:
        self._connection = connection

    def add(self, item: PantryItem) -> None:
        normalize_quantity(item.quantity, positive=True)
        try:
            self._connection.execute(insert(items).values(**asdict(item)))
        except (IntegrityError, OperationalError) as exc:
            raise PantryPersistenceConflictError(
                "Pantry item identity, Household or FoodIngredient state conflicts."
            ) from exc

    def get(self, household_id: UUID, item_id: UUID) -> PantryItem | None:
        row = (
            self._connection.execute(
                select(items).where(
                    items.c.household_id == household_id, items.c.id == item_id
                )
            )
            .mappings()
            .one_or_none()
        )
        return PantryItem(**row) if row is not None else None

    def list_items(
        self,
        household_id: UUID,
        *,
        food_ingredient_id: UUID | None = None,
        location: PantryLocation | None = None,
        include_empty: bool = False,
    ) -> list[PantryItem]:
        query = select(items).where(items.c.household_id == household_id)
        if food_ingredient_id is not None:
            query = query.where(items.c.food_ingredient_id == food_ingredient_id)
        if location is not None:
            query = query.where(items.c.location == location)
        if not include_empty:
            query = query.where(items.c.quantity != Decimal("0.000"))
        return [
            PantryItem(**row)
            for row in self._connection.execute(
                query.order_by(*_fefo_order())
            ).mappings()
        ]

    def list_available_for_ingredient_fefo(
        self, household_id: UUID, food_ingredient_id: UUID
    ) -> list[PantryItem]:
        return self.list_items(household_id, food_ingredient_id=food_ingredient_id)

    def list_expiring(self, household_id: UUID, on_or_before: date) -> list[PantryItem]:
        query = (
            select(items)
            .where(
                items.c.household_id == household_id,
                items.c.quantity != Decimal("0.000"),
                items.c.expires_on <= on_or_before,
            )
            .order_by(*_fefo_order())
        )
        return [PantryItem(**row) for row in self._connection.execute(query).mappings()]

    def update_metadata(self, item: PantryItem) -> None:
        values = {
            name: getattr(item, name)
            for name in (
                "location",
                "estimated",
                "purchased_on",
                "opened_on",
                "expires_on",
                "updated_at",
            )
        }
        try:
            result = self._connection.execute(
                update(items)
                .where(items.c.id == item.id, items.c.household_id == item.household_id)
                .values(**values)
            )
        except (IntegrityError, OperationalError) as exc:
            raise PantryPersistenceConflictError(
                "Pantry metadata update conflicts with persisted state."
            ) from exc
        if result.rowcount != 1:
            raise PantryPersistenceError(
                "Pantry metadata update did not affect one Household item."
            )

    def increase_quantity(
        self,
        household_id: UUID,
        item_id: UUID,
        amount: Decimal,
        *,
        expected_quantity: Decimal,
        updated_at: datetime,
    ) -> bool:
        if self._connection.closed:
            raise ResourceClosedError("This Connection is closed")
        amount = normalize_quantity(amount, positive=True)
        expected = normalize_quantity(expected_quantity)
        target = normalize_quantity(expected + amount)
        return self._compare_and_swap(
            household_id, item_id, expected, target, updated_at
        )

    def decrease_quantity_if_sufficient(
        self,
        household_id: UUID,
        item_id: UUID,
        amount: Decimal,
        *,
        expected_quantity: Decimal,
        updated_at: datetime,
    ) -> bool:
        if self._connection.closed:
            raise ResourceClosedError("This Connection is closed")
        amount = normalize_quantity(amount, positive=True)
        expected = normalize_quantity(expected_quantity)
        if expected < amount:
            return False
        return self._compare_and_swap(
            household_id, item_id, expected, expected - amount, updated_at
        )

    def _compare_and_swap(
        self,
        household_id: UUID,
        item_id: UUID,
        expected: Decimal,
        target: Decimal,
        updated_at: datetime,
    ) -> bool:
        # Equality on canonical DecimalText is exact. A stale reader cannot debit a
        # newer balance; SQLite snapshot/write conflicts also fail closed.
        try:
            result = self._connection.execute(
                update(items)
                .where(
                    items.c.id == item_id,
                    items.c.household_id == household_id,
                    items.c.quantity == expected,
                )
                .values(quantity=target, updated_at=updated_at)
            )
        except (IntegrityError, OperationalError) as exc:
            raise PantryPersistenceConflictError(
                "Pantry stock changed or is busy; retry the command."
            ) from exc
        return result.rowcount == 1


class SqlAlchemyPantryMovementRepository:
    def __init__(self, connection: Connection) -> None:
        self._connection = connection

    def add(self, movement: PantryMovement) -> None:
        try:
            self._connection.execute(insert(movements).values(**asdict(movement)))
        except (IntegrityError, OperationalError) as exc:
            raise PantryPersistenceConflictError(
                "Pantry movement identity or Household item/unit link conflicts."
            ) from exc

    def list_for_item(self, household_id: UUID, item_id: UUID) -> list[PantryMovement]:
        query = (
            select(movements)
            .where(
                movements.c.household_id == household_id,
                movements.c.pantry_item_id == item_id,
            )
            .order_by(movements.c.occurred_at, movements.c.created_at, movements.c.id)
        )
        return [
            PantryMovement(**row) for row in self._connection.execute(query).mappings()
        ]
