"""Household-owned meal-pattern selection and MealPlan/Serving domain."""

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from app.domain.decimal_utils import parse_decimal, quantize_decimal
from app.domain.errors import DomainIssue, DomainIssueCode, DomainValidationError
from app.domain.households import (
    normalize_birth_date,
    normalize_height_cm,
    normalize_utc_instant,
    normalize_weight_kg,
)
from app.domain.meal_patterns import MealRole
from app.domain.nutrition import (
    NutritionStatus,
    NutritionValues,
    RecipeVersionNutrition,
    aggregate_nutrition_status,
    aggregate_nutrition_values,
    scale_nutrition_values,
)

_PORTION_QUANT = Decimal("0.000001")
INITIAL_MAX_OPPORTUNITIES_PER_DAY = 6


class MemberMealPatternSourceKind(StrEnum):
    PROGRAM = "PROGRAM"
    CUSTOM = "CUSTOM"


class MealPlanStatus(StrEnum):
    DRAFT = "DRAFT"
    CONFIRMED = "CONFIRMED"


class MealSourceKind(StrEnum):
    COOK_RECIPE = "COOK_RECIPE"
    ASSEMBLY = "ASSEMBLY"
    LEFTOVER = "LEFTOVER"
    PREPARED = "PREPARED"
    READY_MEAL = "READY_MEAL"
    ORDER_OUT = "ORDER_OUT"
    EAT_OUT = "EAT_OUT"


def _issue(
    code: DomainIssueCode,
    message: str,
    *,
    field: str,
    value: object,
) -> DomainValidationError:
    return DomainValidationError(
        DomainIssue(
            code=code,
            message=message,
            field=field,
            value=str(value),
            next_action=f"Provide a valid {field}.",
        )
    )


def _uuid4(value: object, *, field: str) -> UUID:
    if not isinstance(value, UUID) or value.version != 4:
        raise _issue(
            DomainIssueCode.INVALID_IDENTIFIER,
            f"{field} must be UUIDv4.",
            field=field,
            value=value,
        )
    return value


