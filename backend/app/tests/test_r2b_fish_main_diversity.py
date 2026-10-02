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
from app.seed.r2_breakfast_capacity import seed_r2_breakfast_capacity
from app.seed.r2b_fish_main_diversity import (
    IDENTITY_ONLY_FOOD_CODES,
    PINK_SALMON_FOOD_CODE,
    PINK_SALMON_RECIPE_CODE,
    POLLOCK_RECIPE_CODE,
    RECIPE_CODES,
    seed_r2b_fish_main_diversity,
)
from app.services.meal_plans import MealPlanService
from app.services.planner import (
    AuthoritativeGenerationRequest,
    GenerationMemberConstraints,
    PlannerService,
)

WEEK_START = date(2026, 10, 26)
EXISTING_MAIN_CODES = {
    "BOILED_CHICKEN_MAIN_PRODUCT",
    "SCHOOL2022_54_29M_BEEF_MEATBALLS",
    "SCHOOL2022_54_2M_BEEF_GOULASH",
}


@pytest.fixture(scope="module")
def baseline(tmp_path_factory):
    config = DatabaseConfig(path=tmp_path_factory.mktemp("r2b-base") / "base.sqlite")
    seed_r2_breakfast_capacity(config)
    return config


@pytest.fixture
def database(baseline, tmp_path):
    config = DatabaseConfig(path=tmp_path / "r2b.sqlite")
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


