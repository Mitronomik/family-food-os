"""On-demand Nutrition use cases; no writes, caches or runtime remote inputs."""

from collections.abc import Callable
from datetime import date
from decimal import Decimal
from uuid import UUID

from app.domain.nutrition import (
    IngredientNutrition,
    RecipeVersionNutrition,
    calculate_recipe_nutrition,
    scale_food_nutrition,
)
from app.domain.nutrition_targets import (
    MemberReferenceNutritionTarget,
    calculate_member_reference_target,
)
from app.domain.units import UnitCode
from app.services.nutrition_contracts import NutritionReadScope


class NutritionInputNotFoundError(LookupError):
    """The requested root input is absent from its authorized read scope."""


class NutritionService:
    def __init__(self, read_scope_factory: Callable[[], NutritionReadScope]) -> None:
        self._read = read_scope_factory

    def food_ingredient(
        self, ingredient_id: UUID, quantity: Decimal, unit: UnitCode = UnitCode.GRAM
    ) -> IngredientNutrition:
        with self._read() as scope:
            ingredient = scope.ingredients.get(ingredient_id)
            if ingredient is None:
                raise NutritionInputNotFoundError("FoodIngredient not found.")
            return scale_food_nutrition(
                ingredient,
                scope.nutrition_profiles.get_current(ingredient_id),
                quantity,
                unit,
            )

    def recipe_version(self, version_id: UUID) -> RecipeVersionNutrition:
        with self._read() as scope:
            detail = scope.versions.get_detail(version_id)
            if detail is None:
                raise NutritionInputNotFoundError("RecipeVersion not found.")
            ingredients = {}
            profiles = {}
            for ingredient_id in dict.fromkeys(
                row.food_ingredient_id for row in detail.ingredients
            ):
                ingredient = scope.ingredients.get(ingredient_id)
                if ingredient is not None:
                    ingredients[ingredient_id] = ingredient
                profile = scope.nutrition_profiles.get_current(ingredient_id)
                if profile is not None:
                    profiles[ingredient_id] = profile
            assessments, evidence, pinned_profiles = {}, {}, {}
            for row in detail.ingredients:
                assessment = scope.evidence.get_current_assessment(row.id)
                if assessment is None:
                    continue
                assessments[row.id] = assessment
                profile_id = assessment.nutrition_profile_id
                current = profiles.get(row.food_ingredient_id)
                if profile_id not in pinned_profiles:
                    pinned = (
                        current
                        if current is not None and current.id == profile_id
                        else scope.nutrition_profiles.get_nutrition_profile_by_id(
                            profile_id
                        )
                    )
                    if pinned is not None:
                        pinned_profiles[profile_id] = pinned
                evidence_id = assessment.measure_evidence_id
                if evidence_id is not None and evidence_id not in evidence:
                    measure = scope.evidence.get_evidence(evidence_id)
                    if measure is not None:
                        evidence[evidence_id] = measure
            return calculate_recipe_nutrition(
                detail, ingredients, profiles, assessments, evidence, pinned_profiles
            )

    def member_reference_target(
        self, household_id: UUID, member_id: UUID, *, as_of_date: date
    ) -> MemberReferenceNutritionTarget:
        with self._read() as scope:
            member = scope.members.get_member(household_id, member_id)
            if member is None:
                raise NutritionInputNotFoundError(
                    "HouseholdMember not found in household scope."
                )
            return calculate_member_reference_target(member, as_of_date=as_of_date)