def _positive_int(value: object, *, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise _issue(
            DomainIssueCode.VALUE_OUT_OF_RANGE,
            f"{field} must be a positive integer.",
            field=field,
            value=value,
        )
    return value


def _weekday(value: object) -> int:
    weekday = _positive_int(value, field="weekday")
    if weekday > 7:
        raise _issue(
            DomainIssueCode.VALUE_OUT_OF_RANGE,
            "weekday must be in ISO range 1..7.",
            field="weekday",
            value=value,
        )
    return weekday


def _calendar_date(value: object, *, field: str) -> date:
    if not isinstance(value, date) or isinstance(value, datetime):
        raise _issue(
            DomainIssueCode.INVALID_DATE,
            f"{field} must be a calendar date.",
            field=field,
            value=value,
        )
    return value


def _optional_text(value: object, *, field: str, maximum: int = 200) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise _issue(
            DomainIssueCode.INVALID_CODE,
            f"{field} must be text or null.",
            field=field,
            value=value,
        )
    normalized = " ".join(value.strip().split())
    if not normalized:
        return None
    if len(normalized) > maximum:
        raise _issue(
            DomainIssueCode.VALUE_OUT_OF_RANGE,
            f"{field} must be {maximum} characters or fewer.",
            field=field,
            value=value,
        )
    return normalized


def _required_code(value: object, *, field: str, maximum: int = 120) -> str:
    normalized = _optional_text(value, field=field, maximum=maximum)
    if normalized is None:
        raise _issue(
            DomainIssueCode.REQUIRED_FIELD,
            f"{field} must not be empty.",
            field=field,
            value=value,
        )
    return normalized


def _portion(value: object) -> Decimal:
    parsed = parse_decimal(value, field="portion_servings")  # type: ignore[arg-type]
    if parsed <= 0:
        raise _issue(
            DomainIssueCode.VALUE_OUT_OF_RANGE,
            "portion_servings must be positive.",
            field="portion_servings",
            value=value,
        )
    normalized = quantize_decimal(parsed, _PORTION_QUANT, field="portion_servings")
    if normalized <= 0:
        raise _issue(
            DomainIssueCode.VALUE_OUT_OF_RANGE,
            "portion_servings is below supported precision.",
            field="portion_servings",
            value=value,
        )
    return normalized


@dataclass(frozen=True)
class MemberMealPatternSelection:
    id: UUID
    household_id: UUID
    member_id: UUID
    version_number: int
    source_kind: MemberMealPatternSourceKind
    program_version_id: UUID | None
    recommender_version: str | None
    has_user_overrides: bool
    accepted_at: datetime
    supersedes_selection_id: UUID | None
    created_at: datetime

    def __post_init__(self) -> None:
        for field in ("id", "household_id", "member_id"):
            object.__setattr__(self, field, _uuid4(getattr(self, field), field=field))
        if self.program_version_id is not None:
            object.__setattr__(
                self,
                "program_version_id",
                _uuid4(self.program_version_id, field="program_version_id"),
            )
        if self.supersedes_selection_id is not None:
            object.__setattr__(
                self,
                "supersedes_selection_id",
                _uuid4(
                    self.supersedes_selection_id,
                    field="supersedes_selection_id",
                ),
            )
            if self.supersedes_selection_id == self.id:
                raise _issue(
                    DomainIssueCode.INVALID_IDENTIFIER,
                    "A selection cannot supersede itself.",
                    field="supersedes_selection_id",
                    value=self.supersedes_selection_id,
                )
        object.__setattr__(
            self,
            "version_number",
            _positive_int(self.version_number, field="version_number"),
        )
        try:
            source_kind = MemberMealPatternSourceKind(self.source_kind)
        except (TypeError, ValueError) as exc:
            raise _issue(
                DomainIssueCode.INVALID_CODE,
                "source_kind has an invalid controlled value.",
                field="source_kind",
                value=self.source_kind,
            ) from exc
        object.__setattr__(self, "source_kind", source_kind)
        if source_kind is MemberMealPatternSourceKind.PROGRAM:
            if self.program_version_id is None:
                raise _issue(
                    DomainIssueCode.REQUIRED_FIELD,
                    "PROGRAM selection requires program_version_id.",
                    field="program_version_id",
                    value=self.program_version_id,
                )
        elif self.program_version_id is not None:
            raise _issue(
                DomainIssueCode.INVALID_IDENTIFIER,
                "CUSTOM selection must not reference a program version.",
                field="program_version_id",
                value=self.program_version_id,
            )
        object.__setattr__(
            self,
            "recommender_version",
            _optional_text(
                self.recommender_version,
                field="recommender_version",
                maximum=120,
            ),
        )
        if type(self.has_user_overrides) is not bool:
            raise _issue(
                DomainIssueCode.INVALID_BOOLEAN,
                "has_user_overrides must be boolean.",
                field="has_user_overrides",
                value=self.has_user_overrides,
            )
        if (
            source_kind is MemberMealPatternSourceKind.CUSTOM
            and self.has_user_overrides
        ):
            raise _issue(
                DomainIssueCode.INVALID_BOOLEAN,
                "CUSTOM selection has no program template to override.",
                field="has_user_overrides",
                value=self.has_user_overrides,
            )
        accepted_at = normalize_utc_instant(self.accepted_at, field="accepted_at")
        created_at = normalize_utc_instant(self.created_at, field="created_at")
        if created_at < accepted_at:
            raise _issue(
                DomainIssueCode.INVALID_DATE,
                "created_at must not precede accepted_at.",
                field="created_at",
                value=created_at,
            )
        object.__setattr__(self, "accepted_at", accepted_at)
        object.__setattr__(self, "created_at", created_at)


@dataclass(frozen=True)
class MemberMealPatternOpportunitySnapshot:
    selection_id: UUID
    weekday: int
    position: int
    role: MealRole

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "selection_id", _uuid4(self.selection_id, field="selection_id")
        )
        object.__setattr__(self, "weekday", _weekday(self.weekday))
        object.__setattr__(
            self, "position", _positive_int(self.position, field="position")
        )
        try:
            object.__setattr__(self, "role", MealRole(self.role))
        except (TypeError, ValueError) as exc:
            raise _issue(
                DomainIssueCode.INVALID_CODE,
                "role has an invalid controlled value.",
                field="role",
                value=self.role,
            ) from exc


