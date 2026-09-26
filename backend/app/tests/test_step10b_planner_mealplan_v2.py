"""Step 10-B cross-context Planner → MealPlan Nutrition integration."""

from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import UUID

from app.domain.food_recipes import MealTypeCode
from app.domain.meal_patterns import MealRole
from app.domain.meal_plans import (
    HouseholdMealEvent,
    MealPlan,
    MealPlanDetail,
    MealPlanMemberSelection,
    MealPlanStatus,
    MemberMealPatternOpportunitySnapshot,
    MemberMealPatternSelection,
    MemberMealPatternSelectionDetail,
    MemberMealPatternSourceKind,
    Serving,
    calculate_meal_plan_nutrition,
)
from app.domain.nutrition import NutritionStatus
from app.domain.planner import (
    MemberPlannerConstraints,
    PlannerCandidate,
    PlannerConfig,
    PlannerRequest,
    PlannerSuccess,
    generate_week,
)
from app.domain.recipe_nutrition_v2 import (
    COMPOSITION_CALCULATION_VERSION,
    NUTRIENT_CODES,
    NUTRIENT_SET_VERSION,
    RECIPE_CALCULATION_VERSION,
    REGISTRY_VERSION,
    CanonicalNutrientAmount,
    CanonicalRecipeVersionNutrition,
    RecipeNutritionV2Status,
)
from app.services.recipe_nutrition_v2 import project_recipe_nutrition_consumption

NOW = datetime(2026, 9, 26, tzinfo=timezone.utc)
WEEK_START = date(2026, 9, 28)


def uid(number: int) -> UUID:
    return UUID(f"00000000-0000-4000-8000-{number:012d}")


def selection(member_id: UUID) -> MemberMealPatternSelectionDetail:
    selection_id = uid(100)
    selected = MemberMealPatternSelection(
        selection_id,
        uid(1),
        member_id,
        1,
        MemberMealPatternSourceKind.CUSTOM,
        None,
        None,
        False,
        NOW,
        None,
        NOW,
    )
    opportunities = tuple(
        MemberMealPatternOpportunitySnapshot(
            selection_id, weekday, 1, MealRole.DINNER
        )
        for weekday in range(1, 8)
    )
    return MemberMealPatternSelectionDetail(selected, opportunities)


def canonical(recipe_version_id: UUID) -> CanonicalRecipeVersionNutrition:
    known = {
        "ENERGY_KCAL": Decimal("400.000000"),
        "PROTEIN": Decimal("30.000000"),
        "FAT_TOTAL": Decimal("10.000000"),
        "FIBER_TOTAL_DIETARY": Decimal("5.000000"),
    }
    values = tuple(
        CanonicalNutrientAmount(code, known.get(code)) for code in NUTRIENT_CODES
    )
    return CanonicalRecipeVersionNutrition(
        recipe_version_id=recipe_version_id,
        registry_version=REGISTRY_VERSION,
        nutrient_set_version=NUTRIENT_SET_VERSION,
        composition_calculation_version=COMPOSITION_CALCULATION_VERSION,
        recipe_calculation_version=RECIPE_CALCULATION_VERSION,
        bindings=(),
        required_total=values,
        per_base_serving=values,
        status=RecipeNutritionV2Status.PARTIAL,
        issues=(),
    )


def test_v2_exact_energy_flows_through_planner_mealplan_and_serving() -> None:
    household_id = uid(1)
    member_id = uid(2)
    recipe_version_id = uid(3)
    accepted = selection(member_id)
    projection = project_recipe_nutrition_consumption(canonical(recipe_version_id))

    assert projection.legacy_status is NutritionStatus.INCOMPLETE
    assert projection.exact_energy_ready is True
    assert projection.per_base_serving.carbohydrates_g is None

    request = PlannerRequest(
        household_id,
        WEEK_START,
        (
            MemberPlannerConstraints(
                member_id,
                accepted,
                Decimal("2000"),
            ),
        ),
        (
            PlannerCandidate(
                recipe_version_id,
                MealTypeCode.MAIN,
                frozenset(),
                projection.per_base_serving.kcal,
                projection.legacy_status,
                True,
                15,
                False,
                projection.exact_energy_ready,
            ),
        ),
    )
    planned = generate_week(
        request,
        PlannerConfig(max_recipe_repetitions=10),
    )
    assert isinstance(planned, PlannerSuccess)
    assert planned.trace.config_version == "planner-v0.3"
    assert planned.trace.compatibility_version == "meal-role-recipe-v2"
    assert len(planned.events) == 7

    plan_id = uid(10)
    domain_events = []
    servings = []
    for position, event in enumerate(planned.events, start=1):
        event_id = uid(20 + position)
        domain_events.append(
            HouseholdMealEvent(
                event_id,
                plan_id,
                event.local_date,
                event.position,
                event.role,
                event.source_kind,
                event.recipe_version_id,
                event.source_reference,
                NOW,
            )
        )
        servings.extend(
            Serving(
                uid(1000 + len(servings)),
                event_id,
                participant_id,
                portion,
                NOW,
            )
            for participant_id, portion in event.portions
        )

    detail = MealPlanDetail(
        MealPlan(
            plan_id,
            household_id,
            WEEK_START,
            1,
            MealPlanStatus.CONFIRMED,
            planned.trace.config_version,
            None,
            NOW,
        ),
        (
            MealPlanMemberSelection(
                plan_id,
                member_id,
                accepted.selection.id,
            ),
        ),
        tuple(domain_events),
        tuple(servings),
    )

    nutrition = calculate_meal_plan_nutrition(
        detail,
        {recipe_version_id: projection},
    )
    assert len(nutrition.servings) == 7
    assert len(nutrition.member_days) == 7
    assert len(nutrition.member_weeks) == 1
    assert all(
        item.status is NutritionStatus.INCOMPLETE
        and item.values.kcal is not None
        and item.values.protein_g is not None
        and item.values.fat_g is not None
        and item.values.fiber_g is not None
        and item.values.carbohydrates_g is None
        for item in nutrition.servings
    )
    assert all(
        item.status is NutritionStatus.INCOMPLETE
        and item.values.carbohydrates_g is None
        for item in nutrition.member_days
    )
    assert nutrition.member_weeks[0].status is NutritionStatus.INCOMPLETE
    assert nutrition.member_weeks[0].values.carbohydrates_g is None
