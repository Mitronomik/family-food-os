import json
import shutil
import sqlite3
from dataclasses import replace
from decimal import Decimal

import pytest
from app.db import migrations
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
from app.seed.food_ingredients import seed_food_ingredients
from app.seed.r1f_prepared_output import seed_r1f_prepared_output
from app.seed.r1h_school2022_main import (
    BEEF_FOOD_CODE,
    GOULASH_RECIPE_CODE,
    MEATBALLS_RECIPE_CODE,
    PACKAGE,
    _identity_seeds,
    _load_contract,
    _recipe_seeds_and_specs,
    seed_r1h_school2022_main,
)
from app.seed.ru_nut_db_r1a import seed_ru_nut_db_r1a
from app.seed.ru_nut_db_step4 import seed_ru_nut_db_step4
from app.seed.ru_nut_db_step8_butter import seed_ru_nut_db_step8_butter
from app.services.food_ingredients import (
    FoodCatalogueConflictError,
    TrustedFoodIngredientIdentitySeed,
)
from app.services.food_recipes import (
    FoodRecipeCatalogueService,
    RecipeCatalogueConflictError,
)
from app.services.recipe_nutrition_v2 import RecipeNutritionV2ConflictError


@pytest.fixture(scope="module")
def adversarial_baseline(tmp_path_factory):
    config = DatabaseConfig(
        path=tmp_path_factory.mktemp("r1h-adversarial-base") / "base.sqlite"
    )
    migrations.apply_migrations(config)
    seed_food_ingredients(config)
    seed_ru_nut_db_step4(config)
    seed_ru_nut_db_r1a(config)
    seed_ru_nut_db_step8_butter(config)
    seed_r1f_prepared_output(config)
    return config


@pytest.fixture
def database(adversarial_baseline, tmp_path):
    config = DatabaseConfig(path=tmp_path / "r1h-adversarial.sqlite")
    shutil.copyfile(adversarial_baseline.path, config.path)
    return config


def db_dump(config: DatabaseConfig) -> str:
    with sqlite3.connect(config.path) as db:
        return "\n".join(db.iterdump())


def _selected_counts(config: DatabaseConfig) -> dict[str, int]:
    with sqlite3.connect(config.path) as db:
        recipe_count = db.execute(
            """
            SELECT COUNT(*)
            FROM food_recipes
            WHERE canonical_code IN (?, ?)
            """,
            (MEATBALLS_RECIPE_CODE, GOULASH_RECIPE_CODE),
        ).fetchone()[0]
        authority_count = db.execute(
            """
            SELECT COUNT(*)
            FROM recipe_prepared_nutrition_authorities a
            JOIN food_recipe_versions v ON v.id = a.recipe_version_id
            JOIN food_recipes r ON r.id = v.recipe_id
            WHERE r.canonical_code IN (?, ?)
            """,
            (MEATBALLS_RECIPE_CODE, GOULASH_RECIPE_CODE),
        ).fetchone()[0]
        value_count = db.execute(
            """
            SELECT COUNT(*)
            FROM recipe_prepared_nutrient_values n
            JOIN food_recipe_versions v ON v.id = n.recipe_version_id
            JOIN food_recipes r ON r.id = v.recipe_id
            WHERE r.canonical_code IN (?, ?)
            """,
            (MEATBALLS_RECIPE_CODE, GOULASH_RECIPE_CODE),
        ).fetchone()[0]
    return {
        "recipes": recipe_count,
        "authorities": authority_count,
        "values": value_count,
    }


def test_r1h_rejects_modified_frozen_contract_before_writes(database, tmp_path):
    package = tmp_path / "r1g"
    shutil.copytree(PACKAGE, package)
    spec_path = package / "prepared-publication-specs.json"
    payload = json.loads(spec_path.read_text(encoding="utf-8"))
    payload["recipes"][MEATBALLS_RECIPE_CODE]["prepared_spec"][
        "expected_available_amounts"
    ] = [["ENERGY_KCAL", "154"]]
    spec_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    before = db_dump(database)

    with pytest.raises(ValueError, match="frozen artifact changed"):
        seed_r1h_school2022_main(database, package=package)

    assert db_dump(database) == before


def test_r1h_identity_conflict_fails_closed(database):
    engine = create_sqlite_engine(database)
    try:
        create_food_catalogue_service(engine).reconcile_identity_seed(
            (
                TrustedFoodIngredientIdentitySeed(
                    canonical_code=BEEF_FOOD_CODE,
                    canonical_name="Говядина конфликт",
                    category_code="meat",
                    default_unit="g",
                ),
            )
        )
    finally:
        engine.dispose()

    with pytest.raises(FoodCatalogueConflictError, match="Identity-only seed"):
        seed_r1h_school2022_main(database)

    assert _selected_counts(database) == {
        "recipes": 0,
        "authorities": 0,
        "values": 0,
    }


