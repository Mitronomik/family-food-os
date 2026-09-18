"""Deterministic PR8 planning contracts and explainable baseline heuristic."""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, is_dataclass, replace
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from enum import StrEnum
from uuid import UUID

from app.domain.food_recipes import MealTypeCode
from app.domain.meal_patterns import MealRole
from app.domain.meal_plans import MealSourceKind, MemberMealPatternSelectionDetail
from app.domain.nutrition import NutritionStatus

_VERSION = re.compile(r"^[a-z0-9][a-z0-9._-]{0,119}$")


class PlannerRejectionCode(StrEnum):
    NOT_VERIFIED = "NOT_VERIFIED"
    ROLE_INCOMPATIBLE = "ROLE_INCOMPATIBLE"
    MEMBER_EXCLUDED_INGREDIENT = "MEMBER_EXCLUDED_INGREDIENT"
    NUTRITION_UNAVAILABLE = "NUTRITION_UNAVAILABLE"
    MAX_REPETITIONS = "MAX_REPETITIONS"


class PlannerFailureCode(StrEnum):
    NO_MEMBERS = "NO_MEMBERS"
    INVALID_WEEK_START = "INVALID_WEEK_START"
    MISSING_ACCEPTED_PATTERN = "MISSING_ACCEPTED_PATTERN"
    MISSING_REFERENCE_ENERGY = "MISSING_REFERENCE_ENERGY"
    NO_ELIGIBLE_CANDIDATE = "NO_ELIGIBLE_CANDIDATE"
    INVALID_FIXED_EVENT = "INVALID_FIXED_EVENT"
    AUTHORITATIVE_INPUT_INVALID = "AUTHORITATIVE_INPUT_INVALID"


@dataclass(frozen=True)
class PlannerConfig:
    version: str = "planner-v0.2"
    compatibility_version: str = "meal-role-recipe-v2"
    preference_weight: Decimal = Decimal("20")
    pantry_weight: Decimal = Decimal("4")
    batch_weight: Decimal = Decimal("2")
    time_weight: Decimal = Decimal("0.01")
    repetition_weight: Decimal = Decimal("7")
    max_recipe_repetitions: int = 3

    def __post_init__(self) -> None:
        for name in ("version", "compatibility_version"):
            value = getattr(self, name)
            match = _VERSION.match(value) if isinstance(value, str) else None
            if match is None or match.end() != len(value):
                raise ValueError(f"{name} must be a non-empty version-safe identifier")
        for name in (
            "preference_weight",
            "pantry_weight",
            "batch_weight",
            "time_weight",
            "repetition_weight",
        ):
            value = getattr(self, name)
            if not isinstance(value, Decimal):
                raise TypeError(f"{name} must be Decimal, never float")
            if not value.is_finite() or value < 0:
                raise ValueError(f"{name} must be finite and non-negative")
        if (
            isinstance(self.max_recipe_repetitions, bool)
            or not isinstance(self.max_recipe_repetitions, int)
            or self.max_recipe_repetitions <= 0
        ):
            raise ValueError("max_recipe_repetitions must be a positive integer")


# Only catalogue classifications defensible as self-contained meals in PR8.
ROLE_COMPATIBILITY_V1: dict[MealRole, frozenset[MealTypeCode]] = {
    MealRole.BREAKFAST: frozenset({MealTypeCode.BREAKFAST, MealTypeCode.SANDWICH}),
    MealRole.LUNCH: frozenset({MealTypeCode.MAIN, MealTypeCode.SANDWICH}),
    MealRole.DINNER: frozenset({MealTypeCode.MAIN}),
    MealRole.SNACK: frozenset({MealTypeCode.SANDWICH}),
    MealRole.PRE_WORKOUT: frozenset(),
    MealRole.POST_WORKOUT: frozenset(),
    MealRole.OTHER: frozenset(),
}


