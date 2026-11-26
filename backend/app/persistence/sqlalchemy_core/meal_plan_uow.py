"""Household MealPlan scopes over the shared SQLAlchemy transaction foundation."""

from collections.abc import Mapping
from datetime import datetime
from types import TracebackType
from typing import Self
from uuid import UUID

from sqlalchemy import update
from sqlalchemy.engine import Engine
from sqlalchemy.exc import DBAPIError, IntegrityError, OperationalError

from app.persistence.sqlalchemy_core.household_repositories import (
    SqlAlchemyHouseholdMemberRepository,
)
from app.persistence.sqlalchemy_core.household_tables import household_members_table
from app.persistence.sqlalchemy_core.meal_plan_repositories import (
    SqlAlchemyMealPlanRepository,
    SqlAlchemyMemberMealPatternSelectionRepository,
)
from app.persistence.sqlalchemy_core.reference_methodology_repositories import (
    SqlAlchemyMemberReferenceMethodologySelectionRepository,
)
from app.persistence.sqlalchemy_core.sqlite_errors import (
    is_sqlite_concurrency_conflict,
)
from app.persistence.sqlalchemy_core.uow import (
    SqlAlchemyReadOnlyScope,
    SqlAlchemyUnitOfWork,
)
from app.services.meal_plan_contracts import (
    MealPlanPersistenceConflictError,
    MealPlanPersistenceError,
)


