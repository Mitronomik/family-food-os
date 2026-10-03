import shutil
import sqlite3
from collections import Counter
from datetime import date
from decimal import Decimal

import pytest
from app.db import migrations
from app.db.config import DatabaseConfig
from app.domain.food_recipes import MealTypeCode
from app.domain.meal_patterns import MealRole
from app.domain.meal_plans import MemberMealPatternSourceKind
from app.domain.planner import (
    ROLE_COMPATIBILITY_V1,
    PlannerConfig,
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
)
from app.seed.r2e_cottage_casserole import (
    CASSEROLE_RECIPE_CODE,
    seed_r2e_cottage_casserole,
)
from app.seed.r2f_cheese_sandwich import (
    CHEESE_SANDWICH_RECIPE_CODE,
    IDENTITY_ONLY_FOOD_CODES,
    seed_r2f_cheese_sandwich,
)
from app.services.meal_plans import MealPlanService
from app.services.planner import (
    AuthoritativeGenerationRequest,
    GenerationMemberConstraints,
    PlannerService,
)

WEEK_START = date(2026, 11, 16)

BREAKFAST_ONLY_CODES = {
    EGG_RECIPE_CODE,
    OMELET_RECIPE_CODE,
    OAT_PORRIDGE_RECIPE_CODE,
    WHEAT_RECIPE_CODE,
    BUCKWHEAT_RECIPE_CODE,
    RICE_RECIPE_CODE,
    CASSEROLE_RECIPE_CODE,
}
MILK_BREAKFAST_CODES = {
    OMELET_RECIPE_CODE,
    OAT_PORRIDGE_RECIPE_CODE,
    WHEAT_RECIPE_CODE,
    BUCKWHEAT_RECIPE_CODE,
    RICE_RECIPE_CODE,
}
MILK_UNAFFECTED_CODES = {
    EGG_RECIPE_CODE,
    CASSEROLE_RECIPE_CODE,
    CHEESE_SANDWICH_RECIPE_CODE,
}
EXPECTED_INGREDIENT_CODES = (
    "WHEAT_BREAD_PLAIN",
    "CHEESE_UNSPECIFIED",
)


@pytest.fixture(scope="module")
def baseline(tmp_path_factory):
    config = DatabaseConfig(path=tmp_path_factory.mktemp("r2f-base") / "base.sqlite")
    seed_r2e_cottage_casserole(config)
    return config


@pytest.fixture
def database(baseline, tmp_path):
    config = DatabaseConfig(path=tmp_path / "r2f.sqlite")
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


def test_r2f_fresh_publication_adds_cheese_sandwich_with_exact_prepared_authority(
    database,
):
    result = seed_r2f_cheese_sandwich(database)

    assert result.identity_food_inserted == 2
    assert result.identity_food_existing == 0
    assert result.authority_disposition == "FRESH"
    assert result.active is True
    assert result.exact_energy_kcal == Decimal("83.000000")

    engine = create_sqlite_engine(database)
    try:
        food = create_food_catalogue_service(engine)
        catalogue = create_food_recipe_catalogue_service(engine)
        nutrition = create_recipe_nutrition_v2_service(engine)

        recipe = catalogue.get_by_code(CHEESE_SANDWICH_RECIPE_CODE)
        assert recipe.is_active is True
        detail = catalogue.get_current_verified(recipe.id)
        assert detail.version.id == result.recipe_version_id
        assert detail.version.meal_type_code is MealTypeCode.SANDWICH
        assert detail.version.source_name == "sad28-hosted-kutkina2008-card3-cheese"
        assert (
            detail.version.source_recipe_id
            == "sad28-hosted:techcard:3:cheese-sandwich:20-10"
        )
        assert (
            detail.version.source_document_sha256
            == "77bc74917305adb0d4fee7a54910c9675068b1ec093a051f7c58bd34cc7dd27c"
        )
        assert detail.version.source_output_g == Decimal("30.000000")
        assert detail.version.cook_time_minutes is None
        assert (
            tuple(
                food.get(row.food_ingredient_id).canonical_code
                for row in detail.ingredients
            )
            == EXPECTED_INGREDIENT_CODES
        )
        assert tuple(row.quantity for row in detail.ingredients) == (
            Decimal("20.000000"),
            Decimal("10.000000"),
        )
        assert detail.ingredients[0].source_amount_text == (
            "Хлеб пшеничный: брутто 20 г; нетто 20 г"
        )
        assert detail.ingredients[1].source_amount_text == (
            "Сыр: брутто 11 г; нетто 10 г"
        )
        assert tuple(step.instruction for step in detail.steps) == (
            "На ломтик пшеничного хлеба положить кусочек сыра толщиной 3–4 мм.",
        )

        projection = nutrition.neutral_consumption_projection(detail.version.id)
        assert (
            projection.authority_kind is RecipeNutritionAuthorityKind.PREPARED_OUTPUT_V1
        )
        assert projection.exact_energy_ready is True
        assert projection.per_base_serving.kcal == Decimal("83.000000")

        canonical = nutrition.prepared_canonical_nutrition(detail.version.id)
        assert canonical.status is RecipeNutritionV2Status.PARTIAL
        assert len(canonical.required_total) == len(NUTRIENT_CODES) == 54
        assert canonical.total_amount("ENERGY_KCAL") == Decimal("83.000000")
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
        assert authority.output_mass_g == Decimal("30.000000")

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

        assert (
            db.execute(
                "SELECT COUNT(*) FROM food_ingredients WHERE canonical_code = ?",
                ("BUTTER_CREAM_UNSPECIFIED",),
            ).fetchone()[0]
            == 0
        )
        assert db.execute("PRAGMA foreign_key_check").fetchall() == []

    assert migrations.expected_migration_ids()[-1] == (
        "0042_recipe_prepared_output_nutrition"
    )


