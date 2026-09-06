"""SQLAlchemy Core repositories for the verified Recipe Catalogue."""

from collections.abc import Mapping
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import insert, select, update
from sqlalchemy.engine import Connection
from sqlalchemy.exc import DBAPIError, IntegrityError

from app.domain.food_recipes import (
    Recipe,
    RecipeEquipment,
    RecipeIngredient,
    RecipeStep,
    RecipeVersion,
    RecipeVersionDetail,
    VerificationStatus,
)
from app.persistence.sqlalchemy_core.food_recipe_tables import (
    food_recipe_equipment_table,
    food_recipe_ingredients_table,
    food_recipe_steps_table,
    food_recipe_versions_table,
    food_recipes_table,
)
from app.services.food_recipe_contracts import (
    RecipeCataloguePersistenceConflictError,
    RecipeCataloguePersistenceError,
)


class SqlAlchemyRecipeRepository:
    def __init__(self, connection: Connection) -> None:
        self._connection = connection

    def add(self, recipe: Recipe) -> None:
        try:
            self._connection.execute(
                insert(food_recipes_table).values(**_recipe_values(recipe))
            )
        except IntegrityError as exc:
            raise RecipeCataloguePersistenceConflictError(
                "Recipe identity, canonical code, or normalized name conflicts."
            ) from exc

    def get(self, recipe_id: UUID) -> Recipe | None:
        row = (
            self._connection.execute(
                select(food_recipes_table).where(food_recipes_table.c.id == recipe_id)
            )
            .mappings()
            .one_or_none()
        )
        return None if row is None else _recipe_from_row(row)

    def get_by_code(self, canonical_code: str) -> Recipe | None:
        row = (
            self._connection.execute(
                select(food_recipes_table).where(
                    food_recipes_table.c.canonical_code == canonical_code
                )
            )
            .mappings()
            .one_or_none()
        )
        return None if row is None else _recipe_from_row(row)

    def get_by_name_key(self, canonical_name_key: str) -> Recipe | None:
        row = (
            self._connection.execute(
                select(food_recipes_table).where(
                    food_recipes_table.c.canonical_name_key == canonical_name_key
                )
            )
            .mappings()
            .one_or_none()
        )
        return None if row is None else _recipe_from_row(row)

    def list_active(self, *, limit: int) -> list[Recipe]:
        rows = self._connection.execute(
            select(food_recipes_table)
            .where(food_recipes_table.c.is_active.is_(True))
            .order_by(
                food_recipes_table.c.canonical_name_key,
                food_recipes_table.c.canonical_code,
                food_recipes_table.c.id,
            )
            .limit(limit)
        ).mappings()
        return [_recipe_from_row(row) for row in rows]

    def set_active(
        self, recipe_id: UUID, *, active: bool, updated_at: datetime
    ) -> None:
        result = self._connection.execute(
            update(food_recipes_table)
            .where(food_recipes_table.c.id == recipe_id)
            .values(is_active=active, updated_at=updated_at)
        )
        if result.rowcount != 1:
            raise RecipeCataloguePersistenceError(
                "Recipe activation update did not affect exactly one row."
            )


