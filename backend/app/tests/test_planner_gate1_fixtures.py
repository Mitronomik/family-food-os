"""Repository-backed authoritative PR8 evidence; Gate 1 remains separate."""

from datetime import date, timedelta
from decimal import Decimal

from app.db.config import DatabaseConfig
from app.domain.meal_patterns import MealRole
from app.domain.meal_plans import MemberMealPatternSourceKind, MealSourceKind
from app.domain.planner import PlannerFailure, PlannerFailureCode
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
from app.seed.food_recipes import seed_food_recipes
from app.seed.nutrition_measure_evidence import seed_nutrition_measure_evidence
from app.services.meal_plans import MealEventDraft, MealPlanService
from app.services.planner import (
    AuthoritativeGenerationRequest,
    GenerationMemberConstraints,
    PlannerService,
)


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
    seed_food_recipes(config)
    seed_nutrition_measure_evidence(config)
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
        assert len(verified) == 30
        assert len(load_ingredient_seeds()) >= 80
        assert all(
            nutrition.recipe_version(item.version.id).per_base_serving.kcal is None
            for item in verified
        )

        outcomes = []
        shapes = (
            ((MealRole.DINNER,),),
            ((MealRole.BREAKFAST, MealRole.DINNER), (MealRole.DINNER,)),
            (
                (MealRole.BREAKFAST, MealRole.LUNCH, MealRole.DINNER),
                (MealRole.BREAKFAST, MealRole.DINNER),
                (MealRole.DINNER,),
            ),
        )
        for household_number, roles_by_member in enumerate(shapes, 1):
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
                schedule = {weekday: roles for weekday in range(1, 8)}
                meal_plans.accept_member_pattern(
                    household_id=household.id,
                    member_id=member.id,
                    source_kind=MemberMealPatternSourceKind.CUSTOM,
                    schedule=schedule,
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
                            verified[0].version.id,
                        )
                        for offset in range(7)
                    ],
                    config_version="fixture-history-v1",
                )
            before_history = (
                meal_plans.get_current_plan(
                    household.id, week_start - timedelta(weeks=1)
                ).plan.id
                if household_number == 1
                else None
            )
            result, persisted = planner.generate_authoritative(
                AuthoritativeGenerationRequest(
                    household.id,
                    week_start,
                    tuple(GenerationMemberConstraints(member.id) for member in members),
                )
            )
            assert persisted is None
            assert isinstance(result, PlannerFailure)
            assert result.code is PlannerFailureCode.NO_ELIGIBLE_CANDIDATE
            assert len(result.trace.candidate_pool_ids) == 30
            assert all(item.rejection_codes for item in result.trace.candidates)
            assert result.trace.recent_plan_ids == (
                () if before_history is None else (before_history,)
            )
            repeated, _ = planner.generate_authoritative(
                AuthoritativeGenerationRequest(
                    household.id,
                    week_start,
                    tuple(GenerationMemberConstraints(member.id) for member in members),
                )
            )
            assert repeated.trace.fingerprint == result.trace.fingerprint
            outcomes.append(result)
        assert len(outcomes) == 3
    finally:
        engine.dispose()
