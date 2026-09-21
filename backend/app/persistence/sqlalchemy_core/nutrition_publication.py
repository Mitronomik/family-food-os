"""SQLAlchemy Core adapters for Step 3 reviewed transactional publication."""

from collections.abc import Mapping
from typing import Self
from uuid import UUID

from sqlalchemy import insert, select
from sqlalchemy.engine import Engine
from sqlalchemy.exc import DBAPIError, IntegrityError

from app.domain.food_composition import FoodCompositionVersion
from app.domain.food_ingredients import (
    FoodNutritionProfile,
    NutritionSourceObservation,
    validate_nutrition_profile_observations,
)
from app.domain.nutrient_vector_backfill_v1 import value_set_digest
from app.persistence.sqlalchemy_core.food_composition_repository import (
    SqlAlchemyFoodCompositionRepository,
)
from app.persistence.sqlalchemy_core.food_composition_tables import versions
from app.persistence.sqlalchemy_core.food_ingredient_repositories import (
    SqlAlchemyFoodIngredientRepository,
    SqlAlchemyFoodNutritionProfileRepository,
    SqlAlchemyIngredientAliasRepository,
)
from app.persistence.sqlalchemy_core.food_ingredient_tables import (
    food_nutrition_profile_observations_table,
    food_nutrition_profiles_table,
)
from app.persistence.sqlalchemy_core.nutrient_vector_repository import (
    SqlAlchemyNutrientRegistryRepository,
    SqlAlchemyNutrientVectorRepository,
)
from app.persistence.sqlalchemy_core.nutrient_vector_tables import (
    nutrient_values,
    vector_seals,
)
from app.persistence.sqlalchemy_core.uow import SqlAlchemyUnitOfWork
from app.services.nutrition_publication_contracts import (
    NutritionPublicationPersistenceConflictError,
    NutritionPublicationPersistenceError,
)


def _profile_row(profile: FoodNutritionProfile) -> dict[str, object]:
    return {
        "id": profile.id,
        "food_ingredient_id": profile.food_ingredient_id,
        "basis_grams": profile.basis_grams,
        "kcal": profile.kcal,
        "protein_g": profile.protein_g,
        "fat_g": profile.fat_g,
        "carbohydrates_g": profile.carbohydrates_g,
        "fiber_g": profile.fiber_g,
        "source_name": profile.source_name,
        "source_id": profile.source_id,
        "source_version": profile.source_version,
        "source_data_type": profile.source_data_type,
        "verified_at": profile.verified_at,
        "estimated": profile.estimated,
        "is_current": profile.is_current,
        "created_at": profile.created_at,
    }


def _observation_row(value: NutritionSourceObservation) -> dict[str, object]:
    return {
        "id": value.id,
        "profile_id": value.profile_id,
        "source_field": value.source_field,
        "state": value.state.value,
        "source_literal": value.source_literal,
        "method_reference": value.method_reference,
        "source_locator": value.source_locator,
        "created_at": value.created_at,
    }


class SqlAlchemyReviewedNutritionProfileRepository(
    SqlAlchemyFoodNutritionProfileRepository
):
    """Specialized immutable profile write with no historical V1 bootstrap."""

    def add_unsealed(
        self,
        profile: FoodNutritionProfile,
        observations: tuple[NutritionSourceObservation, ...],
    ) -> None:
        validated = validate_nutrition_profile_observations(profile, observations)
        try:
            self._connection.execute(
                insert(food_nutrition_profiles_table).values(**_profile_row(profile))
            )
            for observation in validated:
                self._connection.execute(
                    insert(food_nutrition_profile_observations_table).values(
                        **_observation_row(observation)
                    )
                )
        except IntegrityError as exc:
            raise NutritionPublicationPersistenceConflictError(
                "Reviewed profile or observation conflicts with persisted truth."
            ) from exc


class SqlAlchemyPublicationCompositionRepository(
    SqlAlchemyFoodCompositionRepository
):
    def find_version(
        self, food_ingredient_id: UUID, version: int
    ) -> FoodCompositionVersion | None:
        key = self._connection.execute(
            select(versions.c.id).where(
                versions.c.food_ingredient_id == food_ingredient_id,
                versions.c.version == version,
            )
        ).scalar_one_or_none()
        return None if key is None else self.get(key)

    def add_versions(self, values: tuple[FoodCompositionVersion, ...]) -> None:
        try:
            super().add_versions(values)
        except IntegrityError as exc:
            raise NutritionPublicationPersistenceConflictError(
                "Reviewed ATOMIC composition conflicts with persisted truth."
            ) from exc


class SqlAlchemyNutritionPublicationUnitOfWork(SqlAlchemyUnitOfWork):
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
    def nutrition_profiles(self) -> SqlAlchemyReviewedNutritionProfileRepository:
        return SqlAlchemyReviewedNutritionProfileRepository(self.adapter_connection)

    @property
    def nutrient_registry(self) -> SqlAlchemyNutrientRegistryRepository:
        return SqlAlchemyNutrientRegistryRepository(self.adapter_connection)

    @property
    def nutrient_vectors(self) -> SqlAlchemyNutrientVectorRepository:
        return SqlAlchemyNutrientVectorRepository(self.adapter_connection)

    @property
    def compositions(self) -> SqlAlchemyPublicationCompositionRepository:
        return SqlAlchemyPublicationCompositionRepository(self.adapter_connection)

    def publish_vector(
        self,
        profile_id: UUID,
        *,
        registry_version: str,
        values: tuple[Mapping[str, object], ...],
        value_sha256: str,
        observations_json: str,
    ) -> None:
        rows = tuple(
            {
                "profile_id": profile_id,
                "registry_version": registry_version,
                "nutrient_code": value["nutrient_code"],
                "amount": value["amount"],
                "provenance_json": value["provenance_json"],
            }
            for value in values
        )
        if value_set_digest(values) != value_sha256:
            raise NutritionPublicationPersistenceConflictError(
                "Vector digest changed between validation and persistence."
            )
        try:
            for row in rows:
                self.adapter_connection.execute(insert(nutrient_values).values(**row))
            self.adapter_connection.execute(
                insert(vector_seals).values(
                    profile_id=profile_id,
                    registry_version=registry_version,
                    value_count=len(rows),
                    value_sha256=value_sha256,
                    observations_json=observations_json,
                )
            )
        except IntegrityError as exc:
            raise NutritionPublicationPersistenceConflictError(
                "Reviewed V2 vector conflicts with persisted truth."
            ) from exc

    def commit(self) -> None:
        try:
            super().commit()
        except IntegrityError as exc:
            raise NutritionPublicationPersistenceConflictError(
                "Reviewed publication commit conflicted with persisted truth."
            ) from exc
        except DBAPIError as exc:
            raise NutritionPublicationPersistenceError(
                "Reviewed publication commit failed at the persistence boundary."
            ) from exc

    def rollback(self) -> None:
        try:
            super().rollback()
        except DBAPIError as exc:
            raise NutritionPublicationPersistenceError(
                "Reviewed publication rollback failed at the persistence boundary."
            ) from exc


def create_nutrition_publication_service(engine: Engine):
    from app.services.nutrition_publication import ReviewedNutritionPublicationService

    return ReviewedNutritionPublicationService(
        lambda: SqlAlchemyNutritionPublicationUnitOfWork(engine)
    )
