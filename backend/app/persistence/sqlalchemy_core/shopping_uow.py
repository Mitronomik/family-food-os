"""PR9-B one-connection SQLite Shopping UoW, with a *physical* BEGIN IMMEDIATE.

The existing SQLite engine opts into sqlite3 autocommit=False (PEP 249).
A SQLAlchemy Connection.begin() is a logical scope and does not acquire a
SQLite RESERVED writer lock. This adapter temporarily uses sqlite3 explicit
SQL transaction mode and restores the pooled connection on exit.
"""

from types import TracebackType
from typing import Self

from sqlalchemy.engine import Connection, Engine
from sqlalchemy.exc import DBAPIError, IntegrityError, OperationalError

from app.persistence.sqlalchemy_core.food_ingredient_repositories import (
    SqlAlchemyFoodIngredientRepository,
)
from app.persistence.sqlalchemy_core.food_recipe_repositories import (
    SqlAlchemyRecipeVersionRepository,
)
from app.persistence.sqlalchemy_core.household_repositories import (
    SqlAlchemyHouseholdRepository,
)
from app.persistence.sqlalchemy_core.meal_plan_repositories import (
    SqlAlchemyMealPlanRepository,
)
from app.persistence.sqlalchemy_core.pantry_repositories import (
    SqlAlchemyPantryItemRepository,
)
from app.persistence.sqlalchemy_core.shopping_repositories import (
    SqlAlchemyShoppingListRepository,
)
from app.persistence.sqlalchemy_core.sqlite_errors import is_sqlite_concurrency_conflict
from app.persistence.sqlalchemy_core.uow import SqlAlchemyReadOnlyScope
from app.services.shopping_contracts import (
    ShoppingPersistenceConflictError,
    ShoppingPersistenceError,
)


class _ShoppingRepositories:
    """Read/write repositories sharing precisely the active Core connection."""

    def _bind(self, connection: Connection) -> None:
        self.shopping = SqlAlchemyShoppingListRepository(connection)
        self.plans = SqlAlchemyMealPlanRepository(connection)
        self.recipes = SqlAlchemyRecipeVersionRepository(connection)
        self.foods = SqlAlchemyFoodIngredientRepository(connection)
        self.pantry = SqlAlchemyPantryItemRepository(connection)
        self.households = SqlAlchemyHouseholdRepository(connection)


class SqlAlchemyShoppingUnitOfWork(_ShoppingRepositories):
    def __init__(self, engine: Engine) -> None:
        self._engine = engine
        self._used = False
        self._connection: Connection | None = None
        self._dbapi = None
        self._original_autocommit = None

    def __enter__(self) -> Self:
        if self._used:
            raise RuntimeError("Shopping UoW is single-use")
        self._used = True
        connection = self._engine.connect()
        self._connection = connection
        try:
            dbapi = connection.connection.driver_connection
            if not hasattr(dbapi, "autocommit") or dbapi.autocommit is not False:
                raise ShoppingPersistenceError(
                    "Shopping requires sqlite3 3.12+ with explicit transaction control"
                )
            self._dbapi = dbapi
            self._original_autocommit = dbapi.autocommit
            # No source reads have occurred. Leaving automatic deferred mode
            # ends the *empty* DBAPI transaction, then BEGIN IMMEDIATE grabs
            # the writer reservation before any domain data is read.
            dbapi.autocommit = True
            connection.exec_driver_sql("BEGIN IMMEDIATE")
            if not dbapi.in_transaction:
                raise ShoppingPersistenceError("BEGIN IMMEDIATE was not acquired")
            self._bind(connection)
        except OperationalError as exc:
            self._cleanup()
            if is_sqlite_concurrency_conflict(exc):
                raise ShoppingPersistenceConflictError(
                    "Shopping source transaction is busy; retry"
                ) from exc
            raise ShoppingPersistenceError(
                "Shopping transaction initialization failed"
            ) from exc
        except BaseException:
            self._cleanup()
            raise
        return self

    def commit(self) -> None:
        connection = self._require_connection()
        try:
            # sqlite3.autocommit=True makes DBAPI .commit() a no-op.
            # SQL COMMIT is essential; then close the SQLAlchemy logical txn.
            connection.exec_driver_sql("COMMIT")
            connection.commit()
        except (OperationalError, IntegrityError) as exc:
            self._cleanup()
            raise ShoppingPersistenceConflictError(
                "Shopping transaction commit conflicted with persisted data"
            ) from exc
        except DBAPIError as exc:
            self._cleanup()
            raise ShoppingPersistenceError("Shopping commit failed") from exc
        else:
            self._cleanup()

    def rollback(self) -> None:
        self._require_connection()
        self._cleanup()

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None:
        del exc_type, exc_value, traceback
        self._cleanup()
        return None

    def _require_connection(self) -> Connection:
        if self._connection is None:
            raise RuntimeError("Shopping UoW is inactive")
        return self._connection

    def _cleanup(self) -> None:
        connection = self._connection
        dbapi = self._dbapi
        self._connection = None
        self._dbapi = None
        self.shopping = self.plans = self.recipes = None
        self.foods = self.pantry = self.households = None
        if connection is None:
            return
        try:
            if dbapi is not None and dbapi.in_transaction:
                try:
                    connection.exec_driver_sql("ROLLBACK")
                except DBAPIError:
                    connection.invalidate()
            try:
                connection.rollback()
            except DBAPIError:
                connection.invalidate()
            if dbapi is not None:
                dbapi.autocommit = self._original_autocommit
        except BaseException:
            connection.invalidate()
            raise
        finally:
            connection.close()


class SqlAlchemyShoppingReadScope(_ShoppingRepositories):
    def __init__(self, engine: Engine) -> None:
        self._scope = SqlAlchemyReadOnlyScope(engine)

    def __enter__(self) -> Self:
        self._scope.__enter__()
        self._bind(self._scope.adapter_connection)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None:
        return self._scope.__exit__(exc_type, exc_value, traceback)
