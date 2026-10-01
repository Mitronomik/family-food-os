import shutil
import sqlite3
from contextlib import contextmanager
from dataclasses import replace
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import pytest
from app.db import migrations
from app.db.config import DatabaseConfig
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
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
from app.seed.r1b_reviewed_recipes import seed_r1b_recipes
from app.seed.r1f_prepared_output import (
    CHICKEN_RECIPE_CODE,
    EGG_RECIPE_CODE,
    _load_evidence,
    _prepared_specs,
    _recipe_seeds,
    seed_r1f_prepared_output,
)
from app.seed.ru_food_data import seed_ru_food_data
from app.seed.ru_nut_db_r1a import seed_ru_nut_db_r1a
from app.seed.ru_nut_db_step4 import seed_ru_nut_db_step4
from app.services.food_recipes import FoodRecipeCatalogueService
from app.services.planner import PlannerAdmissionBlocker, PlannerService
from app.services.prepared_recipe_activation import (
    PreparedRecipeActivationError,
    activate_prepared_recipe,
)
from app.services.recipe_nutrition_v2 import (
    RecipeNutritionV2ConflictError,
    RecipeNutritionV2ContractError,
    RecipeNutritionV2Service,
    RecipeNutritionV2UnavailableError,
)


@pytest.fixture(scope="module")
def adversarial_baseline(tmp_path_factory):
    config = DatabaseConfig(
        path=tmp_path_factory.mktemp("r1f-adversarial-base") / "base.sqlite"
    )
    migrations.apply_migrations(config)
    seed_food_ingredients(config)
    seed_ru_food_data(config)
    seed_ru_nut_db_step4(config)
    seed_ru_nut_db_r1a(config)
    seed_r1b_recipes(config)
    return config


@pytest.fixture
def database(adversarial_baseline, tmp_path):
    config = DatabaseConfig(path=tmp_path / "r1f-adversarial.sqlite")
    shutil.copyfile(adversarial_baseline.path, config.path)
    return config


def _counts(config):
    with sqlite3.connect(config.path) as db:
        return {
            "pilot_recipes": db.execute(
                """
                SELECT COUNT(*)
                FROM food_recipes
                WHERE canonical_code IN (?, ?)
                """,
                (EGG_RECIPE_CODE, CHICKEN_RECIPE_CODE),
            ).fetchone()[0],
            "authorities": db.execute(
                "SELECT COUNT(*) FROM recipe_prepared_nutrition_authorities"
            ).fetchone()[0],
            "values": db.execute(
                "SELECT COUNT(*) FROM recipe_prepared_nutrient_values"
            ).fetchone()[0],
        }


def test_partial_recipe_without_prepared_authority_fails_closed(database):
    engine = create_sqlite_engine(database)
    try:
        catalogue = create_food_recipe_catalogue_service(engine)
        egg_seed, _ = _recipe_seeds(_load_evidence())
        catalogue.reconcile_seed((egg_seed,))
    finally:
        engine.dispose()

    with pytest.raises(RecipeNutritionV2ConflictError, match="Partial persisted"):
        seed_r1f_prepared_output(database)

    with sqlite3.connect(database.path) as db:
        recipe = db.execute(
            "SELECT is_active FROM food_recipes WHERE canonical_code = ?",
            (EGG_RECIPE_CODE,),
        ).fetchone()
        assert recipe == (0,)
        assert (
            db.execute(
                "SELECT COUNT(*) FROM recipe_prepared_nutrition_authorities"
            ).fetchone()[0]
            == 0
        )


