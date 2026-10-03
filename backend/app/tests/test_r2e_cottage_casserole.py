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
from app.domain.planner import (
    PlannerConfig,
    PlannerFailure,
    PlannerFailureCode,
    PlannerRejectionCode,
    PlannerSuccess,
)
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
from app.seed.r1f_prepared_output import EGG_RECIPE_CODE
from app.seed.r2_breakfast_capacity import (
    MILK_FOOD_CODE,
    OAT_PORRIDGE_RECIPE_CODE,
    OMELET_RECIPE_CODE,
)
from app.seed.r2c_breakfast_grain_diversity import (
    BUCKWHEAT_RECIPE_CODE,
    RICE_RECIPE_CODE,
    WHEAT_RECIPE_CODE,
    seed_r2c_breakfast_grain_diversity,
)
from app.seed.r2e_cottage_casserole import (
    CASSEROLE_RECIPE_CODE,
    IDENTITY_ONLY_FOOD_CODES,
    REUSED_FOOD_CODES,
    seed_r2e_cottage_casserole,
)
from app.services.meal_plans import MealPlanNotFoundError, MealPlanService
from app.services.planner import (
    AuthoritativeGenerationRequest,
    GenerationMemberConstraints,
    PlannerService,
)

WEEK_START = date(2026, 11, 9)
EXISTING_BREAKFAST_CODES = {
    EGG_RECIPE_CODE,
    OMELET_RECIPE_CODE,
    OAT_PORRIDGE_RECIPE_CODE,
    WHEAT_RECIPE_CODE,
    BUCKWHEAT_RECIPE_CODE,
    RICE_RECIPE_CODE,
}
MILK_BREAKFAST_CODES = {
    OMELET_RECIPE_CODE,
    OAT_PORRIDGE_RECIPE_CODE,
    WHEAT_RECIPE_CODE,
    BUCKWHEAT_RECIPE_CODE,
    RICE_RECIPE_CODE,
}
EXPECTED_INGREDIENT_CODES = (
    "TVOROG_5",
    "SEMOLINA_GROATS",
    "SUGAR",
    "SOUR_CREAM_15",
    "BREADCRUMBS",
    "EGG",
    "BUTTER_PEASANT_72_5_UNSALTED",
    "SALT_IODIZED",
    "VANILLIN",
    "WATER",
)


@pytest.fixture(scope="module")
def baseline(tmp_path_factory):
    config = DatabaseConfig(path=tmp_path_factory.mktemp("r2e-base") / "base.sqlite")
    seed_r2c_breakfast_grain_diversity(config)
    return config


@pytest.fixture
def database(baseline, tmp_path):
    config = DatabaseConfig(path=tmp_path / "r2e.sqlite")
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


def accepted_recipe_snapshot(config: DatabaseConfig):
    with sqlite3.connect(config.path) as db:
        return db.execute(
            """
            SELECT canonical_code, canonical_name, is_active
            FROM food_recipes
            WHERE canonical_code != ?
            ORDER BY canonical_code
            """,
            (CASSEROLE_RECIPE_CODE,),
        ).fetchall()


def food_ids(config: DatabaseConfig, codes):
    placeholders = ",".join("?" for _ in codes)
    with sqlite3.connect(config.path) as db:
        return dict(
            db.execute(
                f"""
                SELECT canonical_code, id
                FROM food_ingredients
                WHERE canonical_code IN ({placeholders})
                ORDER BY canonical_code
                """,
                tuple(codes),
            ).fetchall()
        )