@dataclass(frozen=True)
class MemberMealPatternSelectionDetail:
    selection: MemberMealPatternSelection
    opportunities: tuple[MemberMealPatternOpportunitySnapshot, ...]

    def __post_init__(self) -> None:
        if any(item.selection_id != self.selection.id for item in self.opportunities):
            raise _issue(
                DomainIssueCode.INVALID_IDENTIFIER,
                "All opportunities must belong to the selection.",
                field="opportunities",
                value=self.selection.id,
            )
        by_day: dict[int, list[MemberMealPatternOpportunitySnapshot]] = defaultdict(list)
        for item in self.opportunities:
            by_day[item.weekday].append(item)
        if set(by_day) != set(range(1, 8)):
            raise _issue(
                DomainIssueCode.REQUIRED_FIELD,
                "Resolved accepted schedule must define all seven weekdays.",
                field="opportunities",
                value=sorted(by_day),
            )
        for weekday, items in by_day.items():
            positions = sorted(item.position for item in items)
            if positions != list(range(1, len(items) + 1)):
                raise _issue(
                    DomainIssueCode.INVALID_CODE,
                    "Daily opportunity positions must be contiguous from one.",
                    field="opportunities",
                    value=(weekday, positions),
                )
            if len(items) > INITIAL_MAX_OPPORTUNITIES_PER_DAY:
                raise _issue(
                    DomainIssueCode.VALUE_OUT_OF_RANGE,
                    "Initial product supports at most six opportunities per day.",
                    field="opportunities",
                    value=(weekday, len(items)),
                )

    def roles_for_weekday(self, weekday: int) -> tuple[MealRole, ...]:
        normalized = _weekday(weekday)
        items = sorted(
            (item for item in self.opportunities if item.weekday == normalized),
            key=lambda item: item.position,
        )
        return tuple(item.role for item in items)


@dataclass(frozen=True)
class MealPlan:
    id: UUID
    household_id: UUID
    week_start: date
    revision_number: int
    status: MealPlanStatus
    config_version: str
    supersedes_plan_id: UUID | None
    created_at: datetime

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _uuid4(self.id, field="id"))
        object.__setattr__(
            self, "household_id", _uuid4(self.household_id, field="household_id")
        )
        object.__setattr__(
            self, "week_start", _calendar_date(self.week_start, field="week_start")
        )
        object.__setattr__(
            self,
            "revision_number",
            _positive_int(self.revision_number, field="revision_number"),
        )
        try:
            object.__setattr__(self, "status", MealPlanStatus(self.status))
        except (TypeError, ValueError) as exc:
            raise _issue(
                DomainIssueCode.INVALID_CODE,
                "status has an invalid controlled value.",
                field="status",
                value=self.status,
            ) from exc
        object.__setattr__(
            self,
            "config_version",
            _required_code(self.config_version, field="config_version"),
        )
        if self.supersedes_plan_id is not None:
            object.__setattr__(
                self,
                "supersedes_plan_id",
                _uuid4(self.supersedes_plan_id, field="supersedes_plan_id"),
            )
            if self.supersedes_plan_id == self.id:
                raise _issue(
                    DomainIssueCode.INVALID_IDENTIFIER,
                    "A MealPlan cannot supersede itself.",
                    field="supersedes_plan_id",
                    value=self.supersedes_plan_id,
                )
        object.__setattr__(
            self,
            "created_at",
            normalize_utc_instant(self.created_at, field="created_at"),
        )


@dataclass(frozen=True)
class MealPlanMemberSelection:
    plan_id: UUID
    member_id: UUID
    selection_id: UUID

    def __post_init__(self) -> None:
        for field in ("plan_id", "member_id", "selection_id"):
            object.__setattr__(self, field, _uuid4(getattr(self, field), field=field))


@dataclass(frozen=True)
class MealPlanMemberReferenceMethodologyPin:
    plan_id: UUID
    member_id: UUID
    reference_methodology_selection_id: UUID
    birth_date: date | None
    sex: str | None
    height_cm: Decimal | None
    weight_kg: Decimal | None
    activity_level: str
    goal: str
    member_updated_at: datetime

    def __post_init__(self) -> None:
        for field in (
            "plan_id",
            "member_id",
            "reference_methodology_selection_id",
        ):
            object.__setattr__(
                self,
                field,
                _uuid4(getattr(self, field), field=field),
            )
        object.__setattr__(self, "birth_date", normalize_birth_date(self.birth_date))
        object.__setattr__(
            self,
            "sex",
            _optional_text(self.sex, field="sex", maximum=200),
        )
        object.__setattr__(self, "height_cm", normalize_height_cm(self.height_cm))
        object.__setattr__(self, "weight_kg", normalize_weight_kg(self.weight_kg))
        object.__setattr__(
            self,
            "activity_level",
            _required_code(
                self.activity_level,
                field="activity_level",
                maximum=200,
            ),
        )
        object.__setattr__(
            self,
            "goal",
            _required_code(self.goal, field="goal", maximum=200),
        )
        object.__setattr__(
            self,
            "member_updated_at",
            normalize_utc_instant(
                self.member_updated_at,
                field="member_updated_at",
            ),
        )


