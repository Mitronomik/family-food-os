"""Transactional commands for confirmed Household stock facts."""

from collections.abc import Callable, Mapping
from dataclasses import replace
from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from app.domain.food_ingredients import FoodIngredient
from app.domain.units import UnitCode
from app.domain.pantry import (
    PantryItem,
    PantryLocation,
    PantryMovement,
    PantryMovementType,
    invalid,
    normalize_date,
    normalize_quantity,
    normalize_unit,
    update_item_metadata,
    validate_ingredient_unit,
    validate_uuid,
)
from app.services.households import HouseholdNotFoundError
from app.services.pantry_contracts import (
    PantryReadScope,
    PantryUnitOfWork,
    PantryPersistenceConflictError,
)


class PantryItemNotFoundError(LookupError):
    pass


class PantryFoodIngredientNotFoundError(LookupError):
    pass


class PantryInactiveFoodIngredientError(ValueError):
    pass


class PantryInsufficientStockError(ValueError):
    pass


class PantryService:
    def __init__(
        self,
        write_scope_factory: Callable[[], PantryUnitOfWork],
        read_scope_factory: Callable[[], PantryReadScope],
        *,
        id_factory: Callable[[], UUID] = uuid4,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._write_scope_factory = write_scope_factory
        self._read_scope_factory = read_scope_factory
        self._id_factory = id_factory
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    @staticmethod
    def _household(scope: PantryReadScope, household_id: UUID) -> None:
        validate_uuid(household_id, field="household_id")
        if scope.households.get_household(household_id) is None:
            raise HouseholdNotFoundError("Household was not found.")

    @staticmethod
    def _ingredient(scope: PantryReadScope, food_ingredient_id: UUID) -> FoodIngredient:
        validate_uuid(food_ingredient_id, field="food_ingredient_id")
        ingredient = scope.food_ingredients.get(food_ingredient_id)
        if ingredient is None:
            raise PantryFoodIngredientNotFoundError("FoodIngredient was not found.")
        return ingredient

    @staticmethod
    def _item(scope: PantryReadScope, household_id: UUID, item_id: UUID) -> PantryItem:
        validate_uuid(item_id, field="item_id")
        item = scope.items.get(household_id, item_id)
        if item is None:
            raise PantryItemNotFoundError(
                "Pantry item was not found in this Household."
            )
        return item

    def _movement(
        self,
        scope: PantryUnitOfWork,
        item: PantryItem,
        movement_type: PantryMovementType,
        quantity: Decimal,
        now: datetime,
    ) -> PantryMovement:
        movement = PantryMovement(
            id=self._id_factory(),
            household_id=item.household_id,
            pantry_item_id=item.id,
            movement_type=movement_type,
            quantity=quantity,
            unit=item.unit,
            occurred_at=now,
            created_at=now,
        )
        scope.movements.add(movement)
        return movement

    def add_stock(
        self,
        household_id: UUID,
        *,
        food_ingredient_id: UUID,
        quantity: Decimal | int | str,
        unit: UnitCode | str,
        location: PantryLocation = PantryLocation.PANTRY,
        estimated: bool = False,
        purchased_on: date | None = None,
        opened_on: date | None = None,
        expires_on: date | None = None,
    ) -> PantryItem:
        quantity = normalize_quantity(quantity, positive=True)
        with self._write_scope_factory() as scope:
            self._household(scope, household_id)
            ingredient = self._ingredient(scope, food_ingredient_id)
            if not ingredient.is_active:
                raise PantryInactiveFoodIngredientError(
                    "New stock requires an active FoodIngredient."
                )
            unit = validate_ingredient_unit(ingredient, unit)
            now = self._clock()
            item = PantryItem(
                self._id_factory(),
                household_id,
                food_ingredient_id,
                quantity,
                unit,
                location,
                estimated,
                purchased_on,
                opened_on,
                expires_on,
                now,
                now,
            )
            scope.items.add(item)
            self._movement(scope, item, PantryMovementType.ADD, quantity, now)
            scope.commit()
            return item

    def _change(
        self,
        scope: PantryUnitOfWork,
        item: PantryItem,
        amount: Decimal,
        movement_type: PantryMovementType,
        now: datetime,
    ) -> tuple[PantryItem, PantryMovement]:
        outgoing = movement_type.direction < 0
        if outgoing and amount > item.quantity:
            raise PantryInsufficientStockError("Insufficient Pantry stock.")
        operation = (
            scope.items.decrease_quantity_if_sufficient
            if outgoing
            else scope.items.increase_quantity
        )
        if not operation(
            item.household_id,
            item.id,
            amount,
            expected_quantity=item.quantity,
            updated_at=now,
        ):
            raise PantryPersistenceConflictError(
                "Pantry stock changed; reload and retry the command."
            )
        movement = self._movement(scope, item, movement_type, amount, now)
        updated = replace(
            item,
            quantity=item.quantity + movement_type.direction * amount,
            updated_at=now,
        )
        return updated, movement

    def consume(
        self,
        household_id: UUID,
        *,
        food_ingredient_id: UUID,
        quantity: Decimal | int | str,
        unit: UnitCode | str,
    ) -> list[PantryMovement]:
        quantity = normalize_quantity(quantity, positive=True)
        unit = normalize_unit(unit)
        with self._write_scope_factory() as scope:
            self._household(scope, household_id)
            ingredient = self._ingredient(scope, food_ingredient_id)
            validate_ingredient_unit(ingredient, unit)
            items = scope.items.list_available_for_ingredient_fefo(
                household_id, food_ingredient_id
            )
            if sum((item.quantity for item in items), Decimal(0)) < quantity:
                raise PantryInsufficientStockError("Insufficient Pantry stock.")
            remaining = quantity
            movements = []
            now = self._clock()
            for item in items:
                if not remaining:
                    break
                amount = min(item.quantity, remaining)
                _, movement = self._change(
                    scope, item, amount, PantryMovementType.CONSUMPTION, now
                )
                movements.append(movement)
                remaining -= amount
            scope.commit()
            return movements

    def waste(
        self,
        household_id: UUID,
        item_id: UUID,
        *,
        quantity: Decimal | int | str,
        unit: UnitCode | str,
    ) -> PantryItem:
        amount = normalize_quantity(quantity, positive=True)
        unit = normalize_unit(unit)
        with self._write_scope_factory() as scope:
            self._household(scope, household_id)
            item = self._item(scope, household_id, item_id)
            if item.unit != unit:
                raise invalid("unit", unit, "Unit must equal the Pantry item's unit.")
            updated, _ = self._change(
                scope, item, amount, PantryMovementType.WASTE, self._clock()
            )
            scope.commit()
            return updated

    def adjust(
        self,
        household_id: UUID,
        item_id: UUID,
        *,
        target_quantity: Decimal | int | str,
        unit: UnitCode | str,
    ) -> PantryItem:
        target = normalize_quantity(target_quantity)
        unit = normalize_unit(unit)
        with self._write_scope_factory() as scope:
            self._household(scope, household_id)
            item = self._item(scope, household_id, item_id)
            if item.unit != unit:
                raise invalid("unit", unit, "Unit must equal the Pantry item's unit.")
            delta = target - item.quantity
            if delta:
                movement_type = (
                    PantryMovementType.ADJUSTMENT_IN
                    if delta > 0
                    else PantryMovementType.ADJUSTMENT_OUT
                )
                item, _ = self._change(
                    scope, item, abs(delta), movement_type, self._clock()
                )
            scope.commit()
            return item

    def update_metadata(
        self, household_id: UUID, item_id: UUID, changes: Mapping[str, object]
    ) -> PantryItem:
        with self._write_scope_factory() as scope:
            self._household(scope, household_id)
            item = self._item(scope, household_id, item_id)
            updated = update_item_metadata(item, changes, updated_at=self._clock())
            scope.items.update_metadata(updated)
            scope.commit()
            return updated

    def get_item(self, household_id: UUID, item_id: UUID) -> PantryItem:
        with self._read_scope_factory() as scope:
            self._household(scope, household_id)
            return self._item(scope, household_id, item_id)

    def list_items(
        self,
        household_id: UUID,
        *,
        food_ingredient_id: UUID | None = None,
        location: PantryLocation | None = None,
        include_empty: bool = False,
    ) -> list[PantryItem]:
        if location is not None:
            try:
                location = PantryLocation(location)
            except (ValueError, TypeError) as exc:
                raise invalid("location", location, "Invalid Pantry location.") from exc
        if type(include_empty) is not bool:
            raise invalid("include_empty", include_empty, "Supply a boolean.")
        with self._read_scope_factory() as scope:
            self._household(scope, household_id)
            if food_ingredient_id is not None:
                self._ingredient(scope, food_ingredient_id)
            return scope.items.list_items(
                household_id,
                food_ingredient_id=food_ingredient_id,
                location=location,
                include_empty=include_empty,
            )

    def get_available_quantity(
        self, household_id: UUID, food_ingredient_id: UUID
    ) -> Decimal:
        with self._read_scope_factory() as scope:
            self._household(scope, household_id)
            self._ingredient(scope, food_ingredient_id)
            return sum(
                (
                    item.quantity
                    for item in scope.items.list_available_for_ingredient_fefo(
                        household_id, food_ingredient_id
                    )
                ),
                Decimal("0.000"),
            )

    def list_expiring(self, household_id: UUID, on_or_before: date) -> list[PantryItem]:
        if normalize_date(on_or_before, field="on_or_before") is None:
            raise invalid(
                "on_or_before", on_or_before, "Supply an explicit calendar date."
            )
        with self._read_scope_factory() as scope:
            self._household(scope, household_id)
            return scope.items.list_expiring(household_id, on_or_before)