@pytest.mark.parametrize("failure_point", ["version", "values", "authority"])
def test_fresh_publication_failure_rolls_back_recipe_and_prepared_state(
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
        seed_r1f_prepared_output(database)

    assert _counts(database) == {
        "pilot_recipes": 0,
        "authorities": 0,
        "values": 0,
    }


def test_activation_failure_keeps_exact_publication_inactive(database, monkeypatch):
    def fail_activate(self, recipe_id):
        del self, recipe_id
        raise RuntimeError("injected activation failure")

    monkeypatch.setattr(
        FoodRecipeCatalogueService, "_activate_after_policy_check", fail_activate
    )

    with pytest.raises(RuntimeError, match="injected activation"):
        seed_r1f_prepared_output(database)

    with sqlite3.connect(database.path) as db:
        rows = db.execute(
            """
            SELECT canonical_code, is_active
            FROM food_recipes
            WHERE canonical_code IN (?, ?)
            ORDER BY canonical_code
            """,
            (EGG_RECIPE_CODE, CHICKEN_RECIPE_CODE),
        ).fetchall()
        assert rows == [
            (CHICKEN_RECIPE_CODE, 0),
            (EGG_RECIPE_CODE, 0),
        ]
        assert (
            db.execute(
                "SELECT COUNT(*) FROM recipe_prepared_nutrition_authorities"
            ).fetchone()[0]
            == 2
        )
        assert (
            db.execute(
                "SELECT COUNT(*) FROM recipe_prepared_nutrient_values"
            ).fetchone()[0]
            == 2
        )


def _reviewed_specs():
    evidence = _load_evidence()
    seeds = _recipe_seeds(evidence)
    return seeds, _prepared_specs(evidence, seeds)


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("output_mass_g", Decimal(39)),
        ("source_document_sha256", "0" * 64),
        ("rights_review_status", "UNREVIEWED"),
        ("rights_basis", "wrong-rights-basis"),
        ("source_name", "WRONG_SOURCE"),
    ),
)
def test_prepared_publication_rejects_wrong_source_output_hash_or_rights(
    database, field, value
):
    seed_r1f_prepared_output(database)
    _, specs = _reviewed_specs()
    engine = create_sqlite_engine(database)
    try:
        nutrition = create_recipe_nutrition_v2_service(engine)
        with pytest.raises(RecipeNutritionV2ContractError):
            nutrition.publish_prepared(replace(specs[0], **{field: value}))
    finally:
        engine.dispose()


@pytest.mark.parametrize(
    "amounts",
    (
        (),
        (("ENERGY_KCAL", Decimal(0)),),
        (("ENERGY_KCAL", Decimal(-1)),),
    ),
)
def test_prepared_publication_rejects_missing_zero_or_negative_energy(
    database, amounts
):
    seed_r1f_prepared_output(database)
    _, specs = _reviewed_specs()
    engine = create_sqlite_engine(database)
    try:
        nutrition = create_recipe_nutrition_v2_service(engine)
        with pytest.raises(
            RecipeNutritionV2ContractError, match="ENERGY_KCAL|nutrient"
        ):
            nutrition.publish_prepared(
                replace(specs[0], expected_available_amounts=amounts)
            )
    finally:
        engine.dispose()


def test_prepared_publication_rejects_unreviewed_available_nutrient(database):
    seed_r1f_prepared_output(database)
    _, specs = _reviewed_specs()
    egg = specs[0]
    unreviewed = replace(
        egg,
        expected_available_amounts=egg.expected_available_amounts
        + (("PROTEIN", Decimal("5.1")),),
    )
    engine = create_sqlite_engine(database)
    try:
        nutrition = create_recipe_nutrition_v2_service(engine)
        with pytest.raises(
            RecipeNutritionV2ContractError, match="AVAILABLE and UNKNOWN"
        ):
            nutrition.publish_prepared(unreviewed)
    finally:
        engine.dispose()


def test_soft_or_medium_egg_cannot_consume_hard_boiled_authority(database):
    seed_r1f_prepared_output(database)
    seeds, specs = _reviewed_specs()
    egg = seeds[0]
    wrong_process = replace(
        egg,
        version=replace(
            egg.version,
            steps=("Сварить яйцо всмятку вместо hard-boiled 8–10 минут.",),
        ),
    )
    engine = create_sqlite_engine(database)
    try:
        nutrition = create_recipe_nutrition_v2_service(engine)
        with pytest.raises(RecipeNutritionV2ConflictError, match="structure/process"):
            nutrition.publish_prepared(
                replace(specs[0], trusted_recipe_seed=wrong_process)
            )
    finally:
        engine.dispose()


