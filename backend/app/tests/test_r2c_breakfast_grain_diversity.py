import shutil
import sqlite3
from collections import Counter
from datetime import date
from decimal import Decimal

import pytest
from app.db import migrations
from app.db.config import DatabaseConfig
from app.domain.meal_patterns import MealRole
from app.domain.meal_plans import MemberMealPatternSourceKind
from app.domain.planner import PlannerConfig, PlannerRejectionCode, PlannerSuccess
from app.domain.recipe_nutrition_v2 import (
    NUTRIENT_CODES,
    RecipeNutritionAuthorityKind,
    RecipeNutritionV2Status,
)
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
from app.persistence.sqlalchemy_core.food_ingredient_composition import (
    create_food_catalogue_service,
)
from app.persistence.sqlalchemy_core.food_recipe_composition import (
    create_food_recipe_catalogue_service,
)
from app.persistence.sqlalchemy_core.household_composition import (
    create_household_service,
)
from app.persistence.sqlalchemy_core.household_uow import SqlAlchemyHouseholdReadScope
from app.persistence.sqlalchemy_core.meal_pattern_uow import (
    SqlAlchemyMealPatternCatalogueReadScope,
)
from app.persistence.sqlalchemy_core.meal_plan_uow import (
    SqlAlchemyMealPlanReadScope,
    SqlAlchemyMealPlanUnitOfWork,
)
from app.persistence.sqlalchemy_core.nutrition_composition import (
    create_nutrition_service,
)
from app.persistence.sqlalchemy_core.pantry_composition import create_pantry_service
from app.persistence.sqlalchemy_core.recipe_nutrition_v2 import (
    SqlAlchemyRecipeNutritionV2ReadScope,
    create_recipe_nutrition_v2_service,
)
from app.seed.r2b_fish_main_diversity import seed_r2b_fish_main_diversity
from app.seed.r2c_breakfast_grain_diversity import (
    BUCKWHEAT_RECIPE_CODE,
    IDENTITY_ONLY_FOOD_CODES,
    RECIPE_CODES,
    RICE_RECIPE_CODE,
    WHEAT_GROATS_FOOD_CODE,
    WHEAT_RECIPE_CODE,
    seed_r2c_breakfast_grain_diversity,
)
from app.services.meal_plans import MealPlanService
from app.services.planner import (
    AuthoritativeGenerationRequest,
    GenerationMemberConstraints,
    PlannerService,
)

WEEK_START = date(2026, 11, 2)
EXISTING_BREAKFAST_CODES = {
    "HARD_BOILED_EGG",
    "SCHOOL2022_54_1O_NATURAL_OMELET",
    "SCHOOL2022_54_9K_MILK_OAT_PORRIDGE",
}


@pytest.fixture(scope="module")
def baseline(tmp_path_factory):
    config = DatabaseConfig(path=tmp_path_factory.mktemp("r2c-base") / "base.sqlite")
    seed_r2b_fish_main_diversity(config)
    return config


@pytest.fixture
def database(baseline, tmp_path):
    config = DatabaseConfig(path=tmp_path / "r2c.sqlite")
    shutil.copyfile(baseline.path, config.path)
    return config


def db_dump(config: DatabaseConfig) -> str:
    with sqlite3.connect(config.path) as db:
        return "\n".join(db.iterdump())


def meal_plan_service(engine) -> MealPlanService:
    return MealPlanService(
        write_scope_factory=lambda: SqlAlchemyMealPlanUnitOfWork(engine),
        read_scope_factory=lambda: SqlAlchemyMealPlanReadScope(engine),
        household_read_scope_factory=lambda: SqlAlchemyHouseholdReadScope(engine),
        pattern_read_scope_factory=lambda: SqlAlchemyMealPatternCatalogueReadScope(
            engine
        ),
    )


