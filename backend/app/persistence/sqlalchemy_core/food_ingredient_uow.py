"""Food Catalogue composition over the generic SQLAlchemy transaction scopes."""

from types import TracebackType

from sqlalchemy.engine import Engine
from sqlalchemy.exc import DBAPIError, IntegrityError

from app.persistence.sqlalchemy_core.food_ingredient_repositories import (
    SqlAlchemyFoodIngredientRepository,
    SqlAlchemyFoodNutritionProfileRepository,
    SqlAlchemyIngredientAliasRepository,
)
from app.persistence.sqlalchemy_core.uow import (
    SqlAlchemyReadOnlyScope,
    SqlAlchemyUnitOfWork,
)
from app.services.food_ingredient_contracts import (
    FoodCataloguePersistenceConflictError,
    FoodCataloguePersistenceError,
)


class SqlAlchemyFoodCatalogueUnitOfWork:
    def __init__(self, engine: Engine) -> None:
        self._scope = SqlAlchemyUnitOfWork(engine)
        self._ingredients: SqlAlchemyFoodIngredientRepository | None = None
        self._aliases: SqlAlchemyIngredientAliasRepository | None = None
        self._nutrition_profiles: SqlAlchemyFoodNutritionProfileRepository | None = None

    @property
    def ingredients(self) -> SqlAlchemyFoodIngredientRepository:
        if self._ingredients is None:
            raise RuntimeError("The Food Catalogue Unit of Work is not active.")
        return self._ingredients

    @property
    def aliases(self) -> SqlAlchemyIngredientAliasRepository:
        if self._aliases is None:
            raise RuntimeError("The Food Catalogue Unit of Work is not active.")
        return self._aliases

    @property
    def nutrition_profiles(self) -> SqlAlchemyFoodNutritionProfileRepository:
        if self._nutrition_profiles is None:
            raise RuntimeError("The Food Catalogue Unit of Work is not active.")
        return self._nutrition_profiles

    def __enter__(self) -> "SqlAlchemyFoodCatalogueUnitOfWork":
        self._scope.__enter__()
        connection = self._scope.adapter_connection
        self._ingredients = SqlAlchemyFoodIngredientRepository(connection)
        self._aliases = SqlAlchemyIngredientAliasRepository(connection)
        self._nutrition_profiles = SqlAlchemyFoodNutritionProfileRepository(connection)
        return self

    def commit(self) -> None:
        try:
            self._scope.commit()
        except IntegrityError as exc:
            raise FoodCataloguePersistenceConflictError(
                "Food Catalogue transaction commit conflicted with persisted state."
            ) from exc
        except DBAPIError as exc:
            raise FoodCataloguePersistenceError(
                "Food Catalogue transaction commit failed at the persistence boundary."
            ) from exc
        finally:
            self._revoke_repositories()

    def rollback(self) -> None:
        try:
            self._scope.rollback()
        except DBAPIError as exc:
            raise FoodCataloguePersistenceError(
                "Food Catalogue transaction rollback failed at the persistence boundary."
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
        self._ingredients = None
        self._aliases = None
        self._nutrition_profiles = None


class SqlAlchemyFoodCatalogueReadScope:
    def __init__(self, engine: Engine) -> None:
        self._scope = SqlAlchemyReadOnlyScope(engine)
        self._ingredients: SqlAlchemyFoodIngredientRepository | None = None
        self._aliases: SqlAlchemyIngredientAliasRepository | None = None
        self._nutrition_profiles: SqlAlchemyFoodNutritionProfileRepository | None = None

    @property
    def ingredients(self) -> SqlAlchemyFoodIngredientRepository:
        if self._ingredients is None:
            raise RuntimeError("The Food Catalogue read scope is not active.")
        return self._ingredients

    @property
    def aliases(self) -> SqlAlchemyIngredientAliasRepository:
        if self._aliases is None:
            raise RuntimeError("The Food Catalogue read scope is not active.")
        return self._aliases

    @property
    def nutrition_profiles(self) -> SqlAlchemyFoodNutritionProfileRepository:
        if self._nutrition_profiles is None:
            raise RuntimeError("The Food Catalogue read scope is not active.")
        return self._nutrition_profiles

    def __enter__(self) -> "SqlAlchemyFoodCatalogueReadScope":
        self._scope.__enter__()
        connection = self._scope.adapter_connection
        self._ingredients = SqlAlchemyFoodIngredientRepository(connection)
        self._aliases = SqlAlchemyIngredientAliasRepository(connection)
        self._nutrition_profiles = SqlAlchemyFoodNutritionProfileRepository(connection)
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
            self._ingredients = None
            self._aliases = None
            self._nutrition_profiles = None
