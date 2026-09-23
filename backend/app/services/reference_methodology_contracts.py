"""Driver-independent Step 6A selection persistence contracts."""

from types import TracebackType
from typing import Protocol, Self
from uuid import UUID

from app.domain.reference_methodology import MemberReferenceMethodologySelection
from app.services.household_contracts import (
    HouseholdMemberRepository,
    HouseholdRepository,
)


class MemberReferenceMethodologySelectionRepository(Protocol):
    def add(self, selection: MemberReferenceMethodologySelection) -> None: ...

    def get(
        self, household_id: UUID, selection_id: UUID
    ) -> MemberReferenceMethodologySelection | None: ...

    def get_by_request_id(
        self,
        household_id: UUID,
        member_id: UUID,
        acceptance_request_id: UUID,
    ) -> MemberReferenceMethodologySelection | None: ...

    def get_current(
        self, household_id: UUID, member_id: UUID
    ) -> MemberReferenceMethodologySelection | None: ...

    def list_history(
        self, household_id: UUID, member_id: UUID
    ) -> list[MemberReferenceMethodologySelection]: ...


class ReferenceMethodologyUnitOfWork(Protocol):
    households: HouseholdRepository
    members: HouseholdMemberRepository
    selections: MemberReferenceMethodologySelectionRepository

    def __enter__(self) -> Self: ...
    def commit(self) -> None: ...
    def rollback(self) -> None: ...
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None: ...


class ReferenceMethodologyReadScope(Protocol):
    selections: MemberReferenceMethodologySelectionRepository

    def __enter__(self) -> Self: ...
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None: ...


class ReferenceMethodologyPersistenceError(RuntimeError):
    """Stable adapter-boundary error for Step 6A persistence failures."""


class ReferenceMethodologyPersistenceConflictError(
    ReferenceMethodologyPersistenceError
):
    """A Step 6A write conflicts with persisted authoritative state."""
