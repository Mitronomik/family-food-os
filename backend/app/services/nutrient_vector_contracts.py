"""Internal full-snapshot read abstraction; no consumer API expansion."""

from typing import Protocol, Self
from types import TracebackType
from uuid import UUID

from app.domain.nutrient_vector import NutrientVector


class NutrientVectorReader(Protocol):
    def get(self, profile_id: UUID) -> NutrientVector:
        """Read all sealed values or raise NutrientVectorUnavailableError.

        Missing nutrients are unknown only within this complete read. An absent
        seal (including an unaudited v1 profile) is never an empty vector.
        """
        ...


class NutrientVectorReadScope(Protocol):
    @property
    def nutrient_vectors(self) -> NutrientVectorReader: ...

    def __enter__(self) -> Self: ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None: ...