def test_category_i_chicken_cannot_satisfy_category_ii_main_authority(database):
    seed_r1f_prepared_output(database)
    seeds, specs = _reviewed_specs()
    chicken = seeds[1]
    category_i_ingredient = replace(
        chicken.version.ingredients[0],
        food_ingredient_code="CHICKEN_CATEGORY_1_RAW",
    )
    wrong_category = replace(
        chicken,
        version=replace(
            chicken.version,
            ingredients=(category_i_ingredient,),
        ),
    )
    engine = create_sqlite_engine(database)
    try:
        nutrition = create_recipe_nutrition_v2_service(engine)
        with pytest.raises(RecipeNutritionV2ConflictError, match="structure/process"):
            nutrition.publish_prepared(
                replace(specs[1], trusted_recipe_seed=wrong_category)
            )
    finally:
        engine.dispose()


def test_697_824_144_kcal_cannot_satisfy_chicken_main_authority(database):
    seed_r1f_prepared_output(database)
    _, specs = _reviewed_specs()
    rejected = replace(
        specs[1],
        source_name="USSR_VOCATIONAL_ORDER_1986",
        source_recipe_id="697/824",
        source_version="1986",
        expected_available_amounts=(("ENERGY_KCAL", Decimal(144)),),
    )
    engine = create_sqlite_engine(database)
    try:
        nutrition = create_recipe_nutrition_v2_service(engine)
        with pytest.raises(RecipeNutritionV2ContractError):
            nutrition.publish_prepared(rejected)
    finally:
        engine.dispose()


def test_catalogue_has_no_public_unchecked_activation_command():
    assert not hasattr(FoodRecipeCatalogueService, "activate")


def test_activation_boundary_rejects_recipe_without_prepared_authority(database):
    seeds, specs = _reviewed_specs()
    engine = create_sqlite_engine(database)
    try:
        catalogue = create_food_recipe_catalogue_service(engine)
        catalogue.reconcile_seed((seeds[0],))
        nutrition = create_recipe_nutrition_v2_service(engine)
        planner = PlannerService(
            None,
            None,
            catalogue,
            None,
            None,
            recipe_nutrition=nutrition,  # type: ignore[arg-type]
        )
        with pytest.raises(PreparedRecipeActivationError, match="authority|Nutrition"):
            activate_prepared_recipe(
                catalogue=catalogue,
                nutrition=nutrition,
                planner=planner,
                spec=specs[0],
            )
        assert catalogue.get_by_code(EGG_RECIPE_CODE).is_active is False
    finally:
        engine.dispose()
    assert _counts(database)["authorities"] == 0


def test_activation_boundary_rejects_unexpected_planner_blocker(database, monkeypatch):
    original = PlannerService.compose_candidate_admission

    def blocked(self):
        rows = original(self)
        return tuple(
            replace(
                row,
                blockers=row.blockers + (PlannerAdmissionBlocker.ROLE_UNSUPPORTED,),
            )
            if row.canonical_code == EGG_RECIPE_CODE
            else row
            for row in rows
        )

    monkeypatch.setattr(PlannerService, "compose_candidate_admission", blocked)
    with pytest.raises(PreparedRecipeActivationError, match="Planner admission"):
        seed_r1f_prepared_output(database)

    with sqlite3.connect(database.path) as db:
        state = db.execute(
            "SELECT is_active FROM food_recipes WHERE canonical_code = ?",
            (EGG_RECIPE_CODE,),
        ).fetchone()
        assert state == (0,)


def test_neutral_projection_rejects_prepared_and_composition_dual_authority():
    ingredient_id = uuid4()
    version_id = uuid4()
    detail = SimpleNamespace(
        ingredients=(SimpleNamespace(id=ingredient_id, optional=False),),
        version=SimpleNamespace(id=version_id),
    )

    @contextmanager
    def read_scope():
        yield SimpleNamespace(
            versions=SimpleNamespace(get_detail=lambda _: detail),
            bindings=SimpleNamespace(get=lambda _: object()),
            prepared=SimpleNamespace(get_authority=lambda _: object()),
        )

    service = RecipeNutritionV2Service(read_scope, lambda: None)

    with pytest.raises(RecipeNutritionV2UnavailableError, match="конфликт"):
        service.neutral_consumption_projection(version_id)
