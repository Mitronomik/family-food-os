"""Shopping v1b: internal diagnostic component demand over immutable source pins.

Version-isolated from shopping-v1a: legacy calculations and fingerprints never change.
No persistence, network, real-family API or Pantry mutation lives here.
"""

import json
from collections import defaultdict
from collections.abc import Mapping
from datetime import date, datetime
from decimal import ROUND_CEILING, ROUND_FLOOR, Decimal, InvalidOperation, localcontext
from hashlib import sha256
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.domain.food_ingredients import FoodIngredient
from app.domain.food_recipes import (
    RecipeVersionDetail,
    RightsReviewStatus,
    VerificationStatus,
)
from app.domain.meal_compositions import rule_snapshot_digest
from app.domain.meal_plans import MealPlanDetail, MealPlanStatus, MealSourceKind
from app.domain.pantry import MAX_QUANTITY, PantryItem
from app.domain.shopping_calculation import (
    FORM_BASIS,
    PANTRY_POLICY_VERSION,
    QUANTITY_STEP,
    ShoppingCalculation,
    ShoppingCalculationError,
    ShoppingLotAllocation,
    ShoppingPriceStatus,
    ShoppingQuantity,
    ShoppingStatus,
    ShoppingUnresolved,
    ShoppingWarning,
    _NON_GROCERY,
    _UNRESOLVED,
)
from app.domain.units import UnitCode

ENGINE_VERSION = "shopping-v1b-composition"
SCHEMA_V2 = "SHOPPING_SOURCE_SNAPSHOT_V2_COMPOSITION"


def _exact(value: Decimal) -> str:
    """Canonical non-exponential finite decimal without insignificant zeros."""
    if not isinstance(value, Decimal) or not value.is_finite():
        raise ShoppingCalculationError("Некорректное точное количество.")
    if not value:
        return "0"
    raw = format(value, "f")
    return raw.rstrip("0").rstrip(".") if "." in raw else raw


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
        raise ShoppingCalculationError(
            "Невозможно точно округлить количество."
        ) from exc
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