def production_planner(engine):
    meal_plans = meal_plan_service(engine)
    households = create_household_service(engine)
    catalogue = create_food_recipe_catalogue_service(engine)
    nutrition = create_nutrition_service(engine)
    pantry = create_pantry_service(engine)
    recipe_nutrition = create_recipe_nutrition_v2_service(engine)
    planner = PlannerService(
        meal_plans,
        households,
        catalogue,
        nutrition,
        pantry,
        PlannerConfig(version="planner-v0.4", max_recipe_repetitions=3),
        recipe_nutrition=recipe_nutrition,
    )
    return planner, meal_plans, households, catalogue


def create_breakfast_household(households, meal_plans, *, name: str):
    household = households.create_household(
        name=name,
        timezone_name="Europe/Moscow",
        city="Санкт-Петербург",
    )
    member = households.add_household_member(
        household.id,
        name="Анна",
        activity_level="active",
        goal="maintain",
        birth_date=date(1990, 5, 20),
        sex="female",
        height_cm=Decimal(168),
        weight_kg=Decimal(62),
    )
    selection = meal_plans.accept_member_pattern(
        household_id=household.id,
        member_id=member.id,
        source_kind=MemberMealPatternSourceKind.CUSTOM,
        schedule={weekday: (MealRole.BREAKFAST,) for weekday in range(1, 8)},
        energy_shares={weekday: (Decimal("0.30"),) for weekday in range(1, 8)},
    )
    return household, member, selection


def accepted_snapshot(config: DatabaseConfig):
    with sqlite3.connect(config.path) as db:
        return db.execute(
            """
            SELECT canonical_code, canonical_name, is_active
            FROM food_recipes
            WHERE canonical_code IN (
                'HARD_BOILED_EGG',
                'SCHOOL2022_54_1O_NATURAL_OMELET',
                'SCHOOL2022_54_9K_MILK_OAT_PORRIDGE',
                'BOILED_CHICKEN_MAIN_PRODUCT',
                'SCHOOL2022_54_29M_BEEF_MEATBALLS',
                'SCHOOL2022_54_2M_BEEF_GOULASH',
                'SCHOOL2022_54_6R_PINK_SALMON_IN_MILK',
                'SCHOOL2022_54_7R_POLLOCK_IN_MILK'
            )
            ORDER BY canonical_code
            """
        ).fetchall()


