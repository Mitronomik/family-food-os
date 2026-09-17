"""Household MealPlan scopes over the shared SQLAlchemy transaction foundation."""

from types import TracebackType

from sqlalchemy.engine import Engine
from sqlalchemy.exc import DBAPIError, IntegrityError

from app.persistence.sqlalchemy_core.meal_plan_repositories import (
    SqlAlchemyMealPlanRepository,
    SqlAlchemyMemberMealPatternSelectionRepository,
)
from app.persistence.sqlalchemy_core.uow import SqlAlchemyReadOnlyScope, SqlAlchemyUnitOfWork
from app.services.meal_plan_contracts import (
    MealPlanPersistenceConflictError,
    MealPlanPersistenceError,
)


class SqlAlchemyMealPlanUnitOfWork:
    def __init__(self, engine: Engine) -> None:
        self._scope = SqlAlchemyUnitOfWork(engine)
        self._selections: SqlAlchemyMemberMealPatternSelectionRepository | None = None
        self._plans: SqlAlchemyMealPlanRepository | None = None

    @property
    def selections(self) -> SqlAlchemyMemberMealPatternSelectionRepository:
        if self._selections is None:
            raise RuntimeError("MealPlan Unit of Work is not active.")
        return self._selections

    @property
    def plans(self) -> SqlAlchemyMealPlanRepository:
        if self._plans is None:
            raise RuntimeError("MealPlan Unit of Work is not active.")
        return self._plans

    def __enter__(self) -> "SqlAlchemyMealPlanUnitOfWork":
        self._scope.__enter__()
        connection = self._scope.adapter_connection
        self._selections = SqlAlchemyMemberMealPatternSelectionRepository(connection)
        self._plans = SqlAlchemyMealPlanRepository(connection)
        return self

    def commit(self) -> None:
        try:
            self._scope.commit()
        except IntegrityError as exc:
            raise MealPlanPersistenceConflictError(
                "MealPlan transaction conflicted with persisted state."
            ) from exc
        except DBAPIError as exc:
            raise MealPlanPersistenceError("MealPlan transaction commit failed.") from exc
        finally:
            self._revoke()

    def rollback(self) -> None:
        try:
            self._scope.rollback()
        except DBAPIError as exc:
            raise MealPlanPersistenceError("MealPlan transaction rollback failed.") from exc
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
        self._selections = None
        self._plans = None


class SqlAlchemyMealPlanReadScope:
    def __init__(self, engine: Engine) -> None:
        self._scope = SqlAlchemyReadOnlyScope(engine)
        self._selections: SqlAlchemyMemberMealPatternSelectionRepository | None = None
        self._plans: SqlAlchemyMealPlanRepository | None = None

    @property
    def selections(self) -> SqlAlchemyMemberMealPatternSelectionRepository:
        if self._selections is None:
            raise RuntimeError("MealPlan read scope is not active.")
        return self._selections

    @property
    def plans(self) -> SqlAlchemyMealPlanRepository:
        if self._plans is None:
            raise RuntimeError("MealPlan read scope is not active.")
        return self._plans

    def __enter__(self) -> "SqlAlchemyMealPlanReadScope":
        self._scope.__enter__()
        connection = self._scope.adapter_connection
        self._selections = SqlAlchemyMemberMealPatternSelectionRepository(connection)
        self._plans = SqlAlchemyMealPlanRepository(connection)
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
            self._plans = None