@dataclass(frozen=True)
class HouseholdMealEvent:
    id: UUID
    plan_id: UUID
    local_date: date
    position: int
    role: MealRole
    source_kind: MealSourceKind
    recipe_version_id: UUID | None
    source_reference: str | None
    created_at: datetime

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _uuid4(self.id, field="id"))
        object.__setattr__(self, "plan_id", _uuid4(self.plan_id, field="plan_id"))
        object.__setattr__(
            self,
            "local_date",
            _calendar_date(self.local_date, field="local_date"),
        )
        object.__setattr__(
            self, "position", _positive_int(self.position, field="position")
        )
        try:
            object.__setattr__(self, "role", MealRole(self.role))
        except (TypeError, ValueError) as exc:
            raise _issue(
                DomainIssueCode.INVALID_CODE,
                "role has an invalid controlled value.",
                field="role",
                value=self.role,
            ) from exc
        try:
            source_kind = MealSourceKind(self.source_kind)
        except (TypeError, ValueError) as exc:
            raise _issue(
                DomainIssueCode.INVALID_CODE,
                "source_kind has an invalid controlled value.",
                field="source_kind",
                value=self.source_kind,
            ) from exc
        object.__setattr__(self, "source_kind", source_kind)
        if self.recipe_version_id is not None:
            object.__setattr__(
                self,
                "recipe_version_id",
                _uuid4(self.recipe_version_id, field="recipe_version_id"),
            )
        object.__setattr__(
            self,
            "source_reference",
            _optional_text(
                self.source_reference,
                field="source_reference",
                maximum=500,
            ),
        )
        if source_kind is MealSourceKind.COOK_RECIPE:
            if self.recipe_version_id is None:
                raise _issue(
                    DomainIssueCode.REQUIRED_FIELD,
                    "COOK_RECIPE event requires recipe_version_id.",
                    field="recipe_version_id",
                    value=self.recipe_version_id,
                )
        elif self.recipe_version_id is not None:
            raise _issue(
                DomainIssueCode.INVALID_IDENTIFIER,
                "Only COOK_RECIPE may carry recipe_version_id in PR7.",
                field="recipe_version_id",
                value=self.recipe_version_id,
            )
        object.__setattr__(
            self,
            "created_at",
            normalize_utc_instant(self.created_at, field="created_at"),
        )


@dataclass(frozen=True)
class Serving:
    id: UUID
    event_id: UUID
    member_id: UUID
    portion_servings: Decimal
    created_at: datetime

    def __post_init__(self) -> None:
        for field in ("id", "event_id", "member_id"):
            object.__setattr__(self, field, _uuid4(getattr(self, field), field=field))
        object.__setattr__(self, "portion_servings", _portion(self.portion_servings))
        object.__setattr__(
            self,
            "created_at",
            normalize_utc_instant(self.created_at, field="created_at"),
        )


