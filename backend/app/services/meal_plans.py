"""Application operations for Household meal-pattern selection and MealPlan revisions."""

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

from app.domain.households import HouseholdMember
from app.domain.meal_patterns import MealPatternEligibilityQuery, MealRole, detail_is_eligible
from app.domain.meal_plans import (
    HouseholdMealEvent,
    MealPlan,
    MealPlanDetail,
    MealPlanMemberReferenceMethodologyPin,
    MealPlanMemberSelection,
    MealPlanNutrition,
    MealPlanStatus,
    MealSourceKind,
    MemberMealPatternOpportunitySnapshot,
    MemberMealPatternSelection,
    MemberMealPatternSelectionDetail,
    MemberMealPatternSourceKind,
    Serving,
    calculate_meal_plan_nutrition,
    validate_complete_plan,
)
from app.domain.nutrition import RecipeVersionNutrition
from app.services.household_contracts import HouseholdReadScope
from app.services.meal_pattern_contracts import MealPatternCatalogueReadScope
from app.services.meal_plan_contracts import (
    MealPlanPersistenceConflictError,
    MealPlanReadScope,
    MealPlanUnitOfWork,
)
from app.services.reference_methodology import (
    BASELINE_NUTRITION_CONFIG_VERSION,
    RUSSIAN_GROUP_REFERENCE_VERSION,
    ReferenceMethodologyUnsupportedError,
    TableProvider,
    validate_russian_group_reference_applicability,
)

WriteScopeFactory = Callable[[], MealPlanUnitOfWork]
ReadScopeFactory = Callable[[], MealPlanReadScope]
HouseholdReadScopeFactory = Callable[[], HouseholdReadScope]
PatternReadScopeFactory = Callable[[], MealPatternCatalogueReadScope]
IdFactory = Callable[[], UUID]
Clock = Callable[[], datetime]


class MealPlanNotFoundError(LookupError):
    pass


class MealPatternSelectionNotFoundError(LookupError):
    pass


class MealPlanValidationError(ValueError):
    pass


@dataclass(frozen=True)
class MealEventDraft:
    local_date: date
    position: int
    role: MealRole
    source_kind: MealSourceKind
    servings: Mapping[UUID, Decimal]
    recipe_version_id: UUID | None = None
    source_reference: str | None = None


