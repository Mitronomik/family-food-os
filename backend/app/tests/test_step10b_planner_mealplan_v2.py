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
    RecipeIngredientCompositionBinding,
    RecipeNutritionV2Status,
)
from app.services.meal_plans import MealPlanNotFoundError
from app.services.planner import (
    AuthoritativeGenerationRequest,
    GenerationMemberConstraints,
    PlannerService,
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
        bindings=(
            RecipeIngredientCompositionBinding(
                recipe_ingredient_id=uid(40),
                composition_version_id=uid(41),
                registry_version=REGISTRY_VERSION,
                nutrient_set_version=NUTRIENT_SET_VERSION,
                composition_calculation_version=COMPOSITION_CALCULATION_VERSION,
                recipe_calculation_version=RECIPE_CALCULATION_VERSION,
                created_at=NOW,
            ),
        ),
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
    canonical_result = canonical(recipe_version_id)
    assert len(canonical_result.bindings) == 1
    projection = project_recipe_nutrition_consumption(canonical_result)

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


class _Households:
    def __init__(self, household_id: UUID, member_id: UUID) -> None:
        self.household_id = household_id
        self.member_id = member_id

    def get_household(self, household_id: UUID):
        assert household_id == self.household_id
        return type(
            "State",
            (),
            {
                "household": type("Household", (), {"id": household_id})(),
                "members": (
                    type(
                        "Member",
                        (),
                        {"id": self.member_id, "active": True},
                    )(),
                ),
            },
        )()


class _Recipes:
    def __init__(self, recipe_version_id: UUID) -> None:
        self.recipe_version_id = recipe_version_id
        self.recipe_id = uid(4)
        self.food_id = uid(5)

    def list_active(self, *, limit: int):
        assert limit == 200
        return (type("Recipe", (), {"id": self.recipe_id})(),)

    def get_current_verified(self, recipe_id: UUID):
        assert recipe_id == self.recipe_id
        version = type(
            "Version",
            (),
            {
                "id": self.recipe_version_id,
                "meal_type_code": MealTypeCode.MAIN,
                "total_time_minutes": 15,
                "batch_friendly": False,
            },
        )()
        row = type("Row", (), {"food_ingredient_id": self.food_id})()
        return type("Detail", (), {"version": version, "ingredients": (row,)})()


class _ReferenceNutrition:
    def member_reference_target(self, household_id, member_id, *, as_of_date):
        del household_id, member_id, as_of_date
        return type("Target", (), {"reference_energy_kcal": Decimal("2000")})()


class _ProjectionNutrition:
    def __init__(self, projection) -> None:
        self.projection = projection

    def neutral_consumption_projection(self, recipe_version_id: UUID):
        assert recipe_version_id == self.projection.recipe_version_id
        return self.projection


class _Pantry:
    def list_items(self, household_id: UUID):
        del household_id
        return ()


class _MealPlans:
    def __init__(self, household_id: UUID, member_id: UUID) -> None:
        self.household_id = household_id
        self.member_id = member_id
        self.selection = selection(member_id)
        self.created: MealPlanDetail | None = None

    def get_current_member_pattern(self, household_id: UUID, member_id: UUID):
        assert household_id == self.household_id
        assert member_id == self.member_id
        return self.selection

    def get_current_plan(self, household_id: UUID, week_start: date):
        del household_id, week_start
        raise MealPlanNotFoundError()

    def create_plan_revision(
        self,
        *,
        household_id: UUID,
        week_start: date,
        member_selection_ids,
        events,
        config_version: str,
        **kwargs,
    ) -> MealPlanDetail:
        del kwargs
        assert household_id == self.household_id
        assert member_selection_ids == {
            self.member_id: self.selection.selection.id
        }
        plan_id = uid(200)
        plan = MealPlan(
            plan_id,
            household_id,
            week_start,
            1,
            MealPlanStatus.CONFIRMED,
            config_version,
            None,
            NOW,
        )
        domain_events = []
        servings = []
        for index, event in enumerate(events, start=1):
            event_id = uid(200 + index)
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
            for participant_id, portion in event.servings.items():
                servings.append(
                    Serving(
                        uid(2000 + len(servings)),
                        event_id,
                        participant_id,
                        portion,
                        NOW,
                    )
                )
        self.created = MealPlanDetail(
            plan,
            (
                MealPlanMemberSelection(
                    plan_id,
                    self.member_id,
                    self.selection.selection.id,
                ),
            ),
            tuple(domain_events),
            tuple(servings),
        )
        return self.created


def test_application_service_full_v2_chain_uses_neutral_projection() -> None:
    household_id = uid(1)
    member_id = uid(2)
    recipe_version_id = uid(3)
    canonical_result = canonical(recipe_version_id)
    projection = project_recipe_nutrition_consumption(canonical_result)
    meal_plans = _MealPlans(household_id, member_id)
    planner = PlannerService(
        meal_plans,
        _Households(household_id, member_id),
        _Recipes(recipe_version_id),
        _ReferenceNutrition(),
        _Pantry(),
        PlannerConfig(max_recipe_repetitions=10),
        recipe_nutrition=_ProjectionNutrition(projection),
    )
    result, detail = planner.generate_authoritative(
        AuthoritativeGenerationRequest(
            household_id,
            WEEK_START,
            (GenerationMemberConstraints(member_id),),
        )
    )

    assert isinstance(result, PlannerSuccess)
    assert detail is meal_plans.created
    assert detail is not None
    assert detail.plan.config_version == "planner-v0.3"
    assert result.trace.compatibility_version == "meal-role-recipe-v2"
    assert all(
        event.recipe_version_id == recipe_version_id for event in detail.events
    )

    nutrition = calculate_meal_plan_nutrition(
        detail,
        {recipe_version_id: projection},
    )
    assert len(nutrition.servings) == 7
    assert all(
        item.status is NutritionStatus.INCOMPLETE
        and item.values.kcal is not None
        and item.values.carbohydrates_g is None
        for item in nutrition.servings
    )
    assert nutrition.member_weeks[0].status is NutritionStatus.INCOMPLETE
    assert nutrition.member_weeks[0].values.carbohydrates_g is None