def calculate_shopping_composition(
    *,
    plan: MealPlanDetail,
    recipes: Mapping[UUID, RecipeVersionDetail],
    foods: Mapping[UUID, FoodIngredient],
    pantry_items: tuple[PantryItem, ...],
    household_timezone: str,
    captured_at: datetime,
) -> tuple[ShoppingCalculation, dict[str, object]]:
    """Compute a complete immutable in-memory Shopping projection.

    This function requires already-authoritative, coherent repository snapshots.
    The future Shopping UoW must acquire BEGIN IMMEDIATE *before* loading them.
    """
    if not isinstance(plan, MealPlanDetail):
        _reject("Требуется проверенная версия недельного плана.")
    if not plan.compositions or plan.plan.status is not MealPlanStatus.DRAFT:
        _reject("Внутренний Shopping v1b требует диагностическую композицию.")
    if {event.local_date for event in plan.events} != set(plan.horizon_dates):
        _reject("Неполная неделя композиционного плана.")
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
    if any(
        not isinstance(x, PantryItem) or x.household_id != household_id for x in lots
    ):
        _reject("В Pantry snapshot присутствуют данные другой семьи.")
    if len({x.id for x in lots}) != len(lots):
        _reject("Pantry snapshot содержит дублирующиеся идентификаторы партий.")

    events = sorted(plan.events, key=lambda e: (e.local_date, e.position, str(e.id)))
    serving_map: dict[UUID, list[Decimal]] = defaultdict(list)
    for serving in plan.servings:
        if serving.member_id not in members:
            _reject("Порция принадлежит участнику другой семьи.")
        serving_map[serving.event_id].append(
            _decimal(serving.portion_servings, positive=True)
        )

    demand: dict[tuple[UUID, UnitCode], list[tuple[date, int, UUID, Decimal]]] = (
        defaultdict(list)
    )
    food_pins: dict[str, list[str]] = {}
    recipe_pins: list[object] = []
    unresolved: list[ShoppingUnresolved] = []
    composition_by_event = {comp.event_id: comp for comp in plan.compositions}
    contributions: list[dict[str, object]] = []
    dated_demands: dict[tuple[UUID, UUID, str, UnitCode], Decimal] = defaultdict(Decimal)
    for event in events:
        if event.plan_id != plan.plan.id:
            _reject("Неполная привязка события к версии плана.")
        kind = MealSourceKind(event.source_kind)
        if kind is MealSourceKind.COOK_COMPOSITION:
            comp = composition_by_event.get(event.id)
            if (
                comp is None
                or event.recipe_version_id is not None
                or event.source_reference is not None
                or serving_map[event.id]
            ):
                _reject("Неполная или ложная привязка композиционного события.")
            occurrences = []
            for part in sorted(comp.components, key=lambda item: item.position):
                portions = sorted(
                    (item for item in comp.servings if item.component_id == part.id),
                    key=lambda item: item.member_id.hex,
                )
                if not portions or any(item.member_id not in members for item in portions):
                    _reject("Отсутствует проверенная порция компонента.")
                occurrences.append((part, part.recipe_version_id, portions))
        elif not serving_map[event.id]:
            _reject("Неполная привязка приёма пищи к версии плана и порциям.")
        elif kind in _UNRESOLVED:
            unresolved.append(ShoppingUnresolved(event.id, kind, _UNRESOLVED[kind]))
            continue
        elif kind in _NON_GROCERY:
            continue
        elif kind is MealSourceKind.COOK_RECIPE and event.recipe_version_id is not None:
            occurrences = [(None, event.recipe_version_id, [
                s for s in plan.servings if s.event_id == event.id
            ])]
        else:
            _reject("Источник еды не имеет проверенной рецептурной потребности.")

        for part, version_id, portions in occurrences:
            detail = recipes.get(version_id)
            if (
                not isinstance(detail, RecipeVersionDetail)
                or detail.version.id != version_id
                or not detail.recipe.is_active
                or detail.version.verification_status is not VerificationStatus.SOURCE_VERIFIED
                or detail.version.rights_review_status is not RightsReviewStatus.REVIEWED
                or not detail.version.source_document_sha256
            ):
                _reject("Закреплённая версия рецепта не подтверждена.")
            base = _decimal(detail.version.base_servings, positive=True)
            total_servings = sum(
                (_decimal(s.portion_servings, positive=True) for s in portions),
                Decimal(0),
            )
            _decimal(total_servings, positive=True)
            member_portions = [
                {"member_id": str(s.member_id),
                 "portion_servings": format(s.portion_servings, ".6f")}
                for s in portions
            ]
            for ingredient in detail.ingredients:
                food = foods.get(ingredient.food_ingredient_id)
                if (
                    not isinstance(food, FoodIngredient)
                    or food.id != ingredient.food_ingredient_id
                    or not food.is_active
                    or ingredient.unit != food.default_unit
                    or ingredient.optional
                ):
                    _reject("Невозможно достоверно определить продукт, форму или единицу.")
                quantity = _decimal(ingredient.quantity, positive=True)
                food_pins[str(food.id)] = [
                    food.canonical_code, str(food.default_unit),
                    food.category_code, food.canonical_name_key,
                ]
                with localcontext() as ctx:
                    ctx.prec = 50
                    numerator = quantity * total_servings
                    scale = total_servings / base
                    amount = numerator / base
                _decimal(amount, positive=True)
                if amount > MAX_QUANTITY:
                    _reject("Рецептурная потребность превышает допустимое количество.")
                demand[(food.id, ingredient.unit)].append(
                    (event.local_date, event.position, event.id, amount)
                )
                dated_demands[(event.id, food.id, FORM_BASIS, ingredient.unit)] += amount
                if part is not None:
                    contributions.append({
                        "meal_event_id": str(event.id),
                        "local_date": event.local_date.isoformat(),
                        "event_position": event.position,
                        "component_id": str(part.id),
                        "component_position": part.position,
                        "course_kind": str(part.course),
                        "recipe_version_id": str(version_id),
                        "recipe_ingredient_id": str(ingredient.id),
                        "food_ingredient_id": str(food.id),
                        "form_basis": FORM_BASIS, "unit": str(ingredient.unit),
                        "base_servings": _exact(base),
                        "member_servings": member_portions,
                        "total_component_servings": _exact(total_servings),
                        "input_quantity": _exact(quantity),
                        "scale_factor": _exact(scale),
                        "contribution_numerator": _exact(numerator),
                        "contribution_denominator": _exact(base),
                        "unrounded_contribution": _exact(amount),
                    })

    pantry_source = [
        str(household_id),
        as_of.isoformat(),
        PANTRY_POLICY_VERSION,
        sorted((_lot_identity(x) for x in lots), key=lambda x: x[0]),
    ]
    pantry_hash = _fingerprint(pantry_source)
    event_by_id = {event.id: event for event in events}
    contributions.sort(key=lambda row: (
        row["local_date"], row["event_position"],
        row["component_position"], row["recipe_ingredient_id"],
    ))
    event_demands = [
        {
            "meal_event_id": str(event_id),
            "local_date": event_by_id[event_id].local_date.isoformat(),
            "event_position": event_by_id[event_id].position,
            "food_ingredient_id": str(food_id), "form_basis": basis,
            "unit": str(unit), "unrounded_required": _exact(amount),
        }
        for (event_id, food_id, basis, unit), amount in sorted(
            dated_demands.items(),
            key=lambda pair: (
                event_by_id[pair[0][0]].local_date,
                event_by_id[pair[0][0]].position,
                str(pair[0][1]), pair[0][2], str(pair[0][3]),
            ),
        )
    ]
    plan_events = [
        {
            "event_id": str(e.id), "local_date": e.local_date.isoformat(),
            "position": e.position, "role": str(e.role),
            "source_kind": str(e.source_kind),
            "recipe_version_id": str(e.recipe_version_id) if e.recipe_version_id else None,
            "source_reference": e.source_reference,
        }
        for e in events
    ]
    member_pins = [
        {"member_id": str(p.member_id), "selection_id": str(p.selection_id)}
        for p in sorted(plan.member_selections, key=lambda p: p.member_id.hex)
    ]
    legacy_servings = [
        {"event_id": str(s.event_id), "member_id": str(s.member_id),
         "portion_servings": format(s.portion_servings, ".6f")}
        for s in sorted(plan.servings, key=lambda s: (
            event_by_id[s.event_id].local_date,
            event_by_id[s.event_id].position, s.member_id.hex,
        ))
    ]
    compositions = []
    for comp in sorted(plan.compositions, key=lambda c: (
        event_by_id[c.event_id].local_date,
        event_by_id[c.event_id].position,
    )):
        rule = comp.rule
        compositions.append({
            "meal_event_id": str(comp.event_id),
            "rule": {
                "schema_version": 1, "code": rule.code, "version": rule.version,
                "meal_role": str(rule.meal_role), "coverage": str(rule.coverage),
                "requirements": [
                    {"kind": str(r.kind), "minimum": r.minimum, "maximum": r.maximum}
                    for r in rule.requirements
                ],
                "sha256": rule_snapshot_digest(rule),
            },
            "components": [
                {
                    "component_id": str(part.id), "position": part.position,
                    "course_kind": str(part.course),
                    "recipe_version_id": str(part.recipe_version_id),
                    "member_servings": [
                        {"member_id": str(s.member_id),
                         "portion_servings": format(s.portion_servings, ".6f")}
                        for s in sorted(
                            (s for s in comp.servings if s.component_id == part.id),
                            key=lambda s: s.member_id.hex,
                        )
                    ],
                }
                for part in sorted(comp.components, key=lambda p: p.position)
            ],
        })
    used_recipes = {
        e.recipe_version_id for e in events if e.source_kind is MealSourceKind.COOK_RECIPE
    } | {part.recipe_version_id for comp in plan.compositions for part in comp.components}
    recipe_inputs = []
    used_foods = set()
    for version_id in sorted(used_recipes, key=str):
        detail = recipes.get(version_id)
        if detail is None:
            _reject("Не хватает версии рецепта для полного provenance.")
        used_foods.update(ing.food_ingredient_id for ing in detail.ingredients)
        recipe_inputs.append({
            "recipe_version_id": str(version_id),
            "recipe_version_number": detail.version.version_number,
            "source_document_sha256": detail.version.source_document_sha256,
            "source_version": detail.version.source_version,
            "verification_status": str(detail.version.verification_status),
            "rights_review_status": str(detail.version.rights_review_status),
            "recipe_is_active": bool(detail.recipe.is_active),
            "base_servings": _exact(detail.version.base_servings),
            "ingredients": [
                {
                    "recipe_ingredient_id": str(i.id),
                    "food_ingredient_id": str(i.food_ingredient_id),
                    "quantity": _exact(i.quantity), "unit": str(i.unit),
                    "optional": i.optional,
                }
                for i in sorted(detail.ingredients, key=lambda i: str(i.id))
            ],
        })
    food_sources = [
        {
            "food_ingredient_id": str(foods[fid].id),
            "canonical_code": foods[fid].canonical_code,
            "canonical_name_key": foods[fid].canonical_name_key,
            "category_code": foods[fid].category_code,
            "default_unit": str(foods[fid].default_unit),
            "is_active": foods[fid].is_active,
            "form_basis": FORM_BASIS,
        }
        for fid in sorted(used_foods, key=str)
    ]
    pantry_sources = [
        {
            "pantry_item_id": str(lot.id),
            "household_id": str(lot.household_id),
            "food_ingredient_id": str(lot.food_ingredient_id),
            "quantity": _exact(lot.quantity), "unit": str(lot.unit),
            "location": str(lot.location), "estimated": lot.estimated,
            "purchased_on": lot.purchased_on.isoformat() if lot.purchased_on else None,
            "opened_on": lot.opened_on.isoformat() if lot.opened_on else None,
            "expires_on": lot.expires_on.isoformat() if lot.expires_on else None,
        }
        for lot in sorted(lots, key=lambda x: str(x.id))
    ]
    source_inputs = {
        "schema": SCHEMA_V2, "engine": ENGINE_VERSION,
        "policy": PANTRY_POLICY_VERSION,
        "calculation": {
            "household_id": str(household_id), "plan_id": str(plan.plan.id),
            "plan_revision": plan.plan.revision_number,
            "week_start": plan.plan.week_start.isoformat(),
            "config_version": plan.plan.config_version,
            "as_of_date": as_of.isoformat(),
            "timezone": household_timezone,
        },
        "plan_events": plan_events,
        "member_selection_pins": member_pins,
        "servings": legacy_servings,
        "compositions": compositions,
        "recipe_inputs": recipe_inputs,
        "foods": food_sources,
        "pantry_items": pantry_sources,
    }
    source_hash = _fingerprint(source_inputs)

    warnings: list[ShoppingWarning] = []
    allocations: list[ShoppingLotAllocation] = []
    computed: list[ShoppingQuantity] = []
    for food_id, unit in sorted(
        demand,
        key=lambda key: (
            foods[key[0]].category_code,
            foods[key[0]].canonical_name_key,
            str(key[0]),
            str(key[1]),
        ),
    ):
        required = Decimal(0)
        allocated = Decimal(0)
        relevant_lots = sorted(
            (
                item
                for item in lots
                if item.food_ingredient_id == food_id and item.quantity > 0
            ),
            key=lambda item: (
                item.expires_on or date.max,
                str(item.location),
                str(item.id),
            ),
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
                if missing <= 0:
                    break
                if (
                    not remaining[lot.id]
                    or lot.estimated
                    or lot.expires_on is None
                    or lot.unit != unit
                ):
                    continue
                if lot.expires_on < use_date:
                    if lot.expires_on >= as_of:
                        warning = ShoppingWarning(
                            "EXPIRES_BEFORE_REQUIRED_DATE", lot.id, event_id, use_date
                        )
                        if warning not in warnings:
                            warnings.append(warning)
                    continue
                taken = min(missing, remaining[lot.id])
                remaining[lot.id] -= taken
                missing -= taken
                allocated += taken
                allocations.append(
                    ShoppingLotAllocation(event_id, lot.id, food_id, taken)
                )
        required_out = _round(required, ROUND_CEILING)
        available_out = _round(allocated, ROUND_FLOOR)
        shortfall = max(required_out - available_out, Decimal(0))
        if unit is UnitCode.PIECE:
            with localcontext() as ctx:
                ctx.prec = 50
                purchase = shortfall.to_integral_value(rounding=ROUND_CEILING).quantize(
                    QUANTITY_STEP
                )
            if purchase > MAX_QUANTITY:
                _reject("Количество штук превышает допустимый предел.")
        else:
            purchase = _round(shortfall, ROUND_CEILING)
        computed.append(
            ShoppingQuantity(
                food_id, FORM_BASIS, unit, required_out, available_out, purchase
            )
        )

    unresolved.sort(key=lambda x: (str(x.meal_event_id), str(x.reason)))
    warnings.sort(
        key=lambda x: (
            x.code,
            str(x.pantry_item_id),
            str(x.meal_event_id) if x.meal_event_id else "",
            x.required_date.isoformat() if x.required_date else "",
        )
    )
    allocation_result = tuple(
        sorted(allocations, key=lambda a: (str(a.meal_event_id), str(a.pantry_item_id)))
    )
    items = tuple(computed)
    items_source = [
        {
            "food_ingredient_id": str(item.food_ingredient_id),
            "form_basis": item.form_basis, "unit": str(item.unit),
            "required_quantity": _exact(item.required_quantity),
            "pantry_available_quantity": _exact(item.pantry_available_quantity),
            "purchase_quantity": _exact(item.purchase_quantity),
            "ordinal": i,
        }
        for i, item in enumerate(items, 1)
    ]
    unresolved_source = [
        {"meal_event_id": str(item.meal_event_id), "source_kind": str(item.source_kind),
         "reason": str(item.reason)}
        for item in unresolved
    ]
    warnings_source = [
        {"code": w.code, "pantry_item_id": str(w.pantry_item_id),
         "meal_event_id": str(w.meal_event_id) if w.meal_event_id else None,
         "required_date": w.required_date.isoformat() if w.required_date else None}
        for w in warnings
    ]
    allocations_source = [
        {"meal_event_id": str(a.meal_event_id),
         "pantry_item_id": str(a.pantry_item_id),
         "food_ingredient_id": str(a.food_ingredient_id),
         "quantity": _exact(a.quantity)}
        for a in allocation_result
    ]
    content_hash = _fingerprint({
        "source_fingerprint": source_hash,
        "component_contributions": contributions,
        "event_demands": event_demands, "items": items_source,
        "unresolved": unresolved_source, "warnings": warnings_source,
        "allocations": allocations_source,
    })
    config_hash = _fingerprint([
        str(plan.plan.id), plan.plan.config_version,
        ENGINE_VERSION, PANTRY_POLICY_VERSION,
    ])
    provenance = {
        **source_inputs,
        "calculation": {
            **source_inputs["calculation"],
            "engine": ENGINE_VERSION,
            "policy": PANTRY_POLICY_VERSION,
            "pantry_hash": pantry_hash,
            "source_hash": source_hash,
            "content_hash": content_hash,
            "config_fingerprint": config_hash,
        },
        "component_contributions": contributions,
        "event_demands": event_demands, "items": items_source,
        "unresolved": unresolved_source, "warnings": warnings_source,
        "allocations": allocations_source,
    }
    calculation = ShoppingCalculation(
        household_id, plan.plan.id, plan.plan.revision_number, as_of,
        ENGINE_VERSION, PANTRY_POLICY_VERSION,
        ShoppingStatus.INCOMPLETE if unresolved else ShoppingStatus.COMPLETE,
        ShoppingPriceStatus.UNKNOWN, items, tuple(unresolved), tuple(warnings),
        allocation_result, pantry_hash, source_hash, content_hash,
    )
    return calculation, provenance

def validate_v2_provenance(payload: dict, calculation: ShoppingCalculation) -> None:
    """Replay source, component arithmetic and item totals without live catalogue."""
    try:
        if (
            not isinstance(payload, dict)
            or payload["schema"] != SCHEMA_V2
            or payload["engine"] != ENGINE_VERSION
            or payload["policy"] != PANTRY_POLICY_VERSION
            or calculation.engine_version != ENGINE_VERSION
        ):
            raise ValueError("invalid V2 version")
        meta = payload["calculation"]
        expected_meta = {
            "household_id": str(calculation.household_id),
            "plan_id": str(calculation.meal_plan_id),
            "plan_revision": calculation.source_plan_revision_number,
            "as_of_date": calculation.as_of_date.isoformat(),
            "engine": ENGINE_VERSION, "policy": PANTRY_POLICY_VERSION,
            "pantry_hash": calculation.pantry_snapshot_hash,
            "source_hash": calculation.source_fingerprint,
            "content_hash": calculation.content_fingerprint,
        }
        if any(meta[key] != val for key, val in expected_meta.items()):
            raise ValueError("V2 header mismatch")
        base_meta_keys = (
            "household_id", "plan_id", "plan_revision", "week_start",
            "config_version", "as_of_date", "timezone",
        )
        source_keys = (
            "plan_events", "member_selection_pins", "servings",
            "compositions", "recipe_inputs", "foods", "pantry_items",
        )
        sources = {
            "schema": SCHEMA_V2, "engine": ENGINE_VERSION,
            "policy": PANTRY_POLICY_VERSION,
            "calculation": {k: meta[k] for k in base_meta_keys},
            **{k: payload[k] for k in source_keys},
        }
        if _fingerprint(sources) != calculation.source_fingerprint:
            raise ValueError("V2 source fingerprint")
        if _fingerprint([
            meta["plan_id"], meta["config_version"],
            ENGINE_VERSION, PANTRY_POLICY_VERSION,
        ]) != meta["config_fingerprint"]:
            raise ValueError("V2 config fingerprint")
        from app.domain.meal_compositions import restore_rule_snapshot

        events = {e["event_id"]: e for e in payload["plan_events"]}
        versions = {r["recipe_version_id"]: r for r in payload["recipe_inputs"]}
        if len(events) != len(payload["plan_events"]) or len(versions) != len(payload["recipe_inputs"]):
            raise ValueError("duplicate source identity")
        legacy: dict[str, list[dict]] = defaultdict(list)
        for serving in payload["servings"]:
            if serving["event_id"] not in events:
                raise ValueError("orphan Serving")
            legacy[serving["event_id"]].append(serving)
        contributions = {}
        demands: dict[tuple[str, str, str, str], Decimal] = defaultdict(Decimal)

        def add(event: dict, food: str, unit: str, amount: Decimal):
            demands[(event["event_id"], food, FORM_BASIS, unit)] += amount

        composed_events = set()
        for comp in payload["compositions"]:
            event = events[comp["meal_event_id"]]
            if event["source_kind"] != "COOK_COMPOSITION":
                raise ValueError("composition source mismatch")
            composed_events.add(comp["meal_event_id"])
            rule = comp["rule"]
            restore_rule_snapshot(
                code=rule["code"], version=rule["version"],
                meal_role=rule["meal_role"], coverage=rule["coverage"],
                schema_version=rule["schema_version"],
                requirements_json=json.dumps(
                    rule["requirements"], sort_keys=True,
                    separators=(",", ":"), ensure_ascii=False,
                ),
                sha256_hex=rule["sha256"],
            )
            for part in comp["components"]:
                servings = part["member_servings"]
                if not servings or len({s["member_id"] for s in servings}) != len(servings):
                    raise ValueError("invalid member-component Servings")
                if any(
                    s["portion_servings"] != format(Decimal(s["portion_servings"]), ".6f")
                    or Decimal(s["portion_servings"]) <= 0
                    for s in servings
                ):
                    raise ValueError("invalid component amount")
                recipe = versions[part["recipe_version_id"]]
                with localcontext() as ctx:
                    ctx.prec = 50
                    total = sum((Decimal(s["portion_servings"]) for s in servings), Decimal(0))
                    base = Decimal(recipe["base_servings"])
                    scale = total / base
                for ingredient in recipe["ingredients"]:
                    key = (comp["meal_event_id"], part["component_id"], ingredient["recipe_ingredient_id"])
                    if key in contributions:
                        raise ValueError("duplicate component input")
                    with localcontext() as ctx:
                        ctx.prec = 50
                        quantity = Decimal(ingredient["quantity"])
                        numerator = quantity * total
                        amount = numerator / base
                    if quantity <= 0 or not amount.is_finite() or amount <= 0:
                        raise ValueError("invalid component ingredient")
                    contributions[key] = {
                        "meal_event_id": comp["meal_event_id"],
                        "local_date": event["local_date"],
                        "event_position": event["position"],
                        "component_id": part["component_id"],
                        "component_position": part["position"],
                        "course_kind": part["course_kind"],
                        "recipe_version_id": part["recipe_version_id"],
                        "recipe_ingredient_id": ingredient["recipe_ingredient_id"],
                        "food_ingredient_id": ingredient["food_ingredient_id"],
                        "form_basis": FORM_BASIS, "unit": ingredient["unit"],
                        "base_servings": _exact(base),
                        "member_servings": servings,
                        "total_component_servings": _exact(total),
                        "input_quantity": _exact(quantity),
                        "scale_factor": _exact(scale),
                        "contribution_numerator": _exact(numerator),
                        "contribution_denominator": _exact(base),
                        "unrounded_contribution": _exact(amount),
                    }
                    add(event, ingredient["food_ingredient_id"], ingredient["unit"], amount)
        if composed_events != {
            e["event_id"] for e in payload["plan_events"]
            if e["source_kind"] == "COOK_COMPOSITION"
        }:
            raise ValueError("composed parent missing")
        provided = {}
        for item in payload["component_contributions"]:
            key = (item["meal_event_id"], item["component_id"], item["recipe_ingredient_id"])
            if key in provided:
                raise ValueError("duplicate contribution")
            provided[key] = item
        if provided != contributions:
            raise ValueError("component contribution mismatch")
        for event in payload["plan_events"]:
            if event["source_kind"] != "COOK_RECIPE":
                continue
            recipe = versions[event["recipe_version_id"]]
            portions = legacy[event["event_id"]]
            if not portions:
                raise ValueError("legacy source lost member Servings")
            with localcontext() as ctx:
                ctx.prec = 50
                total = sum((Decimal(s["portion_servings"]) for s in portions), Decimal(0))
                base = Decimal(recipe["base_servings"])
                for ingredient in recipe["ingredients"]:
                    amount = Decimal(ingredient["quantity"]) * total / base
                    add(event, ingredient["food_ingredient_id"], ingredient["unit"], amount)
        stored_demands = {}
        for row in payload["event_demands"]:
            key = (row["meal_event_id"], row["food_ingredient_id"], row["form_basis"], row["unit"])
            if key in stored_demands:
                raise ValueError("duplicate event demand")
            stored_demands[key] = Decimal(row["unrounded_required"])
        if demands != stored_demands:
            raise ValueError("event sum mismatch")
        totals: dict[tuple[str, str, str], Decimal] = defaultdict(Decimal)
        for (_, food, basis, unit), amount in demands.items():
            totals[(food, basis, unit)] += amount
        if len(totals) != len(payload["items"]):
            raise ValueError("missing Shopping item")
        for ordinal, row in enumerate(payload["items"], 1):
            key = (row["food_ingredient_id"], row["form_basis"], row["unit"])
            if key not in totals or row["ordinal"] != ordinal:
                raise ValueError("unexpected Shopping item")
            if Decimal(row["required_quantity"]) != _round(totals.pop(key), ROUND_CEILING):
                raise ValueError("rounded item total differs")
        if totals or len(calculation.items) != len(payload["items"]):
            raise ValueError("Shopping quantity count differs")
        for raw, stored in zip(payload["items"], calculation.items, strict=True):
            if (
                raw["food_ingredient_id"] != str(stored.food_ingredient_id)
                or raw["unit"] != str(stored.unit)
                or raw["required_quantity"] != _exact(stored.required_quantity)
                or raw["pantry_available_quantity"] != _exact(stored.pantry_available_quantity)
                or raw["purchase_quantity"] != _exact(stored.purchase_quantity)
            ):
                raise ValueError("persisted item differs")
        if _fingerprint({
            "source_fingerprint": calculation.source_fingerprint,
            "component_contributions": payload["component_contributions"],
            "event_demands": payload["event_demands"],
            "items": payload["items"], "unresolved": payload["unresolved"],
            "warnings": payload["warnings"], "allocations": payload["allocations"],
        }) != calculation.content_fingerprint:
            raise ValueError("V2 content fingerprint")
    except (KeyError, IndexError, TypeError, ValueError, ArithmeticError) as exc:
        raise ShoppingCalculationError(
            "Невозможно независимо воспроизвести диагностический Shopping V2."
        ) from exc
