"""Non-persisted MealPlan component proposals (domain-only foundation).

A HouseholdMealEvent is an eating opportunity; it is NOT one RecipeVersion for
all future meal structures. This module validates an explicitly proposed set
of recipe courses and individual course Servings against an existing event.
It grants no recipe-role suitability, physical portion, kcal, Shopping, Prep,
Planner, or persistence authority. No accepted historical plan is changed.

The caller supplies a version-labelled draft structure rule. It is NOT a
published MealPatternProgram or a medical / universal meal structure standard.
"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, replace
from datetime import datetime
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from hashlib import sha256
from uuid import UUID

from app.domain.errors import DomainIssue, DomainIssueCode, DomainValidationError
from app.domain.meal_patterns import MealRole
from app.domain.meal_plans import MealPlanDetail, MealPlanStatus, MealSourceKind

_SERVING_STEP = Decimal("0.000001")
DRAFT_STATUS = "NON_PERSISTENT_RESEARCH_PROPOSAL"


class MealCourseKind(StrEnum):
    """Course order is policy-owned, not inferred from Recipe.meal_type_code."""

    FIRST = "FIRST"
    SECOND = "SECOND"
    DESSERT = "DESSERT"
    MAIN = "MAIN"
    SIDE = "SIDE"
    SNACK = "SNACK"
    DRINK = "DRINK"


class RequiredCourseCoverage(StrEnum):
    """Whether course minima apply to the event or every home participant."""

    EVENT = "EVENT"
    PER_PARTICIPANT = "PER_PARTICIPANT"


def _issue(field: str, reason: str) -> DomainValidationError:
    return DomainValidationError(
        DomainIssue(
            code=DomainIssueCode.INVALID_CODE,
            message=reason,
            field=field,
            value="invalid proposal",
            next_action="Check accepted event, source, and draft structure inputs.",
        )
    )


def _id(value: UUID, field: str) -> UUID:
    if not isinstance(value, UUID) or value.version != 4:
        raise _issue(field, "Identity must be a UUIDv4.")
    return value


def _ordinal(value: int, field: str, *, allow_zero: bool = False) -> int:
    if type(value) is not int or value < (0 if allow_zero else 1):
        raise _issue(field, "Position and count must be valid integers.")
    return value


def _course(kind: MealCourseKind) -> MealCourseKind:
    try:
        return MealCourseKind(kind)
    except (ValueError, TypeError) as exc:
        raise _issue("course", "Unsupported course kind.") from exc


@dataclass(frozen=True)
class CourseCardinality:
    kind: MealCourseKind
    minimum: int
    maximum: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "kind", _course(self.kind))
        _ordinal(self.minimum, "minimum", allow_zero=True)
        _ordinal(self.maximum, "maximum")
        if self.maximum < self.minimum:
            raise _issue("course", "Course maximum cannot be below minimum.")


@dataclass(frozen=True)
class DraftMealStructureRule:
    """Explicit draft rule: cardinality and who must receive each required course.

    PER_PARTICIPANT means every actual home member gets at least the minimum
    number of courses of each required kind. An optional kind (minimum=0)
    remains optional for every member. EVENT checks event-wide counts only.
    Neither mode grants physical portion, nutritional or role suitability.
    """

    code: str
    version: int
    meal_role: MealRole
    requirements: tuple[CourseCardinality, ...]
    coverage: RequiredCourseCoverage

    def __post_init__(self) -> None:
        if not isinstance(self.code, str) or not self.code.strip():
            raise _issue("code", "A versioned rule code is required.")
        _ordinal(self.version, "version")
        try:
            role = MealRole(self.meal_role)
        except (ValueError, TypeError) as exc:
            raise _issue("meal_role", "Unknown meal role.") from exc
        object.__setattr__(self, "meal_role", role)
        try:
            coverage = RequiredCourseCoverage(self.coverage)
        except (ValueError, TypeError) as exc:
            raise _issue(
                "coverage", "Explicit course coverage scope is required."
            ) from exc
        object.__setattr__(self, "coverage", coverage)
        if (
            not isinstance(self.requirements, tuple)
            or not self.requirements
            or any(
                not isinstance(item, CourseCardinality) for item in self.requirements
            )
            or len({item.kind for item in self.requirements}) != len(self.requirements)
        ):
            raise _issue(
                "requirements", "Course requirements must be unique and typed."
            )


@dataclass(frozen=True)
class MealComponentDraft:
    event_id: UUID
    position: int
    course: MealCourseKind
    recipe_version_id: UUID

    def __post_init__(self) -> None:
        _id(self.event_id, "event_id")
        _ordinal(self.position, "position")
        object.__setattr__(self, "course", _course(self.course))
        _id(self.recipe_version_id, "recipe_version_id")


@dataclass(frozen=True)
class MemberComponentServingDraft:
    event_id: UUID
    component_position: int
    member_id: UUID
    portion_servings: Decimal

    def __post_init__(self) -> None:
        _id(self.event_id, "event_id")
        _ordinal(self.component_position, "component_position")
        _id(self.member_id, "member_id")
        value = self.portion_servings
        if not isinstance(value, Decimal) or not value.is_finite() or value <= 0:
            raise _issue("portion_servings", "A finite positive Decimal is required.")
        try:
            if value.quantize(_SERVING_STEP) != value:
                raise _issue(
                    "portion_servings", "Fraction exceeds supported precision."
                )
        except InvalidOperation as exc:
            raise _issue("portion_servings", "Unsupported Decimal precision.") from exc


@dataclass(frozen=True)
class MealEventCompositionDraft:
    """Recipe course plan anchored to one existing event, never a new MealEvent."""

    plan_id: UUID
    event_id: UUID
    components: tuple[MealComponentDraft, ...]
    servings: tuple[MemberComponentServingDraft, ...]

    def __post_init__(self) -> None:
        _id(self.plan_id, "plan_id")
        _id(self.event_id, "event_id")
        if (
            not isinstance(self.components, tuple)
            or not self.components
            or not isinstance(self.servings, tuple)
            or not self.servings
            or any(not isinstance(c, MealComponentDraft) for c in self.components)
            or any(
                not isinstance(s, MemberComponentServingDraft) for s in self.servings
            )
        ):
            raise _issue(
                "components", "Non-empty typed component and Serving rows required."
            )
        positions = [c.position for c in self.components]
        if sorted(positions) != list(range(1, len(positions) + 1)):
            raise _issue(
                "position", "Component positions must be unique and contiguous."
            )
        if any(c.event_id != self.event_id for c in self.components):
            raise _issue("event_id", "Components must refer to the same event.")
        if any(s.event_id != self.event_id for s in self.servings):
            raise _issue(
                "event_id", "Member component Servings must refer to the event."
            )
        if any(s.component_position not in positions for s in self.servings):
            raise _issue(
                "component_position", "Serving refers to an unknown component."
            )
        pairs = [(s.component_position, s.member_id) for s in self.servings]
        if len(pairs) != len(set(pairs)):
            raise _issue(
                "servings", "A member has a repeated Serving for one component."
            )


def validate_composition_draft(
    proposal: MealEventCompositionDraft,
    existing: MealPlanDetail,
    structure: DraftMealStructureRule,
) -> None:
    """Fail closed against actual source plan and explicit draft course structure.

    This does not validate kcal, nutrition completeness, recipe rights,
    ingredient allergens, course suitability, physical sizes or shopping cost.
    The caller must not treat success as permission to persist or publish.
    """
    if (
        not isinstance(proposal, MealEventCompositionDraft)
        or not isinstance(existing, MealPlanDetail)
        or not isinstance(structure, DraftMealStructureRule)
    ):
        raise _issue("proposal", "Typed plan/proposal/rule required.")
    if proposal.plan_id != existing.plan.id:
        raise _issue("plan_id", "Proposal cannot reference another plan revision.")
    matched = [event for event in existing.events if event.id == proposal.event_id]
    if len(matched) != 1:
        raise _issue(
            "event_id", "Composition must reference one accepted source event."
        )
    event = matched[0]
    if event.source_kind is not MealSourceKind.COOK_RECIPE:
        raise _issue(
            "source_kind", "Only recipe-backed source events can be projected."
        )
    if event.role is not structure.meal_role:
        raise _issue("meal_role", "Structure rule does not apply to this meal.")
    if (
        sum(c.recipe_version_id == event.recipe_version_id for c in proposal.components)
        != 1
    ):
        raise _issue(
            "recipe_version_id", "Original source recipe must appear exactly once."
        )

    # Member attendance comes exclusively from persisted Serving rows. No
    # outside-food events, phantom guests or zero-kcal stand-ins are created.
    old_members = {s.member_id for s in existing.servings if s.event_id == event.id}
    new_members = {s.member_id for s in proposal.servings}
    if not old_members or new_members != old_members:
        raise _issue(
            "member_id", "Proposed members must equal actual home participants."
        )

    counts = Counter(c.course for c in proposal.components)
    expected_kinds = {r.kind for r in structure.requirements}
    if set(counts) - expected_kinds:
        raise _issue("course", "The structure does not authorize an added course.")
    for requirement in structure.requirements:
        count = counts[requirement.kind]
        if not requirement.minimum <= count <= requirement.maximum:
            raise _issue("course", "Missing, extra or unsupported meal course.")

    if structure.coverage is RequiredCourseCoverage.PER_PARTICIPANT:
        # Event-wide course counts and total member union alone are insufficient:
        # two participants could each receive only half of the required lunch.
        # Count *actual* course Servings for each existing home participant.
        by_position = {
            component.position: component.course for component in proposal.components
        }
        per_member = {member_id: Counter() for member_id in old_members}
        for serving in proposal.servings:
            per_member[serving.member_id][by_position[serving.component_position]] += 1
        for member_courses in per_member.values():
            for requirement in structure.requirements:
                if member_courses[requirement.kind] < requirement.minimum:
                    raise _issue(
                        "servings",
                        "An at-home participant is missing a required course.",
                    )

    # A rule defines ordering but not universal number of meals or physiological
    # portions. Optional desserts may have their own participant subset.
    order = {r.kind: i for i, r in enumerate(structure.requirements)}
    ordered_components = sorted(proposal.components, key=lambda c: c.position)
    course_order = [order[c.course] for c in ordered_components]
    if course_order != sorted(course_order):
        raise _issue("course", "Course order contradicts this draft structure.")
    served_positions = {s.component_position for s in proposal.servings}
    if served_positions != {c.position for c in proposal.components}:
        raise _issue("servings", "Every included recipe component needs a participant.")


# 0044 immutable persistence form; intentionally distinct from the ephemeral
# research proposal above. No source-to-Shopping authority is gained here.
SNAPSHOT_SCHEMA_VERSION = 1
COMPOSITION_ADMISSION = "DIAGNOSTIC_ONLY"


def _canonical(data: object) -> str:
    return json.dumps(
        data, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    )


def serialized_requirements(rule: DraftMealStructureRule) -> str:
    """Rule order is part of immutable identity; do not sort its courses."""
    return _canonical(
        [
            {
                "kind": requirement.kind.value,
                "minimum": requirement.minimum,
                "maximum": requirement.maximum,
            }
            for requirement in rule.requirements
        ]
    )


def rule_snapshot_digest(rule: DraftMealStructureRule) -> str:
    payload = {
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "code": rule.code,
        "version": rule.version,
        "meal_role": rule.meal_role.value,
        "coverage": rule.coverage.value,
        "requirements": json.loads(serialized_requirements(rule)),
    }
    return sha256(_canonical(payload).encode("utf-8")).hexdigest()


def restore_rule_snapshot(
    *,
    code: str,
    version: int,
    meal_role: MealRole,
    coverage: str,
    schema_version: int,
    requirements_json: str,
    sha256_hex: str,
) -> DraftMealStructureRule:
    """Fail-closed process-independent reconstruction; no rule catalogue lookup."""
    if schema_version != SNAPSHOT_SCHEMA_VERSION or type(schema_version) is not int:
        raise _issue("schema_version", "Unknown course-rule snapshot schema.")
    if not isinstance(requirements_json, str):
        raise _issue("requirements_json", "Missing immutable course requirements.")
    try:
        parsed = json.loads(requirements_json)
    except (ValueError, TypeError) as exc:
        raise _issue(
            "requirements_json", "Malformed immutable course requirements."
        ) from exc
    if not isinstance(parsed, list) or not 1 <= len(parsed) <= 16:
        raise _issue(
            "requirements_json", "Course requirements must be a bounded array."
        )
    requirements = []
    for item in parsed:
        if (
            not isinstance(item, dict)
            or set(item) != {"kind", "minimum", "maximum"}
            or type(item["minimum"]) is not int
            or type(item["maximum"]) is not int
        ):
            raise _issue("requirements_json", "Invalid typed course requirement.")
        requirements.append(
            CourseCardinality(
                kind=item["kind"],
                minimum=item["minimum"],
                maximum=item["maximum"],
            )
        )
    rule = DraftMealStructureRule(
        code=code,
        version=version,
        meal_role=meal_role,
        requirements=tuple(requirements),
        coverage=coverage,
    )
    if (
        serialized_requirements(rule) != requirements_json
        or not isinstance(sha256_hex, str)
        or len(sha256_hex) != 64
        or sha256_hex != rule_snapshot_digest(rule)
    ):
        raise _issue("rule_snapshot_sha256", "Course rule snapshot does not reconcile.")
    return rule


@dataclass(frozen=True)
class PersistedMealComponent:
    id: UUID
    event_id: UUID
    position: int
    course: MealCourseKind
    recipe_version_id: UUID
    created_at: datetime

    def __post_init__(self) -> None:
        for name in ("id", "event_id", "recipe_version_id"):
            _id(getattr(self, name), name)
        _ordinal(self.position, "position")
        object.__setattr__(self, "course", _course(self.course))


@dataclass(frozen=True)
class PersistedMemberComponentServing:
    component_id: UUID
    member_id: UUID
    portion_servings: Decimal
    created_at: datetime

    def __post_init__(self) -> None:
        _id(self.component_id, "component_id")
        _id(self.member_id, "member_id")
        value = self.portion_servings
        if not isinstance(value, Decimal) or not value.is_finite() or value <= 0:
            raise _issue("portion_servings", "A finite positive Decimal is required.")
        if value.as_tuple().exponent < -6 or value > Decimal("999999999999.999999"):
            raise _issue("portion_servings", "Component portion exceeds exact bounds.")


@dataclass(frozen=True)
class PersistedMealEventComposition:
    event_id: UUID
    rule: DraftMealStructureRule
    components: tuple[PersistedMealComponent, ...]
    servings: tuple[PersistedMemberComponentServing, ...]
    created_at: datetime
    admission_status: str = COMPOSITION_ADMISSION

    def __post_init__(self) -> None:
        _id(self.event_id, "event_id")
        if self.admission_status != COMPOSITION_ADMISSION:
            raise _issue(
                "admission_status", "Composed event has no production authority."
            )
        if (
            not isinstance(self.rule, DraftMealStructureRule)
            or not isinstance(self.components, tuple)
            or not isinstance(self.servings, tuple)
            or not self.components
            or not self.servings
        ):
            raise _issue("compositions", "Complete typed composed meal required.")
        positions = sorted(c.position for c in self.components)
        if positions != list(range(1, len(positions) + 1)):
            raise _issue("components", "Component positions must be contiguous.")
        if any(c.event_id != self.event_id for c in self.components):
            raise _issue("event_id", "Component must belong to its composition.")
        by_id = {c.id: c for c in self.components}
        if len(by_id) != len(self.components):
            raise _issue("components", "Component ids must be unique.")
        seen = set()
        served = set()
        member_courses: dict[UUID, Counter[MealCourseKind]] = {}
        for serving in self.servings:
            if serving.component_id not in by_id:
                raise _issue("servings", "Orphan member-component Serving.")
            key = (serving.component_id, serving.member_id)
            if key in seen:
                raise _issue("servings", "Duplicate member-component allocation.")
            seen.add(key)
            served.add(serving.component_id)
            member_courses.setdefault(serving.member_id, Counter())[
                by_id[serving.component_id].course
            ] += 1
        if served != set(by_id):
            raise _issue("servings", "Each component must have a participant.")
        event_counts = Counter(c.course for c in self.components)
        permitted = {entry.kind for entry in self.rule.requirements}
        if set(event_counts) - permitted:
            raise _issue("components", "Unrecognized course for this rule.")
        for requirement in self.rule.requirements:
            total = event_counts[requirement.kind]
            if not requirement.minimum <= total <= requirement.maximum:
                raise _issue("components", "Event-wide course count differs from rule.")
            if self.rule.coverage is RequiredCourseCoverage.PER_PARTICIPANT:
                if any(
                    courses[requirement.kind] < requirement.minimum
                    for courses in member_courses.values()
                ):
                    raise _issue("servings", "A member is missing a required course.")
        course_order = {item.kind: i for i, item in enumerate(self.rule.requirements)}
        if [
            course_order[c.course]
            for c in sorted(self.components, key=lambda c: c.position)
        ] != sorted(course_order[c.course] for c in self.components):
            raise _issue("components", "Course ordering contradicts snapshot.")


def assert_complete_revision_preservation(
    prior: MealPlanDetail, new: MealPlanDetail, target_prior_event_id: UUID
) -> None:
    """Second line of defense for repository and independently reconstructed reads."""
    if (
        new.plan.household_id != prior.plan.household_id
        or new.plan.week_start != prior.plan.week_start
        or new.plan.revision_number != prior.plan.revision_number + 1
        or new.plan.supersedes_plan_id != prior.plan.id
        or new.plan.id == prior.plan.id
        or new.plan.status is not MealPlanStatus.DRAFT
        or len(new.events) != len(prior.events)
        or {pin.member_id: pin.selection_id for pin in new.member_selections}
        != {pin.member_id: pin.selection_id for pin in prior.member_selections}
    ):
        raise _issue("revision", "New plan must preserve full week and pins.")
    old_refs = {
        pin.member_id: replace(pin, plan_id=new.plan.id)
        for pin in prior.reference_methodology_pins
    }
    if {pin.member_id: pin for pin in new.reference_methodology_pins} != old_refs:
        raise _issue("revision", "Reference methodology pins changed.")
    old_slots = {(e.local_date, e.position): e for e in prior.events}
    new_slots = {(e.local_date, e.position): e for e in new.events}
    if set(old_slots) != set(new_slots) or len(old_slots) != len(prior.events):
        raise _issue("revision", "Missing or repeated source weekly slot.")
    old_ids = {e.id for e in prior.events}
    new_ids = {e.id for e in new.events}
    if old_ids & new_ids:
        raise _issue("revision", "A past event id was reused.")
    old_servings_by_event = {}
    new_servings_by_event = {}
    for row in prior.servings:
        old_servings_by_event.setdefault(row.event_id, {})[row.member_id] = row
    for row in new.servings:
        new_servings_by_event.setdefault(row.event_id, {})[row.member_id] = row
    old_composed = {c.event_id: c for c in prior.compositions}
    new_composed = {c.event_id: c for c in new.compositions}
    target_seen = 0
    for slot, old in old_slots.items():
        fresh = new_slots[slot]
        if old.id == target_prior_event_id:
            target_seen += 1
            if (
                old.source_kind is not MealSourceKind.COOK_RECIPE
                or fresh.source_kind is not MealSourceKind.COOK_COMPOSITION
                or fresh.recipe_version_id is not None
                or fresh.source_reference is not None
                or fresh.id not in new_composed
                or fresh.id in new_servings_by_event
                or {s.member_id for s in new_composed[fresh.id].servings}
                != set(old_servings_by_event.get(old.id, {}))
            ):
                raise _issue("revision", "Target composite meal changed attendance.")
            continue
        if (
            fresh.role != old.role
            or fresh.source_kind != old.source_kind
            or fresh.recipe_version_id != old.recipe_version_id
            or fresh.source_reference != old.source_reference
        ):
            raise _issue("revision", "An unrelated meal was changed.")
        old_rows = old_servings_by_event.get(old.id, {})
        new_rows = new_servings_by_event.get(fresh.id, {})
        if set(old_rows) != set(new_rows) or any(
            old_rows[mid].portion_servings != new_rows[mid].portion_servings
            or old_rows[mid].id == new_rows[mid].id
            for mid in old_rows
        ):
            raise _issue("revision", "An unrelated Serving was changed.")
        old_comp = old_composed.get(old.id)
        new_comp = new_composed.get(fresh.id)
        if (old_comp is None) != (new_comp is None):
            raise _issue("revision", "An unrelated composed meal was lost.")
        if old_comp is not None:
            if old_comp.rule != new_comp.rule or len(old_comp.components) != len(
                new_comp.components
            ):
                raise _issue("revision", "Historical course rule changed.")
            old_components = sorted(old_comp.components, key=lambda c: c.position)
            fresh_components = sorted(new_comp.components, key=lambda c: c.position)
            for former, current in zip(old_components, fresh_components):
                if (
                    former.id == current.id
                    or former.position != current.position
                    or former.course != current.course
                    or former.recipe_version_id != current.recipe_version_id
                ):
                    raise _issue("revision", "Historical component changed.")
                old_member_amounts = {
                    s.member_id: s.portion_servings
                    for s in old_comp.servings
                    if s.component_id == former.id
                }
                fresh_member_amounts = {
                    s.member_id: s.portion_servings
                    for s in new_comp.servings
                    if s.component_id == current.id
                }
                if old_member_amounts != fresh_member_amounts:
                    raise _issue("revision", "Historical component Serving changed.")
    if target_seen != 1 or len(new_composed) != len(old_composed) + 1:
        raise _issue("revision", "Exactly one event must be replaced.")
