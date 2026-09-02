"""Focused SQLAlchemy Core repositories for the platform Food Catalogue."""

from collections.abc import Mapping, Sequence
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import case, exists, func, insert, literal, or_, select, update
from sqlalchemy.engine import Connection
from sqlalchemy.exc import IntegrityError

from app.domain.food_ingredients import (
    FoodIngredient,
    FoodNutritionProfile,
    IngredientAlias,
)
from app.persistence.sqlalchemy_core.food_ingredient_tables import (
    food_ingredient_aliases_table,
    food_ingredient_allergens_table,
    food_ingredients_table,
    food_nutrition_profiles_table,
)
from app.services.food_ingredient_contracts import (
    FoodCataloguePersistenceConflictError,
    FoodCataloguePersistenceError,
)


class SqlAlchemyFoodIngredientRepository:
    def __init__(self, connection: Connection) -> None:
        self._connection = connection

    def add(self, ingredient: FoodIngredient) -> None:
        try:
            self._connection.execute(
                insert(food_ingredients_table).values(**_ingredient_values(ingredient))
            )
            if ingredient.allergen_codes:
                self._connection.execute(
                    insert(food_ingredient_allergens_table),
                    [
                        {
                            "food_ingredient_id": ingredient.id,
                            "allergen_code": code,
                            "created_at": ingredient.created_at,
                        }
                        for code in ingredient.allergen_codes
                    ],
                )
        except IntegrityError as exc:
            raise FoodCataloguePersistenceConflictError(
                "FoodIngredient identity, code, normalized name, or allergen metadata conflicts."
            ) from exc

    def get(self, ingredient_id: UUID) -> FoodIngredient | None:
        row = (
            self._connection.execute(
                select(food_ingredients_table).where(
                    food_ingredients_table.c.id == ingredient_id
                )
            )
            .mappings()
            .one_or_none()
        )
        return self._one_with_allergens(row)

    def get_by_code(self, canonical_code: str) -> FoodIngredient | None:
        row = (
            self._connection.execute(
                select(food_ingredients_table).where(
                    food_ingredients_table.c.canonical_code == canonical_code
                )
            )
            .mappings()
            .one_or_none()
        )
        return self._one_with_allergens(row)

    def get_by_name_key(self, canonical_name_key: str) -> FoodIngredient | None:
        row = (
            self._connection.execute(
                select(food_ingredients_table).where(
                    food_ingredients_table.c.canonical_name_key == canonical_name_key
                )
            )
            .mappings()
            .one_or_none()
        )
        return self._one_with_allergens(row)

    def list_active(self, *, limit: int) -> list[FoodIngredient]:
        rows = list(
            self._connection.execute(
                select(food_ingredients_table)
                .where(food_ingredients_table.c.is_active.is_(True))
                .order_by(
                    food_ingredients_table.c.canonical_name_key,
                    food_ingredients_table.c.canonical_code,
                    food_ingredients_table.c.id,
                )
                .limit(limit)
            ).mappings()
        )
        return self._many_with_allergens(rows)

    def search_active(self, search_key: str, *, limit: int) -> list[FoodIngredient]:
        escaped = _escape_like(search_key)
        prefix_pattern = f"{escaped}%"
        contains_pattern = f"%{escaped}%"
        alias_exact = exists(
            select(literal(1)).where(
                food_ingredient_aliases_table.c.food_ingredient_id
                == food_ingredients_table.c.id,
                food_ingredient_aliases_table.c.alias_key == search_key,
            )
        )
        alias_prefix = exists(
            select(literal(1)).where(
                food_ingredient_aliases_table.c.food_ingredient_id
                == food_ingredients_table.c.id,
                food_ingredient_aliases_table.c.alias_key.like(
                    prefix_pattern, escape="\\"
                ),
            )
        )
        alias_contains = exists(
            select(literal(1)).where(
                food_ingredient_aliases_table.c.food_ingredient_id
                == food_ingredients_table.c.id,
                food_ingredient_aliases_table.c.alias_key.like(
                    contains_pattern, escape="\\"
                ),
            )
        )
        code_exact = func.lower(food_ingredients_table.c.canonical_code) == search_key
        canonical_exact = food_ingredients_table.c.canonical_name_key == search_key
        canonical_prefix = food_ingredients_table.c.canonical_name_key.like(
            prefix_pattern, escape="\\"
        )
        canonical_contains = food_ingredients_table.c.canonical_name_key.like(
            contains_pattern, escape="\\"
        )
        rank = case(
            (code_exact, 0),
            (or_(canonical_exact, alias_exact), 1),
            (or_(canonical_prefix, alias_prefix), 2),
            else_=3,
        )
        rows = list(
            self._connection.execute(
                select(food_ingredients_table)
                .where(
                    food_ingredients_table.c.is_active.is_(True),
                    or_(code_exact, canonical_contains, alias_contains),
                )
                .order_by(
                    rank,
                    food_ingredients_table.c.canonical_name_key,
                    food_ingredients_table.c.canonical_code,
                    food_ingredients_table.c.id,
                )
                .limit(limit)
            ).mappings()
        )
        return self._many_with_allergens(rows)

    def set_active(
        self, ingredient_id: UUID, *, active: bool, updated_at: datetime
    ) -> None:
        result = self._connection.execute(
            update(food_ingredients_table)
            .where(food_ingredients_table.c.id == ingredient_id)
            .values(is_active=active, updated_at=updated_at)
        )
        if result.rowcount != 1:
            raise FoodCataloguePersistenceError(
                "FoodIngredient activation update did not affect exactly one row."
            )

    def _one_with_allergens(
        self, row: Mapping[str, Any] | None
    ) -> FoodIngredient | None:
        if row is None:
            return None
        codes = self._allergen_map([row["id"]]).get(row["id"], ())
        return _ingredient_from_row(row, codes)

    def _many_with_allergens(
        self, rows: Sequence[Mapping[str, Any]]
    ) -> list[FoodIngredient]:
        allergen_map = self._allergen_map([row["id"] for row in rows])
        return [
            _ingredient_from_row(row, allergen_map.get(row["id"], ())) for row in rows
        ]

    def _allergen_map(self, ids: Sequence[UUID]) -> dict[UUID, tuple[str, ...]]:
        if not ids:
            return {}
        rows = self._connection.execute(
            select(
                food_ingredient_allergens_table.c.food_ingredient_id,
                food_ingredient_allergens_table.c.allergen_code,
            )
            .where(food_ingredient_allergens_table.c.food_ingredient_id.in_(ids))
            .order_by(
                food_ingredient_allergens_table.c.food_ingredient_id,
                food_ingredient_allergens_table.c.allergen_code,
            )
        )
        result: dict[UUID, list[str]] = {}
        for row in rows:
            result.setdefault(row.food_ingredient_id, []).append(row.allergen_code)
        return {key: tuple(values) for key, values in result.items()}


