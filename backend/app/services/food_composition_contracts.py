"""Internal composition ports; repositories use their caller's active UoW."""

from typing import Protocol, Self
from types import TracebackType
from uuid import UUID

from app.domain.food_composition import (
    FoodCompositionVersion,
    FoodTransformation,
    YieldModel,
    NutrientRetentionProfile,
)
from app.domain.nutrient_vector import NutrientDefinition
from app.services.nutrient_vector_contracts import NutrientVectorReader


class CompositionReader(Protocol):
    def get(self, version_id: UUID) -> FoodCompositionVersion: ...
    def transformation(self, version_id: UUID) -> FoodTransformation: ...
    def yield_model(self, version_id: UUID) -> YieldModel: ...
    def retention_profile(self, version_id: UUID) -> NutrientRetentionProfile: ...
    def nutrient_definition(self, code: str) -> NutrientDefinition: ...


class CompositionWriter(CompositionReader, Protocol):
    def add_versions(self, versions: tuple[FoodCompositionVersion, ...]) -> None: ...
    def add_transformation(self, value: FoodTransformation) -> None: ...
    def add_yield_model(self, value: YieldModel) -> None: ...
    def add_retention_profile(self, value: NutrientRetentionProfile) -> None: ...


class CompositionReadScope(Protocol):
    @property
    def compositions(self) -> CompositionReader: ...

    @property
    def nutrient_vectors(self) -> NutrientVectorReader: ...

    def __enter__(self) -> Self: ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None: ...


class CompositionUnitOfWork(CompositionReadScope, Protocol):
    @property
    def compositions(self) -> CompositionWriter: ...

    def commit(self) -> None: ...

    def rollback(self) -> None: ...
