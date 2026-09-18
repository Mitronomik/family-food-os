"""Authoritative PR8 Planner composition and curated-program recommendation."""

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from time import perf_counter_ns
from uuid import UUID

from app.domain.meal_patterns import MealPatternTagKind
from app.domain.meal_plans import MealPlanDetail
from app.domain.planner import (
    FixedPlannerEvent,
    MemberPlannerConstraints,
    PlannerCandidate,
    PlannerConfig,
    PlannerFailure,
    PlannerRequest,
    PlannerResult,
    PlannerSuccess,
    generate_week,
    with_duration,
)
from app.services.food_recipes import FoodRecipeCatalogueService
from app.services.households import HouseholdService
from app.services.meal_patterns import MealPatternCatalogueService
from app.services.meal_plans import (
    MealEventDraft,
    MealPlanNotFoundError,
    MealPlanService,
)
from app.services.nutrition import NutritionService
from app.services.pantry import PantryService

RECOMMENDER_VERSION = "meal-pattern-recommender-v2"
HISTORY_HORIZON_WEEKS = 1


class PlannerAuthoritativeInputError(ValueError):
    pass


@dataclass(frozen=True)
class GenerationMemberConstraints:
    member_id: UUID
    excluded_food_ingredient_ids: frozenset[UUID] = frozenset()
    preferred_recipe_version_ids: frozenset[UUID] = frozenset()


@dataclass(frozen=True)
class AuthoritativeGenerationRequest:
    household_id: UUID
    week_start: date
    members: tuple[GenerationMemberConstraints, ...]
    fixed_events: tuple[FixedPlannerEvent, ...] = ()


@dataclass(frozen=True)
class RecommenderRequest:
    age_years: int | None
    goal_codes: frozenset[str] = frozenset()
    context_codes: frozenset[str] = frozenset()
    medical_or_therapeutic_request: bool = False


@dataclass(frozen=True)
class RecommendationEvidence:
    program_id: UUID
    version_id: UUID
    score: int
    reasons: tuple[str, ...]
    cautions: tuple[str, ...] = ()


@dataclass(frozen=True)
class RecommenderResult:
    version: str
    rankings: tuple[RecommendationEvidence, ...]
    unsupported_reason: str | None
    requires_user_acceptance: bool = True

    @property
    def ranked_program_version_ids(self) -> tuple[UUID, ...]:
        return tuple(item.version_id for item in self.rankings)


def _rank_published(request: RecommenderRequest, programs) -> RecommenderResult:
    if request.medical_or_therapeutic_request:
        return RecommenderResult(
            RECOMMENDER_VERSION, (), "MEDICAL_OR_THERAPEUTIC_REQUEST_UNSUPPORTED"
        )
    if request.age_years is None:
        return RecommenderResult(RECOMMENDER_VERSION, (), "AGE_REQUIRED_FOR_SAFETY")
    ranked = []
    for detail in programs:
        tags = {(tag.kind, tag.code) for tag in detail.tags}
        goal_matches = sorted(
            code
            for code in request.goal_codes
            if (MealPatternTagKind.GOAL, code) in tags
        )
        context_matches = sorted(
            code
            for code in request.context_codes
            if (MealPatternTagKind.CONTEXT, code) in tags
        )
        score = len(goal_matches) * 2 + len(context_matches)
        reasons = tuple(
            [
                *(f"GOAL_TAG:{code}" for code in goal_matches),
                *(f"CONTEXT_TAG:{code}" for code in context_matches),
            ]
        )
        ranked.append(
            RecommendationEvidence(
                detail.program.id,
                detail.version.id,
                score,
                reasons or ("PUBLISHED_AGE_ELIGIBLE",),
            )
        )
    ranked.sort(
        key=lambda item: (-item.score, item.program_id.hex, item.version_id.hex)
    )
    return RecommenderResult(
        RECOMMENDER_VERSION,
        tuple(ranked),
        None if ranked else "NO_ELIGIBLE_CURATED_PROGRAM",
    )


def recommend_patterns(request: RecommenderRequest, programs) -> RecommenderResult:
    """Pure ranking helper; production callers use MealPatternRecommenderService."""
    return _rank_published(request, programs)


class MealPatternRecommenderService:
    """Reads only current published catalogue truth and never accepts a program object."""

    def __init__(self, catalogue: MealPatternCatalogueService) -> None:
        self._catalogue = catalogue

    def recommend(self, request: RecommenderRequest) -> RecommenderResult:
        if request.medical_or_therapeutic_request or request.age_years is None:
            return _rank_published(request, ())
        from app.domain.meal_patterns import MealPatternEligibilityQuery

        eligible = self._catalogue.list_eligible(
            MealPatternEligibilityQuery(age_years=request.age_years)
        )
        return _rank_published(request, eligible.programs)


