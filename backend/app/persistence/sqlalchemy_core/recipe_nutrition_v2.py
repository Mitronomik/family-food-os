"""SQLAlchemy Core Step 10-A Recipe Nutrition V2 adapters."""

from collections.abc import Callable
from types import TracebackType
from typing import Self
from uuid import UUID

from sqlalchemy import insert, select
from sqlalchemy.engine import Engine
from sqlalchemy.exc import DBAPIError, IntegrityError

from app.domain.recipe_nutrition_v2 import RecipeIngredientCompositionBinding
from app.persistence.sqlalchemy_core.food_composition_repository import (
    SqlAlchemyFoodCompositionRepository,
)
from app.persistence.sqlalchemy_core.food_ingredient_repositories import (
    SqlAlchemyFoodIngredientRepository,
)
from app.persistence.sqlalchemy_core.food_recipe_repositories import (
    SqlAlchemyRecipeRepository,
    SqlAlchemyRecipeVersionRepository,
)
from app.persistence.sqlalchemy_core.nutrient_vector_repository import (
    SqlAlchemyNutrientRegistryRepository,
    SqlAlchemyNutrientVectorRepository,
)
from app.persistence.sqlalchemy_core.recipe_nutrition_v2_tables import (
    recipe_ingredient_composition_bindings_table,
)
from app.persistence.sqlalchemy_core.uow import (
    SqlAlchemyReadOnlyScope,
    SqlAlchemyUnitOfWork,
)
from app.services.recipe_nutrition_v2_contracts import (
    RecipeNutritionV2PersistenceConflictError,
    RecipeNutritionV2PersistenceError,
)


class SqlAlchemyRecipeIngredientCompositionBindingRepository:
    def __init__(self, connection) -> None:
        self._connection = connection

    def get(
        self, recipe_ingredient_id: UUID
    ) -> RecipeIngredientCompositionBinding | None:
        row = (
            self._connection.execute(
                select(recipe_ingredient_composition_bindings_table).where(
                    recipe_ingredient_composition_bindings_table.c.recipe_ingredient_id
                    == recipe_ingredient_id
                )
            )
            .mappings()
            .one_or_none()
        )
        if row is None:
            return None
        return RecipeIngredientCompositionBinding(
            recipe_ingredient_id=row["recipe_ingredient_id"],
            composition_version_id=row["composition_version_id"],
            registry_version=row["registry_version"],
            nutrient_set_version=row["nutrient_set_version"],
            composition_calculation_version=row["composition_calculation_version"],
            recipe_calculation_version=row["recipe_calculation_version"],
            created_at=row["created_at"],
        )

    def add(self, binding: RecipeIngredientCompositionBinding) -> None:
        try:
            self._connection.execute(
                insert(recipe_ingredient_composition_bindings_table).values(
                    recipe_ingredient_id=binding.recipe_ingredient_id,
                    composition_version_id=binding.composition_version_id,
                    registry_version=binding.registry_version,
                    nutrient_set_version=binding.nutrient_set_version,
                    composition_calculation_version=binding.composition_calculation_version,
                    recipe_calculation_version=binding.recipe_calculation_version,
                    created_at=binding.created_at,
                )
            )
        except IntegrityError as exc:
            raise RecipeNutritionV2PersistenceConflictError(
                "Recipe Nutrition binding conflict."
            ) from exc
        except DBAPIError as exc:
            raise RecipeNutritionV2PersistenceError(
                "Recipe Nutrition binding persistence failed."
            ) from exc


class _Repositories:
    @property
    def recipes(self):
        return SqlAlchemyRecipeRepository(self.adapter_connection)

    @property
    def versions(self):
        return SqlAlchemyRecipeVersionRepository(self.adapter_connection)

    @property
    def food_ingredients(self):
        return SqlAlchemyFoodIngredientRepository(self.adapter_connection)

    @property
    def compositions(self):
        return SqlAlchemyFoodCompositionRepository(self.adapter_connection)

    @property
    def nutrient_vectors(self):
        return SqlAlchemyNutrientVectorRepository(self.adapter_connection)

    @property
    def nutrient_registry(self):
        return SqlAlchemyNutrientRegistryRepository(self.adapter_connection)

    @property
    def bindings(self):
        return SqlAlchemyRecipeIngredientCompositionBindingRepository(
            self.adapter_connection
        )


class SqlAlchemyRecipeNutritionV2ReadScope(_Repositories, SqlAlchemyReadOnlyScope):
    def __enter__(self) -> Self:
        super().__enter__()
        return self


class SqlAlchemyRecipeNutritionV2UnitOfWork(_Repositories, SqlAlchemyUnitOfWork):
    def __enter__(self) -> Self:
        super().__enter__()
        return self

    def commit(self) -> None:
        try:
            super().commit()
        except IntegrityError as exc:
            raise RecipeNutritionV2PersistenceConflictError(
                "Recipe Nutrition binding commit conflict."
            ) from exc
        except DBAPIError as exc:
            raise RecipeNutritionV2PersistenceError(
                "Recipe Nutrition binding commit failed."
            ) from exc

    def rollback(self) -> None:
        try:
            super().rollback()
        except DBAPIError as exc:
            raise RecipeNutritionV2PersistenceError(
                "Recipe Nutrition binding rollback failed."
            ) from exc


def create_recipe_nutrition_v2_service(engine: Engine, *, clock=None):
    from app.persistence.sqlalchemy_core.nutrition_composition import (
        create_nutrition_service,
    )
    from app.services.recipe_nutrition_v2 import RecipeNutritionV2Service

    legacy = create_nutrition_service(engine)
    return RecipeNutritionV2Service(
        lambda: SqlAlchemyRecipeNutritionV2ReadScope(engine),
        lambda: SqlAlchemyRecipeNutritionV2UnitOfWork(engine),
        legacy_recipe_nutrition=legacy.recipe_version,
        clock=clock,
    )