class MealPlanService:
    """Coordinates PR7 repositories without importing persistence adapters."""

    def __init__(
        self,
        write_scope_factory: WriteScopeFactory,
        read_scope_factory: ReadScopeFactory,
        household_read_scope_factory: HouseholdReadScopeFactory,
        pattern_read_scope_factory: PatternReadScopeFactory,
        *,
        russian_reference_tables: TableProvider | None = None,
        id_factory: IdFactory = uuid4,
        clock: Clock | None = None,
    ) -> None:
        self._write_scope_factory = write_scope_factory
        self._read_scope_factory = read_scope_factory
        self._household_read_scope_factory = household_read_scope_factory
        self._pattern_read_scope_factory = pattern_read_scope_factory
        self._russian_reference_tables = russian_reference_tables
        self._id_factory = id_factory
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def accept_member_pattern(
        self,
        *,
        household_id: UUID,
        member_id: UUID,
        source_kind: MemberMealPatternSourceKind,
        schedule: Mapping[int, Sequence[MealRole]] | None = None,
        program_version_id: UUID | None = None,
        recommender_version: str | None = None,
        has_user_overrides: bool = False,
    ) -> MemberMealPatternSelectionDetail:
        try:
            source_kind = MemberMealPatternSourceKind(source_kind)
        except (TypeError, ValueError) as exc:
            raise MealPlanValidationError("Unsupported meal-pattern selection source kind.") from exc
        if has_user_overrides and schedule is None:
            raise MealPlanValidationError(
                "A selection marked with user overrides requires the resolved override schedule."
            )

        household, member = self._load_household_member(household_id, member_id)
        accepted_at = self._clock()
        resolved_schedule = schedule
        if source_kind is MemberMealPatternSourceKind.PROGRAM:
            if program_version_id is None:
                raise MealPlanValidationError(
                    "PROGRAM selection requires an exact MealPatternProgramVersion."
                )
            with self._pattern_read_scope_factory() as scope:
                program = scope.versions.get_detail(program_version_id)
            if program is None:
                raise MealPlanValidationError("MealPatternProgramVersion was not found.")
            age_years = _member_age_years(
                member,
                local_date=accepted_at.astimezone(ZoneInfo(household.timezone)).date(),
            )
            if age_years is None or not detail_is_eligible(
                program, MealPatternEligibilityQuery(age_years=age_years)
            ):
                raise MealPlanValidationError(
                    "The selected program version is not published and age-eligible for this member."
                )
            template = tuple(item.role for item in program.opportunities)
            canonical_schedule = {weekday: template for weekday in range(1, 8)}
            if resolved_schedule is None:
                resolved_schedule = canonical_schedule
            elif not has_user_overrides:
                supplied_schedule = {
                    weekday: tuple(roles)
                    for weekday, roles in resolved_schedule.items()
                }
                if supplied_schedule != canonical_schedule:
                    raise MealPlanValidationError(
                        "PROGRAM schedule differs from the published program; "
                        "set has_user_overrides=True for an override snapshot."
                    )
        else:
            if program_version_id is not None:
                raise MealPlanValidationError(
                    "CUSTOM selection must not reference a MealPatternProgramVersion."
                )
            if resolved_schedule is None:
                raise MealPlanValidationError("CUSTOM selection requires a resolved schedule.")

        assert resolved_schedule is not None
        with self._write_scope_factory() as scope:
            current = scope.selections.get_current(household_id, member_id)
            selection_id = self._id_factory()
            selection = MemberMealPatternSelection(
                id=selection_id,
                household_id=household_id,
                member_id=member_id,
                version_number=1
                if current is None
                else current.selection.version_number + 1,
                source_kind=source_kind,
                program_version_id=program_version_id,
                recommender_version=recommender_version,
                has_user_overrides=has_user_overrides,
                accepted_at=accepted_at,
                supersedes_selection_id=None if current is None else current.selection.id,
                created_at=accepted_at,
            )
            opportunities = tuple(
                MemberMealPatternOpportunitySnapshot(
                    selection_id=selection_id,
                    weekday=weekday,
                    position=position,
                    role=role,
                )
                for weekday in sorted(resolved_schedule)
                for position, role in enumerate(resolved_schedule[weekday], start=1)
            )
            detail = MemberMealPatternSelectionDetail(selection, opportunities)
            scope.selections.add_detail(detail)
            scope.commit()
        return detail

    def get_current_member_pattern(
        self, household_id: UUID, member_id: UUID
    ) -> MemberMealPatternSelectionDetail:
        with self._read_scope_factory() as scope:
            detail = scope.selections.get_current(household_id, member_id)
        if detail is None:
            raise MealPatternSelectionNotFoundError(member_id)
        return detail

    def get_member_pattern_history(
        self, household_id: UUID, member_id: UUID
    ) -> tuple[MemberMealPatternSelection, ...]:
        with self._read_scope_factory() as scope:
            history = scope.selections.list_history(household_id, member_id)
        return tuple(history)

    def create_plan_revision(
        self,
        *,
        household_id: UUID,
        week_start: date,
        member_selection_ids: Mapping[UUID, UUID],
        events: Sequence[MealEventDraft],
        reference_methodology_selection_ids: Mapping[UUID, UUID] | None = None,
        status: MealPlanStatus = MealPlanStatus.CONFIRMED,
        config_version: str = "manual-v1",
    ) -> MealPlanDetail:
        with self._household_read_scope_factory() as scope:
            if scope.households.get_household(household_id) is None:
                raise MealPlanValidationError("Household was not found.")
            members = {item.id: item for item in scope.members.list_members(household_id)}
        if not member_selection_ids:
            raise MealPlanValidationError("MealPlan requires at least one Household member.")
        if not set(member_selection_ids).issubset(members):
            raise MealPlanValidationError("MealPlan members must belong to the Household.")

        reference_methodology_selection_ids = dict(
            reference_methodology_selection_ids or {}
        )
        if (
            reference_methodology_selection_ids
            and set(reference_methodology_selection_ids)
            != set(member_selection_ids)
        ):
            raise MealPlanValidationError(
                "Reference-methodology pins must cover all plan members or none."
            )

        now = self._clock()
        selection_details: dict[UUID, MemberMealPatternSelectionDetail] = {}
        reference_selections = {}
        with self._read_scope_factory() as scope:
            current = scope.plans.get_current(household_id, week_start)
            for member_id, selection_id in member_selection_ids.items():
                detail = scope.selections.get_detail(household_id, selection_id)
                if detail is None or detail.selection.member_id != member_id:
                    raise MealPlanValidationError(
                        "MealPlan must pin a valid selection for each Household member."
                    )
                selection_details[selection_id] = detail
            for member_id, selection_id in (
                reference_methodology_selection_ids.items()
            ):
                reference_selection = scope.reference_methodologies.get(
                    household_id, selection_id
                )
                if (
                    reference_selection is None
                    or reference_selection.member_id != member_id
                    or reference_selection.accepted_at > now
                    or reference_selection.nutrition_config_version
                    != BASELINE_NUTRITION_CONFIG_VERSION
                    or reference_selection.group_reference_methodology_version
                    not in (None, RUSSIAN_GROUP_REFERENCE_VERSION)
                ):
                    raise MealPlanValidationError(
                        "MealPlan must pin an accepted supported reference "
                        "methodology for each member."
                    )
                if (
                    reference_selection.group_reference_methodology_version
                    is not None
                ):
                    try:
                        validate_russian_group_reference_applicability(
                            members[member_id],
                            reference_date=week_start,
                            methodology_version=(
                                reference_selection
                                .group_reference_methodology_version
                            ),
                            russian_reference_tables=(
                                self._russian_reference_tables
                            ),
                        )
                    except ReferenceMethodologyUnsupportedError as exc:
                        raise MealPlanValidationError(
                            "Pinned Russian reference methodology is not "
                            "applicable at MealPlan.week_start."
                        ) from exc
                reference_selections[member_id] = reference_selection

        plan_id = self._id_factory()
        plan = MealPlan(
            id=plan_id,
            household_id=household_id,
            week_start=week_start,
            revision_number=1 if current is None else current.plan.revision_number + 1,
            status=status,
            config_version=config_version,
            supersedes_plan_id=None if current is None else current.plan.id,
            created_at=now,
        )
        pins = tuple(
            MealPlanMemberSelection(plan_id, member_id, selection_id)
            for member_id, selection_id in sorted(
                member_selection_ids.items(), key=lambda item: item[0].hex
            )
        )
        domain_events: list[HouseholdMealEvent] = []
        servings: list[Serving] = []
        for event in events:
            event_id = self._id_factory()
            domain_event = HouseholdMealEvent(
                id=event_id,
                plan_id=plan_id,
                local_date=event.local_date,
                position=event.position,
                role=event.role,
                source_kind=event.source_kind,
                recipe_version_id=event.recipe_version_id,
                source_reference=event.source_reference,
                created_at=now,
            )
            domain_events.append(domain_event)
            for member_id, portion in event.servings.items():
                servings.append(
                    Serving(
                        id=self._id_factory(),
                        event_id=event_id,
                        member_id=member_id,
                        portion_servings=portion,
                        created_at=now,
                    )
                )
        reference_pins = tuple(
            MealPlanMemberReferenceMethodologyPin(
                plan_id=plan_id,
                member_id=member_id,
                reference_methodology_selection_id=selection.id,
                birth_date=members[member_id].birth_date,
                sex=members[member_id].sex,
                height_cm=members[member_id].height_cm,
                weight_kg=members[member_id].weight_kg,
                activity_level=members[member_id].activity_level,
                goal=members[member_id].goal,
                member_updated_at=members[member_id].updated_at,
            )
            for member_id, selection in sorted(
                reference_selections.items(),
                key=lambda item: item[0].hex,
            )
        )
        detail = MealPlanDetail(
            plan,
            pins,
            tuple(domain_events),
            tuple(servings),
            reference_pins,
        )
        validate_complete_plan(detail, selection_details)
        try:
            with self._write_scope_factory() as scope:
                for pin in reference_pins:
                    scope.guard_member_state(
                        household_id=household_id,
                        member_id=pin.member_id,
                        member_updated_at=pin.member_updated_at,
                    )
                scope.plans.add_detail(detail)
                scope.commit()
        except MealPlanPersistenceConflictError as exc:
            raise MealPlanValidationError(str(exc)) from exc
        return detail

    def get_plan(self, household_id: UUID, plan_id: UUID) -> MealPlanDetail:
        with self._read_scope_factory() as scope:
            detail = scope.plans.get_detail(household_id, plan_id)
        if detail is None:
            raise MealPlanNotFoundError(plan_id)
        return detail

    def get_current_plan(self, household_id: UUID, week_start: date) -> MealPlanDetail:
        with self._read_scope_factory() as scope:
            detail = scope.plans.get_current(household_id, week_start)
        if detail is None:
            raise MealPlanNotFoundError((household_id, week_start))
        return detail

    def calculate_plan_nutrition(
        self,
        household_id: UUID,
        plan_id: UUID,
        recipe_nutrition_by_version_id: Mapping[UUID, RecipeVersionNutrition],
    ) -> MealPlanNutrition:
        detail = self.get_plan(household_id, plan_id)
        return calculate_meal_plan_nutrition(
            detail, dict(recipe_nutrition_by_version_id)
        )

    def _load_household_member(self, household_id: UUID, member_id: UUID):
        with self._household_read_scope_factory() as scope:
            household = scope.households.get_household(household_id)
            member = scope.members.get_member(household_id, member_id)
        if household is None or member is None:
            raise MealPlanValidationError("Household member was not found.")
        return household, member


def _member_age_years(member: HouseholdMember, *, local_date: date) -> int | None:
    if member.birth_date is None:
        return None
    years = local_date.year - member.birth_date.year
    if (local_date.month, local_date.day) < (member.birth_date.month, member.birth_date.day):
        years -= 1
    return years