class PlannerService:
    """Composes current authoritative cross-context truth before pure planning."""

    def __init__(
        self,
        meal_plans: MealPlanService,
        households: HouseholdService,
        recipes: FoodRecipeCatalogueService,
        nutrition: NutritionService,
        pantry: PantryService,
        config: PlannerConfig = PlannerConfig(),
    ) -> None:
        self._meal_plans = meal_plans
        self._households = households
        self._recipes = recipes
        self._nutrition = nutrition
        self._pantry = pantry
        self._config = config

    def compose_authoritative_request(
        self, command: AuthoritativeGenerationRequest
    ) -> PlannerRequest:
        """Resolve caller constraints against current Household-scoped truth."""
        state = self._households.get_household(command.household_id)
        if state.household.id != command.household_id:
            raise PlannerAuthoritativeInputError("Household scope mismatch")
        active = {member.id: member for member in state.members if member.active}
        requested = {item.member_id: item for item in command.members}
        if (
            not requested
            or len(requested) != len(command.members)
            or not set(requested) <= set(active)
        ):
            raise PlannerAuthoritativeInputError(
                "Planned members must be unique active Household members"
            )
        members = []
        for member_id in sorted(requested, key=lambda value: value.hex):
            selection = self._meal_plans.get_current_member_pattern(
                command.household_id, member_id
            )
            if (
                selection.selection.household_id != command.household_id
                or selection.selection.member_id != member_id
            ):
                raise PlannerAuthoritativeInputError(
                    "Accepted selection scope mismatch"
                )
            target = self._nutrition.member_reference_target(
                command.household_id, member_id, as_of_date=command.week_start
            )
            constraints = requested[member_id]
            members.append(
                MemberPlannerConstraints(
                    member_id,
                    selection,
                    target.reference_energy_kcal,
                    constraints.excluded_food_ingredient_ids,
                    constraints.preferred_recipe_version_ids,
                )
            )
        candidates = []
        for recipe in self._recipes.list_active(limit=200):
            detail = self._recipes.get_current_verified(recipe.id)
            calculated = self._nutrition.recipe_version(detail.version.id)
            candidates.append(
                PlannerCandidate(
                    detail.version.id,
                    detail.version.meal_type_code,
                    frozenset(row.food_ingredient_id for row in detail.ingredients),
                    calculated.per_base_serving.kcal,
                    calculated.status,
                    True,
                    detail.version.total_time_minutes,
                    detail.version.batch_friendly,
                )
            )
        pantry_ids = frozenset(
            item.food_ingredient_id
            for item in self._pantry.list_items(command.household_id)
            if item.quantity > 0
        )
        recent_plan_ids: tuple[UUID, ...] = ()
        recent_recipe_ids: tuple[UUID, ...] = ()
        previous_week = command.week_start - timedelta(weeks=HISTORY_HORIZON_WEEKS)
        try:
            prior = self._meal_plans.get_current_plan(
                command.household_id, previous_week
            )
        except MealPlanNotFoundError:
            pass
        else:
            if (
                prior.plan.household_id != command.household_id
                or prior.plan.week_start != previous_week
            ):
                raise PlannerAuthoritativeInputError("Recent MealPlan scope mismatch")
            recent_plan_ids = (prior.plan.id,)
            recent_recipe_ids = tuple(
                event.recipe_version_id
                for event in prior.events
                if event.recipe_version_id is not None
            )
        return PlannerRequest(
            command.household_id,
            command.week_start,
            tuple(members),
            tuple(candidates),
            pantry_ids,
            command.fixed_events,
            recent_plan_ids,
            recent_recipe_ids,
        )

    def generate_authoritative(
        self, command: AuthoritativeGenerationRequest
    ) -> tuple[PlannerResult, MealPlanDetail | None]:
        started = perf_counter_ns()
        request = self.compose_authoritative_request(command)
        result = generate_week(request, self._config)
        duration = (Decimal(perf_counter_ns() - started) / Decimal(1_000_000)).quantize(
            Decimal("0.001")
        )
        result = with_duration(result, duration)
        if isinstance(result, PlannerFailure):
            return result, None
        assert isinstance(result, PlannerSuccess)
        detail = self._meal_plans.create_plan_revision(
            household_id=command.household_id,
            week_start=command.week_start,
            member_selection_ids={
                member.member_id: member.selection.selection.id
                for member in request.members
            },
            events=[
                MealEventDraft(
                    event.local_date,
                    event.position,
                    event.role,
                    event.source_kind,
                    dict(event.portions),
                    event.recipe_version_id,
                    event.source_reference,
                )
                for event in result.events
            ],
            config_version=self._config.version,
        )
        return result, detail