class SqlAlchemyRecipeVersionRepository:
    def __init__(self, connection: Connection) -> None:
        self._connection = connection

    def add_detail(self, detail: RecipeVersionDetail) -> None:
        previous_id = detail.version.created_from_version_id
        if previous_id is not None:
            previous_recipe_id = self._connection.scalar(
                select(food_recipe_versions_table.c.recipe_id).where(
                    food_recipe_versions_table.c.id == previous_id
                )
            )
            if previous_recipe_id != detail.recipe.id:
                raise RecipeCataloguePersistenceConflictError(
                    "created_from_version_id must reference the same Recipe."
                )
        try:
            self._connection.execute(
                insert(food_recipe_versions_table).values(
                    **_version_values(detail.version)
                )
            )
            self._connection.execute(
                insert(food_recipe_ingredients_table),
                [_ingredient_values(value) for value in detail.ingredients],
            )
            self._connection.execute(
                insert(food_recipe_steps_table),
                [_step_values(value) for value in detail.steps],
            )
            if detail.equipment:
                self._connection.execute(
                    insert(food_recipe_equipment_table),
                    [_equipment_values(value) for value in detail.equipment],
                )
        except IntegrityError as exc:
            raise RecipeCataloguePersistenceConflictError(
                "RecipeVersion identity, provenance, position, or reference conflicts."
            ) from exc
        except DBAPIError as exc:
            raise RecipeCataloguePersistenceError(
                "RecipeVersion aggregate persistence failed."
            ) from exc

    def get(self, version_id: UUID) -> RecipeVersion | None:
        row = (
            self._connection.execute(
                select(food_recipe_versions_table).where(
                    food_recipe_versions_table.c.id == version_id
                )
            )
            .mappings()
            .one_or_none()
        )
        return None if row is None else _version_from_row(row)

    def get_detail(self, version_id: UUID) -> RecipeVersionDetail | None:
        version = self.get(version_id)
        if version is None:
            return None
        recipe_row = (
            self._connection.execute(
                select(food_recipes_table).where(
                    food_recipes_table.c.id == version.recipe_id
                )
            )
            .mappings()
            .one()
        )
        ingredient_rows = self._connection.execute(
            select(food_recipe_ingredients_table)
            .where(food_recipe_ingredients_table.c.recipe_version_id == version_id)
            .order_by(food_recipe_ingredients_table.c.position)
        ).mappings()
        step_rows = self._connection.execute(
            select(food_recipe_steps_table)
            .where(food_recipe_steps_table.c.recipe_version_id == version_id)
            .order_by(food_recipe_steps_table.c.position)
        ).mappings()
        equipment_rows = self._connection.execute(
            select(food_recipe_equipment_table)
            .where(food_recipe_equipment_table.c.recipe_version_id == version_id)
            .order_by(food_recipe_equipment_table.c.position)
        ).mappings()
        return RecipeVersionDetail(
            recipe=_recipe_from_row(recipe_row),
            version=version,
            ingredients=tuple(_ingredient_from_row(row) for row in ingredient_rows),
            steps=tuple(_step_from_row(row) for row in step_rows),
            equipment=tuple(_equipment_from_row(row) for row in equipment_rows),
        )

    def list_for_recipe(self, recipe_id: UUID) -> list[RecipeVersion]:
        rows = self._connection.execute(
            select(food_recipe_versions_table)
            .where(food_recipe_versions_table.c.recipe_id == recipe_id)
            .order_by(food_recipe_versions_table.c.version_number)
        ).mappings()
        return [_version_from_row(row) for row in rows]

    def get_current_verified(self, recipe_id: UUID) -> RecipeVersionDetail | None:
        version_id = self._connection.scalar(
            select(food_recipe_versions_table.c.id)
            .where(
                food_recipe_versions_table.c.recipe_id == recipe_id,
                food_recipe_versions_table.c.verification_status
                == VerificationStatus.SOURCE_VERIFIED.value,
            )
            .order_by(food_recipe_versions_table.c.version_number.desc())
            .limit(1)
        )
        return None if version_id is None else self.get_detail(version_id)

    def get_by_provenance(
        self,
        recipe_id: UUID,
        source_name: str,
        source_recipe_id: str,
        source_version: str,
    ) -> RecipeVersionDetail | None:
        version_id = self._connection.scalar(
            select(food_recipe_versions_table.c.id).where(
                food_recipe_versions_table.c.recipe_id == recipe_id,
                food_recipe_versions_table.c.source_name == source_name,
                food_recipe_versions_table.c.source_recipe_id == source_recipe_id,
                food_recipe_versions_table.c.source_version == source_version,
            )
        )
        return None if version_id is None else self.get_detail(version_id)


def _recipe_values(value: Recipe) -> dict[str, object]:
    return {
        "id": value.id,
        "canonical_code": value.canonical_code,
        "canonical_name": value.canonical_name,
        "canonical_name_key": value.canonical_name_key,
        "is_active": value.is_active,
        "created_at": value.created_at,
        "updated_at": value.updated_at,
    }