class SqlAlchemyMealPlanUnitOfWork:
    def __init__(
        self, engine: Engine, *, enable_internal_composition_writes: bool = False
    ) -> None:
        self._scope = SqlAlchemyUnitOfWork(engine)
        # Never enabled in normal API/Planner composition roots.
        self._allow_internal_compositions = enable_internal_composition_writes
        self._selections: SqlAlchemyMemberMealPatternSelectionRepository | None = None
        self._plans: SqlAlchemyMealPlanRepository | None = None
        self._members: SqlAlchemyHouseholdMemberRepository | None = None
        self._reference_methodologies: (
            SqlAlchemyMemberReferenceMethodologySelectionRepository | None
        ) = None

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

    @property
    def members(self) -> SqlAlchemyHouseholdMemberRepository:
        if self._members is None:
            raise RuntimeError("MealPlan Unit of Work is not active.")
        return self._members

    @property
    def reference_methodologies(
        self,
    ) -> SqlAlchemyMemberReferenceMethodologySelectionRepository:
        if self._reference_methodologies is None:
            raise RuntimeError("MealPlan Unit of Work is not active.")
        return self._reference_methodologies

    def __enter__(self) -> Self:
        self._scope.__enter__()
        connection = self._scope.adapter_connection
        self._selections = SqlAlchemyMemberMealPatternSelectionRepository(connection)
        self._plans = SqlAlchemyMealPlanRepository(
            connection,
            allow_internal_composition_write=self._allow_internal_compositions,
        )
        self._members = SqlAlchemyHouseholdMemberRepository(connection)
        self._reference_methodologies = (
            SqlAlchemyMemberReferenceMethodologySelectionRepository(connection)
        )
        return self

    def guard_member_exclusions(
        self,
        *,
        household_id: UUID,
        expected: Mapping[UUID, frozenset[UUID]],
    ) -> None:
        """Acquire SQLite writer lock, then verify exact snapshot before insert.

        A concurrent preference writer can commit before this lock, in which case
        the comparison fails, or after MealPlan commit. Never validate on an
        independent read transaction: that would reopen the same TOCTOU race.
        """
        connection = self._scope.adapter_connection
        for member_id in sorted(expected, key=lambda value: value.hex):
            values = expected[member_id]
            if not isinstance(values, frozenset) or any(
                not isinstance(value, UUID) for value in values
            ):
                raise MealPlanPersistenceConflictError(
                    "Invalid persisted exclusion snapshot."
                )
            try:
                acquired = connection.execute(
                    update(household_members_table)
                    .where(
                        household_members_table.c.household_id == household_id,
                        household_members_table.c.id == member_id,
                    )
                    .values(updated_at=household_members_table.c.updated_at)
                )
                if acquired.rowcount != 1:
                    raise MealPlanPersistenceConflictError(
                        "Household member changed before MealPlan publication."
                    )
                if self.members.list_excluded_food_ids(household_id, member_id) != values:
                    raise MealPlanPersistenceConflictError(
                        "Member exclusions changed during MealPlan generation."
                    )
            except OperationalError as exc:
                if is_sqlite_concurrency_conflict(exc):
                    raise MealPlanPersistenceConflictError(
                        "Member exclusions concurrently changed during MealPlan publication."
                    ) from exc
                raise MealPlanPersistenceError(
                    "MealPlan exclusion revalidation failed."
                ) from exc
            except DBAPIError as exc:
                raise MealPlanPersistenceError(
                    "MealPlan exclusion revalidation failed."
                ) from exc

    def guard_member_state(
        self,
        *,
        household_id: UUID,
        member_id: UUID,
        member_updated_at: datetime,
    ) -> None:
        connection = self._scope.adapter_connection
        try:
            result = connection.execute(
                update(household_members_table)
                .where(
                    household_members_table.c.household_id == household_id,
                    household_members_table.c.id == member_id,
                    household_members_table.c.updated_at == member_updated_at,
                )
                .values(updated_at=member_updated_at)
            )
            if result.rowcount != 1:
                raise MealPlanPersistenceConflictError(
                    "Household member state changed before MealPlan persistence."
                )
        except OperationalError as exc:
            if is_sqlite_concurrency_conflict(exc):
                raise MealPlanPersistenceConflictError(
                    "Household member state is concurrently being changed."
                ) from exc
            raise MealPlanPersistenceError(
                "MealPlan member state revalidation failed."
            ) from exc
        except DBAPIError as exc:
            raise MealPlanPersistenceError(
                "MealPlan member state revalidation failed."
            ) from exc

    def commit(self) -> None:
        try:
            self._scope.commit()
        except IntegrityError as exc:
            raise MealPlanPersistenceConflictError(
                "MealPlan transaction conflicted with persisted state."
            ) from exc
        except DBAPIError as exc:
            raise MealPlanPersistenceError(
                "MealPlan transaction commit failed."
            ) from exc
        finally:
            self._revoke()

    def rollback(self) -> None:
        try:
            self._scope.rollback()
        except DBAPIError as exc:
            raise MealPlanPersistenceError(
                "MealPlan transaction rollback failed."
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
        self._selections = None
        self._plans = None
        self._members = None
        self._reference_methodologies = None


class SqlAlchemyMealPlanReadScope:
    def __init__(self, engine: Engine) -> None:
        self._scope = SqlAlchemyReadOnlyScope(engine)
        self._selections: SqlAlchemyMemberMealPatternSelectionRepository | None = None
        self._plans: SqlAlchemyMealPlanRepository | None = None
        self._reference_methodologies: (
            SqlAlchemyMemberReferenceMethodologySelectionRepository | None
        ) = None

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

    @property
    def reference_methodologies(
        self,
    ) -> SqlAlchemyMemberReferenceMethodologySelectionRepository:
        if self._reference_methodologies is None:
            raise RuntimeError("MealPlan read scope is not active.")
        return self._reference_methodologies

    def __enter__(self) -> Self:
        self._scope.__enter__()
        connection = self._scope.adapter_connection
        self._selections = SqlAlchemyMemberMealPatternSelectionRepository(connection)
        self._plans = SqlAlchemyMealPlanRepository(connection)
        self._reference_methodologies = (
            SqlAlchemyMemberReferenceMethodologySelectionRepository(connection)
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
            self._plans = None
            self._reference_methodologies = None
