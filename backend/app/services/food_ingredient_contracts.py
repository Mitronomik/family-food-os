"""Driver-independent contracts for the platform Food Catalogue."""

from types import TracebackType
from datetime import datetime
from typing import Protocol, Self
from uuid import UUID

from app.domain.food_ingredients import (
    FoodIngredient,
    FoodNutritionProfile,
    IngredientAlias,
)


class FoodIngredientRepository(Protocol):
    def add(self, ingredient: FoodIngredient) -> None: ...

    def get(self, ingredient_id: UUID) -> FoodIngredient | None: ...

    def get_by_code(self, canonical_code: str) -> FoodIngredient | None: ...

    def get_by_name_key(self, canonical_name_key: str) -> FoodIngredient | None: ...

    def list_active(self, *, limit: int) -> list[FoodIngredient]: ...

    def search_active(self, search_key: str, *, limit: int) -> list[FoodIngredient]: ...

    def set_active(
        self, ingredient_id: UUID, *, active: bool, updated_at: datetime
    ) -> None: ...


class IngredientAliasRepository(Protocol):
    def add(self, alias: IngredientAlias) -> None: ...

    def get_by_key(self, alias_key: str) -> IngredientAlias | None: ...

    def list_for_ingredient(self, ingredient_id: UUID) -> list[IngredientAlias]: ...


class FoodNutritionProfileRepository(Protocol):
    def add(self, profile: FoodNutritionProfile) -> None: ...

    def get_by_provenance(
        self,
        food_ingredient_id: UUID,
        source_name: str,
        source_id: str,
        source_version: str,
    ) -> FoodNutritionProfile | None: ...

    def get_current(self, food_ingredient_id: UUID) -> FoodNutritionProfile | None: ...

    def clear_current(self, food_ingredient_id: UUID) -> None: ...


class FoodCatalogueUnitOfWork(Protocol):
    ingredients: FoodIngredientRepository
    aliases: IngredientAliasRepository
    nutrition_profiles: FoodNutritionProfileRepository

    def __enter__(self) -> Self: ...

    def commit(self) -> None: ...

    def rollback(self) -> None: ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None: ...


class FoodCatalogueReadScope(Protocol):
    ingredients: FoodIngredientRepository
    aliases: IngredientAliasRepository
    nutrition_profiles: FoodNutritionProfileRepository

    def __enter__(self) -> Self: ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None: ...


class FoodCataloguePersistenceError(RuntimeError):
    """Stable adapter-boundary error for expected catalogue failures."""


class FoodCataloguePersistenceConflictError(FoodCataloguePersistenceError):
    """A catalogue write conflicted with authoritative persisted state."""