def test_r2e_fresh_publication_adds_casserole_without_rewriting_existing_corpus(
    database,
):
    before_recipes = accepted_recipe_snapshot(database)
    before_reused = food_ids(database, REUSED_FOOD_CODES)

    result = seed_r2e_cottage_casserole(database)

    assert result.identity_food_inserted == 4
    assert result.identity_food_existing == 0
    assert result.authority_disposition == "FRESH"
    assert result.active is True
    assert result.exact_energy_kcal == Decimal("301.200000")

    engine = create_sqlite_engine(database)
    try:
        food = create_food_catalogue_service(engine)
        catalogue = create_food_recipe_catalogue_service(engine)
        nutrition = create_recipe_nutrition_v2_service(engine)
        recipe = catalogue.get_by_code(CASSEROLE_RECIPE_CODE)
        assert recipe.is_active is True
        detail = catalogue.get_current_verified(recipe.id)
        assert detail.version.id == result.recipe_version_id
        assert detail.version.meal_type_code.value == "breakfast"
        assert detail.version.source_name == "ru-school2022"
        assert detail.version.source_recipe_id == "ru-school2022:recipe:54-1т"
        assert detail.version.source_output_g == Decimal("150.000000")
        assert detail.version.cook_time_minutes is None
        assert tuple(
            food.get(row.food_ingredient_id).canonical_code
            for row in detail.ingredients
        ) == EXPECTED_INGREDIENT_CODES
        assert tuple(row.quantity for row in detail.ingredients) == (
            Decimal("139.500000"),
            Decimal("9.700000"),
            Decimal("9.000000"),
            Decimal("5.200000"),
            Decimal("5.200000"),
            Decimal("4.000000"),
            Decimal("5.200000"),
            Decimal("0.400000"),
            Decimal("0.010000"),
            Decimal("36.000000"),
        )
        assert detail.ingredients[5].source_amount_text == (
            "яйцо куриное: брутто 4.4 г; нетто 4.0 г"
        )
        assert detail.ingredients[9].source_amount_text == (
            "вода: брутто 36 г; нетто 36 г"
        )
        assert all(
            "Температура подачи" not in step.instruction
            and "пароконвектомат" not in step.instruction.lower()
            for step in detail.steps
        )

        projection = nutrition.neutral_consumption_projection(detail.version.id)
        assert (
            projection.authority_kind
            is RecipeNutritionAuthorityKind.PREPARED_OUTPUT_V1
        )
        assert projection.exact_energy_ready is True
        assert projection.per_base_serving.kcal == Decimal("301.200000")

        canonical = nutrition.prepared_canonical_nutrition(detail.version.id)
        assert canonical.status is RecipeNutritionV2Status.PARTIAL
        assert len(canonical.required_total) == len(NUTRIENT_CODES) == 54
        assert canonical.total_amount("ENERGY_KCAL") == Decimal("301.200000")
        unknown = tuple(
            item for item in canonical.required_total if item.code != "ENERGY_KCAL"
        )
        assert len(unknown) == 53
        assert all(
            item.amount is None and item.availability == "UNKNOWN" for item in unknown
        )
        with SqlAlchemyRecipeNutritionV2ReadScope(engine) as scope:
            authority = scope.prepared.get_authority(detail.version.id)
        assert authority is not None
        assert authority.output_mass_g == Decimal("150.000000")

        for code in IDENTITY_ONLY_FOOD_CODES:
            assert food.get_by_code(code).is_active is True
    finally:
        engine.dispose()

    with sqlite3.connect(database.path) as db:
        for code in IDENTITY_ONLY_FOOD_CODES:
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
                (code,),
            ).fetchone()
            assert row == (code, 0, 0)
        assert db.execute("PRAGMA foreign_key_check").fetchall() == []

    assert food_ids(database, REUSED_FOOD_CODES) == before_reused
    assert migrations.expected_migration_ids()[-1] == (
        "0042_recipe_prepared_output_nutrition"
    )
    assert accepted_recipe_snapshot(database) == before_recipes


def test_r2e_exact_replay_is_zero_write(database):
    seed_r2e_cottage_casserole(database)
    before = db_dump(database)

    replay = seed_r2e_cottage_casserole(database)

    assert replay.identity_food_inserted == 0
    assert replay.identity_food_existing == 4
    assert replay.authority_disposition == "EXACT_REPLAY"
    assert replay.active is True
    assert db_dump(database) == before


