"""Driver-independent Shopping application and persistence contracts."""

from datetime import date
from types import TracebackType
from typing import Protocol, Self
from uuid import UUID

from app.domain.food_ingredients import FoodIngredient
from app.domain.food_recipes import RecipeVersionDetail
from app.domain.households import Household
from app.domain.meal_plans import MealPlanDetail
from app.domain.pantry import PantryItem
from app.domain.shopping_lists import ShoppingListDetail


class ShoppingListRepository(Protocol):
    def add_detail(self, detail: ShoppingListDetail) -> None: ...
    def get_detail(
        self, household_id: UUID, list_id: UUID
    ) -> ShoppingListDetail | None: ...
    def get_latest_for_plan(
        self, household_id: UUID, plan_id: UUID
    ) -> ShoppingListDetail | None: ...
    def get_by_source(
        self, household_id: UUID, plan_id: UUID, fingerprint: str
    ) -> ShoppingListDetail | None: ...
    def list_history(
        self, household_id: UUID, plan_id: UUID
    ) -> list[ShoppingListDetail]: ...


class ShoppingPlanReader(Protocol):
    def get_detail(
        self, household_id: UUID, plan_id: UUID
    ) -> MealPlanDetail | None: ...
    def get_current(
        self, household_id: UUID, week_start: date
    ) -> MealPlanDetail | None: ...


class ShoppingRecipeReader(Protocol):
    def get_detail(self, version_id: UUID) -> RecipeVersionDetail | None: ...


class ShoppingFoodReader(Protocol):
    def get(self, ingredient_id: UUID) -> FoodIngredient | None: ...


class ShoppingPantryReader(Protocol):
    def list_items(
        self, household_id: UUID, *, include_empty: bool = False
    ) -> list[PantryItem]: ...


class ShoppingHouseholdReader(Protocol):
    def get_household(self, household_id: UUID) -> Household | None: ...


class ShoppingReadScope(Protocol):
    shopping: ShoppingListRepository
    plans: ShoppingPlanReader
    recipes: ShoppingRecipeReader
    foods: ShoppingFoodReader
    pantry: ShoppingPantryReader
    households: ShoppingHouseholdReader

    def __enter__(self) -> Self: ...
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None: ...


class ShoppingUnitOfWork(ShoppingReadScope, Protocol):
    def commit(self) -> None: ...
    def rollback(self) -> None: ...


class ShoppingNotFoundError(LookupError):
    """Non-disclosing missing or wrong-household source/list."""


class ShoppingPersistenceError(RuntimeError):
    """Shopping adapter failure without leaking DB detail."""


class ShoppingPersistenceConflictError(ShoppingPersistenceError):
    """Retryable writer lock or competing version/source conflict."""
