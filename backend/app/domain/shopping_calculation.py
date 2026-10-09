"""PR9-A: pure, deterministic canonical Shopping quantity calculation.

No persistence, pricing authority, clock, network, Pantry write or Retail adapter.
The accepted PR9 contract is docs/family-food/pr9-shopping-implementation-contract.md.
"""

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation, ROUND_CEILING, ROUND_FLOOR, localcontext
from enum import StrEnum
from hashlib import sha256
import json
from typing import Mapping
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.domain.food_ingredients import FoodIngredient
from app.domain.food_recipes import (
    RecipeVersionDetail,
    RightsReviewStatus,
    VerificationStatus,
)
from app.domain.meal_plans import MealPlanDetail, MealSourceKind
from app.domain.pantry import MAX_QUANTITY, PantryItem
from app.domain.units import UnitCode

QUANTITY_STEP = Decimal("0.001")
ENGINE_VERSION = "shopping-v1a"
PANTRY_POLICY_VERSION = "dated-fefo-v1"
FORM_BASIS = "CANONICAL_FOOD_ID"


class ShoppingCalculationError(ValueError):
    """Rejected authoritative calculation; no partial result is returned."""


class ShoppingStatus(StrEnum):
    COMPLETE = "COMPLETE"
    INCOMPLETE = "INCOMPLETE"


class ShoppingPriceStatus(StrEnum):
    UNKNOWN = "UNKNOWN"


class ShoppingUnresolvedReason(StrEnum):
    ASSEMBLY_UNSUPPORTED = "ASSEMBLY_UNSUPPORTED"
    LEFTOVER_SUPPLY_UNVERIFIED = "LEFTOVER_SUPPLY_UNVERIFIED"
    PREPARED_SUPPLY_UNVERIFIED = "PREPARED_SUPPLY_UNVERIFIED"
    READY_MEAL_UNRESOLVED = "READY_MEAL_UNRESOLVED"


@dataclass(frozen=True)
class ShoppingQuantity:
    food_ingredient_id: UUID
    form_basis: str
    unit: UnitCode
    required_quantity: Decimal
    pantry_available_quantity: Decimal
    purchase_quantity: Decimal


@dataclass(frozen=True)
class ShoppingUnresolved:
    meal_event_id: UUID
    source_kind: MealSourceKind
    reason: ShoppingUnresolvedReason


@dataclass(frozen=True)
class ShoppingWarning:
    code: str
    pantry_item_id: UUID


@dataclass(frozen=True)
class ShoppingLotAllocation:
    meal_event_id: UUID
    pantry_item_id: UUID
    food_ingredient_id: UUID
    quantity: Decimal


@dataclass(frozen=True)
class ShoppingCalculation:
    household_id: UUID
    meal_plan_id: UUID
    source_plan_revision_number: int
    as_of_date: date
    engine_version: str
    pantry_policy_version: str
    status: ShoppingStatus
    price_status: ShoppingPriceStatus
    items: tuple[ShoppingQuantity, ...]
    unresolved: tuple[ShoppingUnresolved, ...]
    warnings: tuple[ShoppingWarning, ...]
    allocations: tuple[ShoppingLotAllocation, ...]
    pantry_snapshot_hash: str
    source_fingerprint: str
    content_fingerprint: str


_UNRESOLVED = {
    MealSourceKind.ASSEMBLY: ShoppingUnresolvedReason.ASSEMBLY_UNSUPPORTED,
    MealSourceKind.LEFTOVER: ShoppingUnresolvedReason.LEFTOVER_SUPPLY_UNVERIFIED,
    MealSourceKind.PREPARED: ShoppingUnresolvedReason.PREPARED_SUPPLY_UNVERIFIED,
    MealSourceKind.READY_MEAL: ShoppingUnresolvedReason.READY_MEAL_UNRESOLVED,
}
_NON_GROCERY = {MealSourceKind.ORDER_OUT, MealSourceKind.EAT_OUT}


def _reject(message: str) -> None:
    raise ShoppingCalculationError(message)


def _decimal(value: Decimal, *, positive: bool = False) -> Decimal:
    if not isinstance(value, Decimal) or not value.is_finite():
        _reject("Количество должно быть конечным Decimal, float не допускается.")
    if value < 0 or (positive and value <= 0):
        _reject("Количество должно быть положительным или нулевым согласно контракту.")
    return value


def _round(value: Decimal, mode: str) -> Decimal:
    try:
        with localcontext() as ctx:
            ctx.prec = 50
            result = value.quantize(QUANTITY_STEP, rounding=mode)
    except InvalidOperation as exc:
        raise ShoppingCalculationError("Невозможно точно округлить количество.") from exc
    if result > MAX_QUANTITY:
        _reject("Количество превышает допустимый предел.")
    return result


def _fingerprint(data: object) -> str:
    raw = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return sha256(raw.encode("utf-8")).hexdigest()


