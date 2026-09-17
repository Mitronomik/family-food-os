"""Driver-independent Meal Pattern Catalogue contracts."""

from types import TracebackType
from typing import Protocol, Self
from uuid import UUID

from app.domain.meal_patterns import (
    MealPatternProgram,
    MealPatternProgramDetail,
    MealPatternProgramVersion,
)


class MealPatternProgramRepository(Protocol):
    def add(self, program: MealPatternProgram) -> None: ...
    def get(self, program_id: UUID) -> MealPatternProgram | None: ...
    def get_by_code(self, code: str) -> MealPatternProgram | None: ...


class MealPatternVersionRepository(Protocol):
    def add_detail(self, detail: MealPatternProgramDetail) -> None: ...
    def get_detail(self, version_id: UUID) -> MealPatternProgramDetail | None: ...
    def get_by_number(
        self, program_id: UUID, version_number: int
    ) -> MealPatternProgramDetail | None: ...
    def list_for_program(self, program_id: UUID) -> list[MealPatternProgramVersion]: ...
    def get_current_published(
        self, program_id: UUID
    ) -> MealPatternProgramDetail | None: ...
    def list_current_published(self) -> list[MealPatternProgramDetail]: ...


class MealPatternCatalogueUnitOfWork(Protocol):
    programs: MealPatternProgramRepository
    versions: MealPatternVersionRepository

    def __enter__(self) -> Self: ...
    def commit(self) -> None: ...
    def rollback(self) -> None: ...
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None: ...


class MealPatternCatalogueReadScope(Protocol):
    programs: MealPatternProgramRepository
    versions: MealPatternVersionRepository

    def __enter__(self) -> Self: ...
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None: ...


class MealPatternPersistenceError(RuntimeError):
    """Stable adapter-boundary error for expected catalogue failures."""


class MealPatternPersistenceConflictError(MealPatternPersistenceError):
    """A catalogue write conflicted with persisted authoritative state."""
