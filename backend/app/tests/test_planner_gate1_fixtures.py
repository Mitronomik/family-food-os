"""Repository-backed Gate 1 proof using the bounded Russian corpus."""

from datetime import date, timedelta
from decimal import Decimal

from app.db.config import DatabaseConfig
from app.domain.meal_patterns import MealRole
from app.domain.meal_plans import MemberMealPatternSourceKind, MealSourceKind
from app.domain.planner import (
    PlannerConfig,
    PlannerRejectionCode,
    PlannerSuccess,
    generate_week,
)
from app.persistence.sqlalchemy_core.b2b2 import B2B2UnitOfWork
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
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
from app.seed.food_ingredients import load_seed_entries as load_ingredient_seeds
from app.seed.gate1_ru_corpus import seed_gate1_ru_corpus
from app.services.meal_plans import MealEventDraft, MealPlanService
from app.services.planner import (
    AuthoritativeGenerationRequest,
    GenerationMemberConstraints,
    PlannerService,
)
from scripts.audit_gate1a_readiness import seed_current
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


def test_three_gate1_households_use_authoritative_application_boundary(
    tmp_path,
) -> None:
    config = DatabaseConfig(path=tmp_path / "planner-gate1.sqlite")
    seed_current(config)
    seed_gate1_ru_corpus(config)

    engine = create_sqlite_engine(config)
    try:
        households = create_household_service(engine)
        recipes = create_food_recipe_catalogue_service(engine)
        nutrition = create_nutrition_service(engine)
        pantry = create_pantry_service(engine)
        meal_plans = meal_plan_service(engine)
        planner = PlannerService(meal_plans, households, recipes, nutrition, pantry)

        verified = [
            recipes.get_current_verified(recipe.id)
            for recipe in recipes.list_active(limit=100)
        ]
        assert len(verified) == 38
        assert len(load_ingredient_seeds()) >= 80

        by_code = {
            recipe.canonical_code: recipes.get_current_verified(recipe.id)
            for recipe in recipes.list_active(limit=100)
        }
        assert RU_CODES <= set(by_code)
        ru_results = {
            code: nutrition.recipe_version(by_code[code].version.id)
            for code in RU_CODES
        }
        assert all(
            result.per_base_serving.kcal is not None
            and result.per_base_serving.kcal > 0
            for result in ru_results.values()
        )

        with B2B2UnitOfWork(engine) as scope:
            chicken = scope.ingredients.get_by_code("CHICKEN_CATEGORY_I")
            assert chicken is not None
        chicken_recipe_ids = {
            by_code["RU82_697_BOILED_CHICKEN"].version.id,
            by_code["RU82_720_CHICKEN_KIEV"].version.id,
        }

        outcomes = []
        for household_number, roles_by_member in enumerate(GATE1_ROLE_SHAPES, 1):
            household = households.create_household(
                name=f"Семья {household_number}",
                timezone_name="Europe/Moscow",
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
                    household.id,
                    members[0].id,
                )
                prior_start = week_start - timedelta(weeks=1)
                history_recipe = by_code["RU82_697_BOILED_CHICKEN"]
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
                            history_recipe.version.id,
                        )
                        for offset in range(7)
                    ],
                    config_version="fixture-history-v1",
                )

            constraints = []
            for member_index, member in enumerate(members):
                exclusions = (
                    frozenset({chicken.id})
                    if household_number == 3 and member_index == 2
                    else frozenset()
                )
                constraints.append(
                    GenerationMemberConstraints(
                        member.id,
                        excluded_food_ingredient_ids=exclusions,
                    )
                )
            command = AuthoritativeGenerationRequest(
                household.id,
                week_start,
                tuple(constraints),
            )

            authoritative_request = planner.compose_authoritative_request(command)
            first = generate_week(authoritative_request, PlannerConfig())
            repeated = generate_week(authoritative_request, PlannerConfig())
            assert isinstance(first, PlannerSuccess)
            assert isinstance(repeated, PlannerSuccess)
            assert repeated.trace.fingerprint == first.trace.fingerprint

            result, persisted = planner.generate_authoritative(command)
            assert isinstance(result, PlannerSuccess)
            assert persisted is not None
            assert result.trace.fingerprint == first.trace.fingerprint
            assert result.trace.failure_code is None
            assert len(result.trace.candidate_pool_ids) == 38
            assert set(result.trace.selected_recipe_version_ids) <= {
                detail.version.id
                for detail in verified
                if (
                    nutrition.recipe_version(detail.version.id).per_base_serving.kcal
                    is not None
                )
            }

            horizon = {
                week_start + timedelta(days=offset) for offset in range(7)
            }
            assert {event.local_date for event in persisted.events} == horizon
            assert len(persisted.servings) == 7 * sum(
                len(roles) for roles in roles_by_member
            )
            assert all(
                isinstance(serving.portion_servings, Decimal)
                and serving.portion_servings > 0
                for serving in persisted.servings
            )
            current = meal_plans.get_current_plan(household.id, week_start)
            assert current.plan.id == persisted.plan.id

            if household_number == 1:
                assert len(result.trace.recent_plan_ids) == 1
            if household_number == 3:
                applied = dict(result.trace.applied_exclusions)
                assert applied[members[2].id] == (chicken.id,)
                assert any(
                    item.recipe_version_id in chicken_recipe_ids
                    and members[2].id in item.excluded_member_ids
                    and PlannerRejectionCode.MEMBER_EXCLUDED_INGREDIENT
                    in item.rejection_codes
                    for item in result.trace.candidates
                )

            outcomes.append((result, persisted))

        assert len(outcomes) == 3
    finally:
        engine.dispose()
