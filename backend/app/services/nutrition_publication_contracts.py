"""Driver-independent ports for reviewed transactional nutrition publication."""

from collections.abc import Mapping
from types import TracebackType
from typing import Protocol, Self
from uuid import UUID

from app.domain.food_composition import FoodCompositionVersion
from app.domain.food_ingredients import (
    FoodNutritionProfile,
    NutritionSourceObservation,
)
from app.services.food_composition_contracts import CompositionWriter
from app.services.food_ingredient_contracts import (
    FoodIngredientRepository,
    IngredientAliasRepository,
)
from app.services.nutrient_vector_contracts import (
    NutrientRegistryReader,
    NutrientVectorReader,
)


class ReviewedNutritionProfileRepository(Protocol):
    def add_unsealed(
        self,
        profile: FoodNutritionProfile,
        observations: tuple[NutritionSourceObservation, ...],
    ) -> None: ...

    def get_by_provenance(
        self,
        food_ingredient_id: UUID,
        source_name: str,
        source_id: str,
        source_version: str,
    ) -> FoodNutritionProfile | None: ...

    def get_current(self, food_ingredient_id: UUID) -> FoodNutritionProfile | None: ...

    def list_observations(
        self, profile_id: UUID
    ) -> tuple[NutritionSourceObservation, ...]: ...


class ReviewedCompositionWriter(CompositionWriter, Protocol):
    def find_version(
        self, food_ingredient_id: UUID, version: int
    ) -> FoodCompositionVersion | None: ...


class NutritionPublicationUnitOfWork(Protocol):
    @property
    def ingredients(self) -> FoodIngredientRepository: ...

    @property
    def aliases(self) -> IngredientAliasRepository: ...

    @property
    def nutrition_profiles(self) -> ReviewedNutritionProfileRepository: ...

    @property
    def nutrient_registry(self) -> NutrientRegistryReader: ...

    @property
    def nutrient_vectors(self) -> NutrientVectorReader: ...

    @property
    def compositions(self) -> ReviewedCompositionWriter: ...

    def publish_vector(
        self,
        profile_id: UUID,
        *,
        registry_version: str,
        values: tuple[Mapping[str, object], ...],
        value_sha256: str,
        observations_json: str,
    ) -> None: ...

    def __enter__(self) -> Self: ...

    def commit(self) -> None: ...

    def rollback(self) -> None: ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None: ...


class NutritionPublicationPersistenceError(RuntimeError):
    """Stable persistence-boundary error for reviewed publication."""


class NutritionPublicationPersistenceConflictError(
    NutritionPublicationPersistenceError
):
    """A reviewed immutable publication conflicts with persisted truth."""
