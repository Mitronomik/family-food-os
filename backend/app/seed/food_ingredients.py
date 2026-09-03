"""Parse, validate, and atomically reconcile the trusted PR3 food seed."""

import csv
from dataclasses import asdict
from datetime import datetime
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
from uuid import uuid4

from app.db.config import DatabaseConfig, REPOSITORY_ROOT
from app.db.migrations import apply_migrations
from app.domain.food_ingredients import (
    FoodIngredient,
    FoodNutritionProfile,
    IngredientAlias,
    normalize_unicode_search_key,
)
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
from app.persistence.sqlalchemy_core.food_ingredient_composition import (
    create_food_catalogue_service,
)
from app.services.food_ingredients import (
    FoodCatalogueSeedSummary,
    TrustedAliasSeed,
    TrustedFoodIngredientSeed,
    TrustedNutritionSeed,
)

DEFAULT_SEED_DIRECTORY = REPOSITORY_ROOT / "data" / "seed" / "food_ingredients"
ALLOWED_SOURCE_DATA_TYPES = {"Foundation", "SR Legacy"}
EXPECTED_SOURCE_NAME = "USDA_FDC"


class FoodIngredientSeedError(ValueError):
    """Stable error for malformed or internally ambiguous trusted seed data."""


def load_seed_entries(
    seed_directory: Path = DEFAULT_SEED_DIRECTORY,
) -> tuple[TrustedFoodIngredientSeed, ...]:
    ingredient_rows = _read_csv(seed_directory / "ingredients.csv")
    alias_rows = _read_csv(seed_directory / "aliases.csv")
    nutrition_rows = _read_csv(seed_directory / "nutrition.csv")

    ingredients: dict[str, dict[str, str]] = {}
    canonical_keys: dict[str, str] = {}
    for row_number, row in enumerate(ingredient_rows, start=2):
        code = row.get("canonical_code", "").strip()
        if not code:
            raise FoodIngredientSeedError(
                f"ingredients.csv:{row_number}: canonical_code is required."
            )
        if code in ingredients:
            raise FoodIngredientSeedError(
                f"ingredients.csv:{row_number}: duplicate canonical_code {code}."
            )
        name_key = normalize_unicode_search_key(
            row.get("canonical_name", ""), field="canonical_name"
        )
        prior_code = canonical_keys.get(name_key)
        if prior_code is not None:
            raise FoodIngredientSeedError(
                f"ingredients.csv:{row_number}: normalized canonical name collides "
                f"between {prior_code} and {code}."
            )
        ingredients[code] = row
        canonical_keys[name_key] = code

    aliases_by_code: dict[str, list[TrustedAliasSeed]] = {
        code: [] for code in ingredients
    }
    alias_keys: dict[str, str] = {}
    for row_number, row in enumerate(alias_rows, start=2):
        code = row.get("canonical_code", "").strip()
        if code not in ingredients:
            raise FoodIngredientSeedError(
                f"aliases.csv:{row_number}: unknown canonical_code {code!r}."
            )
        alias = row.get("alias", "")
        key = normalize_unicode_search_key(alias, field="alias")
        previous = alias_keys.get(key)
        if previous is not None:
            raise FoodIngredientSeedError(
                f"aliases.csv:{row_number}: normalized alias {key!r} is duplicated "
                f"for {previous} and {code}."
            )
        canonical_owner = canonical_keys.get(key)
        if canonical_owner is not None and canonical_owner != code:
            raise FoodIngredientSeedError(
                f"aliases.csv:{row_number}: alias for {code} collides with canonical "
                f"name of {canonical_owner}."
            )
        alias_keys[key] = code
        aliases_by_code[code].append(
            TrustedAliasSeed(
                alias=alias,
                language_code=_optional_text(row.get("language_code", "")),
            )
        )

    nutrition_by_code: dict[str, TrustedNutritionSeed] = {}
    for row_number, row in enumerate(nutrition_rows, start=2):
        code = row.get("canonical_code", "").strip()
        if code not in ingredients:
            raise FoodIngredientSeedError(
                f"nutrition.csv:{row_number}: unknown canonical_code {code!r}."
            )
        if code in nutrition_by_code:
            raise FoodIngredientSeedError(
                f"nutrition.csv:{row_number}: duplicate nutrition row for {code}."
            )
        source_name = row.get("source_name", "").strip()
        source_data_type = row.get("source_data_type", "").strip()
        if source_name != EXPECTED_SOURCE_NAME:
            raise FoodIngredientSeedError(
                f"nutrition.csv:{row_number}: source_name must be USDA_FDC."
            )
        if source_data_type not in ALLOWED_SOURCE_DATA_TYPES:
            raise FoodIngredientSeedError(
                f"nutrition.csv:{row_number}: unsupported source_data_type "
                f"{source_data_type!r}."
            )
        nutrition_by_code[code] = TrustedNutritionSeed(
            basis_grams=_decimal(row, "basis_grams", row_number),
            kcal=_decimal(row, "kcal", row_number),
            protein_g=_decimal(row, "protein_g", row_number),
            fat_g=_decimal(row, "fat_g", row_number),
            carbohydrates_g=_decimal(row, "carbohydrates_g", row_number),
            fiber_g=_optional_decimal(row, "fiber_g", row_number),
            source_name=source_name,
            source_id=row.get("source_id", "").strip(),
            source_version=row.get("source_version", "").strip(),
            source_data_type=source_data_type,
            verified_at=_instant(row.get("verified_at", ""), row_number),
            estimated=_optional_boolean(row.get("estimated", ""), row_number),
        )

    missing_nutrition = sorted(set(ingredients) - set(nutrition_by_code))
    if missing_nutrition:
        raise FoodIngredientSeedError(
            f"Active seed ingredients lack nutrition rows: {missing_nutrition}."
        )

    entries = tuple(
        _entry_from_rows(
            code,
            ingredients[code],
            tuple(aliases_by_code[code]),
            nutrition_by_code[code],
        )
        for code in ingredients
    )
    if not entries:
        raise FoodIngredientSeedError("FoodIngredient seed must not be empty.")
    _validate_domain_objects(entries)
    return entries


