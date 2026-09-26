"""Driver-independent Step 10-A Recipe Nutrition V2 persistence ports."""

from types import TracebackType
from typing import Protocol, Self
from uuid import UUID

from app.domain.food_composition import FoodCompositionVersion
from app.domain.food_ingredients import FoodIngredient
from app.domain.food_recipes import Recipe, RecipeVersionDetail
from app.domain.recipe_nutrition_v2 import RecipeIngredientCompositionBinding
from app.services.food_composition_contracts import CompositionReader
from app.services.nutrient_vector_contracts import (
    NutrientRegistryReader,
    NutrientVectorReader,
)


class RecipeNutritionV2RecipeReader(Protocol):
    def get_by_code(self, canonical_code: str) -> Recipe | None: ...


class RecipeNutritionV2VersionReader(Protocol):
    def get_detail(self, version_id: UUID) -> RecipeVersionDetail | None: ...

    def list_by_provenance(
        self,
        recipe_id: UUID,
        source_name: str,
        source_recipe_id: str,
        source_version: str,
    ) -> list[RecipeVersionDetail]: ...


class RecipeNutritionV2FoodReader(Protocol):
    def get(self, ingredient_id: UUID) -> FoodIngredient | None: ...
    def get_by_code(self, canonical_code: str) -> FoodIngredient | None: ...


class RecipeNutritionV2CompositionReader(CompositionReader, Protocol):
    def get(self, version_id: UUID) -> FoodCompositionVersion: ...

    def find_version(
        self, food_ingredient_id: UUID, version: int
    ) -> FoodCompositionVersion | None: ...


class RecipeIngredientCompositionBindingRepository(Protocol):
    def get(
        self, recipe_ingredient_id: UUID
    ) -> RecipeIngredientCompositionBinding | None: ...

    def add(self, binding: RecipeIngredientCompositionBinding) -> None: ...


class RecipeNutritionV2ReadScope(Protocol):
    @property
    def recipes(self) -> RecipeNutritionV2RecipeReader: ...

    @property
    def versions(self) -> RecipeNutritionV2VersionReader: ...

    @property
    def food_ingredients(self) -> RecipeNutritionV2FoodReader: ...

    @property
    def compositions(self) -> RecipeNutritionV2CompositionReader: ...

    @property
    def nutrient_vectors(self) -> NutrientVectorReader: ...

    @property
    def nutrient_registry(self) -> NutrientRegistryReader: ...

    @property
    def bindings(self) -> RecipeIngredientCompositionBindingRepository: ...

    def __enter__(self) -> Self: ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None: ...


class RecipeNutritionV2UnitOfWork(RecipeNutritionV2ReadScope, Protocol):
    def commit(self) -> None: ...
    def rollback(self) -> None: ...


class RecipeNutritionV2PersistenceError(RuntimeError):
    """Stable persistence-boundary failure for Step 10-A."""


class RecipeNutritionV2PersistenceConflictError(RecipeNutritionV2PersistenceError):
    """Immutable binding conflicts with persisted authority."""