def test_r2f_exact_replay_is_zero_write(database):
    seed_r2f_cheese_sandwich(database)
    before = db_dump(database)

    replay = seed_r2f_cheese_sandwich(database)

    assert replay.identity_food_inserted == 0
    assert replay.identity_food_existing == 2
    assert replay.authority_disposition == "EXACT_REPLAY"
    assert replay.active is True
    assert db_dump(database) == before


def test_r2f_replay_preserves_deliberate_deactivation(database):
    seed_r2f_cheese_sandwich(database)
    engine = create_sqlite_engine(database)
    try:
        catalogue = create_food_recipe_catalogue_service(engine)
        recipe = catalogue.get_by_code(CHEESE_SANDWICH_RECIPE_CODE)
        catalogue.deactivate(recipe.id)
    finally:
        engine.dispose()
    before = db_dump(database)

    replay = seed_r2f_cheese_sandwich(database)

    assert replay.authority_disposition == "EXACT_REPLAY"
    assert replay.active is False
    assert db_dump(database) == before


def test_r2f_existing_role_compatibility_is_reused_without_mapping_change():
    assert MealTypeCode.SANDWICH in ROLE_COMPATIBILITY_V1[MealRole.BREAKFAST]
    assert MealTypeCode.SANDWICH in ROLE_COMPATIBILITY_V1[MealRole.LUNCH]
    assert MealTypeCode.SANDWICH in ROLE_COMPATIBILITY_V1[MealRole.SNACK]
    assert MealTypeCode.SANDWICH not in ROLE_COMPATIBILITY_V1[MealRole.DINNER]


def test_r2f_milk_exclusion_seven_breakfast_week_succeeds_with_capacity_nine(database):
    seed_r2f_cheese_sandwich(database)
    engine = create_sqlite_engine(database)
    try:
        planner, meal_plans, households, catalogue = production_planner(engine)
        food = create_food_catalogue_service(engine)
        household, member, selection = create_breakfast_household(
            households,
            meal_plans,
            name="R2-F milk exclusion closure",
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

        assert isinstance(result, PlannerSuccess)
        assert detail is not None
        assert detail.member_selections[0].selection_id == selection.selection.id

        expected_codes = BREAKFAST_ONLY_CODES | {CHEESE_SANDWICH_RECIPE_CODE}
        admissions = {
            row.recipe_version_id: row
            for row in planner.compose_candidate_admission()
            if row.canonical_code in expected_codes
        }
        selected = Counter(
            admissions[event.recipe_version_id].canonical_code for event in result.events
        )

        assert set(selected) == MILK_UNAFFECTED_CODES
        assert sum(selected.values()) == 7
        assert max(selected.values()) <= 3
        assert selected[CHEESE_SANDWICH_RECIPE_CODE] >= 1

        persisted = meal_plans.get_current_plan(household.id, WEEK_START)
        assert persisted.plan.id == detail.plan.id
        assert len(persisted.events) == 7
        assert len(persisted.servings) == 7

        versions = {
            code: catalogue.get_current_verified(
                catalogue.get_by_code(code).id
            ).version.id
            for code in expected_codes
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

        for code in MILK_UNAFFECTED_CODES:
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
    finally:
        engine.dispose()
