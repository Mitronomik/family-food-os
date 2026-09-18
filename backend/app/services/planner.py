"""PR8 Planner application facade and curated-program recommender."""

from dataclasses import dataclass
from uuid import UUID

from app.domain.meal_patterns import (
    MealPatternProgramDetail,
    MealPatternTagKind,
    detail_is_eligible,
    MealPatternEligibilityQuery,
)
from app.domain.meal_plans import MealPlanDetail
from app.domain.planner import (
    PlannerConfig,
    PlannerFailure,
    PlannerRequest,
    PlannerResult,
    PlannerSuccess,
    generate_week,
)
from app.services.meal_plans import MealEventDraft, MealPlanService


RECOMMENDER_VERSION = "meal-pattern-recommender-v1"


@dataclass(frozen=True)
class RecommenderRequest:
    age_years: int | None
    goal_codes: frozenset[str] = frozenset()
    context_codes: frozenset[str] = frozenset()
    medical_or_therapeutic_request: bool = False


@dataclass(frozen=True)
class RecommenderResult:
    version: str
    ranked_program_version_ids: tuple[UUID, ...]
    unsupported_reason: str | None
    requires_user_acceptance: bool = True


def recommend_patterns(
    request: RecommenderRequest, programs: tuple[MealPatternProgramDetail, ...]
) -> RecommenderResult:
    if request.medical_or_therapeutic_request:
        return RecommenderResult(
            RECOMMENDER_VERSION, (), "MEDICAL_OR_THERAPEUTIC_REQUEST_UNSUPPORTED"
        )
    if request.age_years is None:
        return RecommenderResult(RECOMMENDER_VERSION, (), "AGE_REQUIRED_FOR_SAFETY")
    ranked: list[tuple[int, str, UUID]] = []
    for detail in programs:
        if not detail_is_eligible(
            detail, MealPatternEligibilityQuery(age_years=request.age_years)
        ):
            continue
        tags = {(tag.kind, tag.code) for tag in detail.tags}
        score = (
            sum((MealPatternTagKind.GOAL, code) in tags for code in request.goal_codes)
            * 2
        )
        score += sum(
            (MealPatternTagKind.CONTEXT, code) in tags for code in request.context_codes
        )
        ranked.append((score, detail.program.code, detail.version.id))
    ranked.sort(key=lambda item: (-item[0], item[1], item[2].hex))
    reason = None if ranked else "NO_ELIGIBLE_CURATED_PROGRAM"
    return RecommenderResult(
        RECOMMENDER_VERSION, tuple(item[2] for item in ranked), reason
    )


class PlannerService:
    """Generates fully in memory and delegates the single append-only write to PR7."""

    def __init__(
        self, meal_plans: MealPlanService, config: PlannerConfig = PlannerConfig()
    ) -> None:
        self._meal_plans = meal_plans
        self._config = config

    def generate(
        self, request: PlannerRequest
    ) -> tuple[PlannerResult, MealPlanDetail | None]:
        result = generate_week(request, self._config)
        if isinstance(result, PlannerFailure):
            return result, None
        assert isinstance(result, PlannerSuccess)
        detail = self._meal_plans.create_plan_revision(
            household_id=request.household_id,
            week_start=request.week_start,
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