@dataclass(frozen=True)
class MealPlanDetail:
    plan: MealPlan
    member_selections: tuple[MealPlanMemberSelection, ...]
    events: tuple[HouseholdMealEvent, ...]
    servings: tuple[Serving, ...]
    reference_methodology_pins: tuple[
        MealPlanMemberReferenceMethodologyPin, ...
    ] = ()

    def __post_init__(self) -> None:
        plan_id = self.plan.id
        if any(item.plan_id != plan_id for item in self.member_selections):
            raise _issue(
                DomainIssueCode.INVALID_IDENTIFIER,
                "Member selection pins must belong to the MealPlan.",
                field="member_selections",
                value=plan_id,
            )
        if any(item.plan_id != plan_id for item in self.events):
            raise _issue(
                DomainIssueCode.INVALID_IDENTIFIER,
                "Events must belong to the MealPlan.",
                field="events",
                value=plan_id,
            )
        member_ids = [item.member_id for item in self.member_selections]
        if len(member_ids) != len(set(member_ids)):
            raise _issue(
                DomainIssueCode.INVALID_IDENTIFIER,
                "A member may have only one pinned selection per plan revision.",
                field="member_selections",
                value=member_ids,
            )
        if any(
            item.plan_id != plan_id
            for item in self.reference_methodology_pins
        ):
            raise _issue(
                DomainIssueCode.INVALID_IDENTIFIER,
                "Reference-methodology pins must belong to the MealPlan.",
                field="reference_methodology_pins",
                value=plan_id,
            )
        reference_member_ids = [
            item.member_id for item in self.reference_methodology_pins
        ]
        if len(reference_member_ids) != len(set(reference_member_ids)):
            raise _issue(
                DomainIssueCode.INVALID_IDENTIFIER,
                "A member may have only one reference-methodology pin per plan.",
                field="reference_methodology_pins",
                value=reference_member_ids,
            )
        if reference_member_ids and set(reference_member_ids) != set(member_ids):
            raise _issue(
                DomainIssueCode.REQUIRED_FIELD,
                "Reference-methodology pins must cover all plan members or none.",
                field="reference_methodology_pins",
                value=reference_member_ids,
            )
        event_by_id = {event.id: event for event in self.events}
        if len(event_by_id) != len(self.events):
            raise _issue(
                DomainIssueCode.INVALID_IDENTIFIER,
                "Event ids must be unique within a plan revision.",
                field="events",
                value="duplicate event id",
            )
        start = self.plan.week_start
        end = start + timedelta(days=6)
        positions_by_date: dict[date, list[int]] = defaultdict(list)
        for event in self.events:
            if not start <= event.local_date <= end:
                raise _issue(
                    DomainIssueCode.INVALID_DATE,
                    "Event local_date must fall inside the seven-day plan horizon.",
                    field="local_date",
                    value=event.local_date,
                )
            positions_by_date[event.local_date].append(event.position)
        for event_date, positions in positions_by_date.items():
            ordered = sorted(positions)
            if ordered != list(range(1, len(ordered) + 1)):
                raise _issue(
                    DomainIssueCode.INVALID_CODE,
                    "Event positions must be contiguous from one within each date.",
                    field="events",
                    value=(event_date, ordered),
                )
        pinned_members = set(member_ids)
        seen_servings: set[tuple[UUID, UUID]] = set()
        participating_event_ids: set[UUID] = set()
        for serving in self.servings:
            if serving.event_id not in event_by_id:
                raise _issue(
                    DomainIssueCode.INVALID_IDENTIFIER,
                    "Serving event must belong to this MealPlan.",
                    field="event_id",
                    value=serving.event_id,
                )
            if serving.member_id not in pinned_members:
                raise _issue(
                    DomainIssueCode.INVALID_IDENTIFIER,
                    "Serving member must have a pinned selection in the MealPlan.",
                    field="member_id",
                    value=serving.member_id,
                )
            key = (serving.event_id, serving.member_id)
            if key in seen_servings:
                raise _issue(
                    DomainIssueCode.INVALID_IDENTIFIER,
                    "A member may have only one Serving per event.",
                    field="servings",
                    value=key,
                )
            seen_servings.add(key)
            participating_event_ids.add(serving.event_id)
        missing_participation = [
            event.id for event in self.events if event.id not in participating_event_ids
        ]
        if missing_participation:
            raise _issue(
                DomainIssueCode.REQUIRED_FIELD,
                "Every Household meal event requires at least one participant Serving.",
                field="servings",
                value=missing_participation,
            )

    @property
    def horizon_dates(self) -> tuple[date, ...]:
        return tuple(self.plan.week_start + timedelta(days=offset) for offset in range(7))


@dataclass(frozen=True)
class ServingNutrition:
    serving: Serving
    event: HouseholdMealEvent
    values: NutritionValues
    status: NutritionStatus


@dataclass(frozen=True)
class MemberDayNutrition:
    member_id: UUID
    local_date: date
    values: NutritionValues
    status: NutritionStatus


@dataclass(frozen=True)
class MemberWeekNutrition:
    member_id: UUID
    values: NutritionValues
    status: NutritionStatus


@dataclass(frozen=True)
class MealPlanNutrition:
    servings: tuple[ServingNutrition, ...]
    member_days: tuple[MemberDayNutrition, ...]
    member_weeks: tuple[MemberWeekNutrition, ...]


