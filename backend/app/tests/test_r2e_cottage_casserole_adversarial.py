import shutil
import sqlite3
from dataclasses import replace
from decimal import Decimal

import pytest
from app.db.config import DatabaseConfig
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
from app.persistence.sqlalchemy_core.food_ingredient_composition import (
    create_food_catalogue_service,
)
from app.persistence.sqlalchemy_core.food_recipe_composition import (
    create_food_recipe_catalogue_service,
)
from app.persistence.sqlalchemy_core.food_recipe_repositories import (
    SqlAlchemyRecipeVersionRepository,
)
from app.persistence.sqlalchemy_core.recipe_nutrition_v2 import (
    SqlAlchemyPreparedRecipeNutritionRepository,
    create_recipe_nutrition_v2_service,
)
from app.seed.r2c_breakfast_grain_diversity import (
    seed_r2c_breakfast_grain_diversity,
)
from app.seed.r2e_cottage_casserole import (
    APPLICABILITY_PATH,
    CASSEROLE_RECIPE_CODE,
    IDENTITY_ONLY_FOOD_CODES,
    IDENTITY_REVIEW_PATH,
    PACKAGE,
    PUBLICATION_SPECS_PATH,
    SELECTION_PATH,
    TVOROG_5_FOOD_CODE,
    _identity_seeds,
    _load_contract,
    _recipe_seed_and_spec,
    seed_r2e_cottage_casserole,
)
from app.services.food_ingredients import (
    FoodCatalogueConflictError,
    TrustedFoodIngredientIdentitySeed,
)
from app.services.food_recipes import FoodRecipeCatalogueService
from app.services.recipe_nutrition_v2 import RecipeNutritionV2ConflictError


def selected_counts(config: DatabaseConfig) -> dict[str, int]:
    with sqlite3.connect(config.path) as db:
        recipe_id = db.execute(
            "SELECT id FROM food_recipes WHERE canonical_code = ?",
            (CASSEROLE_RECIPE_CODE,),
        ).fetchone()
        recipe_count = 0 if recipe_id is None else 1
        if recipe_id is None:
            return {"recipes": 0, "authorities": 0, "values": 0}
        version_ids = tuple(
            row[0]
            for row in db.execute(
                "SELECT id FROM food_recipe_versions WHERE recipe_id = ?",
                (recipe_id[0],),
            ).fetchall()
        )
        if not version_ids:
            return {"recipes": recipe_count, "authorities": 0, "values": 0}
        placeholders = ",".join("?" for _ in version_ids)
        authorities = db.execute(
            f"""
            SELECT COUNT(*)
            FROM recipe_prepared_nutrition_authorities
            WHERE recipe_version_id IN ({placeholders})
            """,
            version_ids,
        ).fetchone()[0]
        values = db.execute(
            f"""
            SELECT COUNT(*)
            FROM recipe_prepared_nutrient_values
            WHERE recipe_version_id IN ({placeholders})
            """,
            version_ids,
        ).fetchone()[0]
    return {"recipes": recipe_count, "authorities": authorities, "values": values}


@pytest.mark.parametrize(
    ("artifact_name", "old", "new"),
    (
        (SELECTION_PATH.name, '"301.2"', '"301.3"'),
        (IDENTITY_REVIEW_PATH.name, '"TVOROG_5"', '"TVOROG_9"'),
        (APPLICABILITY_PATH.name, '"HOUSEHOLD_APPLICABLE"', '"BLOCKED"'),
        (PUBLICATION_SPECS_PATH.name, '"301.2"', '"301.3"'),
    ),
)
def test_r2e_hash_pinned_contract_rejects_any_tampered_artifact(
    tmp_path, artifact_name, old, new
):
    package = tmp_path / "package"
    shutil.copytree(PACKAGE, package)
    artifact = package / artifact_name
    artifact.write_text(artifact.read_text().replace(old, new, 1))

    with pytest.raises(ValueError, match="R2-E frozen artifact changed"):
        _load_contract(package)


def test_r2e_partial_recipe_without_prepared_authority_fails_closed(tmp_path):
    config = DatabaseConfig(path=tmp_path / "partial.sqlite")
    seed_r2c_breakfast_grain_diversity(config)
    _, _, _, payload = _load_contract()
    seed, _ = _recipe_seed_and_spec(payload)

    engine = create_sqlite_engine(config)
    try:
        food = create_food_catalogue_service(engine)
        food.reconcile_identity_seed(_identity_seeds(payload))
        catalogue = create_food_recipe_catalogue_service(engine)
        catalogue.reconcile_seed((seed,))
    finally:
        engine.dispose()

    with pytest.raises(
        RecipeNutritionV2ConflictError,
        match="Partial persisted R2-E state",
    ):
        seed_r2e_cottage_casserole(config)


