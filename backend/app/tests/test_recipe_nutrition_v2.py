"""Focused Step 10-A canonical Recipe Nutrition V2 tests."""

from dataclasses import replace
from datetime import datetime, timezone
from decimal import Decimal
import shutil
import sqlite3

import pytest
from sqlalchemy import event

from app.db.config import DatabaseConfig
from app.domain.nutrition import NutritionStatus
from app.domain.recipe_nutrition_v2 import (
    NUTRIENT_CODES,
    CanonicalNutrientAmount,
    CanonicalRecipeVersionNutrition,
    RecipeNutritionV2Status,
)
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
from app.persistence.sqlalchemy_core.recipe_nutrition_v2 import (
    create_recipe_nutrition_v2_service,
)
from app.persistence.sqlalchemy_core.food_ingredient_composition import (
    create_food_catalogue_service,
)
from app.seed.food_recipes import seed_food_recipes
from app.seed.ru_nut_db_step8_butter import seed_ru_nut_db_step8_butter
from app.seed.ru_school2022_step9_recipe import (
    FOOD_CODE,
    RECIPE_CODE,
    SCHOOL_PDF_SHA256,
    SOURCE_RECIPE_ID,
    EXPECTED_RECIPE_AMOUNTS,
    load_ru_school2022_step9_recipe_seed,
    seed_ru_school2022_step9_recipe,
)
from app.services.recipe_nutrition_v2 import (
    BindingDisposition,
    RecipeNutritionV2ConflictError,
    ReviewedRecipeIngredientBindingSpec,
    project_recipe_nutrition_consumption,
)

SOURCE_VERSION = f"sha256:{SCHOOL_PDF_SHA256}"


@pytest.fixture(scope="module")
def baseline(tmp_path_factory):
    config = DatabaseConfig(path=tmp_path_factory.mktemp("step10a-base") / "base.sqlite")
    seed_food_recipes(config)
    seed_ru_nut_db_step8_butter(config)
    seed_ru_school2022_step9_recipe(config)
    return config


@pytest.fixture
def database(baseline, tmp_path):
    config = DatabaseConfig(path=tmp_path / "step10a.sqlite")
    shutil.copyfile(baseline.path, config.path)
    return config


def spec():
    trusted_seed, _ = load_ru_school2022_step9_recipe_seed()
    return ReviewedRecipeIngredientBindingSpec(
        trusted_recipe_seed=trusted_seed,
        recipe_code=RECIPE_CODE,
        source_name="ru-school2022",
        source_recipe_id=SOURCE_RECIPE_ID,
        source_version=SOURCE_VERSION,
        recipe_version_number=1,
        ingredient_position=1,
        food_ingredient_code=FOOD_CODE,
        quantity=Decimal("10"),
        unit="g",
        composition_version=1,
    )


def db_dump(config):
    with sqlite3.connect(config.path) as db:
        return "\n".join(db.iterdump())


def test_fresh_binding_replay_and_step9_canonical_projection(database):
    engine = create_sqlite_engine(database)
    try:
        service = create_recipe_nutrition_v2_service(engine)
        first = service.publish_binding(spec())
        assert first.disposition is BindingDisposition.FRESH

        canonical = service.calculate(first.recipe_version_id)
        assert canonical.status is RecipeNutritionV2Status.PARTIAL
        assert len(canonical.required_total) == 54
        known = {
            item.code: item.amount
            for item in canonical.required_total
            if item.amount is not None
        }
        assert known == EXPECTED_RECIPE_AMOUNTS
        assert canonical.total_amount("WATER") is None
        assert canonical.total_amount("CARBOHYDRATE_AVAILABLE") is None
        assert canonical.total_amount("CARBOHYDRATE_BY_DIFFERENCE") is None

        projection = service.consumption_projection(first.recipe_version_id)
        assert projection.legacy_status is NutritionStatus.INCOMPLETE
        assert projection.required_total.kcal == Decimal("66.090000")
        assert projection.required_total.protein_g == Decimal("0.080000")
        assert projection.required_total.fat_g == Decimal("7.250000")
        assert projection.required_total.fiber_g == Decimal("0.000000")
        assert projection.required_total.carbohydrates_g is None
        assert projection.exact_energy_ready is True

        before = db_dump(database)
        second = service.publish_binding(spec())
        assert second.disposition is BindingDisposition.EXACT_REPLAY
        assert second.binding == first.binding
        assert db_dump(database) == before
    finally:
        engine.dispose()


def test_fresh_publication_rechecks_active_dependency_after_external_read(database):
    engine = create_sqlite_engine(database)
    try:
        food = create_food_catalogue_service(engine).get_by_code(FOOD_CODE)
        assert food.is_active is True
        with engine.begin() as connection:
            connection.exec_driver_sql(
                "UPDATE food_ingredients SET is_active = 0 WHERE canonical_code = ?",
                (FOOD_CODE,),
            )
        with pytest.raises(RecipeNutritionV2ConflictError, match="inactive"):
            create_recipe_nutrition_v2_service(engine).publish_binding(spec())
        with sqlite3.connect(database.path) as db:
            assert db.execute(
                "SELECT COUNT(*) FROM recipe_ingredient_composition_bindings"
            ).fetchone()[0] == 0
    finally:
        engine.dispose()