class SqlAlchemyIngredientAliasRepository:
    def __init__(self, connection: Connection) -> None:
        self._connection = connection

    def add(self, alias: IngredientAlias) -> None:
        try:
            self._connection.execute(
                insert(food_ingredient_aliases_table).values(**_alias_values(alias))
            )
        except IntegrityError as exc:
            raise FoodCataloguePersistenceConflictError(
                "Ingredient alias identity, normalized key, or FoodIngredient link conflicts."
            ) from exc

    def get_by_key(self, alias_key: str) -> IngredientAlias | None:
        row = (
            self._connection.execute(
                select(food_ingredient_aliases_table).where(
                    food_ingredient_aliases_table.c.alias_key == alias_key
                )
            )
            .mappings()
            .one_or_none()
        )
        return None if row is None else _alias_from_row(row)

    def list_for_ingredient(self, ingredient_id: UUID) -> list[IngredientAlias]:
        rows = self._connection.execute(
            select(food_ingredient_aliases_table)
            .where(food_ingredient_aliases_table.c.food_ingredient_id == ingredient_id)
            .order_by(
                food_ingredient_aliases_table.c.alias_key,
                food_ingredient_aliases_table.c.id,
            )
        ).mappings()
        return [_alias_from_row(row) for row in rows]


class SqlAlchemyFoodNutritionProfileRepository:
    def __init__(self, connection: Connection) -> None:
        self._connection = connection

    def add(self, profile: FoodNutritionProfile) -> None:
        try:
            self._connection.execute(
                insert(food_nutrition_profiles_table).values(
                    **_nutrition_values(profile)
                )
            )
        except IntegrityError as exc:
            raise FoodCataloguePersistenceConflictError(
                "Nutrition provenance or current-profile state conflicts."
            ) from exc

    def get_by_provenance(
        self,
        food_ingredient_id: UUID,
        source_name: str,
        source_id: str,
        source_version: str,
    ) -> FoodNutritionProfile | None:
        row = (
            self._connection.execute(
                select(food_nutrition_profiles_table).where(
                    food_nutrition_profiles_table.c.food_ingredient_id
                    == food_ingredient_id,
                    food_nutrition_profiles_table.c.source_name == source_name,
                    food_nutrition_profiles_table.c.source_id == source_id,
                    food_nutrition_profiles_table.c.source_version == source_version,
                )
            )
            .mappings()
            .one_or_none()
        )
        return None if row is None else _nutrition_from_row(row)

    def get_current(self, food_ingredient_id: UUID) -> FoodNutritionProfile | None:
        row = (
            self._connection.execute(
                select(food_nutrition_profiles_table).where(
                    food_nutrition_profiles_table.c.food_ingredient_id
                    == food_ingredient_id,
                    food_nutrition_profiles_table.c.is_current.is_(True),
                )
            )
            .mappings()
            .one_or_none()
        )
        return None if row is None else _nutrition_from_row(row)

    def clear_current(self, food_ingredient_id: UUID) -> None:
        self._connection.execute(
            update(food_nutrition_profiles_table)
            .where(
                food_nutrition_profiles_table.c.food_ingredient_id
                == food_ingredient_id,
                food_nutrition_profiles_table.c.is_current.is_(True),
            )
            .values(is_current=False)
        )