@dataclass(frozen=True)
class PlannerCandidate:
    recipe_version_id: UUID
    meal_type_code: MealTypeCode
    food_ingredient_ids: frozenset[UUID]
    kcal_per_serving: Decimal | None
    nutrition_status: NutritionStatus
    is_verified: bool = True
    total_time_minutes: int | None = None
    batch_friendly: bool | None = None


@dataclass(frozen=True)
class MemberPlannerConstraints:
    member_id: UUID
    selection: MemberMealPatternSelectionDetail
    reference_energy_kcal: Decimal | None
    excluded_food_ingredient_ids: frozenset[UUID] = frozenset()
    preferred_recipe_version_ids: frozenset[UUID] = frozenset()


@dataclass(frozen=True)
class FixedPlannerEvent:
    local_date: date
    role: MealRole
    occurrence: int
    source_kind: MealSourceKind
    source_reference: str
    participant_member_ids: frozenset[UUID]
    portions: tuple[tuple[UUID, Decimal], ...] = ()


@dataclass(frozen=True)
class PlannerRequest:
    household_id: UUID
    week_start: date
    members: tuple[MemberPlannerConstraints, ...]
    candidates: tuple[PlannerCandidate, ...]
    pantry_food_ingredient_ids: frozenset[UUID] = frozenset()
    fixed_events: tuple[FixedPlannerEvent, ...] = ()
    recent_plan_ids: tuple[UUID, ...] = ()
    recent_recipe_version_ids: tuple[UUID, ...] = ()


@dataclass(frozen=True)
class PlannedEvent:
    local_date: date
    position: int
    role: MealRole
    participant_member_ids: tuple[UUID, ...]
    source_kind: MealSourceKind
    recipe_version_id: UUID | None
    source_reference: str | None
    portions: tuple[tuple[UUID, Decimal], ...]


@dataclass(frozen=True)
class CandidateTrace:
    local_date: date
    position: int
    role: MealRole
    participant_member_ids: tuple[UUID, ...]
    recipe_version_id: UUID
    rejection_codes: tuple[PlannerRejectionCode, ...]
    score_components: tuple[tuple[str, str], ...]
    total_score: str | None
    selected: bool


@dataclass(frozen=True)
class TraceEvent:
    local_date: date
    position: int
    role: MealRole
    participant_member_ids: tuple[UUID, ...]
    source_kind: MealSourceKind
    recipe_version_id: UUID | None
    source_reference: str | None


@dataclass(frozen=True)
class PlannerTrace:
    household_id: UUID
    week_start: date
    member_selection_ids: tuple[tuple[UUID, UUID], ...]
    config_version: str
    compatibility_version: str
    recent_plan_ids: tuple[UUID, ...]
    applied_exclusions: tuple[tuple[UUID, tuple[UUID, ...]], ...]
    candidate_pool_ids: tuple[UUID, ...]
    request_fingerprint: str
    candidates: tuple[CandidateTrace, ...]
    warnings: tuple[str, ...]
    selected_recipe_version_ids: tuple[UUID, ...]
    final_events: tuple[TraceEvent, ...]
    fixed_events: tuple[TraceEvent, ...]
    failure_code: PlannerFailureCode | None
    failure_reason: str | None
    fingerprint: str
    duration_ms: Decimal = Decimal("0")


@dataclass(frozen=True)
class PlannerSuccess:
    events: tuple[PlannedEvent, ...]
    trace: PlannerTrace


@dataclass(frozen=True)
class PlannerFailure:
    code: PlannerFailureCode
    message: str
    trace: PlannerTrace


PlannerResult = PlannerSuccess | PlannerFailure


def with_duration(result: PlannerResult, duration_ms: Decimal) -> PlannerResult:
    return replace(result, trace=replace(result.trace, duration_ms=duration_ms))


def _canonical(value: object) -> str:
    def default(item: object) -> object:
        if isinstance(item, (UUID, date, Decimal, StrEnum)):
            return str(item)
        if isinstance(item, frozenset):
            return sorted(str(value) for value in item)
        if is_dataclass(item) and not isinstance(item, type):
            return asdict(item)
        raise TypeError(type(item).__name__)

    return json.dumps(value, default=default, sort_keys=True, separators=(",", ":"))


