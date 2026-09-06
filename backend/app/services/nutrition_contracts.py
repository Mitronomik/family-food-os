"""Read-only, driver-independent cross-context Nutrition input contracts."""

from types import TracebackType
from typing import Protocol, Self
from uuid import UUID

from app.domain.food_ingredients import FoodIngredient, FoodNutritionProfile
from app.domain.food_recipes import RecipeVersionDetail
from app.domain.households import HouseholdMember


from app.services.nutrition_evidence_contracts import NutritionEvidenceReader


class NutritionIngredientReader(Protocol):
    def get(self, ingredient_id: UUID) -> FoodIngredient | None: ...


class NutritionProfileReader(Protocol):
    def get_nutrition_profile_by_id(
        self, profile_id: UUID
    ) -> FoodNutritionProfile | None: ...

    def get_current(self, food_ingredient_id: UUID) -> FoodNutritionProfile | None: ...


class NutritionRecipeReader(Protocol):
    def get_detail(self, version_id: UUID) -> RecipeVersionDetail | None: ...


class NutritionMemberReader(Protocol):
    def get_member(
        self, household_id: UUID, member_id: UUID
    ) -> HouseholdMember | None: ...


class NutritionReadScope(Protocol):
    """All readers share one coherent view, closed on every exit path."""

    evidence: NutritionEvidenceReader
    ingredients: NutritionIngredientReader
    nutrition_profiles: NutritionProfileReader
    versions: NutritionRecipeReader
    members: NutritionMemberReader

    def __enter__(self) -> Self: ...
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None: ...
