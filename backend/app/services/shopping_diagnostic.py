"""Test/developer-only Shopping v1b composition writer and guarded readback.

NOT registered in app.main, FastAPI, public ShoppingService or consumer flows.
Existing v1a APIs remain legacy-only; provenance and quantities never leak.
"""

import json
from datetime import datetime
from uuid import UUID

from app.domain.meal_plans import MealPlanStatus, MealSourceKind
from app.domain.shopping_calculation import ShoppingCalculationError
from app.domain.shopping_composition_calculation import (
    ENGINE_VERSION,
    SCHEMA_V2,
    calculate_shopping_composition,
)
from app.domain.shopping_lists import ShoppingListDetail
from app.services.shopping import ShoppingService
from app.services.shopping_contracts import (
    ShoppingNotFoundError,
    ShoppingPersistenceError,
)


class DiagnosticCompositionShoppingService(ShoppingService):
    """Explicit internal-only capability. No public dependency ever constructs it."""

    def _calculate_diagnostic(self, scope, household_id: UUID, plan_id: UUID, captured: datetime):
        household = scope.households.get_household(household_id)
        plan = scope.plans.get_detail(household_id, plan_id)
        if household is None or plan is None:
            raise ShoppingNotFoundError("План не найден для диагностического расчёта.")
        current = scope.plans.get_current(household_id, plan.plan.week_start)
        if (
            current is None or current.plan.id != plan_id
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
                raise ShoppingCalculationError("Недоступна закреплённая версия рецепта.")
            recipes[vid] = detail
            food_ids.update(i.food_ingredient_id for i in detail.ingredients)
        foods = {}
        for fid in sorted(food_ids, key=str):
            food = scope.foods.get(fid)
            if food is None:
                raise ShoppingCalculationError("Недоступен канонический FoodIngredient.")
            foods[fid] = food
        return calculate_shopping_composition(
            plan=plan, recipes=recipes, foods=foods,
            pantry_items=tuple(scope.pantry.list_items(household_id, include_empty=True)),
            household_timezone=household.timezone,
            captured_at=captured,
        )

    def generate_diagnostic(self, household_id: UUID, plan_id: UUID) -> ShoppingListDetail:
        """Synthetic-only atomic source-backed list. No implicit public promotion."""
        captured = self._clock()
        with self._write() as scope:
            calculated, provenance = self._calculate_diagnostic(
                scope, household_id, plan_id, captured
            )
            return self._persist_calculated(
                scope, household_id, plan_id, captured, calculated, provenance
            )

    def get_diagnostic_detail(self, household_id: UUID, list_id: UUID) -> ShoppingListDetail:
        """Restricted test/dev reader; public ShoppingService never calls this."""
        with self._read() as scope:
            detail = scope.shopping.get_detail(household_id, list_id)
            if detail is None:
                raise ShoppingNotFoundError("Диагностический список не найден.")
            plan = scope.plans.get_detail(household_id, detail.shopping_list.meal_plan_id)
            if plan is None or not plan.compositions:
                raise ShoppingNotFoundError("Диагностический список не найден.")
            try:
                source = json.loads(detail.shopping_list.provenance_json)
            except (TypeError, ValueError) as exc:
                raise ShoppingPersistenceError("Повреждён diagnostic provenance.") from exc
            if (
                detail.shopping_list.engine_version != ENGINE_VERSION
                or not isinstance(source, dict)
                or source.get("schema") != SCHEMA_V2
                or not isinstance(source.get("calculation"), dict)
                or source["calculation"].get("engine") != ENGINE_VERSION
            ):
                raise ShoppingPersistenceError("Недопустимая диагностическая версия.")
            return detail
