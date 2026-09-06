"""Trusted offline loader for the accepted PR4 Recipe Catalogue seed."""

import json
from dataclasses import asdict
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from app.db.config import DatabaseConfig
from app.db.migrations import apply_migrations
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
from app.persistence.sqlalchemy_core.food_recipe_composition import (
    create_food_recipe_catalogue_service,
)
from app.seed.food_ingredients import seed_food_ingredients
from app.services.food_recipes import (
    RecipeSeedSummary,
    TrustedRecipeIngredientSeed,
    TrustedRecipeSeed,
    TrustedRecipeVersionSeed,
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_SEED_DIRECTORY = PROJECT_ROOT / "data" / "seed" / "recipes"
CURATION_DIRECTORY = PROJECT_ROOT / "data" / "curation" / "pr4-data2"
EXPECTED_RECIPE_COUNT = 30
EXPECTED_INGREDIENT_COUNT = 189
EXPECTED_STEP_COUNT = 169
EXPECTED_EQUIPMENT_COUNT = 86
EXPECTED_EQUIPMENT_CODE_COUNT = 34
EXPECTED_FOOD_INGREDIENT_CODE_COUNT = 81


class FoodRecipeSeedError(ValueError):
    pass


def load_seed_entries(
    seed_directory: Path = DEFAULT_SEED_DIRECTORY,
) -> tuple[TrustedRecipeSeed, ...]:
    recipes_payload = _json(seed_directory / "recipes.json")
    manifest_payload = _json(seed_directory / "source-manifest.json")
    corpus_payload = _json(CURATION_DIRECTORY / "recipe-corpus.json")
    recipe_rows = recipes_payload.get("recipes")
    source_rows = manifest_payload.get("sources")
    corpus_rows = corpus_payload.get("recipes")
    if not isinstance(recipe_rows, list) or len(recipe_rows) != EXPECTED_RECIPE_COUNT:
        raise FoodRecipeSeedError("recipes.json must contain exactly 30 recipes.")
    if not isinstance(source_rows, list) or len(source_rows) != EXPECTED_RECIPE_COUNT:
        raise FoodRecipeSeedError(
            "source-manifest.json must contain exactly 30 sources."
        )
    if not isinstance(corpus_rows, list) or len(corpus_rows) != EXPECTED_RECIPE_COUNT:
        raise FoodRecipeSeedError(
            "Accepted PR4-DATA2 corpus must contain exactly 30 recipes."
        )

    corpus_by_id = _unique_by(corpus_rows, "recipe_source_id", "accepted DATA2 corpus")
    manifest_by_id = _unique_by(source_rows, "recipe_source_id", "source manifest")
    accepted_ids = set(corpus_by_id)
    if set(manifest_by_id) != accepted_ids:
        raise FoodRecipeSeedError(
            "Source manifest identities differ from accepted PR4-DATA2."
        )

    accepted_codes = {
        line.strip()
        for line in (CURATION_DIRECTORY / "mvp0-food-ingredient-codes.txt")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    }
    if len(accepted_codes) != EXPECTED_FOOD_INGREDIENT_CODE_COUNT:
        raise FoodRecipeSeedError(
            "Accepted PR4-DATA2 FoodIngredient manifest must contain 81 codes."
        )

    entries: list[TrustedRecipeSeed] = []
    used_codes: set[str] = set()
    seen_source_ids: set[str] = set()
    seen_recipe_identities: set[tuple[str, str]] = set()
    ingredient_count = 0
    step_count = 0
    equipment_count = 0
    equipment_codes: set[str] = set()

    for index, row in enumerate(recipe_rows, start=1):
        if not isinstance(row, dict) or not isinstance(row.get("version"), dict):
            raise FoodRecipeSeedError(f"recipes.json record {index} is invalid.")
        version = row["version"]
        source_id = _required(version, "source_recipe_id", index)
        if source_id in seen_source_ids:
            raise FoodRecipeSeedError("Recipe source identities must be unique.")
        seen_source_ids.add(source_id)
        manifest = manifest_by_id.get(source_id)
        corpus = corpus_by_id.get(source_id)
        if manifest is None or corpus is None:
            raise FoodRecipeSeedError(
                f"recipes.json record {index} is outside accepted PR4-DATA2."
            )
        _validate_provenance(version, manifest, corpus, index)

        ingredient_rows = version.get("ingredients")
        steps_raw = version.get("steps")
        equipment_raw = version.get("equipment_codes")
        if not isinstance(ingredient_rows, list) or not ingredient_rows:
            raise FoodRecipeSeedError(
                f"recipes.json record {index} requires ingredients."
            )
        if (
            not isinstance(steps_raw, list)
            or not steps_raw
            or any(not isinstance(step, str) or not step.strip() for step in steps_raw)
        ):
            raise FoodRecipeSeedError(
                f"recipes.json record {index} requires nonblank ordered steps."
            )
        if not isinstance(equipment_raw, list):
            raise FoodRecipeSeedError(
                f"recipes.json record {index} equipment is invalid."
            )

        ingredients = tuple(
            _ingredient(item, index, ingredient_index)
            for ingredient_index, item in enumerate(ingredient_rows, start=1)
        )
        steps = tuple(step.strip() for step in steps_raw)
        equipment = tuple(_equipment_code(code, index) for code in equipment_raw)
        if len(set(equipment)) != len(equipment):
            raise FoodRecipeSeedError(
                f"recipes.json record {index} contains duplicate equipment codes."
            )

        used_codes.update(item.food_ingredient_code for item in ingredients)
        equipment_codes.update(equipment)
        ingredient_count += len(ingredients)
        step_count += len(steps)
        equipment_count += len(equipment)

        canonical_code = _required(row, "canonical_code", index)
        canonical_name = _required(row, "canonical_name", index)
        identity = (canonical_code, " ".join(canonical_name.casefold().split()))
        if identity in seen_recipe_identities:
            raise FoodRecipeSeedError("Recipe seed identities must be unique.")
        seen_recipe_identities.add(identity)

        entries.append(
            TrustedRecipeSeed(
                canonical_code=canonical_code,
                canonical_name=canonical_name,
                version=TrustedRecipeVersionSeed(
                    base_servings=_decimal(version, "base_servings", index),
                    meal_type_code=_required(version, "meal_type_code", index),
                    prep_time_minutes=_optional_int(
                        version, "prep_time_minutes", index
                    ),
                    cook_time_minutes=_optional_int(
                        version, "cook_time_minutes", index
                    ),
                    total_time_minutes=_optional_int(
                        version, "total_time_minutes", index
                    ),
                    difficulty_code=_optional_text(version.get("difficulty_code")),
                    batch_friendly=_optional_bool(version, "batch_friendly", index),
                    freezable=_optional_bool(version, "freezable", index),
                    storage_days_fridge=_optional_int(
                        version, "storage_days_fridge", index
                    ),
                    storage_days_freezer=_optional_int(
                        version, "storage_days_freezer", index
                    ),
                    verification_status=_required(
                        version, "verification_status", index
                    ),
                    verified_at=_optional_instant(version.get("verified_at"), index),
                    source_name=_required(version, "source_name", index),
                    source_recipe_id=source_id,
                    source_url=_required(version, "source_url", index),
                    source_version=_required(version, "source_version", index),
                    source_retrieved_at=_optional_instant(
                        version.get("source_retrieved_at"), index
                    ),
                    source_document_sha256=_required(
                        version, "source_document_sha256", index
                    ),
                    source_original_servings=_decimal(
                        version, "source_original_servings", index
                    ),
                    rights_review_status=_required(
                        version, "rights_review_status", index
                    ),
                    rights_basis=_optional_text(version.get("rights_basis")),
                    change_note=_required(version, "change_note", index),
                    ingredients=ingredients,
                    steps=steps,
                    equipment_codes=equipment,
                ),
            )
        )

    if seen_source_ids != accepted_ids:
        raise FoodRecipeSeedError(
            "Recipe seed source IDs differ from accepted PR4-DATA2."
        )
    if ingredient_count != EXPECTED_INGREDIENT_COUNT:
        raise FoodRecipeSeedError(
            f"Recipe seed must contain 189 ingredients, got {ingredient_count}."
        )
    if step_count != EXPECTED_STEP_COUNT:
        raise FoodRecipeSeedError(
            f"Recipe seed must contain 169 steps, got {step_count}."
        )
    if equipment_count != EXPECTED_EQUIPMENT_COUNT:
        raise FoodRecipeSeedError(
            f"Recipe seed must contain 86 equipment rows, got {equipment_count}."
        )
    if len(equipment_codes) != EXPECTED_EQUIPMENT_CODE_COUNT:
        raise FoodRecipeSeedError(
            "Recipe seed must contain 34 distinct equipment codes."
        )
    if used_codes != accepted_codes:
        missing = sorted(accepted_codes - used_codes)
        extra = sorted(used_codes - accepted_codes)
        raise FoodRecipeSeedError(
            f"Recipe seed FoodIngredient coverage differs from accepted DATA2; missing={missing}, extra={extra}."
        )
    return tuple(entries)


def seed_food_recipes(
    config: DatabaseConfig | None = None,
    *,
    seed_directory: Path = DEFAULT_SEED_DIRECTORY,
) -> RecipeSeedSummary:
    entries = load_seed_entries(seed_directory)
    seed_food_ingredients(config)
    apply_migrations(config)
    engine = create_sqlite_engine(config)
    try:
        return create_food_recipe_catalogue_service(engine).reconcile_seed(entries)
    finally:
        engine.dispose()


def _unique_by(
    rows: list[object], key: str, label: str
) -> dict[str, dict[str, object]]:
    result: dict[str, dict[str, object]] = {}
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get(key), str):
            raise FoodRecipeSeedError(f"Invalid row in {label}.")
        value = row[key]
        if value in result:
            raise FoodRecipeSeedError(f"Duplicate {key} in {label}.")
        result[value] = row
    return result


