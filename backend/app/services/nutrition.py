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
from app.domain.russian_reference_targets import (
    ReviewedRussianReferenceTable,
    RussianReferenceSelection,
    select_russian_reference_targets,
)


class NutritionInputNotFoundError(LookupError):
    """The requested root input is absent from its authorized read scope."""


class NutritionService:
    def __init__(
        self,
        read_scope_factory: Callable[[], NutritionReadScope],
        *,
        russian_reference_tables: Callable[[str], ReviewedRussianReferenceTable]
        | None = None,
    ) -> None:
        self._read = read_scope_factory
        self._russian_reference_tables = russian_reference_tables

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

    def russian_member_group_reference(
        self,
        household_id: UUID,
        member_id: UUID,
        *,
        as_of_date: date,
        methodology_version: str,
        physical_activity_coefficient: Decimal | None,
        definition_codes: tuple[str, ...],
    ) -> RussianReferenceSelection:
        """Explicit group-reference path; does not replace personalized NASEM v1.

        The table provider is a controlled publication boundary, not a consumer
        input. No implicit activity mapping or missing-table fallback is allowed.
        """
        if type(as_of_date) is not date:
            raise TypeError("Нужна явная календарная дата расчёта.")
        if self._russian_reference_tables is None:
            raise NutritionInputNotFoundError(
                "Проверенная российская таблица норм не подключена."
            )
        with self._read() as scope:
            member = scope.members.get_member(household_id, member_id)
            if (
                member is None
                or member.id != member_id
                or member.household_id != household_id
            ):
                raise NutritionInputNotFoundError(
                    "Участник семьи не найден в указанной семье."
                )
            table = self._russian_reference_tables(methodology_version)
            if (
                not isinstance(table, ReviewedRussianReferenceTable)
                or table.methodology_version != methodology_version
            ):
                raise ValueError("Версия таблицы не соответствует выбранной методике.")
            born = member.birth_date
            age = (
                None
                if born is None or born > as_of_date
                else (
                    as_of_date.year
                    - born.year
                    - ((as_of_date.month, as_of_date.day) < (born.month, born.day))
                )
            )
            return select_russian_reference_targets(
                table,
                age_years=age,
                sex=member.sex,
                physical_activity_coefficient=physical_activity_coefficient,
                life_stage="adult" if age is not None and age >= 18 else "child",
                definition_codes=definition_codes,
            )
