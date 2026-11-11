"""Explain canonical Shopping gross by actual persisted RecipeIngredient/Serving rows.

Developer-only product evidence. This is not a second Shopping authority:
every unrounded event contribution must reconcile to the existing engine's
rounded gross or the preview is blocked. Do not infer food purchasing policy.
"""

from __future__ import annotations

from collections import defaultdict
from decimal import ROUND_CEILING, Decimal, InvalidOperation, localcontext

from app.domain.meal_plans import MealSourceKind
from app.domain.shopping_calculation import QUANTITY_STEP


class ShoppingOriginBlocked(ValueError):
    """Invalid sources cannot support an explainable shopping item."""


def shopping_origins(*, plan, recipes, shopping):
    """Return event-level origin rows keyed by immutable FoodIngredient and unit.

    Values are rounded UP to 0.001 only for human display. The reconciliation
    uses unrounded Decimal source quantities, same as Shopping's aggregate.
    Origin rows intentionally do not contain run-local UUIDs.
    """
    event_totals = defaultdict(lambda: Decimal(0))
    for serving in plan.servings:
        if (
            not isinstance(serving.portion_servings, Decimal)
            or not serving.portion_servings.is_finite()
            or serving.portion_servings <= 0
        ):
            raise ShoppingOriginBlocked("Invalid persisted Serving in Shopping origin")
        event_totals[serving.event_id] += serving.portion_servings

    gross = defaultdict(lambda: Decimal(0))
    origin_values = defaultdict(lambda: defaultdict(lambda: Decimal(0)))
    events = sorted(plan.events, key=lambda e: (e.local_date, e.position, str(e.id)))
    with localcontext() as ctx:
        ctx.prec = 50
        for event in events:
            if (
                event.source_kind is not MealSourceKind.COOK_RECIPE
                or event.recipe_version_id not in recipes
                or event.id not in event_totals
            ):
                raise ShoppingOriginBlocked("Unbound or non-recipe Shopping source")
            detail = recipes[event.recipe_version_id]
            base = detail.version.base_servings
            total = event_totals[event.id]
            if not isinstance(base, Decimal) or not base.is_finite() or base <= 0:
                raise ShoppingOriginBlocked("Invalid source RecipeVersion servings")
            identity = (
                event.local_date.isoformat(),
                event.position,
                event.role.value,
                detail.recipe.canonical_code,
                detail.recipe.canonical_name,
            )
            for ingredient in detail.ingredients:
                quantity = ingredient.quantity
                if (
                    not isinstance(quantity, Decimal)
                    or not quantity.is_finite()
                    or quantity <= 0
                ):
                    raise ShoppingOriginBlocked(
                        "Invalid source RecipeIngredient quantity"
                    )
                key = ingredient.food_ingredient_id, ingredient.unit
                value = quantity * total / base
                if not value.is_finite() or value <= 0:
                    raise ShoppingOriginBlocked("Invalid scaled ingredient demand")
                gross[key] += value
                origin_values[key][identity] += value

        expected_keys = {
            (item.food_ingredient_id, item.unit) for item in shopping.items
        }
        if len(expected_keys) != len(shopping.items) or set(gross) != expected_keys:
            raise ShoppingOriginBlocked("Shopping items and event origins differ")

        result = {}
        for item in shopping.items:
            key = item.food_ingredient_id, item.unit
            try:
                required = gross[key].quantize(QUANTITY_STEP, rounding=ROUND_CEILING)
            except InvalidOperation as exc:
                raise ShoppingOriginBlocked(
                    "Unroundable source ingredient demand"
                ) from exc
            if required != item.required_quantity:
                raise ShoppingOriginBlocked("Event source gross differs from Shopping")
            origins = []
            for (day, position, role, code, title), raw in sorted(
                origin_values[key].items()
            ):
                if not title or raw <= 0:
                    raise ShoppingOriginBlocked(
                        "Missing recipe display/source quantity"
                    )
                amount = raw.quantize(QUANTITY_STEP, rounding=ROUND_CEILING)
                origins.append(
                    {
                        "date": day,
                        "position": position,
                        "role": role,
                        "recipe_code": code,
                        "recipe_title_ru": title,
                        "source_demand_up_001": format(amount, "f"),
                        "unit": item.unit.value,
                    }
                )
            if not origins:
                raise ShoppingOriginBlocked("Missing Shopping source events")
            result[key] = origins
    return result


def assert_origins_match_sources(*, plan, recipes, shopping, published_origins):
    """Reject a plausible but reallocated breakdown using trusted recipe facts.

    Gross-only validation cannot detect two correct MealEvents exchanging their
    displayed amounts. Recompute each individual contribution from persisted
    RecipeIngredients and exact Decimal Servings before publication. The HTML
    renderer has only a projection and cannot independently establish this.
    """
    expected = shopping_origins(plan=plan, recipes=recipes, shopping=shopping)
    if published_origins != expected:
        raise ShoppingOriginBlocked(
            "Individual Shopping origins differ from source RecipeIngredients/Servings"
        )