def _lot_identity(item: PantryItem) -> list[str | None]:
    return [
        str(item.id),
        str(item.food_ingredient_id),
        str(item.quantity),
        str(item.unit),
        str(item.location),
        str(item.estimated),
        item.purchased_on.isoformat() if item.purchased_on else None,
        item.opened_on.isoformat() if item.opened_on else None,
        item.expires_on.isoformat() if item.expires_on else None,
    ]


def calculate_shopping(
    *,
    plan: MealPlanDetail,
    recipes: Mapping[UUID, RecipeVersionDetail],
    foods: Mapping[UUID, FoodIngredient],
    pantry_items: tuple[PantryItem, ...],
    household_timezone: str,
    captured_at: datetime,
) -> ShoppingCalculation:
    """Compute a complete immutable in-memory Shopping projection.

    This function requires already-authoritative, coherent repository snapshots.
    The future Shopping UoW must acquire BEGIN IMMEDIATE *before* loading them.
    """
    if not isinstance(plan, MealPlanDetail):
        _reject("Требуется проверенная версия недельного плана.")
    if not isinstance(captured_at, datetime) or captured_at.tzinfo is None:
        _reject("Дата расчёта должна содержать часовой пояс.")
    try:
        zone = ZoneInfo(household_timezone)
        as_of = captured_at.astimezone(zone).date()
    except (TypeError, ValueError, ZoneInfoNotFoundError) as exc:
        raise ShoppingCalculationError("Некорректный часовой пояс семьи.") from exc

    household_id = plan.plan.household_id
    members = {p.member_id for p in plan.member_selections}
    if not members:
        _reject("У плана отсутствуют подтверждённые участники.")
    lots = tuple(pantry_items)
    if any(not isinstance(x, PantryItem) or x.household_id != household_id for x in lots):
        _reject("В Pantry snapshot присутствуют данные другой семьи.")
    if len({x.id for x in lots}) != len(lots):
        _reject("Pantry snapshot содержит дублирующиеся идентификаторы партий.")

    events = sorted(plan.events, key=lambda e: (e.local_date, e.position, str(e.id)))
    serving_map: dict[UUID, list[Decimal]] = defaultdict(list)
    for serving in plan.servings:
        if serving.member_id not in members:
            _reject("Порция принадлежит участнику другой семьи.")
        serving_map[serving.event_id].append(_decimal(serving.portion_servings, positive=True))

    demand: dict[tuple[UUID, UnitCode], list[tuple[date, int, UUID, Decimal]]] = defaultdict(list)
    food_pins: dict[str, list[str]] = {}
    recipe_pins: list[object] = []
    unresolved: list[ShoppingUnresolved] = []
    for event in events:
        if event.plan_id != plan.plan.id or not serving_map[event.id]:
            _reject("Неполная привязка приёма пищи к версии плана и порциям.")
        kind = MealSourceKind(event.source_kind)
        if kind in _UNRESOLVED:
            unresolved.append(ShoppingUnresolved(event.id, kind, _UNRESOLVED[kind]))
            continue
        if kind in _NON_GROCERY:
            continue
        if kind is not MealSourceKind.COOK_RECIPE or event.recipe_version_id is None:
            _reject("Источник еды не имеет проверенной рецептурной потребности.")
        detail = recipes.get(event.recipe_version_id)
        if not isinstance(detail, RecipeVersionDetail) or detail.version.id != event.recipe_version_id:
            _reject("Не найдена закреплённая неизменяемая версия рецепта.")
        if (
            not detail.recipe.is_active
            or detail.version.verification_status is not VerificationStatus.SOURCE_VERIFIED
            or detail.version.rights_review_status is not RightsReviewStatus.REVIEWED
        ):
            _reject("Версия рецепта не подтверждена для продуктового каталога.")
        base = _decimal(detail.version.base_servings, positive=True)
        total_servings = sum(serving_map[event.id], Decimal(0))
        recipe_pins.append([
            str(event.id), str(detail.version.id), detail.version.version_number,
            detail.version.source_document_sha256, detail.version.source_version,
            str(base), str(total_servings),
        ])
        for ingredient in detail.ingredients:
            food = foods.get(ingredient.food_ingredient_id)
            if not isinstance(food, FoodIngredient) or food.id != ingredient.food_ingredient_id:
                _reject("Отсутствует канонический ингредиент рецепта.")
            if not food.is_active or ingredient.unit != food.default_unit:
                _reject("Несовместимые единицы или неактивный канонический продукт.")
            if ingredient.optional:
                _reject("Выбор необязательного ингредиента не зафиксирован в плане.")
            quantity = _decimal(ingredient.quantity, positive=True)
            food_pins[str(food.id)] = [food.canonical_code, str(food.default_unit)]
            with localcontext() as ctx:
                ctx.prec = 50
                amount = quantity * total_servings / base
            _decimal(amount, positive=True)
            if amount > MAX_QUANTITY:
                _reject("Рецептурная потребность превышает допустимое количество.")
            demand[(food.id, ingredient.unit)].append(
                (event.local_date, event.position, event.id, amount)
            )
            recipe_pins.append([str(ingredient.id), str(quantity), str(ingredient.unit), str(food.id)])

    pantry_source = [
        str(household_id), as_of.isoformat(), PANTRY_POLICY_VERSION,
        sorted((_lot_identity(x) for x in lots), key=lambda x: x[0]),
    ]
    pantry_hash = _fingerprint(pantry_source)
    source_hash = _fingerprint({
        "plan": [str(plan.plan.id), plan.plan.revision_number, plan.plan.week_start.isoformat(),
                 plan.plan.config_version],
        "events": [[str(e.id), e.local_date.isoformat(), e.position, str(e.source_kind),
                    str(e.recipe_version_id) if e.recipe_version_id else None,
                    e.source_reference] for e in events],
        "servings": sorted([[str(s.event_id), str(s.member_id), str(s.portion_servings)]
                            for s in plan.servings]),
        "recipes": sorted(recipe_pins, key=lambda x: str(x)),
        "foods": food_pins,
        "pantry_hash": pantry_hash,
        "timezone": household_timezone,
        "version": ENGINE_VERSION,
    })

    warnings: list[ShoppingWarning] = []
    allocations: list[ShoppingLotAllocation] = []
    computed: list[ShoppingQuantity] = []
    for food_id, unit in sorted(demand, key=lambda key: (foods[key[0]].category_code,
                                                        foods[key[0]].canonical_name_key,
                                                        str(key[0]), str(key[1]))):
        required = Decimal(0)
        allocated = Decimal(0)
        relevant_lots = sorted(
            (item for item in lots if item.food_ingredient_id == food_id and item.quantity > 0),
            key=lambda item: (item.expires_on or date.max, str(item.location), str(item.id)),
        )
        remaining = {item.id: _decimal(item.quantity) for item in relevant_lots}
        for lot in relevant_lots:
            if lot.estimated:
                warnings.append(ShoppingWarning("ESTIMATED_STOCK", lot.id))
            elif lot.expires_on is None:
                warnings.append(ShoppingWarning("EXPIRY_UNKNOWN", lot.id))
            elif lot.expires_on < as_of:
                warnings.append(ShoppingWarning("EXPIRED_STOCK", lot.id))
            elif lot.unit != unit:
                warnings.append(ShoppingWarning("INCOMPATIBLE_UNIT", lot.id))
        for meal_date, position, event_id, amount in sorted(
            demand[(food_id, unit)], key=lambda row: (row[0], row[1], str(row[2]))
        ):
            required += amount
            missing = amount
            use_date = max(as_of, meal_date)
            for lot in relevant_lots:
                if (
                    missing <= 0 or not remaining[lot.id] or lot.estimated
                    or lot.expires_on is None or lot.expires_on < use_date
                    or lot.unit != unit
                ):
                    continue
                taken = min(missing, remaining[lot.id])
                remaining[lot.id] -= taken
                missing -= taken
                allocated += taken
                allocations.append(ShoppingLotAllocation(event_id, lot.id, food_id, taken))
        required_out = _round(required, ROUND_CEILING)
        available_out = _round(allocated, ROUND_FLOOR)
        shortfall = max(required_out - available_out, Decimal(0))
        if unit is UnitCode.PIECE:
            with localcontext() as ctx:
                ctx.prec = 50
                purchase = shortfall.to_integral_value(rounding=ROUND_CEILING).quantize(QUANTITY_STEP)
            if purchase > MAX_QUANTITY:
                _reject("Количество штук превышает допустимый предел.")
        else:
            purchase = _round(shortfall, ROUND_CEILING)
        computed.append(
            ShoppingQuantity(food_id, FORM_BASIS, unit, required_out, available_out, purchase)
        )

    unresolved.sort(key=lambda x: (str(x.meal_event_id), str(x.reason)))
    warnings.sort(key=lambda x: (x.code, str(x.pantry_item_id)))
    allocation_result = tuple(sorted(allocations, key=lambda a: (str(a.meal_event_id),
                                                                  str(a.pantry_item_id))))
    items = tuple(computed)
    content_hash = _fingerprint({
        "source": source_hash,
        "items": [[str(x.food_ingredient_id), x.form_basis, str(x.unit),
                   str(x.required_quantity), str(x.pantry_available_quantity),
                   str(x.purchase_quantity)] for x in items],
        "unresolved": [[str(x.meal_event_id), str(x.source_kind), str(x.reason)]
                       for x in unresolved],
        "warnings": [[x.code, str(x.pantry_item_id)] for x in warnings],
        "allocations": [[str(x.meal_event_id), str(x.pantry_item_id),
                         str(x.quantity)] for x in allocation_result],
    })
    return ShoppingCalculation(
        household_id, plan.plan.id, plan.plan.revision_number, as_of,
        ENGINE_VERSION, PANTRY_POLICY_VERSION,
        ShoppingStatus.INCOMPLETE if unresolved else ShoppingStatus.COMPLETE,
        ShoppingPriceStatus.UNKNOWN, items, tuple(unresolved), tuple(warnings),
        allocation_result, pantry_hash, source_hash, content_hash,
    )
