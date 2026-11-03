"""PR10-A1: pure, NON-EXECUTABLE Prep quantity and obligation diagnostics.

No persistence, application reader, D3 eligibility grant, clock, network, AI,
Shopping/Pantry mutations, executable PrepTask, or kitchen/storage instructions.
See docs/family-food/pr10-pure-calculation-sequencing-amendment-2026-11-02.md.
"""

from __future__ import annotations

import json
from collections import defaultdict
from collections.abc import Mapping
from dataclasses import dataclass, field
from decimal import Decimal, DecimalException, localcontext
from enum import StrEnum
from hashlib import sha256
from uuid import UUID

from app.domain.food_ingredients import FoodIngredient
from app.domain.food_recipes import (
    RecipeVersionDetail,
    RightsReviewStatus,
    VerificationStatus,
)
from app.domain.meal_plans import MealPlanDetail, MealSourceKind
from app.domain.pantry import MAX_QUANTITY
from app.domain.units import UnitCode

ENGINE_VERSION = "prep-diagnostic-a1-v1"


class PrepDiagnosticError(ValueError):
    """Invalid source/quantity/Household snapshot: no result, no partial write."""


class PrepDiagnosticStatus(StrEnum):
    INCOMPLETE = "INCOMPLETE"


class PrepDiagnosticReason(StrEnum):
    STEP_ELIGIBILITY_UNVERIFIED = "STEP_ELIGIBILITY_UNVERIFIED"
    ASSEMBLY_UNSUPPORTED = "ASSEMBLY_UNSUPPORTED"
    LEFTOVER_SUPPLY_UNVERIFIED = "LEFTOVER_SUPPLY_UNVERIFIED"
    PREPARED_SUPPLY_UNVERIFIED = "PREPARED_SUPPLY_UNVERIFIED"
    READY_MEAL_UNRESOLVED = "READY_MEAL_UNRESOLVED"


@dataclass(frozen=True)
class SourceBackedIngredientRequirement:
    meal_event_id: UUID
    recipe_version_id: UUID
    recipe_ingredient_id: UUID
    food_ingredient_id: UUID
    food_code: str
    unit: UnitCode
    source_quantity: Decimal
    base_servings: Decimal
    total_servings: Decimal
    required_quantity: Decimal


@dataclass(frozen=True)
class NonExecutableSourceStepReference:
    meal_event_id: UUID
    recipe_version_id: UUID
    recipe_step_id: UUID
    position: int
    instruction_sha256: str

    # No source instruction text or eligibility flag is exposed by A1.


@dataclass(frozen=True)
class PrepUnresolvedDiagnostic:
    meal_event_id: UUID
    reason: PrepDiagnosticReason
    recipe_step_id: UUID | None = None


@dataclass(frozen=True)
class PrepDiagnosticResult:
    household_id: UUID
    meal_plan_id: UUID
    source_plan_revision_number: int
    policy_version: str
    engine_version: str
    status: PrepDiagnosticStatus
    event_ingredient_quantities: tuple[SourceBackedIngredientRequirement, ...]
    candidate_step_references: tuple[NonExecutableSourceStepReference, ...]
    unresolved: tuple[PrepUnresolvedDiagnostic, ...]
    source_fingerprint: str
    content_fingerprint: str
    # Cannot be passed into the constructor or populated via the calculator.
    executable_tasks: tuple[()] = field(default=(), init=False)


_OTHER_UNRESOLVED: dict[MealSourceKind, PrepDiagnosticReason] = {
    MealSourceKind.ASSEMBLY: PrepDiagnosticReason.ASSEMBLY_UNSUPPORTED,
    MealSourceKind.LEFTOVER: PrepDiagnosticReason.LEFTOVER_SUPPLY_UNVERIFIED,
    MealSourceKind.PREPARED: PrepDiagnosticReason.PREPARED_SUPPLY_UNVERIFIED,
    MealSourceKind.READY_MEAL: PrepDiagnosticReason.READY_MEAL_UNRESOLVED,
}
_OUTSIDE_HOME = frozenset({MealSourceKind.ORDER_OUT, MealSourceKind.EAT_OUT})


def _reject(message: str) -> None:
    raise PrepDiagnosticError(message)


def _positive_decimal(value: object) -> Decimal:
    if not isinstance(value, Decimal) or not value.is_finite() or value <= 0:
        _reject("Нужно положительное конечное Decimal; float не допускается.")
    if value > MAX_QUANTITY:
        _reject("Количество выходит за допустимые границы.")
    return value


def _canonical_decimal(value: Decimal) -> str:
    raw = format(value, "f")
    return raw.rstrip("0").rstrip(".") if "." in raw else raw


