"""Repository-backed PR8 evidence; Gate 1 remains a separate review decision."""

from collections import Counter
from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import UUID

from app.db.config import DatabaseConfig
from app.domain.meal_patterns import MealRole
from app.domain.meal_plans import (
    MemberMealPatternOpportunitySnapshot,
    MemberMealPatternSelection,
    MemberMealPatternSelectionDetail,
    MemberMealPatternSourceKind,
)
from app.domain.planner import (
    MemberPlannerConstraints,
    PlannerCandidate,
    PlannerFailure,
    PlannerFailureCode,
    PlannerRequest,
    generate_week,
)
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
from app.persistence.sqlalchemy_core.food_recipe_composition import (
    create_food_recipe_catalogue_service,
)
from app.persistence.sqlalchemy_core.nutrition_composition import (
    create_nutrition_service,
)
from app.seed.food_ingredients import load_seed_entries as load_ingredient_seeds
from app.seed.food_recipes import seed_food_recipes
from app.seed.nutrition_measure_evidence import seed_nutrition_measure_evidence


def uid(number: int) -> UUID:
    return UUID(f"10000000-0000-4000-8000-{number:012d}")


def pattern(
    household_id: UUID, member_id: UUID, roles: tuple[MealRole, ...]
) -> MemberMealPatternSelectionDetail:
    now = datetime(2026, 9, 18, tzinfo=timezone.utc)
    selection_id = uid(100 + int(member_id.hex[-2:], 16))
    selected = MemberMealPatternSelection(
        selection_id,
        household_id,
        member_id,
        1,
        MemberMealPatternSourceKind.CUSTOM,
        None,
        None,
        False,
        now,
        None,
        now,
    )
    return MemberMealPatternSelectionDetail(
        selected,
        tuple(
            MemberMealPatternOpportunitySnapshot(selection_id, weekday, position, role)
            for weekday in range(1, 8)
            for position, role in enumerate(roles, start=1)
        ),
    )


def test_three_gate1_households_use_exact_repository_corpus_and_fail_explicitly_when_nutrition_is_unknown(
    tmp_path,
) -> None:
    config = DatabaseConfig(path=tmp_path / "planner-gate1.sqlite")
    seed_food_recipes(config)
    seed_nutrition_measure_evidence(config)
    engine = create_sqlite_engine(config)
    try:
        recipes = create_food_recipe_catalogue_service(engine)
        nutrition = create_nutrition_service(engine)
        candidates = []
        statuses = Counter()
        for recipe in recipes.list_active(limit=100):
            detail = recipes.get_current_verified(recipe.id)
            calculated = nutrition.recipe_version(detail.version.id)
            statuses[calculated.status] += 1
            candidates.append(
                PlannerCandidate(
                    recipe_version_id=detail.version.id,
                    meal_type_code=detail.version.meal_type_code,
                    food_ingredient_ids=frozenset(
                        row.food_ingredient_id for row in detail.ingredients
                    ),
                    kcal_per_serving=calculated.per_base_serving.kcal,
                    nutrition_status=calculated.status,
                    total_time_minutes=detail.version.total_time_minutes,
                    batch_friendly=detail.version.batch_friendly,
                )
            )
    finally:
        engine.dispose()

    assert len(load_ingredient_seeds()) >= 80
    assert len(candidates) == 30
    assert sum(statuses.values()) == 30
    outcomes = []
    for household_number, roles_by_member in enumerate(
        (
            ((MealRole.DINNER,),),
            ((MealRole.BREAKFAST, MealRole.DINNER), (MealRole.DINNER,)),
            (
                (MealRole.BREAKFAST, MealRole.LUNCH, MealRole.DINNER),
                (MealRole.BREAKFAST, MealRole.DINNER),
                (MealRole.DINNER,),
            ),
        ),
        start=1,
    ):
        household_id = uid(household_number)
        members = tuple(
            MemberPlannerConstraints(
                member_id := uid(household_number * 10 + index),
                pattern(household_id, member_id, roles),
                Decimal("2000") + Decimal(index * 200),
            )
            for index, roles in enumerate(roles_by_member, start=1)
        )
        outcomes.append(
            generate_week(
                PlannerRequest(
                    household_id, date(2026, 9, 14), members, tuple(candidates)
                )
            )
        )
    assert all(isinstance(outcome, PlannerFailure) for outcome in outcomes)
    assert {outcome.code for outcome in outcomes} == {
        PlannerFailureCode.NO_ELIGIBLE_CANDIDATE
    }
    assert all(outcome.trace.fingerprint for outcome in outcomes)