def create_dinner_household(households, meal_plans, *, name: str):
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
        schedule={weekday: (MealRole.DINNER,) for weekday in range(1, 8)},
        energy_shares={weekday: (Decimal("0.25"),) for weekday in range(1, 8)},
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
                'SCHOOL2022_54_2M_BEEF_GOULASH'
            )
            ORDER BY canonical_code
            """
        ).fetchall()


def test_r2b_fresh_publication_adds_fish_mains_without_rewriting_accepted_corpus(
    database,
):
    before = accepted_snapshot(database)

    result = seed_r2b_fish_main_diversity(database)

    assert result.identity_food_inserted == 2
    assert result.identity_food_existing == 0
    assert set(result.active_recipe_codes) == set(RECIPE_CODES)
    assert dict(result.authority_dispositions) == {
        PINK_SALMON_RECIPE_CODE: "FRESH",
        POLLOCK_RECIPE_CODE: "FRESH",
    }
    assert dict(result.exact_energy_kcal) == {
        PINK_SALMON_RECIPE_CODE: Decimal("144.800000"),
        POLLOCK_RECIPE_CODE: Decimal("105.300000"),
    }

    engine = create_sqlite_engine(database)
    try:
        food = create_food_catalogue_service(engine)
        catalogue = create_food_recipe_catalogue_service(engine)
        nutrition = create_recipe_nutrition_v2_service(engine)
        expected = {
            PINK_SALMON_RECIPE_CODE: (Decimal(80), Decimal("144.800000")),
            POLLOCK_RECIPE_CODE: (Decimal(80), Decimal("105.300000")),
        }
        for code, (output_g, energy) in expected.items():
            recipe = catalogue.get_by_code(code)
            assert recipe.is_active is True
            detail = catalogue.get_current_verified(recipe.id)
            assert detail.version.meal_type_code.value == "main"
            assert detail.version.source_name == "ru-school2022"
            assert detail.version.source_output_g == output_g
            assert detail.version.cook_time_minutes is None
            assert all(
                "Температура подачи" not in step.instruction for step in detail.steps
            )
            assert all(
                "пароконвектомат" not in step.instruction for step in detail.steps
            )
            assert all(
                "размораживать" not in step.instruction.lower()
                for step in detail.steps
            )
            assert all(
                "филе горбуша" not in step.instruction.lower()
                and "филе минтай" not in step.instruction.lower()
                for step in detail.steps
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
            assert authority.output_mass_g == output_g

        for code in IDENTITY_ONLY_FOOD_CODES:
            assert food.get_by_code(code).is_active is True
    finally:
        engine.dispose()

    with sqlite3.connect(database.path) as db:
        rows = db.execute(
            f"""
            SELECT i.canonical_code,
                   (SELECT COUNT(*) FROM food_nutrition_profiles p
                    WHERE p.food_ingredient_id = i.id),
                   (SELECT COUNT(*) FROM food_composition_versions c
                    WHERE c.food_ingredient_id = i.id)
            FROM food_ingredients i
            WHERE i.canonical_code IN ({",".join("?" for _ in IDENTITY_ONLY_FOOD_CODES)})
            ORDER BY i.canonical_code
            """,
            IDENTITY_ONLY_FOOD_CODES,
        ).fetchall()
        assert len(rows) == 2
        assert all(
            profile_count == 0 and composition_count == 0
            for _, profile_count, composition_count in rows
        )
        assert db.execute("PRAGMA foreign_key_check").fetchall() == []

    assert migrations.expected_migration_ids()[-1] == (
        "0042_recipe_prepared_output_nutrition"
    )
    assert accepted_snapshot(database) == before


def test_r2b_exact_replay_is_zero_write(database):
    seed_r2b_fish_main_diversity(database)
    before = db_dump(database)

    replay = seed_r2b_fish_main_diversity(database)

    assert replay.identity_food_inserted == 0
    assert replay.identity_food_existing == 2
    assert dict(replay.authority_dispositions) == {
        PINK_SALMON_RECIPE_CODE: "EXACT_REPLAY",
        POLLOCK_RECIPE_CODE: "EXACT_REPLAY",
    }
    assert set(replay.active_recipe_codes) == set(RECIPE_CODES)
    assert db_dump(database) == before


def test_r2b_replay_preserves_deliberate_deactivation(database):
    seed_r2b_fish_main_diversity(database)
    engine = create_sqlite_engine(database)
    try:
        catalogue = create_food_recipe_catalogue_service(engine)
        recipe = catalogue.get_by_code(PINK_SALMON_RECIPE_CODE)
        catalogue.deactivate(recipe.id)
    finally:
        engine.dispose()

    replay = seed_r2b_fish_main_diversity(database)

    assert PINK_SALMON_RECIPE_CODE not in replay.active_recipe_codes
    assert POLLOCK_RECIPE_CODE in replay.active_recipe_codes


def test_r2b_authoritative_planner_persists_varied_main_week(database):
    seed_r2b_fish_main_diversity(database)
    engine = create_sqlite_engine(database)
    try:
        planner, meal_plans, households, catalogue = production_planner(engine)
        household, member, selection = create_dinner_household(
            households, meal_plans, name="R2-B fish diversity"
        )
        fish_versions = frozenset(
            catalogue.get_current_verified(catalogue.get_by_code(code).id).version.id
            for code in RECIPE_CODES
        )
        command = AuthoritativeGenerationRequest(
            household.id,
            WEEK_START,
            (
                GenerationMemberConstraints(
                    member.id,
                    preferred_recipe_version_ids=fish_versions,
                ),
            ),
        )

        result, detail = planner.generate_authoritative(command)

        assert isinstance(result, PlannerSuccess)
        assert detail is not None
        assert detail.member_selections[0].selection_id == selection.selection.id

        main_rows = {
            row.recipe_version_id: row.canonical_code
            for row in planner.compose_candidate_admission()
            if row.meal_type_code == "main"
            and row.is_active
            and row.eligible
            and row.exact_energy_ready
        }
        assert set(main_rows.values()) == EXISTING_MAIN_CODES | set(RECIPE_CODES)
        assert len(main_rows) == 5

        selected = Counter(
            main_rows[event.recipe_version_id] for event in result.events
        )
        assert PINK_SALMON_RECIPE_CODE in selected
        assert POLLOCK_RECIPE_CODE in selected
        assert sum(selected.values()) == 7
        assert max(selected.values()) <= 3

        persisted = meal_plans.get_current_plan(household.id, WEEK_START)
        assert persisted.plan.id == detail.plan.id
        assert len(persisted.events) == 7
        assert len(persisted.servings) == 7
        assert all(serving.portion_servings > 0 for serving in persisted.servings)
    finally:
        engine.dispose()


def test_r2b_fish_exclusion_removes_only_affected_candidate_and_week_stays_feasible(
    database,
):
    seed_r2b_fish_main_diversity(database)
    engine = create_sqlite_engine(database)
    try:
        planner, meal_plans, households, catalogue = production_planner(engine)
        food = create_food_catalogue_service(engine)
        household, member, _ = create_dinner_household(
            households, meal_plans, name="R2-B fish exclusion"
        )
        pink_id = food.get_by_code(PINK_SALMON_FOOD_CODE).id
        fish_versions = {
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
                    excluded_food_ingredient_ids=frozenset({pink_id}),
                    preferred_recipe_version_ids=frozenset(fish_versions.values()),
                ),
            ),
        )

        result, detail = planner.generate_authoritative(command)

        assert isinstance(result, PlannerSuccess)
        assert detail is not None
        assert all(
            event.recipe_version_id != fish_versions[PINK_SALMON_RECIPE_CODE]
            for event in result.events
        )
        assert any(
            event.recipe_version_id == fish_versions[POLLOCK_RECIPE_CODE]
            for event in result.events
        )

        pink_traces = [
            row
            for row in result.trace.candidates
            if row.recipe_version_id == fish_versions[PINK_SALMON_RECIPE_CODE]
        ]
        pollock_traces = [
            row
            for row in result.trace.candidates
            if row.recipe_version_id == fish_versions[POLLOCK_RECIPE_CODE]
        ]
        assert pink_traces
        assert any(
            PlannerRejectionCode.MEMBER_EXCLUDED_INGREDIENT in row.rejection_codes
            for row in pink_traces
        )
        assert pollock_traces
        assert all(
            PlannerRejectionCode.MEMBER_EXCLUDED_INGREDIENT not in row.rejection_codes
            for row in pollock_traces
        )

        persisted = meal_plans.get_current_plan(household.id, WEEK_START)
        assert persisted.plan.id == detail.plan.id
    finally:
        engine.dispose()
