"""Meal Pattern Catalogue scopes over the shared SQLAlchemy transaction foundation."""

from types import TracebackType

from sqlalchemy.engine import Engine
from sqlalchemy.exc import DBAPIError, IntegrityError

from app.persistence.sqlalchemy_core.meal_pattern_repositories import (
    SqlAlchemyMealPatternProgramRepository,
    SqlAlchemyMealPatternVersionRepository,
)
from app.persistence.sqlalchemy_core.uow import (
    SqlAlchemyReadOnlyScope,
    SqlAlchemyUnitOfWork,
)
from app.services.meal_pattern_contracts import (
    MealPatternPersistenceConflictError,
    MealPatternPersistenceError,
)


class SqlAlchemyMealPatternCatalogueUnitOfWork:
    def __init__(self, engine: Engine) -> None:
        self._scope = SqlAlchemyUnitOfWork(engine)
        self._programs: SqlAlchemyMealPatternProgramRepository | None = None
        self._versions: SqlAlchemyMealPatternVersionRepository | None = None

    @property
    def programs(self) -> SqlAlchemyMealPatternProgramRepository:
        if self._programs is None:
            raise RuntimeError("Meal Pattern Catalogue Unit of Work is not active.")
        return self._programs

    @property
    def versions(self) -> SqlAlchemyMealPatternVersionRepository:
        if self._versions is None:
            raise RuntimeError("Meal Pattern Catalogue Unit of Work is not active.")
        return self._versions

    def __enter__(self) -> "SqlAlchemyMealPatternCatalogueUnitOfWork":
        self._scope.__enter__()
        connection = self._scope.adapter_connection
        self._programs = SqlAlchemyMealPatternProgramRepository(connection)
        self._versions = SqlAlchemyMealPatternVersionRepository(connection)
        return self

    def commit(self) -> None:
        try:
            self._scope.commit()
        except IntegrityError as exc:
            raise MealPatternPersistenceConflictError(
                "Meal Pattern Catalogue transaction conflicted with persisted state."
            ) from exc
        except DBAPIError as exc:
            raise MealPatternPersistenceError(
                "Meal Pattern Catalogue transaction commit failed."
            ) from exc
        finally:
            self._revoke()

    def rollback(self) -> None:
        try:
            self._scope.rollback()
        except DBAPIError as exc:
            raise MealPatternPersistenceError(
                "Meal Pattern Catalogue transaction rollback failed."
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
        self._programs = None
        self._versions = None


class SqlAlchemyMealPatternCatalogueReadScope:
    def __init__(self, engine: Engine) -> None:
        self._scope = SqlAlchemyReadOnlyScope(engine)
        self._programs: SqlAlchemyMealPatternProgramRepository | None = None
        self._versions: SqlAlchemyMealPatternVersionRepository | None = None

    @property
    def programs(self) -> SqlAlchemyMealPatternProgramRepository:
        if self._programs is None:
            raise RuntimeError("Meal Pattern Catalogue read scope is not active.")
        return self._programs

    @property
    def versions(self) -> SqlAlchemyMealPatternVersionRepository:
        if self._versions is None:
            raise RuntimeError("Meal Pattern Catalogue read scope is not active.")
        return self._versions

    def __enter__(self) -> "SqlAlchemyMealPatternCatalogueReadScope":
        self._scope.__enter__()
        connection = self._scope.adapter_connection
        self._programs = SqlAlchemyMealPatternProgramRepository(connection)
        self._versions = SqlAlchemyMealPatternVersionRepository(connection)
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
            self._programs = None
            self._versions = None