def test_r2e_replay_preserves_deliberate_deactivation(database):
    seed_r2e_cottage_casserole(database)
    engine = create_sqlite_engine(database)
    try:
        catalogue = create_food_recipe_catalogue_service(engine)
        recipe = catalogue.get_by_code(CASSEROLE_RECIPE_CODE)
        catalogue.deactivate(recipe.id)
    finally:
        engine.dispose()
    before = db_dump(database)

    replay = seed_r2e_cottage_casserole(database)

    assert replay.authority_disposition == "EXACT_REPLAY"
    assert replay.active is False
    assert db_dump(database) == before


def test_r2e_authoritative_planner_uses_active_casserole(database):
    seed_r2e_cottage_casserole(database)
    engine = create_sqlite_engine(database)
    try:
        planner, meal_plans, households, catalogue = production_planner(engine)
        household, member, selection = create_breakfast_household(
            households, meal_plans, name="R2-E active casserole"
        )
        casserole_version = catalogue.get_current_verified(
            catalogue.get_by_code(CASSEROLE_RECIPE_CODE).id
        ).version.id
        command = AuthoritativeGenerationRequest(
            household.id,
            WEEK_START,
            (
                GenerationMemberConstraints(
                    member.id,
                    preferred_recipe_version_ids=frozenset({casserole_version}),
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
        assert set(breakfast_rows.values()) == EXISTING_BREAKFAST_CODES | {
            CASSEROLE_RECIPE_CODE
        }
        assert len(breakfast_rows) == 7

        selected = Counter(
            breakfast_rows[event.recipe_version_id] for event in result.events
        )
        assert selected[CASSEROLE_RECIPE_CODE] >= 1
        assert selected[CASSEROLE_RECIPE_CODE] <= 3
        assert sum(selected.values()) == 7
        assert max(selected.values()) <= 3

        persisted = meal_plans.get_current_plan(household.id, WEEK_START)
        assert persisted.plan.id == detail.plan.id
        assert len(persisted.events) == 7
        assert len(persisted.servings) == 7
    finally:
        engine.dispose()


def test_r2e_milk_exclusion_leaves_two_candidates_but_six_capacity_no_partial_plan(
    database,
):
    seed_r2e_cottage_casserole(database)
    engine = create_sqlite_engine(database)
    try:
        planner, meal_plans, households, catalogue = production_planner(engine)
        food = create_food_catalogue_service(engine)
        household, member, _ = create_breakfast_household(
            households, meal_plans, name="R2-E milk exclusion"
        )
        milk_id = food.get_by_code(MILK_FOOD_CODE).id
        command = AuthoritativeGenerationRequest(
            household.id,
            WEEK_START,
            (
                GenerationMemberConstraints(
                    member.id,
                    excluded_food_ingredient_ids=frozenset({milk_id}),
                ),
            ),
        )

        result, detail = planner.generate_authoritative(command)

        assert isinstance(result, PlannerFailure)
        assert result.code is PlannerFailureCode.NO_ELIGIBLE_CANDIDATE
        assert detail is None
        with pytest.raises(MealPlanNotFoundError):
            meal_plans.get_current_plan(household.id, WEEK_START)

        versions = {
            code: catalogue.get_current_verified(
                catalogue.get_by_code(code).id
            ).version.id
            for code in EXISTING_BREAKFAST_CODES | {CASSEROLE_RECIPE_CODE}
        }

        for code in MILK_BREAKFAST_CODES:
            traces = [
                row
                for row in result.trace.candidates
                if row.recipe_version_id == versions[code]
            ]
            assert traces
            assert any(
                PlannerRejectionCode.MEMBER_EXCLUDED_INGREDIENT in row.rejection_codes
                for row in traces
            )

        for code in (EGG_RECIPE_CODE, CASSEROLE_RECIPE_CODE):
            traces = [
                row
                for row in result.trace.candidates
                if row.recipe_version_id == versions[code]
            ]
            assert traces
            assert all(
                PlannerRejectionCode.MEMBER_EXCLUDED_INGREDIENT
                not in row.rejection_codes
                for row in traces
            )
            assert any(
                PlannerRejectionCode.MAX_REPETITIONS in row.rejection_codes
                for row in traces
            )
    finally:
        engine.dispose()