def test_r2c_fresh_publication_adds_three_grain_breakfasts_without_rewriting_corpus(
    database,
):
    before = accepted_snapshot(database)

    result = seed_r2c_breakfast_grain_diversity(database)

    assert result.identity_food_inserted == 1
    assert result.identity_food_existing == 0
    assert set(result.active_recipe_codes) == set(RECIPE_CODES)
    assert dict(result.authority_dispositions) == {
        WHEAT_RECIPE_CODE: "FRESH",
        BUCKWHEAT_RECIPE_CODE: "FRESH",
        RICE_RECIPE_CODE: "FRESH",
    }
    assert dict(result.exact_energy_kcal) == {
        WHEAT_RECIPE_CODE: Decimal("270.300000"),
        BUCKWHEAT_RECIPE_CODE: Decimal("187.300000"),
        RICE_RECIPE_CODE: Decimal("184.500000"),
    }

    engine = create_sqlite_engine(database)
    try:
        food = create_food_catalogue_service(engine)
        catalogue = create_food_recipe_catalogue_service(engine)
        nutrition = create_recipe_nutrition_v2_service(engine)
        expected = {
            WHEAT_RECIPE_CODE: Decimal("270.300000"),
            BUCKWHEAT_RECIPE_CODE: Decimal("187.300000"),
            RICE_RECIPE_CODE: Decimal("184.500000"),
        }
        for code, energy in expected.items():
            recipe = catalogue.get_by_code(code)
            assert recipe.is_active is True
            detail = catalogue.get_current_verified(recipe.id)
            assert detail.version.meal_type_code.value == "breakfast"
            assert detail.version.source_name == "ru-school2022"
            assert detail.version.source_output_g == Decimal(200)
            assert detail.version.cook_time_minutes is None
            if code == RICE_RECIPE_CODE:
                assert detail.ingredients[0].source_amount_text == (
                    "крупа рисовая: брутто 30,8 г; нетто 30,8 г"
                )
            assert all(
                "Температура подачи" not in step.instruction for step in detail.steps
            )

            projection = nutrition.neutral_consumption_projection(detail.version.id)
            assert (
                projection.authority_kind
                is RecipeNutritionAuthorityKind.PREPARED_OUTPUT_V1
            )
            assert projection.exact_energy_ready is True
            assert projection.per_base_serving.kcal == energy

            canonical = nutrition.prepared_canonical_nutrition(detail.version.id)
            assert canonical.status is RecipeNutritionV2Status.PARTIAL
            assert len(canonical.required_total) == len(NUTRIENT_CODES) == 54
            assert canonical.total_amount("ENERGY_KCAL") == energy
            unknown = tuple(
                item for item in canonical.required_total if item.code != "ENERGY_KCAL"
            )
            assert len(unknown) == 53
            assert all(
                item.amount is None and item.availability == "UNKNOWN"
                for item in unknown
            )
            with SqlAlchemyRecipeNutritionV2ReadScope(engine) as scope:
                authority = scope.prepared.get_authority(detail.version.id)
            assert authority is not None
            assert authority.output_mass_g == Decimal(200)

        for code in IDENTITY_ONLY_FOOD_CODES:
            assert food.get_by_code(code).is_active is True
        assert food.get_by_code("BUCKWHEAT").canonical_name == "Гречневая крупа"
        assert food.get_by_code("RICE_GROATS").canonical_name == "Крупа рисовая"
    finally:
        engine.dispose()

    with sqlite3.connect(database.path) as db:
        row = db.execute(
            """
            SELECT i.canonical_code,
                   (SELECT COUNT(*) FROM food_nutrition_profiles p
                    WHERE p.food_ingredient_id = i.id),
                   (SELECT COUNT(*) FROM food_composition_versions c
                    WHERE c.food_ingredient_id = i.id)
            FROM food_ingredients i
            WHERE i.canonical_code = ?
            """,
            (WHEAT_GROATS_FOOD_CODE,),
        ).fetchone()
        assert row == (WHEAT_GROATS_FOOD_CODE, 0, 0)
        assert db.execute("PRAGMA foreign_key_check").fetchall() == []

    assert migrations.expected_migration_ids()[-1] == "0043_shopping_engine"
    assert accepted_snapshot(database) == before


def test_r2c_exact_replay_is_zero_write(database):
    seed_r2c_breakfast_grain_diversity(database)
    before = db_dump(database)

    replay = seed_r2c_breakfast_grain_diversity(database)

    assert replay.identity_food_inserted == 0
    assert replay.identity_food_existing == 1
    assert dict(replay.authority_dispositions) == {
        WHEAT_RECIPE_CODE: "EXACT_REPLAY",
        BUCKWHEAT_RECIPE_CODE: "EXACT_REPLAY",
        RICE_RECIPE_CODE: "EXACT_REPLAY",
    }
    assert set(replay.active_recipe_codes) == set(RECIPE_CODES)
    assert db_dump(database) == before


def test_r2c_replay_preserves_deliberate_deactivation(database):
    seed_r2c_breakfast_grain_diversity(database)
    engine = create_sqlite_engine(database)
    try:
        catalogue = create_food_recipe_catalogue_service(engine)
        recipe = catalogue.get_by_code(WHEAT_RECIPE_CODE)
        catalogue.deactivate(recipe.id)
    finally:
        engine.dispose()

    replay = seed_r2c_breakfast_grain_diversity(database)

    assert WHEAT_RECIPE_CODE not in replay.active_recipe_codes
    assert BUCKWHEAT_RECIPE_CODE in replay.active_recipe_codes
    assert RICE_RECIPE_CODE in replay.active_recipe_codes


