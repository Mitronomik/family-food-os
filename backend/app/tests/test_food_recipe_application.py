from dataclasses import replace
from decimal import Decimal
import sqlite3

import pytest

from app.db.config import DatabaseConfig
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
from app.persistence.sqlalchemy_core.food_ingredient_composition import (
    create_food_catalogue_service,
)
from app.persistence.sqlalchemy_core.food_recipe_composition import (
    create_food_recipe_catalogue_service,
)
from app.seed.food_recipes import load_seed_entries, seed_food_recipes
from app.services.food_recipes import (
    FoodIngredientResolutionError,
    RecipeCatalogueConflictError,
    RecipeNotFoundError,
)


@pytest.fixture
def catalogue(tmp_path):
    config = DatabaseConfig(path=tmp_path / "application.sqlite")
    seed_food_recipes(config)
    engine = create_sqlite_engine(config)
    try:
        yield config, engine, create_food_recipe_catalogue_service(engine)
    finally:
        engine.dispose()


def _seed(code):
    return next(item for item in load_seed_entries() if item.canonical_code == code)


def test_create_trusted_rejects_duplicate_code_and_normalized_name(catalogue):
    _, _, service = catalogue
    existing = _seed("SPICED_OATMEAL")

    with pytest.raises(RecipeCatalogueConflictError, match="code"):
        service.create_trusted(existing)
    with pytest.raises(RecipeCatalogueConflictError, match="name"):
        service.create_trusted(
            replace(
                existing,
                canonical_code="A_DISTINCT_CODE",
                canonical_name="  SPICED   OATMEAL  ",
            )
        )


def test_unresolved_ingredient_rolls_back_complete_new_aggregate(catalogue):
    config, _, service = catalogue
    source = _seed("SPICED_OATMEAL")
    candidate = replace(
        source,
        canonical_code="ATOMIC_RECIPE",
        canonical_name="Atomic Recipe",
        version=replace(
            source.version,
            source_recipe_id="atomic-recipe",
            source_version="atomic-v1",
            ingredients=(
                *source.version.ingredients,
                replace(
                    source.version.ingredients[0],
                    food_ingredient_code="DOES_NOT_EXIST",
                ),
            ),
        ),
    )

    with pytest.raises(FoodIngredientResolutionError, match="DOES_NOT_EXIST"):
        service.create_trusted(candidate)

    with pytest.raises(RecipeNotFoundError):
        service.get_by_code("ATOMIC_RECIPE")
    with sqlite3.connect(config.path) as connection:
        assert (
            connection.execute(
                "SELECT COUNT(*) FROM food_recipes WHERE canonical_code='ATOMIC_RECIPE'"
            ).fetchone()[0]
            == 0
        )


def test_inactive_ingredient_rejects_append_without_partial_version(catalogue):
    _, engine, recipe_service = catalogue
    food_service = create_food_catalogue_service(engine)
    food_service.deactivate(food_service.get_by_code("OATS_ROLLED").id)
    recipe = recipe_service.get_by_code("SPICED_OATMEAL")
    before = recipe_service.list_versions(recipe.id)

    with pytest.raises(FoodIngredientResolutionError, match="OATS_ROLLED"):
        recipe_service.append_trusted_version(
            recipe.id,
            replace(
                _seed("SPICED_OATMEAL").version,
                source_version="inactive-fi-v2",
                source_document_sha256="e" * 64,
                change_note="Inactive FoodIngredient fixture.",
            ),
        )

    assert recipe_service.list_versions(recipe.id) == before


def test_current_verified_requires_active_recipe(catalogue):
    _, _, service = catalogue
    recipe = service.get_by_code("SPICED_OATMEAL")

    service.deactivate(recipe.id)

    with pytest.raises(RecipeNotFoundError):
        service.get_current_verified(recipe.id)
    assert (
        service.get_version_detail(service.list_versions(recipe.id)[0].id).recipe.id
        == recipe.id
    )


def test_service_scaling_preserves_identity_and_fractional_pieces(catalogue):
    _, _, service = catalogue
    recipe = service.get_by_code("SPICED_OATMEAL")
    original = service.get_current_verified(recipe.id)
    scaled = service.scale_version(original.version.id, Decimal("3"))

    assert scaled.version == original.version
    assert scaled.steps == original.steps
    assert [line.position for line in scaled.ingredients] == [
        line.position for line in original.ingredients
    ]
    assert all(
        scaled_line.quantity
        == (original_line.quantity / Decimal("2")).quantize(Decimal("0.000001"))
        for original_line, scaled_line in zip(original.ingredients, scaled.ingredients)
    )
