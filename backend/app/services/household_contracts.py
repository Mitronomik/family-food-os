"""Driver-independent Household repository and transaction contracts."""

from types import TracebackType
from typing import Protocol, Self
from uuid import UUID

from app.domain.households import Household, HouseholdMember


class HouseholdRepository(Protocol):
    def add_household(self, household: Household) -> None: ...

    def get_household(self, household_id: UUID) -> Household | None: ...

    def update_household(self, household: Household) -> None: ...


class HouseholdMemberRepository(Protocol):
    def add_member(self, member: HouseholdMember) -> None: ...

    def get_member(
        self, household_id: UUID, member_id: UUID
    ) -> HouseholdMember | None: ...

    def list_members(self, household_id: UUID) -> list[HouseholdMember]: ...

    def update_member(self, member: HouseholdMember) -> None: ...


class HouseholdUnitOfWork(Protocol):
    households: HouseholdRepository
    members: HouseholdMemberRepository

    def __enter__(self) -> Self: ...

    def commit(self) -> None: ...

    def rollback(self) -> None: ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None: ...


class HouseholdReadScope(Protocol):
    households: HouseholdRepository
    members: HouseholdMemberRepository

    def __enter__(self) -> Self: ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None: ...


class HouseholdPersistenceError(RuntimeError):
    """Stable adapter-boundary error for expected Household write failures."""


class HouseholdPersistenceConflictError(HouseholdPersistenceError):
    """A Household write conflicted with an existing or linked record."""