def _version_values(value: RecipeVersion) -> dict[str, object]:
    return {
        "id": value.id,
        "recipe_id": value.recipe_id,
        "version_number": value.version_number,
        "base_servings": value.base_servings,
        "meal_type_code": value.meal_type_code.value,
        "prep_time_minutes": value.prep_time_minutes,
        "cook_time_minutes": value.cook_time_minutes,
        "total_time_minutes": value.total_time_minutes,
        "difficulty_code": value.difficulty_code,
        "batch_friendly": value.batch_friendly,
        "freezable": value.freezable,
        "storage_days_fridge": value.storage_days_fridge,
        "storage_days_freezer": value.storage_days_freezer,
        "verification_status": value.verification_status.value,
        "verified_at": value.verified_at,
        "source_name": value.source_name,
        "source_recipe_id": value.source_recipe_id,
        "source_url": value.source_url,
        "source_version": value.source_version,
        "source_retrieved_at": value.source_retrieved_at,
        "source_document_sha256": value.source_document_sha256,
        "source_original_servings": value.source_original_servings,
        "rights_review_status": value.rights_review_status.value,
        "rights_basis": value.rights_basis,
        "created_from_version_id": value.created_from_version_id,
        "change_note": value.change_note,
        "created_at": value.created_at,
    }


def _ingredient_values(value: RecipeIngredient) -> dict[str, object]:
    return {
        "id": value.id,
        "recipe_version_id": value.recipe_version_id,
        "food_ingredient_id": value.food_ingredient_id,
        "position": value.position,
        "quantity": value.quantity,
        "unit": value.unit.value,
        "source_amount_text": value.source_amount_text,
        "normalization_note": value.normalization_note,
        "prep_note": value.prep_note,
        "optional": value.optional,
        "created_at": value.created_at,
    }


def _step_values(value: RecipeStep) -> dict[str, object]:
    return {
        "id": value.id,
        "recipe_version_id": value.recipe_version_id,
        "position": value.position,
        "instruction": value.instruction,
        "stage_code": value.stage_code,
        "created_at": value.created_at,
    }


def _equipment_values(value: RecipeEquipment) -> dict[str, object]:
    return {
        "recipe_version_id": value.recipe_version_id,
        "position": value.position,
        "equipment_code": value.equipment_code,
    }


def _recipe_from_row(row: Mapping[str, Any]) -> Recipe:
    return Recipe(
        id=row["id"],
        canonical_code=row["canonical_code"],
        canonical_name=row["canonical_name"],
        canonical_name_key=row["canonical_name_key"],
        is_active=row["is_active"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _version_from_row(row: Mapping[str, Any]) -> RecipeVersion:
    return RecipeVersion(
        id=row["id"],
        recipe_id=row["recipe_id"],
        version_number=row["version_number"],
        base_servings=row["base_servings"],
        meal_type_code=row["meal_type_code"],
        prep_time_minutes=row["prep_time_minutes"],
        cook_time_minutes=row["cook_time_minutes"],
        total_time_minutes=row["total_time_minutes"],
        difficulty_code=row["difficulty_code"],
        batch_friendly=row["batch_friendly"],
        freezable=row["freezable"],
        storage_days_fridge=row["storage_days_fridge"],
        storage_days_freezer=row["storage_days_freezer"],
        verification_status=row["verification_status"],
        verified_at=row["verified_at"],
        source_name=row["source_name"],
        source_recipe_id=row["source_recipe_id"],
        source_url=row["source_url"],
        source_version=row["source_version"],
        source_retrieved_at=row["source_retrieved_at"],
        source_document_sha256=row["source_document_sha256"],
        source_original_servings=row["source_original_servings"],
        rights_review_status=row["rights_review_status"],
        rights_basis=row["rights_basis"],
        created_from_version_id=row["created_from_version_id"],
        change_note=row["change_note"],
        created_at=row["created_at"],
    )


def _ingredient_from_row(row: Mapping[str, Any]) -> RecipeIngredient:
    return RecipeIngredient(
        id=row["id"],
        recipe_version_id=row["recipe_version_id"],
        food_ingredient_id=row["food_ingredient_id"],
        position=row["position"],
        quantity=row["quantity"],
        unit=row["unit"],
        source_amount_text=row["source_amount_text"],
        normalization_note=row["normalization_note"],
        prep_note=row["prep_note"],
        optional=row["optional"],
        created_at=row["created_at"],
    )


def _step_from_row(row: Mapping[str, Any]) -> RecipeStep:
    return RecipeStep(
        id=row["id"],
        recipe_version_id=row["recipe_version_id"],
        position=row["position"],
        instruction=row["instruction"],
        stage_code=row["stage_code"],
        created_at=row["created_at"],
    )


def _equipment_from_row(row: Mapping[str, Any]) -> RecipeEquipment:
    return RecipeEquipment(
        recipe_version_id=row["recipe_version_id"],
        position=row["position"],
        equipment_code=row["equipment_code"],
    )