def test_binding_publication_rejects_drifted_step9_structure(database):
    reviewed = spec()
    drifted_seed = replace(
        reviewed.trusted_recipe_seed,
        version=replace(
            reviewed.trusted_recipe_seed.version,
            steps=("изменённая инструкция",)
            + reviewed.trusted_recipe_seed.version.steps[1:],
        ),
    )
    drifted = replace(reviewed, trusted_recipe_seed=drifted_seed)

    engine = create_sqlite_engine(database)
    try:
        with pytest.raises(RecipeNutritionV2ConflictError, match="structure/provenance"):
            create_recipe_nutrition_v2_service(engine).publish_binding(drifted)
        with sqlite3.connect(database.path) as db:
            assert db.execute(
                "SELECT COUNT(*) FROM recipe_ingredient_composition_bindings"
            ).fetchone()[0] == 0
    finally:
        engine.dispose()


def test_deactivation_blocks_replay_but_historical_read_still_replays(database):
    engine = create_sqlite_engine(database)
    try:
        service = create_recipe_nutrition_v2_service(engine)
        first = service.publish_binding(spec())
        canonical_before = service.calculate(first.recipe_version_id)
        with engine.begin() as connection:
            connection.exec_driver_sql(
                "UPDATE food_ingredients SET is_active = 0 WHERE canonical_code = ?",
                (FOOD_CODE,),
            )

        with pytest.raises(RecipeNutritionV2ConflictError, match="inactive"):
            service.publish_binding(spec())

        canonical_after = service.calculate(first.recipe_version_id)
        assert canonical_after == canonical_before
    finally:
        engine.dispose()


def test_injected_late_binding_write_failure_rolls_back(database):
    engine = create_sqlite_engine(database)
    before = db_dump(database)

    def fail(connection, cursor, statement, parameters, context, executemany):
        del connection, cursor, parameters, context, executemany
        if statement.strip().startswith(
            "INSERT INTO recipe_ingredient_composition_bindings"
        ):
            raise RuntimeError("injected Step 10-A binding failure")

    event.listen(engine, "before_cursor_execute", fail)
    try:
        with pytest.raises(RuntimeError, match="injected Step 10-A"):
            create_recipe_nutrition_v2_service(engine).publish_binding(spec())
    finally:
        event.remove(engine, "before_cursor_execute", fail)
        engine.dispose()
    assert db_dump(database) == before


def _synthetic_canonical(*, available=None, by_difference=None, starch=None, sugars=None):
    values = {
        code: None for code in NUTRIENT_CODES
    }
    values.update(
        {
            "ENERGY_KCAL": Decimal("100"),
            "PROTEIN": Decimal("10"),
            "FAT_TOTAL": Decimal("5"),
            "FIBER_TOTAL_DIETARY": Decimal("2"),
            "CARBOHYDRATE_AVAILABLE": available,
            "CARBOHYDRATE_BY_DIFFERENCE": by_difference,
            "STARCH": starch,
            "SUGARS_TOTAL": sugars,
        }
    )
    nutrient_values = tuple(
        CanonicalNutrientAmount(code, values[code]) for code in NUTRIENT_CODES
    )
    return CanonicalRecipeVersionNutrition(
        recipe_version_id=__import__("uuid").uuid4(),
        registry_version="RU_NUTRIENT_REGISTRY_V2",
        nutrient_set_version="RECIPE_V2_NUTRIENT_SET_V1",
        composition_calculation_version="FOOD_COMPOSITION_APPLICABILITY_V2",
        recipe_calculation_version="RECIPE_COMPOSITION_NUTRITION_V1",
        bindings=(),
        required_total=nutrient_values,
        per_base_serving=nutrient_values,
        status=RecipeNutritionV2Status.PARTIAL,
        issues=(),
    )


def test_recipe_v1_decimal_scaling_and_unknown_propagation_helpers_are_exact():
    from app.domain.food_composition import calculation_context
    from decimal import localcontext

    repeating = Decimal("1") / Decimal("3")
    with localcontext(calculation_context()):
        scaled = Decimal("1") * Decimal("10") / Decimal("3")
        assert scaled == Decimal("3.3333333333333333333333333333333333333333333333333333333333333333333333333333333")
        assert scaled.quantize(Decimal("0.000001")) == Decimal("3.333333")

    # Canonical unknown stays unknown in compatibility projection; it is never
    # synthesized from other carbohydrate concepts.
    projected = project_recipe_nutrition_consumption(
        _synthetic_canonical(
            available=Decimal("12"),
            by_difference=None,
            starch=Decimal("7"),
            sugars=Decimal("3"),
        )
    )
    assert projected.required_total.carbohydrates_g is None
    assert projected.legacy_status is NutritionStatus.INCOMPLETE


def test_legacy_carbohydrate_projection_is_by_difference_only():
    available_only = project_recipe_nutrition_consumption(
        _synthetic_canonical(available=Decimal("12"))
    )
    assert available_only.required_total.carbohydrates_g is None
    assert available_only.legacy_status is NutritionStatus.INCOMPLETE

    by_difference = project_recipe_nutrition_consumption(
        _synthetic_canonical(by_difference=Decimal("15"))
    )
    assert by_difference.required_total.carbohydrates_g == Decimal("15")

    both = project_recipe_nutrition_consumption(
        _synthetic_canonical(
            available=Decimal("12"), by_difference=Decimal("15")
        )
    )
    assert both.required_total.carbohydrates_g == Decimal("15")

    components_only = project_recipe_nutrition_consumption(
        _synthetic_canonical(starch=Decimal("7"), sugars=Decimal("3"))
    )
    assert components_only.required_total.carbohydrates_g is None