def test_r2e_conflicting_exact_identity_fails_closed(tmp_path):
    config = DatabaseConfig(path=tmp_path / "identity-conflict.sqlite")
    seed_r2c_breakfast_grain_diversity(config)
    engine = create_sqlite_engine(config)
    try:
        food = create_food_catalogue_service(engine)
        food.reconcile_identity_seed(
            (
                TrustedFoodIngredientIdentitySeed(
                    canonical_code=TVOROG_5_FOOD_CODE,
                    canonical_name="Творог 5% конфликт",
                    category_code="dairy",
                    default_unit="g",
                ),
            )
        )
    finally:
        engine.dispose()

    with pytest.raises(FoodCatalogueConflictError):
        seed_r2e_cottage_casserole(config)


def test_r2e_existing_301_3_prepared_authority_conflicts_with_frozen_301_2(tmp_path):
    config = DatabaseConfig(path=tmp_path / "wrong-energy.sqlite")
    seed_r2c_breakfast_grain_diversity(config)
    _, _, _, payload = _load_contract()
    seed, spec = _recipe_seed_and_spec(payload)

    engine = create_sqlite_engine(config)
    try:
        food = create_food_catalogue_service(engine)
        food.reconcile_identity_seed(_identity_seeds(payload))
        catalogue = create_food_recipe_catalogue_service(engine)
        catalogue.reconcile_seed((seed,))
        nutrition = create_recipe_nutrition_v2_service(engine)
        nutrition.publish_prepared(
            replace(
                spec,
                expected_available_amounts=(("ENERGY_KCAL", Decimal("301.3")),),
            )
        )
    finally:
        engine.dispose()

    with pytest.raises(RecipeNutritionV2ConflictError):
        seed_r2e_cottage_casserole(config)


@pytest.mark.parametrize("failure_point", ("version", "values", "authority"))
def test_r2e_fresh_recipe_and_authority_failure_rolls_back(
    tmp_path, monkeypatch, failure_point
):
    config = DatabaseConfig(path=tmp_path / f"{failure_point}.sqlite")
    seed_r2c_breakfast_grain_diversity(config)

    def fail(*args, **kwargs):
        del args, kwargs
        raise RuntimeError(f"injected {failure_point} failure")

    if failure_point == "version":
        monkeypatch.setattr(SqlAlchemyRecipeVersionRepository, "add_detail", fail)
    elif failure_point == "values":
        monkeypatch.setattr(
            SqlAlchemyPreparedRecipeNutritionRepository, "add_values", fail
        )
    else:
        monkeypatch.setattr(
            SqlAlchemyPreparedRecipeNutritionRepository, "add_authority", fail
        )

    with pytest.raises(RuntimeError, match=f"injected {failure_point}"):
        seed_r2e_cottage_casserole(config)

    assert selected_counts(config) == {
        "recipes": 0,
        "authorities": 0,
        "values": 0,
    }
    with sqlite3.connect(config.path) as db:
        placeholders = ",".join("?" for _ in IDENTITY_ONLY_FOOD_CODES)
        assert (
            db.execute(
                f"""
                SELECT COUNT(*)
                FROM food_ingredients
                WHERE canonical_code IN ({placeholders})
                """,
                IDENTITY_ONLY_FOOD_CODES,
            ).fetchone()[0]
            == 4
        )


def test_r2e_activation_failure_keeps_exact_publication_inactive(tmp_path, monkeypatch):
    config = DatabaseConfig(path=tmp_path / "activation.sqlite")
    seed_r2c_breakfast_grain_diversity(config)

    def fail_activate(self, recipe_id):
        del self, recipe_id
        raise RuntimeError("injected activation failure")

    monkeypatch.setattr(
        FoodRecipeCatalogueService,
        "_activate_after_policy_check",
        fail_activate,
    )

    with pytest.raises(RuntimeError, match="injected activation failure"):
        seed_r2e_cottage_casserole(config)

    assert selected_counts(config) == {
        "recipes": 1,
        "authorities": 1,
        "values": 1,
    }
    with sqlite3.connect(config.path) as db:
        row = db.execute(
            """
            SELECT canonical_code, is_active
            FROM food_recipes
            WHERE canonical_code = ?
            """,
            (CASSEROLE_RECIPE_CODE,),
        ).fetchone()
    assert row == (CASSEROLE_RECIPE_CODE, 0)
