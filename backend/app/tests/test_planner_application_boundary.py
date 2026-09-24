from datetime import date
from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.domain.food_recipes import MealTypeCode
from app.domain.households import HouseholdState
from app.domain.meal_patterns import MealRole
from app.domain.nutrition import NutritionStatus, NutritionValues
from app.domain.planner import PlannerConfig
from app.services.meal_plans import MealPlanNotFoundError
from app.services.planner import (
    AuthoritativeGenerationRequest,
    GenerationMemberConstraints,
    MealPatternRecommenderService,
    PlannerAuthoritativeInputError,
    PlannerService,
    RecommenderRequest,
)
from app.tests.test_planner import selection, uid


class Households:
    def __init__(self, household_id, member_id):
        self.household_id, self.member_id = household_id, member_id

    def get_household(self, household_id):
        return HouseholdState(
            household=SimpleNamespace(id=self.household_id),
            members=(SimpleNamespace(id=self.member_id, active=True),),
        )


class Recipes:
    def __init__(self):
        self.current_id = uid(20)

    def list_active(self, *, limit):
        return [SimpleNamespace(id=uid(10))]

    def get_current_verified(self, recipe_id):
        version = SimpleNamespace(
            id=self.current_id,
            meal_type_code=MealTypeCode.MAIN,
            total_time_minutes=10,
            batch_friendly=False,
        )
        return SimpleNamespace(
            version=version, ingredients=(SimpleNamespace(food_ingredient_id=uid(50)),)
        )


class Nutrition:
    def __init__(self):
        self.kcal = Decimal("500")

    def member_reference_target(self, household_id, member_id, *, as_of_date):
        return SimpleNamespace(reference_energy_kcal=Decimal("2000"))

    def recipe_version(self, version_id):
        return SimpleNamespace(
            per_base_serving=NutritionValues(kcal=self.kcal),
            status=NutritionStatus.COMPLETE,
        )


class Pantry:
    def __init__(self):
        self.calls = []

    def list_items(self, household_id):
        self.calls.append(household_id)
        return [SimpleNamespace(food_ingredient_id=uid(50), quantity=Decimal("2"))]


class MealPlans:
    def __init__(self, household_id, member_id):
        self.selection = selection(member_id, (MealRole.DINNER,))
        object.__setattr__(self.selection.selection, "household_id", household_id)
        self.prior = None
        self.writes = []

    def get_current_member_pattern(self, household_id, member_id):
        return self.selection

    def get_current_plan(self, household_id, week_start):
        if self.prior is None:
            raise MealPlanNotFoundError()
        return self.prior

    def create_plan_revision(self, **kwargs):
        self.writes.append(kwargs)
        return SimpleNamespace()


def service():
    household_id, member_id = uid(1), uid(2)
    meals = MealPlans(household_id, member_id)
    pantry = Pantry()
    recipes = Recipes()
    nutrition = Nutrition()
    planner = PlannerService(
        meals,
        Households(household_id, member_id),
        recipes,
        nutrition,
        pantry,
        PlannerConfig(max_recipe_repetitions=10),
    )
    command = AuthoritativeGenerationRequest(
        household_id, date(2026, 9, 14), (GenerationMemberConstraints(member_id),)
    )
    return planner, command, meals, pantry, recipes, nutrition


def test_authoritative_composition_owns_selection_recipe_nutrition_and_pantry() -> None:
    planner, command, _, pantry, recipes, nutrition = service()
    request = planner.compose_authoritative_request(command)
    assert (
        request.members[0].selection.selection.id
        == selection(uid(2), (MealRole.DINNER,)).selection.id
    )
    assert request.candidates[0].recipe_version_id == recipes.current_id
    assert request.candidates[0].kcal_per_serving == nutrition.kcal
    assert request.candidates[0].is_verified is True
    assert request.pantry_food_ingredient_ids == frozenset({uid(50)})
    assert pantry.calls == [uid(1)]


def test_caller_cannot_supply_stale_recipe_or_fabricated_kcal() -> None:
    _, command, *_ = service()
    assert not hasattr(command, "candidates")
    assert not hasattr(command, "kcal_per_serving")


def test_wrong_household_member_and_selection_fail_closed() -> None:
    planner, command, meals, *_ = service()
    with pytest.raises(PlannerAuthoritativeInputError):
        planner.compose_authoritative_request(
            AuthoritativeGenerationRequest(
                command.household_id,
                command.week_start,
                (GenerationMemberConstraints(uid(99)),),
            )
        )
    object.__setattr__(meals.selection.selection, "household_id", uid(99))
    with pytest.raises(PlannerAuthoritativeInputError, match="selection"):
        planner.compose_authoritative_request(command)


def test_previous_week_history_is_scoped_and_exact_revision_is_traced() -> None:
    planner, command, meals, *_ = service()
    plan_id = uid(70)
    meals.prior = SimpleNamespace(
        plan=SimpleNamespace(
            id=plan_id, household_id=command.household_id, week_start=date(2026, 9, 7)
        ),
        events=(SimpleNamespace(recipe_version_id=uid(20)),),
    )
    request = planner.compose_authoritative_request(command)
    assert request.recent_plan_ids == (plan_id,)
    assert request.recent_recipe_version_ids == (uid(20),)
    meals.prior.plan.household_id = uid(99)
    with pytest.raises(PlannerAuthoritativeInputError, match="MealPlan"):
        planner.compose_authoritative_request(command)


def test_infeasible_authoritative_generation_never_writes() -> None:
    planner, command, meals, _, _, nutrition = service()
    nutrition.kcal = None
    result, detail = planner.generate_authoritative(command)
    assert detail is None and result.trace.failure_code is not None
    assert meals.writes == []


def test_authoritative_generation_does_not_enable_reference_pins_by_default() -> None:
    planner, command, meals, *_ = service()

    result, detail = planner.generate_authoritative(command)

    assert result.trace.failure_code is None
    assert detail is not None
    assert len(meals.writes) == 1
    assert "reference_methodology_selection_ids" not in meals.writes[0]


class Catalogue:
    def __init__(self, programs):
        self.programs = programs
        self.calls = 0

    def list_eligible(self, query):
        self.calls += 1
        return SimpleNamespace(programs=self.programs)


def test_catalogue_backed_recommender_has_stable_evidence_and_never_accepts_objects() -> (
    None
):
    detail = SimpleNamespace(
        program=SimpleNamespace(id=uid(80)),
        version=SimpleNamespace(id=uid(81)),
        tags=(),
    )
    catalogue = Catalogue((detail,))
    recommender = MealPatternRecommenderService(catalogue)
    first = recommender.recommend(RecommenderRequest(age_years=35))
    second = recommender.recommend(RecommenderRequest(age_years=35))
    assert first == second
    assert first.rankings[0].reasons == ("PUBLISHED_AGE_ELIGIBLE",)
    assert catalogue.calls == 2
    assert not hasattr(recommender, "accept_member_pattern")
    medical = recommender.recommend(
        RecommenderRequest(age_years=35, medical_or_therapeutic_request=True)
    )
    assert medical.unsupported_reason == "MEDICAL_OR_THERAPEUTIC_REQUEST_UNSUPPORTED"
