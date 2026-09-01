"""Household-specific composition over the generic SQLAlchemy scopes."""

from types import TracebackType

from sqlalchemy.engine import Engine
from sqlalchemy.exc import DBAPIError, IntegrityError

from app.persistence.sqlalchemy_core.household_repositories import (
    SqlAlchemyHouseholdMemberRepository,
    SqlAlchemyHouseholdRepository,
)
from app.persistence.sqlalchemy_core.uow import (
    SqlAlchemyReadOnlyScope,
    SqlAlchemyUnitOfWork,
)
from app.services.household_contracts import (
    HouseholdPersistenceConflictError,
    HouseholdPersistenceError,
)


class SqlAlchemyHouseholdUnitOfWork:
    def __init__(self, engine: Engine) -> None:
        self._scope = SqlAlchemyUnitOfWork(engine)
        self._households: SqlAlchemyHouseholdRepository | None = None
        self._members: SqlAlchemyHouseholdMemberRepository | None = None

    @property
    def households(self) -> SqlAlchemyHouseholdRepository:
        if self._households is None:
            raise RuntimeError("The Household Unit of Work is not active.")
        return self._households

    @property
    def members(self) -> SqlAlchemyHouseholdMemberRepository:
        if self._members is None:
            raise RuntimeError("The Household Unit of Work is not active.")
        return self._members

    def __enter__(self) -> "SqlAlchemyHouseholdUnitOfWork":
        self._scope.__enter__()
        connection = self._scope.adapter_connection
        self._households = SqlAlchemyHouseholdRepository(connection)
        self._members = SqlAlchemyHouseholdMemberRepository(connection)
        return self

    def commit(self) -> None:
        try:
            self._scope.commit()
        except IntegrityError as exc:
            raise HouseholdPersistenceConflictError(
                "Household transaction commit conflicted with persisted state."
            ) from exc
        except DBAPIError as exc:
            raise HouseholdPersistenceError(
                "Household transaction commit failed at the persistence boundary."
            ) from exc
        finally:
            self._revoke_repositories()

    def rollback(self) -> None:
        try:
            self._scope.rollback()
        except DBAPIError as exc:
            raise HouseholdPersistenceError(
                "Household transaction rollback failed at the persistence boundary."
            ) from exc
        finally:
            self._revoke_repositories()

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None:
        try:
            return self._scope.__exit__(exc_type, exc_value, traceback)
        finally:
            self._revoke_repositories()

    def _revoke_repositories(self) -> None:
        self._households = None
        self._members = None


class SqlAlchemyHouseholdReadScope:
    def __init__(self, engine: Engine) -> None:
        self._scope = SqlAlchemyReadOnlyScope(engine)
        self._households: SqlAlchemyHouseholdRepository | None = None
        self._members: SqlAlchemyHouseholdMemberRepository | None = None

    @property
    def households(self) -> SqlAlchemyHouseholdRepository:
        if self._households is None:
            raise RuntimeError("The Household read scope is not active.")
        return self._households

    @property
    def members(self) -> SqlAlchemyHouseholdMemberRepository:
        if self._members is None:
            raise RuntimeError("The Household read scope is not active.")
        return self._members

    def __enter__(self) -> "SqlAlchemyHouseholdReadScope":
        self._scope.__enter__()
        connection = self._scope.adapter_connection
        self._households = SqlAlchemyHouseholdRepository(connection)
        self._members = SqlAlchemyHouseholdMemberRepository(connection)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None:
        try:
            return self._scope.__exit__(exc_type, exc_value, traceback)
        finally:
            self._households = None
            self._members = None
