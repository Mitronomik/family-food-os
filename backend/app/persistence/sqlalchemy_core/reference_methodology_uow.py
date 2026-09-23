"""Step 6A SQLAlchemy transaction/read scopes."""

from types import TracebackType

from sqlalchemy.engine import Engine
from sqlalchemy.exc import DBAPIError, IntegrityError

from app.persistence.sqlalchemy_core.household_repositories import (
    SqlAlchemyHouseholdMemberRepository,
    SqlAlchemyHouseholdRepository,
)
from app.persistence.sqlalchemy_core.reference_methodology_repositories import (
    SqlAlchemyMemberReferenceMethodologySelectionRepository,
)
from app.persistence.sqlalchemy_core.uow import SqlAlchemyReadOnlyScope, SqlAlchemyUnitOfWork
from app.services.reference_methodology_contracts import (
    ReferenceMethodologyPersistenceConflictError,
    ReferenceMethodologyPersistenceError,
)


class SqlAlchemyReferenceMethodologyUnitOfWork:
    def __init__(self, engine: Engine) -> None:
        self._scope = SqlAlchemyUnitOfWork(engine)
        self._households: SqlAlchemyHouseholdRepository | None = None
        self._members: SqlAlchemyHouseholdMemberRepository | None = None
        self._selections: (
            SqlAlchemyMemberReferenceMethodologySelectionRepository | None
        ) = None

    @property
    def households(self) -> SqlAlchemyHouseholdRepository:
        if self._households is None:
            raise RuntimeError("Reference-methodology Unit of Work is not active.")
        return self._households

    @property
    def members(self) -> SqlAlchemyHouseholdMemberRepository:
        if self._members is None:
            raise RuntimeError("Reference-methodology Unit of Work is not active.")
        return self._members

    @property
    def selections(self) -> SqlAlchemyMemberReferenceMethodologySelectionRepository:
        if self._selections is None:
            raise RuntimeError("Reference-methodology Unit of Work is not active.")
        return self._selections

    def __enter__(self) -> "SqlAlchemyReferenceMethodologyUnitOfWork":
        self._scope.__enter__()
        connection = self._scope.adapter_connection
        self._households = SqlAlchemyHouseholdRepository(connection)
        self._members = SqlAlchemyHouseholdMemberRepository(connection)
        self._selections = SqlAlchemyMemberReferenceMethodologySelectionRepository(
            connection
        )
        return self

    def commit(self) -> None:
        try:
            self._scope.commit()
        except IntegrityError as exc:
            raise ReferenceMethodologyPersistenceConflictError(
                "Reference-methodology transaction commit conflicted."
            ) from exc
        except DBAPIError as exc:
            raise ReferenceMethodologyPersistenceError(
                "Reference-methodology transaction commit failed."
            ) from exc
        finally:
            self._revoke()

    def rollback(self) -> None:
        try:
            self._scope.rollback()
        except DBAPIError as exc:
            raise ReferenceMethodologyPersistenceError(
                "Reference-methodology transaction rollback failed."
            ) from exc
        finally:
            self._revoke()

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None:
        try:
            return self._scope.__exit__(exc_type, exc_value, traceback)
        finally:
            self._revoke()

    def _revoke(self) -> None:
        self._households = None
        self._members = None
        self._selections = None


class SqlAlchemyReferenceMethodologyReadScope:
    def __init__(self, engine: Engine) -> None:
        self._scope = SqlAlchemyReadOnlyScope(engine)
        self._selections: (
            SqlAlchemyMemberReferenceMethodologySelectionRepository | None
        ) = None

    @property
    def selections(self) -> SqlAlchemyMemberReferenceMethodologySelectionRepository:
        if self._selections is None:
            raise RuntimeError("Reference-methodology read scope is not active.")
        return self._selections

    def __enter__(self) -> "SqlAlchemyReferenceMethodologyReadScope":
        self._scope.__enter__()
        self._selections = SqlAlchemyMemberReferenceMethodologySelectionRepository(
            self._scope.adapter_connection
        )
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
            self._selections = None