def _fingerprint(value: object) -> str:
    return hashlib.sha256(_canonical(value).encode()).hexdigest()


def _trace(
    request: PlannerRequest,
    config: PlannerConfig,
    candidates: list[CandidateTrace],
    warnings: tuple[str, ...],
    events: tuple[PlannedEvent, ...] = (),
    failure: tuple[PlannerFailureCode, str] | None = None,
) -> PlannerTrace:
    selections = tuple(
        sorted(
            ((m.member_id, m.selection.selection.id) for m in request.members),
            key=lambda x: x[0].hex,
        )
    )
    exclusions = tuple(
        sorted(
            (
                (
                    m.member_id,
                    tuple(sorted(m.excluded_food_ingredient_ids, key=lambda x: x.hex)),
                )
                for m in request.members
            ),
            key=lambda x: x[0].hex,
        )
    )
    pool = tuple(
        sorted((c.recipe_version_id for c in request.candidates), key=lambda x: x.hex)
    )
    final = tuple(
        TraceEvent(
            e.local_date,
            e.position,
            e.role,
            e.participant_member_ids,
            e.source_kind,
            e.recipe_version_id,
            e.source_reference,
        )
        for e in events
    )
    fixed = tuple(e for e in final if e.source_kind is not MealSourceKind.COOK_RECIPE)
    selected = tuple(
        e.recipe_version_id for e in final if e.recipe_version_id is not None
    )
    request_hash = _fingerprint(asdict(request))
    code, reason = failure if failure else (None, None)
    deterministic = (
        request.household_id,
        request.week_start,
        selections,
        config.version,
        config.compatibility_version,
        request.recent_plan_ids,
        exclusions,
        pool,
        request_hash,
        tuple(asdict(c) for c in candidates),
        warnings,
        selected,
        final,
        fixed,
        code,
        reason,
    )
    return PlannerTrace(
        request.household_id,
        request.week_start,
        selections,
        config.version,
        config.compatibility_version,
        request.recent_plan_ids,
        exclusions,
        pool,
        request_hash,
        tuple(candidates),
        warnings,
        selected,
        final,
        fixed,
        code,
        reason,
        _fingerprint(deterministic),
    )


def _failure(
    request: PlannerRequest,
    config: PlannerConfig,
    code: PlannerFailureCode,
    reason: str,
    candidates: list[CandidateTrace] | None = None,
) -> PlannerFailure:
    return PlannerFailure(
        code,
        reason,
        _trace(request, config, candidates or [], (reason,), failure=(code, reason)),
    )


