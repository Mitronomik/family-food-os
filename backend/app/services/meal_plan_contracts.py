"""Driver-independent contracts for Household MealPlan / Serving state."""

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from types import TracebackType
from typing import Protocol, Self
from uuid import UUID

from app.domain.meal_plans import (
    MealPlan,
    MealPlanDetail,
    MemberMealPatternSelection,
    MemberMealPatternSelectionDetail,
)
from app.services.household_contracts import HouseholdMemberRepository


@dataclass(frozen=True)
class DiagnosticIngredientFacts:
    """Database facts, not an admission verdict, for one recipe ingredient."""

    canonical_code: str
    quantity: Decimal
    unit: str
    default_unit: str
    optional: bool
    is_active: bool
    allergens_reviewed: bool
    allergen_codes: tuple[str, ...]


@dataclass(frozen=True)
class DiagnosticRecipeFacts:
    """One pinned RecipeVersion and its ingredient facts in the active UoW."""

    verification_status: str | None
    rights_review_status: str | None
    source_document_sha256: str | None
    is_active: bool
    ingredients: tuple[DiagnosticIngredientFacts, ...]

from app.services.reference_methodology_contracts import (
    MemberReferenceMethodologySelectionRepository,
)


class MemberMealPatternSelectionRepository(Protocol):
    def add_detail(self, detail: MemberMealPatternSelectionDetail) -> None: ...
    def get_detail(
        self, household_id: UUID, selection_id: UUID
    ) -> MemberMealPatternSelectionDetail | None: ...
    def get_current(
        self, household_id: UUID, member_id: UUID
    ) -> MemberMealPatternSelectionDetail | None: ...
    def list_history(
        self, household_id: UUID, member_id: UUID
    ) -> list[MemberMealPatternSelection]: ...


class MealPlanRepository(Protocol):
    def add_detail(self, detail: MealPlanDetail) -> None: ...
    def get_diagnostic_recipe_facts(
        self, version_ids: set[UUID]
    ) -> dict[UUID, DiagnosticRecipeFacts]: ...
    def get_diagnostic_rule_digests(
        self, identities: set[tuple[str, int]]
    ) -> dict[tuple[str, int], tuple[str, ...]]: ...
    def add_validated_diagnostic_detail(self, detail: MealPlanDetail) -> None: ...
    def get_detail(self, household_id: UUID, plan_id: UUID) -> MealPlanDetail | None: ...
    def get_current(
        self, household_id: UUID, week_start: date
    ) -> MealPlanDetail | None: ...
    def list_history(self, household_id: UUID, week_start: date) -> list[MealPlan]: ...


class MealPlanUnitOfWork(Protocol):
    selections: MemberMealPatternSelectionRepository
    plans: MealPlanRepository
    members: HouseholdMemberRepository
    reference_methodologies: MemberReferenceMethodologySelectionRepository

    def __enter__(self) -> Self: ...

    def guard_member_state(
        self,
        *,
        household_id: UUID,
        member_id: UUID,
        member_updated_at: datetime,
    ) -> None: ...

    def commit(self) -> None: ...
    def rollback(self) -> None: ...
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None: ...


class MealPlanReadScope(Protocol):
    selections: MemberMealPatternSelectionRepository
    plans: MealPlanRepository
    reference_methodologies: MemberReferenceMethodologySelectionRepository

    def __enter__(self) -> Self: ...
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None: ...


class MealPlanPersistenceError(RuntimeError):
    """Stable adapter-boundary error for expected MealPlan persistence failures."""


class MealPlanPersistenceConflictError(MealPlanPersistenceError):
    """A MealPlan write conflicted with persisted authoritative state."""