def _ingredient(
    row: object, recipe_index: int, ingredient_index: int
) -> TrustedRecipeIngredientSeed:
    if not isinstance(row, dict):
        raise FoodRecipeSeedError(
            f"recipes.json record {recipe_index} ingredient {ingredient_index} is invalid."
        )
    return TrustedRecipeIngredientSeed(
        food_ingredient_code=_required(row, "food_ingredient_code", recipe_index),
        quantity=_decimal(row, "quantity", recipe_index),
        unit=_required(row, "unit", recipe_index),
        source_amount_text=_required(row, "source_amount_text", recipe_index),
        normalization_note=_optional_text(row.get("normalization_note")),
        prep_note=_optional_text(row.get("prep_note")),
        optional=_bool(row, "optional", recipe_index),
    )


def _validate_provenance(
    version: dict[str, object],
    manifest: dict[str, object],
    corpus: dict[str, object],
    index: int,
) -> None:
    for field in (
        "source_name",
        "source_url",
        "source_version",
        "source_retrieved_at",
        "source_document_sha256",
        "rights_review_status",
        "rights_basis",
    ):
        if version.get(field) != manifest.get(field):
            raise FoodRecipeSeedError(
                f"recipes.json record {index} {field} differs from source manifest."
            )

    source_servings = _finite_decimal_value(
        version.get("source_original_servings"), index
    )
    manifest_servings = _finite_decimal_value(
        manifest.get("source_original_servings"), index
    )
    corpus_servings = _finite_decimal_value(corpus.get("source_servings"), index)
    base_servings = _finite_decimal_value(version.get("base_servings"), index)
    if not (source_servings == manifest_servings == corpus_servings == base_servings):
        raise FoodRecipeSeedError(
            f"recipes.json record {index} servings differ from accepted DATA2."
        )
    if version.get("source_url") != corpus.get("source_url"):
        raise FoodRecipeSeedError(
            f"recipes.json record {index} URL differs from accepted DATA2."
        )
    if version.get("meal_type_code") != corpus.get("meal_type_code"):
        raise FoodRecipeSeedError(
            f"recipes.json record {index} meal type differs from accepted DATA2."
        )
    digest = version.get("source_document_sha256")
    if digest != corpus.get("source_sha256") or not _is_sha256(digest):
        raise FoodRecipeSeedError(
            f"recipes.json record {index} hash differs from accepted DATA2."
        )
    if version.get("source_version") != f"sha256:{digest}":
        raise FoodRecipeSeedError(
            f"recipes.json record {index} source_version must identify accepted hash."
        )
    if (
        version.get("verification_status") != "SOURCE_VERIFIED"
        or version.get("verified_at") is None
    ):
        raise FoodRecipeSeedError(
            f"recipes.json record {index} is not source verified."
        )
    rights = corpus.get("rights_review")
    if not isinstance(rights, dict):
        raise FoodRecipeSeedError(f"Accepted DATA2 rights record {index} is invalid.")
    if version.get("rights_review_status") != "REVIEWED" or version.get(
        "rights_basis"
    ) != rights.get("basis"):
        raise FoodRecipeSeedError(
            f"recipes.json record {index} rights review differs from accepted DATA2."
        )
    if manifest.get("accepted_data2_sha256") != digest:
        raise FoodRecipeSeedError(
            f"source-manifest.json record {index} lacks accepted DATA2 lineage."
        )
    _optional_instant(version.get("source_retrieved_at"), index)


