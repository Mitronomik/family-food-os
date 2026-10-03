import shutil

import pytest
from app.db.config import DatabaseConfig
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
from app.persistence.sqlalchemy_core.food_ingredient_composition import (
    create_food_catalogue_service,
)
from app.persistence.sqlalchemy_core.food_recipe_composition import (
    create_food_recipe_catalogue_service,
)
from app.seed.r2_breakfast_capacity import seed_r2_breakfast_capacity
from app.seed.r2b_fish_main_diversity import (
    PACKAGE,
    PINK_SALMON_FOOD_CODE,
    PUBLICATION_SPECS_PATH,
    _identity_seeds,
    _load_contract,
    _recipe_seeds_and_specs,
    seed_r2b_fish_main_diversity,
)
from app.services.food_ingredients import (
    FoodCatalogueConflictError,
    TrustedFoodIngredientIdentitySeed,
)
from app.services.recipe_nutrition_v2 import RecipeNutritionV2ConflictError


def test_r2b_hash_pinned_contract_rejects_tampered_publication_specs(tmp_path):
    package = tmp_path / "package"
    shutil.copytree(PACKAGE, package)
    specs = package / PUBLICATION_SPECS_PATH.name
    specs.write_text(specs.read_text().replace('"144.8"', '"144.9"', 1))

    with pytest.raises(ValueError, match="frozen artifact changed"):
        _load_contract(package)


def test_r2b_partial_recipe_without_prepared_authority_fails_closed(tmp_path):
    config = DatabaseConfig(path=tmp_path / "partial.sqlite")
    seed_r2_breakfast_capacity(config)
    _, _, payload = _load_contract()
    seeds, _ = _recipe_seeds_and_specs(payload)

    engine = create_sqlite_engine(config)
    try:
        food = create_food_catalogue_service(engine)
        food.reconcile_identity_seed(_identity_seeds(payload))
        catalogue = create_food_recipe_catalogue_service(engine)
        catalogue.reconcile_seed((seeds[0],))
    finally:
        engine.dispose()

    with pytest.raises(
        RecipeNutritionV2ConflictError,
        match="Partial persisted R2-B state",
    ):
        seed_r2b_fish_main_diversity(config)


def test_r2b_conflicting_fish_identity_fails_closed(tmp_path):
    config = DatabaseConfig(path=tmp_path / "identity-conflict.sqlite")
    seed_r2_breakfast_capacity(config)
    engine = create_sqlite_engine(config)
    try:
        food = create_food_catalogue_service(engine)
        food.reconcile_identity_seed(
            (
                TrustedFoodIngredientIdentitySeed(
                    canonical_code=PINK_SALMON_FOOD_CODE,
                    canonical_name="Горбуша, филе конфликт",
                    category_code="fish_seafood",
                    default_unit="g",
                ),
            )
        )
    finally:
        engine.dispose()

    with pytest.raises(FoodCatalogueConflictError):
        seed_r2b_fish_main_diversity(config)
