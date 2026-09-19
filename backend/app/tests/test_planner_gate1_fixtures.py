"""Repository-backed Gate1 proof using the bounded Russian normative corpus."""

from datetime import date, timedelta
from decimal import Decimal

from app.db.config import DatabaseConfig
from app.domain.meal_patterns import MealRole
from app.domain.meal_plans import MemberMealPatternSourceKind, MealSourceKind
from app.domain.planner import PlannerRejectionCode, PlannerSuccess
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
from app.seed.b2b2 import upgrade_b2b2
from app.seed.food_recipes import seed_food_recipes
from app.seed.gate1_ru_corpus import seed_gate1_ru_corpus
from app.seed.nutrition_measure_evidence import seed_nutrition_measure_evidence
from app.seed.recipe_corrections import (
    seed_correction_assessments,
    seed_recipe_corrections,
)
from app.seed.ru_food_data import seed_ru_food_data
from app.services.meal_plans import MealEventDraft, MealPlanService
from app.services.planner import (
    AuthoritativeGenerationRequest,
    GenerationMemberConstraints,
    PlannerService,
)
from scripts.gate1a_fixture_spec import GATE1_ROLE_SHAPES


RU_CODES = {
    "RU82_467_OMELET_NATURAL",
    "RU82_492_SYRNIKI",
    "RU82_1081_BLINI",
    "RU82_208_RASSOLNIK_LENINGRAD",
    "RU82_263_MILK_SOUP_POTATO_DUMPLINGS",
    "RU82_462_FRIED_EGGS_POTATO",
    "RU82_697_BOILED_CHICKEN",
    "RU82_720_CHICKEN_KIEV",
}


def meal_plan_service(engine):
    return MealPlanService(
        lambda: SqlAlchemyMealPlanUnitOfWork(engine),
        lambda: SqlAlchemyMealPlanReadScope(engine),
        lambda: SqlAlchemyHouseholdReadScope(engine),
        lambda: SqlAlchemyMealPatternCatalogueReadScope(engine),
    )


def seed_current(config: DatabaseConfig) -> None:
    seed_food_recipes(config)
    seed_nutrition_measure_evidence(config)
    seed_recipe_corrections(config)
    seed_correction_assessments(config)
    seed_ru_food_data(config)
    upgrade_b2b2(config)
    seed_gate1_ru_corpus(config)