def test_r2c_authoritative_planner_persists_grain_diverse_breakfast_week(database):
    seed_r2c_breakfast_grain_diversity(database)
    engine = create_sqlite_engine(database)
    try:
        planner, meal_plans, households, catalogue = production_planner(engine)
        household, member, selection = create_breakfast_household(
            households, meal_plans, name="R2-C grain diversity"
        )
        grain_versions = frozenset(
            catalogue.get_current_verified(catalogue.get_by_code(code).id).version.id
            for code in RECIPE_CODES
        )
        command = AuthoritativeGenerationRequest(
            household.id,
            WEEK_START,
            (
                GenerationMemberConstraints(
                    member.id,
                    preferred_recipe_version_ids=grain_versions,
                ),
            ),
        )

        result, detail = planner.generate_authoritative(command)

        assert isinstance(result, PlannerSuccess)
        assert detail is not None
        assert detail.member_selections[0].selection_id == selection.selection.id

        breakfast_rows = {
            row.recipe_version_id: row.canonical_code
            for row in planner.compose_candidate_admission()
            if row.meal_type_code == "breakfast"
            and row.is_active
            and row.eligible
            and row.exact_energy_ready
        }
        assert set(breakfast_rows.values()) == EXISTING_BREAKFAST_CODES | set(
            RECIPE_CODES
        )
        assert len(breakfast_rows) == 6

        selected = Counter(
            breakfast_rows[event.recipe_version_id] for event in result.events
        )
        assert set(RECIPE_CODES).issubset(selected)
        assert sum(selected.values()) == 7
        assert max(selected.values()) <= 3

        persisted = meal_plans.get_current_plan(household.id, WEEK_START)
        assert persisted.plan.id == detail.plan.id
        assert len(persisted.events) == 7
        assert len(persisted.servings) == 7
        assert all(serving.portion_servings > 0 for serving in persisted.servings)
    finally:
        engine.dispose()


def test_r2c_wheat_exclusion_removes_only_wheat_candidate_and_week_stays_feasible(
    database,
):
    seed_r2c_breakfast_grain_diversity(database)
    engine = create_sqlite_engine(database)
    try:
        planner, meal_plans, households, catalogue = production_planner(engine)
        food = create_food_catalogue_service(engine)
        household, member, _ = create_breakfast_household(
            households, meal_plans, name="R2-C wheat exclusion"
        )
        wheat_id = food.get_by_code(WHEAT_GROATS_FOOD_CODE).id
        versions = {
            code: catalogue.get_current_verified(
                catalogue.get_by_code(code).id
            ).version.id
            for code in RECIPE_CODES
        }
        command = AuthoritativeGenerationRequest(
            household.id,
            WEEK_START,
            (
                GenerationMemberConstraints(
                    member.id,
                    excluded_food_ingredient_ids=frozenset({wheat_id}),
                    preferred_recipe_version_ids=frozenset(versions.values()),
                ),
            ),
        )

        result, detail = planner.generate_authoritative(command)

        assert isinstance(result, PlannerSuccess)
        assert detail is not None
        assert all(
            event.recipe_version_id != versions[WHEAT_RECIPE_CODE]
            for event in result.events
        )
        assert any(
            event.recipe_version_id == versions[BUCKWHEAT_RECIPE_CODE]
            for event in result.events
        )
        assert any(
            event.recipe_version_id == versions[RICE_RECIPE_CODE]
            for event in result.events
        )

        wheat_traces = [
            row
            for row in result.trace.candidates
            if row.recipe_version_id == versions[WHEAT_RECIPE_CODE]
        ]
        assert wheat_traces
        assert any(
            PlannerRejectionCode.MEMBER_EXCLUDED_INGREDIENT in row.rejection_codes
            for row in wheat_traces
        )
        for code in (BUCKWHEAT_RECIPE_CODE, RICE_RECIPE_CODE):
            unaffected = [
                row
                for row in result.trace.candidates
                if row.recipe_version_id == versions[code]
            ]
            assert unaffected
            assert all(
                PlannerRejectionCode.MEMBER_EXCLUDED_INGREDIENT
                not in row.rejection_codes
                for row in unaffected
            )

        persisted = meal_plans.get_current_plan(household.id, WEEK_START)
        assert persisted.plan.id == detail.plan.id
    finally:
        engine.dispose()