def seed_food_ingredients(
    config: DatabaseConfig | None = None,
    *,
    seed_directory: Path = DEFAULT_SEED_DIRECTORY,
) -> FoodCatalogueSeedSummary:
    """Validate outside the transaction, then reconcile all rows in one UoW."""

    entries = load_seed_entries(seed_directory)
    apply_migrations(config)
    engine = create_sqlite_engine(config)
    try:
        return create_food_catalogue_service(engine).reconcile_seed(entries)
    finally:
        engine.dispose()


def _entry_from_rows(
    code: str,
    row: dict[str, str],
    aliases: tuple[TrustedAliasSeed, ...],
    nutrition: TrustedNutritionSeed,
) -> TrustedFoodIngredientSeed:
    return TrustedFoodIngredientSeed(
        canonical_code=code,
        canonical_name=row.get("canonical_name", ""),
        category_code=row.get("category_code", ""),
        default_unit=row.get("default_unit", ""),
        density_g_per_ml=_optional_decimal(row, "density_g_per_ml", 0),
        edible_fraction=_optional_decimal(row, "edible_fraction", 0),
        allergens_reviewed=_boolean(
            row.get("allergens_reviewed", ""),
            "allergens_reviewed",
            0,
        ),
        allergen_codes=(),
        storage_profile_code=_optional_text(row.get("storage_profile_code", "")),
        aliases=aliases,
        nutrition=nutrition,
    )


def _validate_domain_objects(entries: tuple[TrustedFoodIngredientSeed, ...]) -> None:
    now = datetime.fromisoformat("2026-09-02T00:00:00+00:00")
    for entry in entries:
        ingredient_id = uuid4()
        ingredient = FoodIngredient(
            id=ingredient_id,
            canonical_code=entry.canonical_code,
            canonical_name=entry.canonical_name,
            canonical_name_key=normalize_unicode_search_key(
                entry.canonical_name, field="canonical_name"
            ),
            category_code=entry.category_code,
            default_unit=entry.default_unit,  # type: ignore[arg-type]
            density_g_per_ml=entry.density_g_per_ml,
            edible_fraction=entry.edible_fraction,
            allergens_reviewed=entry.allergens_reviewed,
            allergen_codes=entry.allergen_codes,
            storage_profile_code=entry.storage_profile_code,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        for alias in entry.aliases:
            IngredientAlias(
                id=uuid4(),
                food_ingredient_id=ingredient.id,
                alias=alias.alias,
                alias_key=normalize_unicode_search_key(alias.alias, field="alias"),
                language_code=alias.language_code,
                created_at=now,
            )
        nutrition = entry.nutrition
        FoodNutritionProfile(
            id=uuid4(),
            food_ingredient_id=ingredient.id,
            basis_grams=nutrition.basis_grams,
            kcal=nutrition.kcal,
            protein_g=nutrition.protein_g,
            fat_g=nutrition.fat_g,
            carbohydrates_g=nutrition.carbohydrates_g,
            fiber_g=nutrition.fiber_g,
            source_name=nutrition.source_name,
            source_id=nutrition.source_id,
            source_version=nutrition.source_version,
            source_data_type=nutrition.source_data_type,
            verified_at=nutrition.verified_at,
            estimated=nutrition.estimated,
            is_current=True,
            created_at=now,
        )


def _read_csv(path: Path) -> list[dict[str, str]]:
    try:
        with path.open(encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))
    except (OSError, UnicodeError, csv.Error) as exc:
        raise FoodIngredientSeedError(
            f"Could not read trusted seed file {path}."
        ) from exc


def _decimal(row: dict[str, str], field: str, row_number: int) -> Decimal:
    value = row.get(field, "").strip()
    if not value:
        raise FoodIngredientSeedError(
            f"nutrition.csv:{row_number}: {field} is required."
        )
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise FoodIngredientSeedError(
            f"nutrition.csv:{row_number}: {field} is not a decimal."
        ) from exc
    if not parsed.is_finite():
        raise FoodIngredientSeedError(
            f"nutrition.csv:{row_number}: {field} must be finite."
        )
    return parsed


def _optional_decimal(
    row: dict[str, str], field: str, row_number: int
) -> Decimal | None:
    if not row.get(field, "").strip():
        return None
    return _decimal(row, field, row_number)


def _boolean(value: str, field: str, row_number: int) -> bool:
    normalized = value.strip().casefold()
    if normalized == "true":
        return True
    if normalized == "false":
        return False
    raise FoodIngredientSeedError(
        f"ingredients.csv:{row_number}: {field} must be true or false."
    )


def _optional_boolean(value: str, row_number: int) -> bool | None:
    if not value.strip():
        return None
    return _boolean(value, "estimated", row_number)


def _instant(value: str, row_number: int) -> datetime:
    try:
        return datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError as exc:
        raise FoodIngredientSeedError(
            f"nutrition.csv:{row_number}: verified_at is not an ISO instant."
        ) from exc


def _optional_text(value: str) -> str | None:
    normalized = value.strip()
    return normalized or None


if __name__ == "__main__":
    print(
        json.dumps(asdict(seed_food_ingredients()), ensure_ascii=False, sort_keys=True)
    )
