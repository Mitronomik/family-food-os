"""Deterministic PR8 planning contracts and explainable baseline heuristic."""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from enum import StrEnum
from uuid import UUID

from app.domain.food_recipes import MealTypeCode
from app.domain.meal_patterns import MealRole
from app.domain.meal_plans import MealSourceKind, MemberMealPatternSelectionDetail
from app.domain.nutrition import NutritionStatus


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


@dataclass(frozen=True)
class PlannerConfig:
    version: str = "planner-v0.1"
    compatibility_version: str = "meal-role-recipe-v1"
    preference_weight: Decimal = Decimal("20")
    pantry_weight: Decimal = Decimal("4")
    batch_weight: Decimal = Decimal("2")
    time_weight: Decimal = Decimal("0.01")
    repetition_weight: Decimal = Decimal("7")
    max_recipe_repetitions: int = 3


ROLE_COMPATIBILITY_V1: dict[MealRole, frozenset[MealTypeCode]] = {
    MealRole.BREAKFAST: frozenset({MealTypeCode.BREAKFAST, MealTypeCode.SANDWICH}),
    MealRole.LUNCH: frozenset(
        {MealTypeCode.MAIN, MealTypeCode.SALAD, MealTypeCode.SANDWICH}
    ),
    MealRole.DINNER: frozenset(
        {MealTypeCode.MAIN, MealTypeCode.SALAD, MealTypeCode.SIDE}
    ),
    MealRole.SNACK: frozenset(
        {MealTypeCode.SANDWICH, MealTypeCode.SALAD, MealTypeCode.OTHER}
    ),
    MealRole.PRE_WORKOUT: frozenset(
        {MealTypeCode.BREAKFAST, MealTypeCode.SANDWICH, MealTypeCode.OTHER}
    ),
    MealRole.POST_WORKOUT: frozenset(
        {MealTypeCode.MAIN, MealTypeCode.BREAKFAST, MealTypeCode.OTHER}
    ),
    MealRole.OTHER: frozenset(MealTypeCode),
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
    previous_plan_id: UUID | None = None


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
    recipe_version_id: UUID
    rejection_codes: tuple[PlannerRejectionCode, ...]
    score_components: tuple[tuple[str, str], ...]
    total_score: str | None
    selected: bool


@dataclass(frozen=True)
class PlannerTrace:
    config_version: str
    compatibility_version: str
    request_fingerprint: str
    candidates: tuple[CandidateTrace, ...]
    warnings: tuple[str, ...]
    selected_recipe_version_ids: tuple[str, ...]
    fingerprint: str


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


def _canonical(value: object) -> str:
    def default(item: object) -> object:
        if isinstance(item, (UUID, date, Decimal, StrEnum)):
            return str(item)
        if isinstance(item, frozenset):
            return sorted(str(value) for value in item)
        raise TypeError(type(item).__name__)

    return json.dumps(value, default=default, sort_keys=True, separators=(",", ":"))


def _fingerprint(value: object) -> str:
    return hashlib.sha256(_canonical(value).encode()).hexdigest()


def _empty_trace(
    config: PlannerConfig, request: PlannerRequest, warning: str
) -> PlannerTrace:
    request_hash = _fingerprint(asdict(request))
    body = (
        config.version,
        config.compatibility_version,
        request_hash,
        (),
        (warning,),
        (),
    )
    return PlannerTrace(*body, _fingerprint(body))


def generate_week(
    request: PlannerRequest, config: PlannerConfig = PlannerConfig()
) -> PlannerResult:
    """Build a complete semantic week in memory; callers persist only success."""
    if request.week_start.isoweekday() != 1:
        return PlannerFailure(
            PlannerFailureCode.INVALID_WEEK_START,
            "week_start must be Monday",
            _empty_trace(config, request, "invalid_week_start"),
        )
    if not request.members:
        return PlannerFailure(
            PlannerFailureCode.NO_MEMBERS,
            "At least one member is required",
            _empty_trace(config, request, "no_members"),
        )
    if any(
        member.selection.selection.member_id != member.member_id
        for member in request.members
    ):
        return PlannerFailure(
            PlannerFailureCode.MISSING_ACCEPTED_PATTERN,
            "Every member must have its accepted pattern",
            _empty_trace(config, request, "selection_member_mismatch"),
        )
    if any(
        member.reference_energy_kcal is None or member.reference_energy_kcal <= 0
        for member in request.members
    ):
        return PlannerFailure(
            PlannerFailureCode.MISSING_REFERENCE_ENERGY,
            "Weekly normalization requires reference energy for every member",
            _empty_trace(config, request, "missing_reference_energy"),
        )

    members = {member.member_id: member for member in request.members}
    slots: dict[tuple[date, MealRole, int], set[UUID]] = defaultdict(set)
    slot_order: dict[tuple[date, MealRole, int], int] = {}
    for member in sorted(request.members, key=lambda item: item.member_id.hex):
        for day_offset in range(7):
            roles = member.selection.roles_for_weekday(day_offset + 1)
            occurrences: Counter[MealRole] = Counter()
            for schedule_position, role in enumerate(roles, start=1):
                occurrences[role] += 1
                key = (
                    request.week_start + timedelta(days=day_offset),
                    role,
                    occurrences[role],
                )
                slots[key].add(member.member_id)
                slot_order[key] = min(
                    slot_order.get(key, schedule_position), schedule_position
                )

    fixed = {
        (event.local_date, event.role, event.occurrence): event
        for event in request.fixed_events
    }
    if len(fixed) != len(request.fixed_events) or any(
        key not in slots for key in fixed
    ):
        return PlannerFailure(
            PlannerFailureCode.INVALID_FIXED_EVENT,
            "Fixed event must identify one planned opportunity",
            _empty_trace(config, request, "invalid_fixed_event"),
        )

    counts: Counter[UUID] = Counter()
    traces: list[CandidateTrace] = []
    provisional: list[
        tuple[
            date,
            int,
            MealRole,
            tuple[UUID, ...],
            PlannerCandidate | None,
            FixedPlannerEvent | None,
        ]
    ] = []
    positions: Counter[date] = Counter()
    ordered_slots = sorted(
        slots.items(),
        key=lambda item: (
            item[0][0],
            slot_order[item[0]],
            item[0][1].value,
            item[0][2],
        ),
    )
    for (local_date, role, occurrence), participant_set in ordered_slots:
        positions[local_date] += 1
        position = positions[local_date]
        participants = tuple(sorted(participant_set, key=lambda value: value.hex))
        if fixed_event := fixed.get((local_date, role, occurrence)):
            fixed_portions = dict(fixed_event.portions)
            if (
                fixed_event.participant_member_ids != participant_set
                or fixed_event.source_kind is MealSourceKind.COOK_RECIPE
                or set(fixed_portions) != participant_set
                or any(portion <= 0 for portion in fixed_portions.values())
            ):
                return PlannerFailure(
                    PlannerFailureCode.INVALID_FIXED_EVENT,
                    "Fixed event participants/source are invalid",
                    _empty_trace(config, request, "invalid_fixed_event"),
                )
            provisional.append(
                (local_date, position, role, participants, None, fixed_event)
            )
            continue

        ranked: list[
            tuple[Decimal, str, PlannerCandidate, tuple[tuple[str, str], ...]]
        ] = []
        for candidate in sorted(
            request.candidates, key=lambda item: item.recipe_version_id.hex
        ):
            rejected: list[PlannerRejectionCode] = []
            if not candidate.is_verified:
                rejected.append(PlannerRejectionCode.NOT_VERIFIED)
            if candidate.meal_type_code not in ROLE_COMPATIBILITY_V1[role]:
                rejected.append(PlannerRejectionCode.ROLE_INCOMPATIBLE)
            if (
                candidate.nutrition_status is NutritionStatus.INCOMPLETE
                or candidate.kcal_per_serving is None
                or candidate.kcal_per_serving <= 0
            ):
                rejected.append(PlannerRejectionCode.NUTRITION_UNAVAILABLE)
            if any(
                candidate.food_ingredient_ids
                & members[mid].excluded_food_ingredient_ids
                for mid in participants
            ):
                rejected.append(PlannerRejectionCode.MEMBER_EXCLUDED_INGREDIENT)
            if counts[candidate.recipe_version_id] >= config.max_recipe_repetitions:
                rejected.append(PlannerRejectionCode.MAX_REPETITIONS)
            components: tuple[tuple[str, str], ...] = ()
            total: Decimal | None = None
            if not rejected:
                preference = config.preference_weight * sum(
                    candidate.recipe_version_id
                    in members[mid].preferred_recipe_version_ids
                    for mid in participants
                )
                pantry = config.pantry_weight * Decimal(
                    len(
                        candidate.food_ingredient_ids
                        & request.pantry_food_ingredient_ids
                    )
                )
                batch = (
                    config.batch_weight if candidate.batch_friendly else Decimal("0")
                )
                time = -(
                    config.time_weight * Decimal(candidate.total_time_minutes or 0)
                )
                repetition = -(
                    config.repetition_weight * counts[candidate.recipe_version_id]
                )
                total = preference + pantry + batch + time + repetition
                components = tuple(
                    (name, str(value))
                    for name, value in (
                        ("preference", preference),
                        ("pantry", pantry),
                        ("batch", batch),
                        ("time", time),
                        ("repetition", repetition),
                    )
                )
                ranked.append(
                    (total, candidate.recipe_version_id.hex, candidate, components)
                )
            traces.append(
                CandidateTrace(
                    local_date,
                    position,
                    role,
                    candidate.recipe_version_id,
                    tuple(rejected),
                    components,
                    None if total is None else str(total),
                    False,
                )
            )
        if not ranked:
            warning = f"no_candidate:{local_date}:{role.value}:{occurrence}"
            trace = _make_trace(config, request, traces, (warning,), provisional)
            return PlannerFailure(
                PlannerFailureCode.NO_ELIGIBLE_CANDIDATE, warning, trace
            )
        _, _, selected, _ = min(ranked, key=lambda item: (-item[0], item[1]))
        counts[selected.recipe_version_id] += 1
        last = next(
            index
            for index in range(len(traces) - 1, -1, -1)
            if traces[index].recipe_version_id == selected.recipe_version_id
            and traces[index].local_date == local_date
            and traces[index].position == position
        )
        traces[last] = CandidateTrace(**{**asdict(traces[last]), "selected": True})
        provisional.append((local_date, position, role, participants, selected, None))

    base_kcal: dict[UUID, Decimal] = defaultdict(lambda: Decimal("0"))
    for _, _, _, participants, candidate, fixed_event in provisional:
        if candidate is not None:
            for member_id in participants:
                base_kcal[member_id] += candidate.kcal_per_serving or Decimal("0")
        elif fixed_event and fixed_event.portions:
            # Fixed non-recipe nutrition is unknown and is deliberately not credited.
            pass
    if any(base_kcal[mid] <= 0 for mid in members):
        return PlannerFailure(
            PlannerFailureCode.MISSING_REFERENCE_ENERGY,
            "Recipe-backed energy is required for weekly normalization",
            _make_trace(
                config,
                request,
                traces,
                ("fixed_event_energy_not_credited",),
                provisional,
            ),
        )
    factors = {
        mid: (
            (members[mid].reference_energy_kcal or Decimal("0")) * 7 / base_kcal[mid]
        ).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)
        for mid in members
    }
    events: list[PlannedEvent] = []
    for local_date, position, role, participants, candidate, fixed_event in provisional:
        if candidate:
            portions = tuple((mid, factors[mid]) for mid in participants)
            events.append(
                PlannedEvent(
                    local_date,
                    position,
                    role,
                    participants,
                    MealSourceKind.COOK_RECIPE,
                    candidate.recipe_version_id,
                    None,
                    portions,
                )
            )
        else:
            assert fixed_event is not None
            events.append(
                PlannedEvent(
                    local_date,
                    position,
                    role,
                    participants,
                    fixed_event.source_kind,
                    None,
                    fixed_event.source_reference,
                    fixed_event.portions,
                )
            )
    trace = _make_trace(
        config,
        request,
        traces,
        ("cost_not_scored_unknown", "fixed_non_recipe_nutrition_not_credited"),
        provisional,
    )
    return PlannerSuccess(tuple(events), trace)


def _make_trace(
    config: PlannerConfig,
    request: PlannerRequest,
    traces: list[CandidateTrace],
    warnings: tuple[str, ...],
    provisional: object,
) -> PlannerTrace:
    request_hash = _fingerprint(asdict(request))
    selected = tuple(str(item.recipe_version_id) for item in traces if item.selected)
    body = (
        config.version,
        config.compatibility_version,
        request_hash,
        tuple(asdict(item) for item in traces),
        warnings,
        selected,
    )
    return PlannerTrace(
        config.version,
        config.compatibility_version,
        request_hash,
        tuple(traces),
        warnings,
        selected,
        _fingerprint(body),
    )
