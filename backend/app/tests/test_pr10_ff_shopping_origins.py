"""Shopping source trace: exact unrounded reconciliation, no new authority."""

from dataclasses import replace
from datetime import date
from decimal import Decimal
from types import SimpleNamespace as Row
from uuid import uuid4

import pytest

from app.domain.meal_patterns import MealRole
from app.domain.meal_plans import MealSourceKind
from app.domain.units import UnitCode
from scripts.pr10_ff_shopping_origins import ShoppingOriginBlocked, shopping_origins


def _scenario():
    food_id, recipe_id = uuid4(), uuid4()
    events = [
        Row(
            id=uuid4(),
            local_date=date(2026, 11, day),
            position=1,
            role=MealRole.BREAKFAST,
            source_kind=MealSourceKind.COOK_RECIPE,
            recipe_version_id=recipe_id,
        )
        for day in (2, 3)
    ]
    plan = Row(
        events=tuple(events),
        servings=tuple(
            Row(
                event_id=event.id,
                portion_servings=Decimal("1.000000"),
            )
            for event in events
        ),
    )
    recipe = Row(
        recipe=Row(
            canonical_code="SOURCE_BACKED_TEST",
            canonical_name="Проверочный рецепт",
        ),
        version=Row(base_servings=Decimal(3)),
        ingredients=(
            Row(
                food_ingredient_id=food_id,
                unit=UnitCode.GRAM,
                quantity=Decimal(100),
            ),
        ),
    )
    gross = Decimal("66.667")
    item = Row(
        food_ingredient_id=food_id,
        unit=UnitCode.GRAM,
        required_quantity=gross,
    )
    shopping = Row(items=(item,))
    return plan, {recipe_id: recipe}, shopping


def test_two_events_reconcile_to_rounded_shopping_aggregate():
    plan, recipes, shopping = _scenario()
    out = shopping_origins(plan=plan, recipes=recipes, shopping=shopping)
    assert len(out) == 1
    sources = next(iter(out.values()))
    assert [x["date"] for x in sources] == ["2026-11-02", "2026-11-03"]
    assert [x["source_demand_up_001"] for x in sources] == [
        "33.334",
        "33.334",
    ]
    assert sum(
        Decimal(x["source_demand_up_001"]) for x in sources
    ) > shopping.items[0].required_quantity
    assert all(x["recipe_title_ru"] == "Проверочный рецепт" for x in sources)
    assert all(x["unit"] == "g" for x in sources)


def test_bad_gross_is_blocked_instead_of_rewritten():
    plan, recipes, shopping = _scenario()
    shopping.items = (Row(
        food_ingredient_id=shopping.items[0].food_ingredient_id,
        unit=UnitCode.GRAM,
        required_quantity=Decimal("66.666"),
    ),)
    with pytest.raises(ShoppingOriginBlocked, match="differs"):
        shopping_origins(plan=plan, recipes=recipes, shopping=shopping)


@pytest.mark.parametrize("mutation", ["missing_serving", "bad_serving", "bad_recipe", "bad_ingredient", "no_event"])
def test_bad_source_is_blocked(mutation):
    plan, recipes, shopping = _scenario()
    key = next(iter(recipes))
    if mutation == "missing_serving":
        plan.servings = plan.servings[1:]
    elif mutation == "bad_serving":
        plan.servings = (Row(event_id=plan.servings[0].event_id, portion_servings=Decimal("NaN")), *plan.servings[1:])
    elif mutation == "bad_recipe":
        recipes[key].version.base_servings = Decimal(0)
    elif mutation == "bad_ingredient":
        recipes[key].ingredients = (Row(
            food_ingredient_id=shopping.items[0].food_ingredient_id,
            unit=UnitCode.GRAM,
            quantity=Decimal("-1"),
        ),)
    elif mutation == "no_event":
        plan.events = ()
    with pytest.raises(ShoppingOriginBlocked):
        shopping_origins(plan=plan, recipes=recipes, shopping=shopping)
