"""Pantry scopes over the shared SQLAlchemy transaction foundation."""

from types import TracebackType

from sqlalchemy.engine import Engine
from sqlalchemy.exc import DBAPIError, IntegrityError, OperationalError

from app.persistence.sqlalchemy_core.food_ingredient_repositories import (
    SqlAlchemyFoodIngredientRepository,
)
from app.persistence.sqlalchemy_core.household_repositories import (
    SqlAlchemyHouseholdRepository,
)
from app.persistence.sqlalchemy_core.pantry_repositories import (
    SqlAlchemyPantryItemRepository,
    SqlAlchemyPantryMovementRepository,
)
from app.persistence.sqlalchemy_core.uow import (
    SqlAlchemyReadOnlyScope,
    SqlAlchemyUnitOfWork,
)
from app.services.pantry_contracts import (
    PantryPersistenceConflictError,
    PantryPersistenceError,
)


class SqlAlchemyPantryUnitOfWork:
    def __init__(self, engine: Engine) -> None:
        self._scope = SqlAlchemyUnitOfWork(engine)
        self._items: SqlAlchemyPantryItemRepository | None = None
        self._movements: SqlAlchemyPantryMovementRepository | None = None
        self._food_ingredients: SqlAlchemyFoodIngredientRepository | None = None
        self._households: SqlAlchemyHouseholdRepository | None = None

    @property
    def items(self) -> SqlAlchemyPantryItemRepository:
        if self._items is None:
            raise RuntimeError("The Pantry Unit of Work is not active.")
        return self._items

    @property
    def movements(self) -> SqlAlchemyPantryMovementRepository:
        if self._movements is None:
            raise RuntimeError("The Pantry Unit of Work is not active.")
        return self._movements

    @property
    def households(self) -> SqlAlchemyHouseholdRepository:
        if self._households is None:
            raise RuntimeError("The Pantry scope is not active.")
        return self._households

    @property
    def food_ingredients(self) -> SqlAlchemyFoodIngredientRepository:
        if self._food_ingredients is None:
            raise RuntimeError("The Pantry Unit of Work is not active.")
        return self._food_ingredients

    def __enter__(self) -> "SqlAlchemyPantryUnitOfWork":
        self._scope.__enter__()
        connection = self._scope.adapter_connection
        self._items = SqlAlchemyPantryItemRepository(connection)
        self._movements = SqlAlchemyPantryMovementRepository(connection)
        self._food_ingredients = SqlAlchemyFoodIngredientRepository(connection)
        self._households = SqlAlchemyHouseholdRepository(connection)
        return self

    def commit(self) -> None:
        try:
            self._scope.commit()
        except (IntegrityError, OperationalError) as exc:
            raise PantryPersistenceConflictError(
                "Pantry transaction commit conflicted with persisted state."
            ) from exc
        except DBAPIError as exc:
            raise PantryPersistenceError(
                "Pantry transaction commit failed at the persistence boundary."
            ) from exc
        finally:
            self._revoke()

    def rollback(self) -> None:
        try:
            self._scope.rollback()
        except DBAPIError as exc:
            raise PantryPersistenceError(
                "Pantry transaction rollback failed at the persistence boundary."
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
        self._items = None
        self._movements = None
        self._food_ingredients = None
        self._households = None


class SqlAlchemyPantryReadScope:
    def __init__(self, engine: Engine) -> None:
        self._scope = SqlAlchemyReadOnlyScope(engine)
        self._items: SqlAlchemyPantryItemRepository | None = None
        self._movements: SqlAlchemyPantryMovementRepository | None = None
        self._food_ingredients: SqlAlchemyFoodIngredientRepository | None = None
        self._households: SqlAlchemyHouseholdRepository | None = None

    @property
    def items(self) -> SqlAlchemyPantryItemRepository:
        if self._items is None:
            raise RuntimeError("The Pantry read scope is not active.")
        return self._items

    @property
    def movements(self) -> SqlAlchemyPantryMovementRepository:
        if self._movements is None:
            raise RuntimeError("The Pantry read scope is not active.")
        return self._movements

    @property
    def households(self) -> SqlAlchemyHouseholdRepository:
        if self._households is None:
            raise RuntimeError("The Pantry scope is not active.")
        return self._households

    @property
    def food_ingredients(self) -> SqlAlchemyFoodIngredientRepository:
        if self._food_ingredients is None:
            raise RuntimeError("The Pantry read scope is not active.")
        return self._food_ingredients

    def __enter__(self) -> "SqlAlchemyPantryReadScope":
        self._scope.__enter__()
        connection = self._scope.adapter_connection
        self._items = SqlAlchemyPantryItemRepository(connection)
        self._movements = SqlAlchemyPantryMovementRepository(connection)
        self._food_ingredients = SqlAlchemyFoodIngredientRepository(connection)
        self._households = SqlAlchemyHouseholdRepository(connection)
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
            self._items = None
            self._movements = None
            self._food_ingredients = None
            self._households = None