def validate_complete_plan(
    detail: MealPlanDetail,
    selection_details: dict[UUID, MemberMealPatternSelectionDetail],
) -> None:
    """Validate a complete manual week against the pinned resolved schedules."""
    expected_dates = set(detail.horizon_dates)
    actual_dates = {event.local_date for event in detail.events}
    if actual_dates != expected_dates:
        raise _issue(
            DomainIssueCode.REQUIRED_FIELD,
            "A complete MealPlan must contain at least one event on every horizon date.",
            field="events",
            value=sorted(actual_dates),
        )
    pin_by_member = {
        item.member_id: item.selection_id for item in detail.member_selections
    }
    participants_by_event: dict[UUID, set[UUID]] = defaultdict(set)
    for serving in detail.servings:
        participants_by_event[serving.event_id].add(serving.member_id)
    ordered_events = sorted(
        detail.events, key=lambda event: (event.local_date, event.position)
    )
    for member_id, selection_id in pin_by_member.items():
        selection_detail = selection_details.get(selection_id)
        if selection_detail is None:
            raise _issue(
                DomainIssueCode.REQUIRED_FIELD,
                "Pinned selection detail is required for complete-plan validation.",
                field="selection_id",
                value=selection_id,
            )
        if selection_detail.selection.member_id != member_id:
            raise _issue(
                DomainIssueCode.INVALID_IDENTIFIER,
                "Pinned selection must belong to the pinned member.",
                field="selection_id",
                value=selection_id,
            )
        if selection_detail.selection.household_id != detail.plan.household_id:
            raise _issue(
                DomainIssueCode.INVALID_IDENTIFIER,
                "Pinned selection must belong to the MealPlan Household.",
                field="selection_id",
                value=selection_id,
            )
        for local_date in detail.horizon_dates:
            expected = selection_detail.roles_for_weekday(local_date.isoweekday())
            actual = tuple(
                event.role
                for event in ordered_events
                if event.local_date == local_date
                and member_id in participants_by_event[event.id]
            )
            if actual != expected:
                raise _issue(
                    DomainIssueCode.INVALID_CODE,
                    "Member event roles and order must match the accepted resolved schedule.",
                    field="servings",
                    value=(member_id, local_date, actual, expected),
                )


def calculate_meal_plan_nutrition(
    detail: MealPlanDetail,
    recipe_nutrition_by_version_id: dict[UUID, RecipeVersionNutrition],
) -> MealPlanNutrition:
    """Compose existing Nutrition truth; unsupported source nutrition stays unknown."""
    event_by_id = {event.id: event for event in detail.events}
    serving_results: list[ServingNutrition] = []
    for serving in detail.servings:
        event = event_by_id[serving.event_id]
        if (
            event.source_kind is MealSourceKind.COOK_RECIPE
            and event.recipe_version_id is not None
        ):
            nutrition = recipe_nutrition_by_version_id.get(event.recipe_version_id)
            if nutrition is None:
                values = NutritionValues()
                status = NutritionStatus.INCOMPLETE
            elif nutrition.version.id != event.recipe_version_id:
                raise _issue(
                    DomainIssueCode.INVALID_IDENTIFIER,
                    "Recipe nutrition must match the event RecipeVersion.",
                    field="recipe_version_id",
                    value=event.recipe_version_id,
                )
            else:
                values = scale_nutrition_values(
                    nutrition.per_base_serving,
                    serving.portion_servings,
                )
                status = aggregate_nutrition_status((nutrition.status,), values)
        else:
            values = NutritionValues()
            status = NutritionStatus.INCOMPLETE
        serving_results.append(ServingNutrition(serving, event, values, status))

    grouped_days: dict[tuple[UUID, date], list[ServingNutrition]] = defaultdict(list)
    for result in serving_results:
        grouped_days[(result.serving.member_id, result.event.local_date)].append(result)
    member_days: list[MemberDayNutrition] = []
    for (member_id, local_date), results in sorted(
        grouped_days.items(), key=lambda item: (item[0][0].hex, item[0][1])
    ):
        values = aggregate_nutrition_values(item.values for item in results)
        status = aggregate_nutrition_status(
            (item.status for item in results), values
        )
        member_days.append(MemberDayNutrition(member_id, local_date, values, status))

    grouped_weeks: dict[UUID, list[MemberDayNutrition]] = defaultdict(list)
    for result in member_days:
        grouped_weeks[result.member_id].append(result)
    member_weeks: list[MemberWeekNutrition] = []
    for member_id, results in sorted(
        grouped_weeks.items(), key=lambda item: item[0].hex
    ):
        values = aggregate_nutrition_values(item.values for item in results)
        status = aggregate_nutrition_status(
            (item.status for item in results), values
        )
        member_weeks.append(MemberWeekNutrition(member_id, values, status))

    return MealPlanNutrition(
        servings=tuple(serving_results),
        member_days=tuple(member_days),
        member_weeks=tuple(member_weeks),
    )