def _digest(value: object) -> str:
    return sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def _multiply(source: Decimal, total: Decimal, base: Decimal) -> Decimal:
    try:
        with localcontext() as ctx:
            ctx.prec = 50
            amount = source * total / base
    except DecimalException as exc:
        raise PrepDiagnosticError("Не удалось безопасно масштабировать рецепт.") from exc
    return _positive_decimal(amount)


def calculate_prep_diagnostic(
    *,
    plan: MealPlanDetail,
    recipes: Mapping[UUID, RecipeVersionDetail],
    foods: Mapping[UUID, FoodIngredient],
    member_exclusions: Mapping[UUID, frozenset[UUID]],
    policy_version: str,
) -> PrepDiagnosticResult:
    """Calculate *non-actionable* demand only; no step can become executable.

    All dependencies must be supplied as independently validated immutable
    Household-scoped snapshots by a future application-layer caller. Missing
    member exclusions fail closed; no inferred empty exclusion set.
    """
    if not isinstance(plan, MealPlanDetail) or not plan.events:
        _reject("Требуется версия плана с событиями и участниками.")
    if not isinstance(policy_version, str) or not (0 < len(policy_version) <= 120):
        _reject("Не задана версия диагностической политики.")
    if not isinstance(recipes, Mapping) or not isinstance(foods, Mapping):
        _reject("Требуются проверенные справочники рецептов и продуктов.")
    if not isinstance(member_exclusions, Mapping):
        _reject("Требуется проверенный снимок исключений участников.")

    household_id = plan.plan.household_id
    member_ids = {pin.member_id for pin in plan.member_selections}
    if not member_ids or set(member_exclusions) != member_ids:
        _reject("Снимок исключений должен охватывать всех участников плана.")
    for member_id, excluded in member_exclusions.items():
        if not isinstance(member_id, UUID) or not isinstance(excluded, frozenset):
            _reject("Некорректный снимок исключений участника.")
        if any(not isinstance(food_id, UUID) for food_id in excluded):
            _reject("Некорректный FoodIngredient в исключениях.")

    member_ordinals = {
        pin.member_id: index
        for index, pin in enumerate(
            sorted(plan.member_selections, key=lambda pin: pin.member_id.hex), start=1
        )
    }
    member_servings: dict[UUID, list[tuple[UUID, Decimal]]] = defaultdict(list)
    for serving in plan.servings:
        if serving.member_id not in member_ids:
            _reject("Порция ссылается на участника вне плана.")
        member_servings[serving.event_id].append(
            (serving.member_id, _positive_decimal(serving.portion_servings))
        )

    requirements: list[SourceBackedIngredientRequirement] = []
    candidates: list[NonExecutableSourceStepReference] = []
    unresolved: list[PrepUnresolvedDiagnostic] = []
    source_events: list[object] = []
    content_events: list[object] = []
    events = sorted(plan.events, key=lambda item: (item.local_date, item.position, item.id.hex))
    for event in events:
        if event.plan_id != plan.plan.id:
            _reject("Событие относится к другой ревизии плана.")
        participants = sorted(member_servings[event.id], key=lambda item: item[0].hex)
        if not participants or len({member for member, _ in participants}) != len(
            participants
        ):
            _reject("У события нет однозначных порций участников.")
        source_event: list[object] = [
            str(event.id),
            event.local_date.isoformat(),
            event.position,
            event.role.value,
            event.source_kind.value,
            str(event.recipe_version_id) if event.recipe_version_id else None,
            [[str(member), _canonical_decimal(value)] for member, value in participants],
        ]
        content_event: list[object] = [
            event.local_date.isoformat(),
            event.position,
            event.role.value,
            event.source_kind.value,
            sorted(
                [member_ordinals[member], _canonical_decimal(value)]
                for member, value in participants
            ),
        ]
        kind = event.source_kind
        if kind in _OTHER_UNRESOLVED:
            reason = _OTHER_UNRESOLVED[kind]
            unresolved.append(PrepUnresolvedDiagnostic(event.id, reason))
            source_event.append(reason.value)
            content_event.append(reason.value)
        elif kind in _OUTSIDE_HOME:
            source_event.append("NO_HOME_PREP")
            content_event.append("NO_HOME_PREP")
        elif kind is MealSourceKind.COOK_RECIPE:
            detail = recipes.get(event.recipe_version_id)
            if (
                not isinstance(detail, RecipeVersionDetail)
                or detail.version.id != event.recipe_version_id
                or not detail.recipe.is_active
                or detail.version.verification_status
                is not VerificationStatus.SOURCE_VERIFIED
                or detail.version.rights_review_status is not RightsReviewStatus.REVIEWED
            ):
                _reject("Не найдена активная исходно подтверждённая версия рецепта.")
            base = _positive_decimal(detail.version.base_servings)
            total = sum((value for _, value in participants), Decimal(0))
            _positive_decimal(total)
            ingredient_pins: list[object] = []
            content_ingredients: list[object] = []
            ingredient_ids = {item.food_ingredient_id for item in detail.ingredients}
            for member_id, _ in participants:
                if member_exclusions[member_id].intersection(ingredient_ids):
                    _reject("Рецепт нарушает исключения участника.")
            for ingredient in detail.ingredients:
                food = foods.get(ingredient.food_ingredient_id)
                if (
                    not isinstance(food, FoodIngredient)
                    or food.id != ingredient.food_ingredient_id
                    or not food.is_active
                    or food.default_unit != ingredient.unit
                    or ingredient.optional
                ):
                    _reject("Неизвестная форма, единица или выбор ингредиента.")
                source = _positive_decimal(ingredient.quantity)
                required = _multiply(source, total, base)
                requirements.append(
                    SourceBackedIngredientRequirement(
                        event.id,
                        detail.version.id,
                        ingredient.id,
                        food.id,
                        food.canonical_code,
                        ingredient.unit,
                        source,
                        base,
                        total,
                        required,
                    )
                )
                ingredient_pins.append(
                    [
                        str(ingredient.id),
                        str(food.id),
                        food.canonical_code,
                        ingredient.unit.value,
                        _canonical_decimal(source),
                        _canonical_decimal(required),
                    ]
                )
                content_ingredients.append(
                    [food.canonical_code, ingredient.unit.value, _canonical_decimal(required)]
                )
            step_pins: list[object] = []
            content_steps: list[object] = []
            for step in detail.steps:
                digest = sha256(step.instruction.encode("utf-8")).hexdigest()
                candidates.append(
                    NonExecutableSourceStepReference(
                        event.id, detail.version.id, step.id, step.position, digest
                    )
                )
                unresolved.append(
                    PrepUnresolvedDiagnostic(
                        event.id, PrepDiagnosticReason.STEP_ELIGIBILITY_UNVERIFIED, step.id
                    )
                )
                step_pins.append([str(step.id), step.position, digest, step.stage_code])
                content_steps.append([step.position, digest, step.stage_code])
            if len({step.id for step in detail.steps}) != len(detail.steps):
                _reject("В версии рецепта повторяются идентификаторы шагов.")
            source_event.extend(
                [
                    str(detail.version.id),
                    detail.version.version_number,
                    detail.version.source_name,
                    detail.version.source_recipe_id,
                    detail.version.source_version,
                    detail.version.source_document_sha256,
                    _canonical_decimal(base),
                    ingredient_pins,
                    step_pins,
                ]
            )
            content_event.extend(
                [
                    detail.recipe.canonical_code,
                    detail.version.version_number,
                    detail.version.source_name,
                    detail.version.source_recipe_id,
                    detail.version.source_version,
                    detail.version.source_document_sha256,
                    _canonical_decimal(base),
                    content_ingredients,
                    content_steps,
                ]
            )
        else:
            _reject("Неподдерживаемый MealSourceKind.")
        source_events.append(source_event)
        content_events.append(content_event)

    source_hash = _digest(
        {
            "engine": ENGINE_VERSION,
            "policy": policy_version,
            "plan": [
                str(plan.plan.id),
                str(household_id),
                plan.plan.week_start.isoformat(),
                plan.plan.revision_number,
                plan.plan.config_version,
                sorted(
                    [str(pin.member_id), str(pin.selection_id)]
                    for pin in plan.member_selections
                ),
            ],
            "exclusions": sorted(
                [str(member), sorted(str(food) for food in excluded)]
                for member, excluded in member_exclusions.items()
            ),
            "events": source_events,
        }
    )
    content_hash = _digest(
        {
            "engine": ENGINE_VERSION,
            "policy": policy_version,
            "events": content_events,
            "status": PrepDiagnosticStatus.INCOMPLETE.value,
        }
    )
    return PrepDiagnosticResult(
        household_id=household_id,
        meal_plan_id=plan.plan.id,
        source_plan_revision_number=plan.plan.revision_number,
        policy_version=policy_version,
        engine_version=ENGINE_VERSION,
        status=PrepDiagnosticStatus.INCOMPLETE,
        event_ingredient_quantities=tuple(requirements),
        candidate_step_references=tuple(candidates),
        unresolved=tuple(unresolved),
        source_fingerprint=source_hash,
        content_fingerprint=content_hash,
    )