def test_three_gate1_households_complete_authoritative_week(
    tmp_path,
) -> None:
    config = DatabaseConfig(path=tmp_path / "planner-gate1.sqlite")
    seed_current(config)
    engine = create_sqlite_engine(config)
    try:
        households = create_household_service(engine)
        foods = create_food_catalogue_service(engine)
        recipes = create_food_recipe_catalogue_service(engine)
        nutrition = create_nutrition_service(engine)
        pantry = create_pantry_service(engine)
        meal_plans = meal_plan_service(engine)
        planner = PlannerService(meal_plans, households, recipes, nutrition, pantry)

        verified = [
            recipes.get_current_verified(recipe.id)
            for recipe in recipes.list_active(limit=200)
        ]
        assert len(verified) == 38
        assert len(foods.list_active(limit=200)) >= 80

        ru_details = {
            code: recipes.get_current_verified(recipes.get_by_code(code).id)
            for code in RU_CODES
        }
        assert all(
            nutrition.recipe_version(detail.version.id).per_base_serving.kcal
            is not None
            and nutrition.recipe_version(detail.version.id).per_base_serving.kcal
            > Decimal("0")
            for detail in ru_details.values()
        )
        # Historical FNS truth is not rewritten just to pass Gate1.
        old_fns = recipes.get_current_verified(
            recipes.get_by_code("FNS4_OVEN_FRIED_FISH").id
        )
        assert nutrition.recipe_version(old_fns.version.id).per_base_serving.kcal is None

        excluded_food = foods.get_by_code("CUCUMBER_PICKLED_SALTED")
        rassolnik_id = ru_details["RU82_208_RASSOLNIK_LENINGRAD"].version.id
        chicken_id = ru_details["RU82_697_BOILED_CHICKEN"].version.id

        outcomes = []
        for household_number, roles_by_member in enumerate(GATE1_ROLE_SHAPES, 1):
            household = households.create_household(
                name=f"Семья {household_number}", timezone_name="Europe/Moscow"
            )
            members = []
            for index, roles in enumerate(roles_by_member, 1):
                member = households.add_household_member(
                    household.id,
                    name=f"Участник {index}",
                    birth_date=date(1990, 1, index),
                    sex="female" if index % 2 else "male",
                    height_cm=Decimal("170"),
                    weight_kg=Decimal("65"),
                    activity_level="active",
                    goal="maintain",
                )
                meal_plans.accept_member_pattern(
                    household_id=household.id,
                    member_id=member.id,
                    source_kind=MemberMealPatternSourceKind.CUSTOM,
                    schedule={weekday: roles for weekday in range(1, 8)},
                )
                members.append(member)

            week_start = date(2026, 9, 14)
            if household_number == 1:
                current = meal_plans.get_current_member_pattern(
                    household.id, members[0].id
                )
                prior_start = week_start - timedelta(weeks=1)
                meal_plans.create_plan_revision(
                    household_id=household.id,
                    week_start=prior_start,
                    member_selection_ids={members[0].id: current.selection.id},
                    events=[
                        MealEventDraft(
                            prior_start + timedelta(days=offset),
                            1,
                            MealRole.DINNER,
                            MealSourceKind.COOK_RECIPE,
                            {members[0].id: Decimal("1")},
                            chicken_id,
                        )
                        for offset in range(7)
                    ],
                    config_version="fixture-history-v1",
                )

            constraints = tuple(
                GenerationMemberConstraints(
                    member.id,
                    excluded_food_ingredient_ids=(
                        frozenset({excluded_food.id})
                        if household_number == 1 and index == 0
                        else frozenset()
                    ),
                )
                for index, member in enumerate(members)
            )
            result, persisted = planner.generate_authoritative(
                AuthoritativeGenerationRequest(
                    household.id,
                    week_start,
                    constraints,
                )
            )
            assert isinstance(result, PlannerSuccess)
            assert persisted is not None
            assert result.trace.failure_code is None
            assert len(result.trace.candidate_pool_ids) == 38
            assert len(persisted.events) == 7 * len(
                {role for roles in roles_by_member for role in roles}
            )
            assert len(persisted.servings) == 7 * sum(
                len(roles) for roles in roles_by_member
            )
            assert persisted.servings
            assert all(
                isinstance(serving.portion_servings, Decimal)
                and serving.portion_servings > 0
                for serving in persisted.servings
            )
            assert all(
                event.recipe_version_id is not None for event in persisted.events
            )

            selected_ids = set(result.trace.selected_recipe_version_ids)
            assert selected_ids & {detail.version.id for detail in ru_details.values()}
            if household_number == 3:
                main_ids = {
                    ru_details[code].version.id
                    for code in {
                        "RU82_208_RASSOLNIK_LENINGRAD",
                        "RU82_263_MILK_SOUP_POTATO_DUMPLINGS",
                        "RU82_462_FRIED_EGGS_POTATO",
                        "RU82_697_BOILED_CHICKEN",
                        "RU82_720_CHICKEN_KIEV",
                    }
                }
                assert main_ids <= selected_ids

            if household_number == 1:
                rejected = [
                    item
                    for item in result.trace.candidates
                    if item.recipe_version_id == rassolnik_id
                ]
                assert rejected
                assert any(
                    PlannerRejectionCode.MEMBER_EXCLUDED_INGREDIENT
                    in item.rejection_codes
                    for item in rejected
                )
                assert result.trace.applied_exclusions == (
                    (members[0].id, (excluded_food.id,)),
                )
                assert len(result.trace.recent_plan_ids) == 1

            repeated, repeated_persisted = planner.generate_authoritative(
                AuthoritativeGenerationRequest(
                    household.id,
                    week_start,
                    constraints,
                )
            )
            assert isinstance(repeated, PlannerSuccess)
            assert repeated_persisted is not None
            assert repeated.trace.fingerprint == result.trace.fingerprint
            assert repeated.events == result.events
            outcomes.append(result)

        assert len(outcomes) == 3
    finally:
        engine.dispose()
