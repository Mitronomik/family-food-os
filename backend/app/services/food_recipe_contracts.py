"""Driver-independent Recipe Catalogue contracts."""

from datetime import datetime
from types import TracebackType
from typing import Protocol, Self
from uuid import UUID

from app.domain.food_ingredients import FoodIngredient
from app.domain.food_recipes import Recipe, RecipeVersion, RecipeVersionDetail


class RecipeRepository(Protocol):
    def add(self, recipe: Recipe) -> None: ...
    def get(self, recipe_id: UUID) -> Recipe | None: ...
    def get_by_code(self, canonical_code: str) -> Recipe | None: ...
    def get_by_name_key(self, canonical_name_key: str) -> Recipe | None: ...
    def list_active(self, *, limit: int) -> list[Recipe]: ...
    def set_active(
        self, recipe_id: UUID, *, active: bool, updated_at: datetime
    ) -> None: ...


class RecipeVersionRepository(Protocol):
    def add_detail(self, detail: RecipeVersionDetail) -> None: ...
    def get(self, version_id: UUID) -> RecipeVersion | None: ...
    def get_detail(self, version_id: UUID) -> RecipeVersionDetail | None: ...
    def list_for_recipe(self, recipe_id: UUID) -> list[RecipeVersion]: ...
    def get_current_verified(self, recipe_id: UUID) -> RecipeVersionDetail | None: ...
    def get_by_provenance(
        self,
        recipe_id: UUID,
        source_name: str,
        source_recipe_id: str,
        source_version: str,
    ) -> RecipeVersionDetail | None: ...


class FoodIngredientLookup(Protocol):
    def get(self, ingredient_id: UUID) -> FoodIngredient | None: ...
    def get_by_code(self, canonical_code: str) -> FoodIngredient | None: ...


class RecipeCatalogueUnitOfWork(Protocol):
    recipes: RecipeRepository
    versions: RecipeVersionRepository
    food_ingredients: FoodIngredientLookup

    def __enter__(self) -> Self: ...
    def commit(self) -> None: ...
    def rollback(self) -> None: ...
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None: ...


class RecipeCatalogueReadScope(Protocol):
    recipes: RecipeRepository
    versions: RecipeVersionRepository
    food_ingredients: FoodIngredientLookup

    def __enter__(self) -> Self: ...
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None: ...


class RecipeCataloguePersistenceError(RuntimeError):
    """Stable adapter-boundary error for expected Recipe Catalogue failures."""


class RecipeCataloguePersistenceConflictError(RecipeCataloguePersistenceError):
    """A Recipe Catalogue write conflicted with persisted authoritative state."""