def generate_week(
    request: PlannerRequest, config: PlannerConfig = PlannerConfig()
) -> PlannerResult:
    """Build a complete semantic week in memory; callers persist only success."""
    if request.week_start.isoweekday() != 1:
        return _failure(
            request,
            config,
            PlannerFailureCode.INVALID_WEEK_START,
            "week_start must be Monday",
        )
    if not request.members:
        return _failure(
            request,
            config,
            PlannerFailureCode.NO_MEMBERS,
            "At least one member is required",
        )
    if any(
        m.selection.selection.member_id != m.member_id
        or m.selection.selection.household_id != request.household_id
        for m in request.members
    ):
        return _failure(
            request,
            config,
            PlannerFailureCode.MISSING_ACCEPTED_PATTERN,
            "Every member must have its Household-scoped accepted pattern",
        )
    if any(
        m.reference_energy_kcal is None or m.reference_energy_kcal <= 0
        for m in request.members
    ):
        return _failure(
            request,
            config,
            PlannerFailureCode.MISSING_REFERENCE_ENERGY,
            "Weekly normalization requires reference energy for every member",
        )

    members = {m.member_id: m for m in request.members}
    slots: dict[tuple[date, MealRole, int], set[UUID]] = defaultdict(set)
    slot_order: dict[tuple[date, MealRole, int], int] = {}
    for member in sorted(request.members, key=lambda x: x.member_id.hex):
        for offset in range(7):
            seen: Counter[MealRole] = Counter()
            for order, role in enumerate(
                member.selection.roles_for_weekday(offset + 1), 1
            ):
                seen[role] += 1
                key = (request.week_start + timedelta(days=offset), role, seen[role])
                slots[key].add(member.member_id)
                slot_order[key] = min(slot_order.get(key, order), order)

    fixed: dict[tuple[date, MealRole, int], FixedPlannerEvent] = {}
    for event in request.fixed_events:
        key = (event.local_date, event.role, event.occurrence)
        portions = dict(event.portions)
        if (
            key in fixed
            or key not in slots
            or event.source_kind is MealSourceKind.COOK_RECIPE
            or not event.participant_member_ids
            or not event.participant_member_ids <= slots[key]
            or set(portions) != event.participant_member_ids
            or any(v <= 0 for v in portions.values())
        ):
            return _failure(
                request,
                config,
                PlannerFailureCode.INVALID_FIXED_EVENT,
                "Fixed event identity, participants, source, or portions are invalid",
            )
        fixed[key] = event

    counts = Counter(request.recent_recipe_version_ids)
    traces: list[CandidateTrace] = []
    provisional: list[
        tuple[
            date,
            MealRole,
            tuple[UUID, ...],
            PlannerCandidate | None,
            FixedPlannerEvent | None,
        ]
    ] = []
    ordered = sorted(
        slots.items(), key=lambda x: (x[0][0], slot_order[x[0]], x[0][1].value, x[0][2])
    )
    for (local_date, role, occurrence), all_participants in ordered:
        remaining = set(all_participants)
        if fixed_event := fixed.get((local_date, role, occurrence)):
            participants = tuple(
                sorted(fixed_event.participant_member_ids, key=lambda x: x.hex)
            )
            provisional.append((local_date, role, participants, None, fixed_event))
            remaining -= fixed_event.participant_member_ids
        while remaining:
            choices: list[
                tuple[
                    int,
                    Decimal,
                    str,
                    PlannerCandidate,
                    tuple[UUID, ...],
                    tuple[tuple[str, str], ...],
                ]
            ] = []
            trace_position = len(provisional) + 1
            for candidate in sorted(
                request.candidates, key=lambda x: x.recipe_version_id.hex
            ):
                base_rejections: list[PlannerRejectionCode] = []
                if not candidate.is_verified:
                    base_rejections.append(PlannerRejectionCode.NOT_VERIFIED)
                if candidate.meal_type_code not in ROLE_COMPATIBILITY_V1[role]:
                    base_rejections.append(PlannerRejectionCode.ROLE_INCOMPATIBLE)
                if (
                    candidate.nutrition_status is NutritionStatus.INCOMPLETE
                    or candidate.kcal_per_serving is None
                    or candidate.kcal_per_serving <= 0
                ):
                    base_rejections.append(PlannerRejectionCode.NUTRITION_UNAVAILABLE)
                if counts[candidate.recipe_version_id] >= config.max_recipe_repetitions:
                    base_rejections.append(PlannerRejectionCode.MAX_REPETITIONS)
                compatible = tuple(
                    sorted(
                        (
                            mid
                            for mid in remaining
                            if not candidate.food_ingredient_ids
                            & members[mid].excluded_food_ingredient_ids
                        ),
                        key=lambda x: x.hex,
                    )
                )
                rejected = list(base_rejections)
                if len(compatible) != len(remaining):
                    rejected.append(PlannerRejectionCode.MEMBER_EXCLUDED_INGREDIENT)
                components: tuple[tuple[str, str], ...] = ()
                total = None
                if not base_rejections and compatible:
                    preference = config.preference_weight * sum(
                        candidate.recipe_version_id
                        in members[mid].preferred_recipe_version_ids
                        for mid in compatible
                    )
                    pantry = config.pantry_weight * Decimal(
                        len(
                            candidate.food_ingredient_ids
                            & request.pantry_food_ingredient_ids
                        )
                    )
                    batch = (
                        config.batch_weight if candidate.batch_friendly else Decimal(0)
                    )
                    time_score = -(
                        config.time_weight * Decimal(candidate.total_time_minutes or 0)
                    )
                    historical = (
                        config.repetition_weight * counts[candidate.recipe_version_id]
                    )
                    repetition = -historical
                    total = preference + pantry + batch + time_score + repetition
                    components = tuple(
                        (k, str(v))
                        for k, v in (
                            ("preference", preference),
                            ("pantry", pantry),
                            ("batch", batch),
                            ("time", time_score),
                            ("repetition", repetition),
                        )
                    )
                    choices.append(
                        (
                            len(compatible),
                            total,
                            candidate.recipe_version_id.hex,
                            candidate,
                            compatible,
                            components,
                        )
                    )
                traces.append(
                    CandidateTrace(
                        local_date,
                        trace_position,
                        role,
                        tuple(sorted(remaining, key=lambda x: x.hex)),
                        candidate.recipe_version_id,
                        tuple(rejected),
                        components,
                        None if total is None else str(total),
                        False,
                    )
                )
            if not choices:
                return _failure(
                    request,
                    config,
                    PlannerFailureCode.NO_ELIGIBLE_CANDIDATE,
                    f"no_candidate:{local_date}:{role.value}:{occurrence}",
                    traces,
                )
            _, _, _, selected, group, _ = min(
                choices, key=lambda x: (-x[0], -x[1], x[2])
            )
            counts[selected.recipe_version_id] += 1
            for index in range(len(traces) - 1, -1, -1):
                item = traces[index]
                if (
                    item.local_date == local_date
                    and item.role is role
                    and item.recipe_version_id == selected.recipe_version_id
                    and item.position == trace_position
                ):
                    traces[index] = replace(
                        item, participant_member_ids=group, selected=True
                    )
                    break
            provisional.append((local_date, role, group, selected, None))
            remaining -= set(group)

    base_kcal: dict[UUID, Decimal] = defaultdict(lambda: Decimal(0))
    for _, _, participants, candidate, _ in provisional:
        if candidate:
            for member_id in participants:
                base_kcal[member_id] += candidate.kcal_per_serving or Decimal(0)
    if any(base_kcal[mid] <= 0 for mid in members):
        return _failure(
            request,
            config,
            PlannerFailureCode.MISSING_REFERENCE_ENERGY,
            "Recipe-backed energy is required for weekly normalization",
            traces,
        )
    factors = {
        mid: (
            (members[mid].reference_energy_kcal or Decimal(0)) * 7 / base_kcal[mid]
        ).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)
        for mid in members
    }
    positions: Counter[date] = Counter()
    events: list[PlannedEvent] = []
    for local_date, role, participants, candidate, fixed_event in provisional:
        positions[local_date] += 1
        if candidate:
            events.append(
                PlannedEvent(
                    local_date,
                    positions[local_date],
                    role,
                    participants,
                    MealSourceKind.COOK_RECIPE,
                    candidate.recipe_version_id,
                    None,
                    tuple((mid, factors[mid]) for mid in participants),
                )
            )
        else:
            assert fixed_event
            events.append(
                PlannedEvent(
                    local_date,
                    positions[local_date],
                    role,
                    participants,
                    fixed_event.source_kind,
                    None,
                    fixed_event.source_reference,
                    fixed_event.portions,
                )
            )
    event_tuple = tuple(events)
    trace = _trace(
        request,
        config,
        traces,
        ("cost_not_scored_unknown", "fixed_non_recipe_nutrition_not_credited"),
        event_tuple,
    )
    return PlannerSuccess(event_tuple, trace)
