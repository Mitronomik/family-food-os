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

from collections import Counter
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from uuid import UUID

from app.domain.errors import DomainIssue, DomainIssueCode, DomainValidationError
from app.domain.meal_patterns import MealRole
from app.domain.meal_plans import MealPlanDetail, MealSourceKind

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
            raise _issue("coverage", "Explicit course coverage scope is required.") from exc
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
        by_position = {component.position: component.course for component in proposal.components}
        per_member = {member_id: Counter() for member_id in old_members}
        for serving in proposal.servings:
            per_member[serving.member_id][by_position[serving.component_position]] += 1
        for member_courses in per_member.values():
            for requirement in structure.requirements:
                if member_courses[requirement.kind] < requirement.minimum:
                    raise _issue(
                        "servings", "An at-home participant is missing a required course."
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
