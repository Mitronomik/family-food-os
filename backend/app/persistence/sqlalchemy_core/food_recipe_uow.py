"""Recipe Catalogue scopes over the shared SQLAlchemy transaction foundation."""

from types import TracebackType

from sqlalchemy.engine import Engine
from sqlalchemy.exc import DBAPIError, IntegrityError

from app.persistence.sqlalchemy_core.food_ingredient_repositories import (
    SqlAlchemyFoodIngredientRepository,
)
from app.persistence.sqlalchemy_core.food_recipe_repositories import (
    SqlAlchemyRecipeRepository,
    SqlAlchemyRecipeVersionRepository,
)
from app.persistence.sqlalchemy_core.uow import (
    SqlAlchemyReadOnlyScope,
    SqlAlchemyUnitOfWork,
)
from app.services.food_recipe_contracts import (
    RecipeCataloguePersistenceConflictError,
    RecipeCataloguePersistenceError,
)


class SqlAlchemyRecipeCatalogueUnitOfWork:
    def __init__(self, engine: Engine) -> None:
        self._scope = SqlAlchemyUnitOfWork(engine)
        self._recipes: SqlAlchemyRecipeRepository | None = None
        self._versions: SqlAlchemyRecipeVersionRepository | None = None
        self._food_ingredients: SqlAlchemyFoodIngredientRepository | None = None

    @property
    def recipes(self) -> SqlAlchemyRecipeRepository:
        if self._recipes is None:
            raise RuntimeError("The Recipe Catalogue Unit of Work is not active.")
        return self._recipes

    @property
    def versions(self) -> SqlAlchemyRecipeVersionRepository:
        if self._versions is None:
            raise RuntimeError("The Recipe Catalogue Unit of Work is not active.")
        return self._versions

    @property
    def food_ingredients(self) -> SqlAlchemyFoodIngredientRepository:
        if self._food_ingredients is None:
            raise RuntimeError("The Recipe Catalogue Unit of Work is not active.")
        return self._food_ingredients

    def __enter__(self) -> "SqlAlchemyRecipeCatalogueUnitOfWork":
        self._scope.__enter__()
        connection = self._scope.adapter_connection
        self._recipes = SqlAlchemyRecipeRepository(connection)
        self._versions = SqlAlchemyRecipeVersionRepository(connection)
        self._food_ingredients = SqlAlchemyFoodIngredientRepository(connection)
        return self

    def commit(self) -> None:
        try:
            self._scope.commit()
        except IntegrityError as exc:
            raise RecipeCataloguePersistenceConflictError(
                "Recipe Catalogue transaction commit conflicted with persisted state."
            ) from exc
        except DBAPIError as exc:
            raise RecipeCataloguePersistenceError(
                "Recipe Catalogue transaction commit failed at the persistence boundary."
            ) from exc
        finally:
            self._revoke()

    def rollback(self) -> None:
        try:
            self._scope.rollback()
        except DBAPIError as exc:
            raise RecipeCataloguePersistenceError(
                "Recipe Catalogue transaction rollback failed at the persistence boundary."
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
        self._recipes = None
        self._versions = None
        self._food_ingredients = None


class SqlAlchemyRecipeCatalogueReadScope:
    def __init__(self, engine: Engine) -> None:
        self._scope = SqlAlchemyReadOnlyScope(engine)
        self._recipes: SqlAlchemyRecipeRepository | None = None
        self._versions: SqlAlchemyRecipeVersionRepository | None = None
        self._food_ingredients: SqlAlchemyFoodIngredientRepository | None = None

    @property
    def recipes(self) -> SqlAlchemyRecipeRepository:
        if self._recipes is None:
            raise RuntimeError("The Recipe Catalogue read scope is not active.")
        return self._recipes

    @property
    def versions(self) -> SqlAlchemyRecipeVersionRepository:
        if self._versions is None:
            raise RuntimeError("The Recipe Catalogue read scope is not active.")
        return self._versions

    @property
    def food_ingredients(self) -> SqlAlchemyFoodIngredientRepository:
        if self._food_ingredients is None:
            raise RuntimeError("The Recipe Catalogue read scope is not active.")
        return self._food_ingredients

    def __enter__(self) -> "SqlAlchemyRecipeCatalogueReadScope":
        self._scope.__enter__()
        connection = self._scope.adapter_connection
        self._recipes = SqlAlchemyRecipeRepository(connection)
        self._versions = SqlAlchemyRecipeVersionRepository(connection)
        self._food_ingredients = SqlAlchemyFoodIngredientRepository(connection)
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
            self._recipes = None
            self._versions = None
            self._food_ingredients = None
