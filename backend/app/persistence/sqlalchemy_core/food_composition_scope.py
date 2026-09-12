"""Composition repositories share existing project transactions and vector reader."""

from typing import Self

from app.persistence.sqlalchemy_core.food_composition_repository import (
    SqlAlchemyFoodCompositionRepository,
)
from app.persistence.sqlalchemy_core.nutrient_vector_repository import (
    SqlAlchemyNutrientVectorRepository,
)
from app.persistence.sqlalchemy_core.uow import (
    SqlAlchemyReadOnlyScope,
    SqlAlchemyUnitOfWork,
)


class SqlAlchemyCompositionReadScope(SqlAlchemyReadOnlyScope):
    def __enter__(self) -> Self:
        super().__enter__()
        return self

    @property
    def compositions(self) -> SqlAlchemyFoodCompositionRepository:
        return SqlAlchemyFoodCompositionRepository(self.adapter_connection)

    @property
    def nutrient_vectors(self) -> SqlAlchemyNutrientVectorRepository:
        return SqlAlchemyNutrientVectorRepository(self.adapter_connection)


class SqlAlchemyCompositionUnitOfWork(SqlAlchemyUnitOfWork):
    def __enter__(self) -> Self:
        super().__enter__()
        return self

    @property
    def compositions(self) -> SqlAlchemyFoodCompositionRepository:
        return SqlAlchemyFoodCompositionRepository(self.adapter_connection)

    @property
    def nutrient_vectors(self) -> SqlAlchemyNutrientVectorRepository:
        return SqlAlchemyNutrientVectorRepository(self.adapter_connection)