def _required(row: dict[str, object], field: str, index: int) -> str:
    value = row.get(field)
    if not isinstance(value, str) or not value.strip():
        raise FoodRecipeSeedError(f"recipes.json record {index} requires {field}.")
    return value.strip()


def _decimal(row: dict[str, object], field: str, index: int) -> Decimal:
    return _finite_decimal_value(row.get(field), index)


def _finite_decimal_value(value: object, index: int) -> Decimal:
    if isinstance(value, bool) or value is None:
        raise FoodRecipeSeedError(
            f"recipes.json record {index} has invalid decimal value."
        )
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise FoodRecipeSeedError(
            f"recipes.json record {index} has invalid decimal value."
        ) from exc
    if not parsed.is_finite():
        raise FoodRecipeSeedError(
            f"recipes.json record {index} decimal must be finite."
        )
    return parsed


def _optional_int(row: dict[str, object], field: str, index: int) -> int | None:
    value = row.get(field)
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise FoodRecipeSeedError(f"recipes.json record {index} {field} is invalid.")
    return value


def _bool(row: dict[str, object], field: str, index: int) -> bool:
    value = row.get(field)
    if type(value) is not bool:
        raise FoodRecipeSeedError(f"recipes.json record {index} {field} is invalid.")
    return value


def _optional_bool(row: dict[str, object], field: str, index: int) -> bool | None:
    return None if row.get(field) is None else _bool(row, field, index)


def _optional_instant(value: object, index: int) -> datetime | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise FoodRecipeSeedError(
            f"recipes.json record {index} has an invalid instant."
        )
    try:
        instant = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise FoodRecipeSeedError(
            f"recipes.json record {index} has an invalid instant."
        ) from exc
    if instant.tzinfo is None or instant.utcoffset() is None:
        raise FoodRecipeSeedError(
            f"recipes.json record {index} instant must be timezone-aware."
        )
    return instant


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise FoodRecipeSeedError("Optional text must be null or non-empty text.")
    return value.strip()


def _equipment_code(value: object, index: int) -> str:
    if not isinstance(value, str) or not value or value != value.lower():
        raise FoodRecipeSeedError(
            f"recipes.json record {index} equipment code must be lowercase text."
        )
    return value


def _is_sha256(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(c in "0123456789abcdef" for c in value)
    )


def _json(path: Path) -> dict[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise FoodRecipeSeedError(f"Could not read trusted seed file {path}.") from exc
    if not isinstance(value, dict):
        raise FoodRecipeSeedError(f"Trusted seed file {path} must contain an object.")
    return value


if __name__ == "__main__":
    print(json.dumps(asdict(seed_food_recipes()), ensure_ascii=False, sort_keys=True))
