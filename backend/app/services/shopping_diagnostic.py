"""Test/developer-only Shopping v1b composition writer and guarded readback.

NOT registered in app.main, FastAPI, public ShoppingService or consumer flows.
Existing v1a APIs remain legacy-only; provenance and quantities never leak.
"""

import json
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from app.domain.meal_plans import MealPlanStatus, MealSourceKind
from app.domain.shopping_calculation import (
    ShoppingCalculation,
    ShoppingCalculationError,
    ShoppingLotAllocation,
    ShoppingQuantity,
    ShoppingUnresolved,
    ShoppingWarning,
)
from app.domain.shopping_composition_calculation import (
    ENGINE_VERSION,
    SCHEMA_V2,
    calculate_shopping_composition,
    validate_v2_provenance,
)
from app.domain.shopping_lists import ShoppingListDetail
from app.services.shopping import ShoppingService
from app.services.shopping_contracts import (
    ShoppingNotFoundError,
    ShoppingPersistenceError,
)


class DiagnosticCompositionShoppingService(ShoppingService):
    """Explicit internal-only capability. No public dependency ever constructs it."""

    def _calculate_diagnostic(
        self, scope, household_id: UUID, plan_id: UUID, captured: datetime
    ):
        household = scope.households.get_household(household_id)
        plan = scope.plans.get_detail(household_id, plan_id)
        if household is None or plan is None:
            raise ShoppingNotFoundError("План не найден для диагностического расчёта.")
        current = scope.plans.get_current(household_id, plan.plan.week_start)
        if (
            current is None
            or current.plan.id != plan_id
            or not plan.compositions
            or plan.plan.status is not MealPlanStatus.DRAFT
        ):
            raise ShoppingCalculationError(
                "Для внутреннего Shopping требуется текущая диагностическая ревизия."
            )
        versions = {
            e.recipe_version_id
            for e in plan.events
            if e.source_kind is MealSourceKind.COOK_RECIPE
        } | {
            part.recipe_version_id
            for comp in plan.compositions
            for part in comp.components
        }
        recipes = {}
        food_ids = set()
        for vid in sorted(versions, key=str):
            if vid is None:
                raise ShoppingCalculationError("Неполная ссылка на рецепт.")
            detail = scope.recipes.get_detail(vid)
            if detail is None:
                raise ShoppingCalculationError(
                    "Недоступна закреплённая версия рецепта."
                )
            recipes[vid] = detail
            food_ids.update(i.food_ingredient_id for i in detail.ingredients)
        foods = {}
        for fid in sorted(food_ids, key=str):
            food = scope.foods.get(fid)
            if food is None:
                raise ShoppingCalculationError(
                    "Недоступен канонический FoodIngredient."
                )
            foods[fid] = food
        return calculate_shopping_composition(
            plan=plan,
            recipes=recipes,
            foods=foods,
            pantry_items=tuple(
                scope.pantry.list_items(household_id, include_empty=True)
            ),
            household_timezone=household.timezone,
            captured_at=captured,
        )

    def generate_diagnostic(
        self, household_id: UUID, plan_id: UUID
    ) -> ShoppingListDetail:
        """Synthetic-only atomic source-backed list. No implicit public promotion."""
        captured = self._clock()
        with self._write() as scope:
            calculated, provenance = self._calculate_diagnostic(
                scope, household_id, plan_id, captured
            )
            validate_v2_provenance(provenance, calculated)
            return self._persist_calculated(
                scope, household_id, plan_id, captured, calculated, provenance
            )

    def get_diagnostic_detail(
        self, household_id: UUID, list_id: UUID
    ) -> ShoppingListDetail:
        """Restricted test/dev reader; public ShoppingService never calls this."""
        with self._read() as scope:
            detail = scope.shopping.get_detail(household_id, list_id)
            if detail is None:
                raise ShoppingNotFoundError("Диагностический список не найден.")
            plan = scope.plans.get_detail(
                household_id, detail.shopping_list.meal_plan_id
            )
            if plan is None or not plan.compositions:
                raise ShoppingNotFoundError("Диагностический список не найден.")
            try:
                source = json.loads(detail.shopping_list.provenance_json)
            except (TypeError, ValueError) as exc:
                raise ShoppingPersistenceError(
                    "Повреждён diagnostic provenance."
                ) from exc
            if (
                detail.shopping_list.engine_version != ENGINE_VERSION
                or not isinstance(source, dict)
                or source.get("schema") != SCHEMA_V2
                or not isinstance(source.get("calculation"), dict)
                or source["calculation"].get("engine") != ENGINE_VERSION
            ):
                raise ShoppingPersistenceError("Недопустимая диагностическая версия.")
            header = detail.shopping_list
            try:
                meta = source["calculation"]
                if (
                    header.household_id != household_id
                    or header.meal_plan_id != plan.plan.id
                    or header.source_plan_revision_number != plan.plan.revision_number
                    or meta["week_start"] != plan.plan.week_start.isoformat()
                    or meta["config_version"] != plan.plan.config_version
                    or meta["config_fingerprint"] != header.config_fingerprint
                ):
                    raise ValueError("V2 persisted header differs from plan/provenance")
                if len(source["items"]) != len(detail.items) or len(
                    source["unresolved"]
                ) != len(detail.unresolved):
                    raise ValueError("V2 persisted row count differs")
                for ordinal, (raw, item) in enumerate(
                    zip(source["items"], detail.items, strict=True), 1
                ):
                    if (
                        item.shopping_list_id != header.id
                        or item.household_id != household_id
                        or item.ordinal != ordinal
                        or raw["ordinal"] != ordinal
                        or raw["food_ingredient_id"] != str(item.food_ingredient_id)
                        or raw["form_basis"] != item.form_basis
                        or raw["unit"] != str(item.unit)
                        or Decimal(raw["required_quantity"]) != item.required_quantity
                        or Decimal(raw["pantry_available_quantity"])
                        != item.pantry_available_quantity
                        or Decimal(raw["purchase_quantity"]) != item.purchase_quantity
                    ):
                        raise ValueError("V2 persisted Shopping item differs")
                for ordinal, (raw, item) in enumerate(
                    zip(source["unresolved"], detail.unresolved, strict=True), 1
                ):
                    if (
                        item.shopping_list_id != header.id
                        or item.household_id != household_id
                        or item.ordinal != ordinal
                        or raw["meal_event_id"] != str(item.meal_event_id)
                        or raw["source_kind"] != str(item.source_kind)
                        or raw["reason"] != str(item.reason)
                    ):
                        raise ValueError("V2 persisted unresolved obligation differs")
                reconstructed = ShoppingCalculation(
                    household_id=header.household_id,
                    meal_plan_id=header.meal_plan_id,
                    source_plan_revision_number=header.source_plan_revision_number,
                    as_of_date=header.as_of_date,
                    engine_version=header.engine_version,
                    pantry_policy_version=header.pantry_policy_version,
                    status=header.status,
                    price_status=header.price_status,
                    items=tuple(
                        ShoppingQuantity(
                            item.food_ingredient_id,
                            item.form_basis,
                            item.unit,
                            item.required_quantity,
                            item.pantry_available_quantity,
                            item.purchase_quantity,
                        )
                        for item in detail.items
                    ),
                    unresolved=tuple(
                        ShoppingUnresolved(
                            item.meal_event_id, item.source_kind, item.reason
                        )
                        for item in detail.unresolved
                    ),
                    warnings=tuple(
                        ShoppingWarning(
                            item["code"],
                            UUID(item["pantry_item_id"]),
                            UUID(item["meal_event_id"])
                            if item["meal_event_id"]
                            else None,
                            date.fromisoformat(item["required_date"])
                            if item["required_date"]
                            else None,
                        )
                        for item in source["warnings"]
                    ),
                    allocations=tuple(
                        ShoppingLotAllocation(
                            UUID(item["meal_event_id"]),
                            UUID(item["pantry_item_id"]),
                            UUID(item["food_ingredient_id"]),
                            Decimal(item["quantity"]),
                        )
                        for item in source["allocations"]
                    ),
                    pantry_snapshot_hash=header.source_pantry_snapshot_hash,
                    source_fingerprint=header.source_fingerprint,
                    content_fingerprint=header.content_fingerprint,
                )
                validate_v2_provenance(source, reconstructed)
            except (ValueError, KeyError, TypeError) as exc:
                raise ShoppingPersistenceError(
                    "Диагностический V2 provenance не воспроизводится."
                ) from exc
            return detail
