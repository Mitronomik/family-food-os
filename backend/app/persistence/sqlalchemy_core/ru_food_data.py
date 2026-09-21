"""RU operation adapters sharing the project UoW; schema remains migration 0029."""

from typing import Any, Self
from uuid import UUID

from sqlalchemy import column, insert, select, table

from app.domain.food_composition import FoodCompositionVersion
from app.domain.food_ingredients import FoodNutritionProfile
from app.domain.nutrient_vector_backfill_v1 import REGISTRY_VERSION, value_set_digest
from app.persistence.sqlalchemy_core.food_composition_repository import (
    SqlAlchemyFoodCompositionRepository,
)
from app.persistence.sqlalchemy_core.food_composition_tables import versions
from app.persistence.sqlalchemy_core.food_ingredient_repositories import (
    SqlAlchemyFoodIngredientRepository,
    SqlAlchemyFoodNutritionProfileRepository,
    SqlAlchemyIngredientAliasRepository,
)
from app.persistence.sqlalchemy_core.nutrient_vector_repository import (
    SqlAlchemyNutrientVectorRepository,
)
from app.persistence.sqlalchemy_core.nutrient_vector_tables import (
    nutrient_values,
    vector_seals,
)
from app.persistence.sqlalchemy_core.uow import SqlAlchemyUnitOfWork


def _versioned_registry_schema_available(connection) -> bool:
    migrations = table("schema_migrations", column("migration_id"))
    return (
        connection.execute(
            select(migrations.c.migration_id).where(
                migrations.c.migration_id == "0035_versioned_nutrient_registry"
            )
        ).first()
        is not None
    )


class RuCompositionRepository(SqlAlchemyFoodCompositionRepository):
    def find_version(
        self, food_id: UUID, version: int
    ) -> FoodCompositionVersion | None:
        key = self._connection.execute(
            select(versions.c.id).where(
                versions.c.food_ingredient_id == food_id,
                versions.c.version == version,
            )
        ).scalar_one_or_none()
        return None if key is None else self.get(key)


class SqlAlchemyRuFoodUnitOfWork(SqlAlchemyUnitOfWork):
    def __enter__(self) -> Self:
        super().__enter__()
        return self

    @property
    def ingredients(self) -> SqlAlchemyFoodIngredientRepository:
        return SqlAlchemyFoodIngredientRepository(self.adapter_connection)

    @property
    def aliases(self) -> SqlAlchemyIngredientAliasRepository:
        return SqlAlchemyIngredientAliasRepository(self.adapter_connection)

    @property
    def nutrition_profiles(self) -> SqlAlchemyFoodNutritionProfileRepository:
        return SqlAlchemyFoodNutritionProfileRepository(self.adapter_connection)

    @property
    def compositions(self) -> RuCompositionRepository:
        return RuCompositionRepository(self.adapter_connection)

    @property
    def nutrient_vectors(self) -> SqlAlchemyNutrientVectorRepository:
        return SqlAlchemyNutrientVectorRepository(self.adapter_connection)

    def publish_vector(
        self,
        profile: FoodNutritionProfile,
        values: list[dict[str, Any]],
        observations: str,
    ) -> None:
        """Seal last; caller has validated the hash-pinned reviewed operation."""
        if values:
            versioned = _versioned_registry_schema_available(self.adapter_connection)
            rows = []
            for value in values:
                row = dict(value, profile_id=profile.id)
                if versioned:
                    row["registry_version"] = REGISTRY_VERSION
                rows.append(row)
            self.adapter_connection.execute(insert(nutrient_values), rows)
        self.adapter_connection.execute(
            insert(vector_seals).values(
                profile_id=profile.id,
                registry_version=REGISTRY_VERSION,
                value_count=len(values),
                value_sha256=value_set_digest(values),
                observations_json=observations,
            )
        )