def _escape_like(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _ingredient_values(ingredient: FoodIngredient) -> dict[str, object]:
    return {
        "id": ingredient.id,
        "canonical_code": ingredient.canonical_code,
        "canonical_name": ingredient.canonical_name,
        "canonical_name_key": ingredient.canonical_name_key,
        "category_code": ingredient.category_code,
        "default_unit": ingredient.default_unit.value,
        "density_g_per_ml": ingredient.density_g_per_ml,
        "edible_fraction": ingredient.edible_fraction,
        "allergens_reviewed": ingredient.allergens_reviewed,
        "storage_profile_code": ingredient.storage_profile_code,
        "is_active": ingredient.is_active,
        "created_at": ingredient.created_at,
        "updated_at": ingredient.updated_at,
    }


def _alias_values(alias: IngredientAlias) -> dict[str, object]:
    return {
        "id": alias.id,
        "food_ingredient_id": alias.food_ingredient_id,
        "alias": alias.alias,
        "alias_key": alias.alias_key,
        "language_code": alias.language_code,
        "created_at": alias.created_at,
    }


def _nutrition_values(profile: FoodNutritionProfile) -> dict[str, object]:
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


def _ingredient_from_row(
    row: Mapping[str, Any], allergen_codes: tuple[str, ...]
) -> FoodIngredient:
    return FoodIngredient(
        id=row["id"],
        canonical_code=row["canonical_code"],
        canonical_name=row["canonical_name"],
        canonical_name_key=row["canonical_name_key"],
        category_code=row["category_code"],
        default_unit=row["default_unit"],
        density_g_per_ml=row["density_g_per_ml"],
        edible_fraction=row["edible_fraction"],
        allergens_reviewed=row["allergens_reviewed"],
        allergen_codes=allergen_codes,
        storage_profile_code=row["storage_profile_code"],
        is_active=row["is_active"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _alias_from_row(row: Mapping[str, Any]) -> IngredientAlias:
    return IngredientAlias(
        id=row["id"],
        food_ingredient_id=row["food_ingredient_id"],
        alias=row["alias"],
        alias_key=row["alias_key"],
        language_code=row["language_code"],
        created_at=row["created_at"],
    )


def _nutrition_from_row(row: Mapping[str, Any]) -> FoodNutritionProfile:
    return FoodNutritionProfile(
        id=row["id"],
        food_ingredient_id=row["food_ingredient_id"],
        basis_grams=row["basis_grams"],
        kcal=row["kcal"],
        protein_g=row["protein_g"],
        fat_g=row["fat_g"],
        carbohydrates_g=row["carbohydrates_g"],
        fiber_g=row["fiber_g"],
        source_name=row["source_name"],
        source_id=row["source_id"],
        source_version=row["source_version"],
        source_data_type=row["source_data_type"],
        verified_at=row["verified_at"],
        estimated=row["estimated"],
        is_current=row["is_current"],
        created_at=row["created_at"],
    )