def test_r1h_partial_recipe_without_prepared_authority_fails_closed(database):
    specs_payload, batch_payload = _load_contract()
    seeds, _ = _recipe_seeds_and_specs(specs_payload)
    engine = create_sqlite_engine(database)
    try:
        create_food_catalogue_service(engine).reconcile_identity_seed(
            _identity_seeds(batch_payload)
        )
        create_food_recipe_catalogue_service(engine).reconcile_seed((seeds[0],))
    finally:
        engine.dispose()

    with pytest.raises(RecipeNutritionV2ConflictError, match="Partial persisted R1-H"):
        seed_r1h_school2022_main(database)

    assert _selected_counts(database) == {
        "recipes": 1,
        "authorities": 0,
        "values": 0,
    }


def test_r1h_conflicting_recipe_seed_fails_closed(database):
    specs_payload, batch_payload = _load_contract()
    seeds, _ = _recipe_seeds_and_specs(specs_payload)
    conflicting = replace(
        seeds[0],
        version=replace(seeds[0].version, steps=("Конфликтующий шаг.",)),
    )
    engine = create_sqlite_engine(database)
    try:
        create_food_catalogue_service(engine).reconcile_identity_seed(
            _identity_seeds(batch_payload)
        )
        create_food_recipe_catalogue_service(engine).reconcile_seed((conflicting,))
    finally:
        engine.dispose()

    with pytest.raises(RecipeCatalogueConflictError):
        seed_r1h_school2022_main(database)


def test_r1h_conflicting_prepared_authority_fails_closed(database):
    specs_payload, batch_payload = _load_contract()
    seeds, reviewed = _recipe_seeds_and_specs(specs_payload)
    engine = create_sqlite_engine(database)
    try:
        create_food_catalogue_service(engine).reconcile_identity_seed(
            _identity_seeds(batch_payload)
        )
        catalogue = create_food_recipe_catalogue_service(engine)
        catalogue.reconcile_seed((seeds[0],))
        nutrition = create_recipe_nutrition_v2_service(engine)
        wrong = replace(
            reviewed[0],
            expected_available_amounts=(("ENERGY_KCAL", Decimal("999")),),
        )
        nutrition.publish_prepared(wrong)
    finally:
        engine.dispose()

    with pytest.raises(RecipeNutritionV2ConflictError):
        seed_r1h_school2022_main(database)


@pytest.mark.parametrize("failure_point", ("version", "values", "authority"))
def test_r1h_fresh_recipe_and_authority_failure_rolls_back(
    database, monkeypatch, failure_point
):
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
        seed_r1h_school2022_main(database)

    assert _selected_counts(database) == {
        "recipes": 0,
        "authorities": 0,
        "values": 0,
    }
    with sqlite3.connect(database.path) as db:
        assert (
            db.execute(
                """
                SELECT COUNT(*)
                FROM food_ingredients
                WHERE canonical_code IN (
                    'BEEF_CATEGORY_1_RAW',
                    'WHEAT_BREAD_HIGH_GRADE_STALE',
                    'SALT_IODIZED',
                    'TOMATO_PUREE_PASTE'
                )
                """
            ).fetchone()[0]
            == 4
        )


def test_r1h_activation_failure_keeps_exact_publication_inactive(
    database, monkeypatch
):
    def fail_activate(self, recipe_id):
        del self, recipe_id
        raise RuntimeError("injected activation failure")

    monkeypatch.setattr(
        FoodRecipeCatalogueService,
        "_activate_after_policy_check",
        fail_activate,
    )

    with pytest.raises(RuntimeError, match="injected activation failure"):
        seed_r1h_school2022_main(database)

    assert _selected_counts(database) == {
        "recipes": 2,
        "authorities": 2,
        "values": 2,
    }
    with sqlite3.connect(database.path) as db:
        rows = db.execute(
            """
            SELECT canonical_code, is_active
            FROM food_recipes
            WHERE canonical_code IN (?, ?)
            ORDER BY canonical_code
            """,
            (MEATBALLS_RECIPE_CODE, GOULASH_RECIPE_CODE),
        ).fetchall()
    assert rows == [
        (MEATBALLS_RECIPE_CODE, 0),
        (GOULASH_RECIPE_CODE, 0),
    ]
