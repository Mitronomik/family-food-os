"""Trusted, offline loader for the frozen PR4 verified recipe seed."""

from dataclasses import asdict
from datetime import datetime
from decimal import Decimal, InvalidOperation
import json
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
CURATION_DIRECTORY = PROJECT_ROOT / "data" / "curation" / "pr4"
EXPECTED_RECIPE_COUNT = 30
EXPECTED_MANIFEST_CODE_COUNT = 119


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
        raise FoodRecipeSeedError("Frozen PR4 corpus must contain exactly 30 sources.")

    corpus_by_id = {row["recipe_source_id"]: row for row in corpus_rows}
    manifest_by_id = {row["recipe_source_id"]: row for row in source_rows}
    if (
        len(corpus_by_id) != EXPECTED_RECIPE_COUNT
        or len(manifest_by_id) != EXPECTED_RECIPE_COUNT
    ):
        raise FoodRecipeSeedError("Recipe source identities must be unique.")

    accepted_codes = {
        line.strip()
        for line in (CURATION_DIRECTORY / "mvp0-food-ingredient-codes.txt")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    }
    if len(accepted_codes) != EXPECTED_MANIFEST_CODE_COUNT:
        raise FoodRecipeSeedError(
            "Accepted PR4 FoodIngredient manifest must contain 119 codes."
        )

    entries: list[TrustedRecipeSeed] = []
    used_codes: set[str] = set()
    seen_recipe_identities: set[tuple[str, str]] = set()
    for index, row in enumerate(recipe_rows, start=1):
        if not isinstance(row, dict) or not isinstance(row.get("version"), dict):
            raise FoodRecipeSeedError(f"recipes.json record {index} is invalid.")
        version = row["version"]
        source_id = _required(version, "source_recipe_id", index)
        manifest = manifest_by_id.get(source_id)
        corpus = corpus_by_id.get(source_id)
        if manifest is None or corpus is None:
            raise FoodRecipeSeedError(
                f"recipes.json record {index} is outside the frozen corpus."
            )
        _validate_provenance(version, manifest, corpus, index)
        ingredients = tuple(
            _ingredient(item, index, ingredient_index)
            for ingredient_index, item in enumerate(
                version.get("ingredients", []), start=1
            )
        )
        steps_raw = version.get("steps")
        if not ingredients or not isinstance(steps_raw, list) or not steps_raw:
            raise FoodRecipeSeedError(
                f"recipes.json record {index} requires ingredients and steps."
            )
        steps = tuple(str(step) for step in steps_raw)
        equipment_raw = version.get("equipment_codes", [])
        if not isinstance(equipment_raw, list):
            raise FoodRecipeSeedError(
                f"recipes.json record {index} equipment is invalid."
            )
        used_codes.update(item.food_ingredient_code for item in ingredients)
        canonical_code = _required(row, "canonical_code", index)
        canonical_name = _required(row, "canonical_name", index)
        identity = (canonical_code, canonical_name.casefold())
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
                    source_retrieved_at=_instant(
                        _required(version, "source_retrieved_at", index), index
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
                    equipment_codes=tuple(str(code) for code in equipment_raw),
                ),
            )
        )
    if used_codes != accepted_codes:
        missing = sorted(accepted_codes - used_codes)
        extra = sorted(used_codes - accepted_codes)
        raise FoodRecipeSeedError(
            f"Recipe seed FoodIngredient coverage differs from accepted manifest; missing={missing}, extra={extra}."
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
    fields = (
        "source_name",
        "source_url",
        "source_version",
        "source_retrieved_at",
        "source_document_sha256",
        "rights_review_status",
        "rights_basis",
    )
    for field in fields:
        if version.get(field) != manifest.get(field):
            raise FoodRecipeSeedError(
                f"recipes.json record {index} {field} differs from source manifest."
            )
    try:
        source_servings = Decimal(str(version.get("source_original_servings")))
        manifest_servings = Decimal(str(manifest.get("source_original_servings")))
    except InvalidOperation as exc:
        raise FoodRecipeSeedError(
            f"recipes.json record {index} has invalid source_original_servings."
        ) from exc
    if (
        not source_servings.is_finite()
        or not manifest_servings.is_finite()
        or source_servings != manifest_servings
    ):
        raise FoodRecipeSeedError(
            f"recipes.json record {index} source_original_servings differs from source manifest."
        )
    if version.get("source_url") != corpus.get("source_url"):
        raise FoodRecipeSeedError(
            f"recipes.json record {index} URL differs from frozen corpus."
        )
    digest = version.get("source_document_sha256")
    if (
        not isinstance(digest, str)
        or len(digest) != 64
        or any(character not in "0123456789abcdef" for character in digest)
    ):
        raise FoodRecipeSeedError(f"recipes.json record {index} has invalid SHA-256.")
    if version.get("verification_status") != "SOURCE_VERIFIED":
        raise FoodRecipeSeedError(
            f"recipes.json record {index} is not SOURCE_VERIFIED."
        )
    if version.get("rights_review_status") != "REVIEWED" or not version.get(
        "rights_basis"
    ):
        raise FoodRecipeSeedError(f"recipes.json record {index} lacks rights review.")
    if (
        manifest.get("rights_evidence_url")
        != "https://www.ars.usda.gov/ott/templates-agreements/"
    ):
        raise FoodRecipeSeedError(
            f"source-manifest.json record {index} lacks reviewed rights evidence."
        )


def _json(path: Path) -> dict[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise FoodRecipeSeedError(f"Could not read trusted seed file {path}.") from exc
    if not isinstance(value, dict):
        raise FoodRecipeSeedError(f"Trusted seed file {path} must contain an object.")
    return value


def _required(row: dict[str, object], field: str, index: int) -> str:
    value = row.get(field)
    if not isinstance(value, str) or not value.strip():
        raise FoodRecipeSeedError(f"recipes.json record {index} requires {field}.")
    return value.strip()


def _decimal(row: dict[str, object], field: str, index: int) -> Decimal:
    value = row.get(field)
    if not isinstance(value, str):
        raise FoodRecipeSeedError(
            f"recipes.json record {index} {field} must be a decimal string."
        )
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise FoodRecipeSeedError(
            f"recipes.json record {index} {field} is invalid."
        ) from exc
    if not parsed.is_finite():
        raise FoodRecipeSeedError(
            f"recipes.json record {index} {field} must be finite."
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


def _instant(value: str, index: int) -> datetime:
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


def _optional_instant(value: object, index: int) -> datetime | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise FoodRecipeSeedError(
            f"recipes.json record {index} has an invalid verified_at."
        )
    return _instant(value, index)


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise FoodRecipeSeedError("Optional text must be null or non-empty text.")
    return value.strip()


if __name__ == "__main__":
    print(json.dumps(asdict(seed_food_recipes()), ensure_ascii=False, sort_keys=True))
