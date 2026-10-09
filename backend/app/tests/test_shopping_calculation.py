"""Contract tests for the pure PR9-A Shopping calculation seam."""

from dataclasses import replace
from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from app.domain.errors import DomainValidationError
from app.domain.meal_patterns import MealRole
from app.domain.meal_plans import (
    HouseholdMealEvent,
    MealPlan,
    MealPlanDetail,
    MealPlanMemberSelection,
    MealPlanStatus,
    MealSourceKind,
    Serving,
)
from app.domain.pantry import PantryItem, PantryLocation
from app.domain.shopping_calculation import (
    ShoppingCalculationError,
    ShoppingPriceStatus,
    ShoppingStatus,
    ShoppingUnresolvedReason,
    calculate_shopping,
)
from app.domain.units import UnitCode
from app.tests.test_food_ingredient_domain import ingredient
from app.tests.test_food_recipe_domain import _detail

AS_OF = datetime(2026, 10, 9, 10, tzinfo=timezone.utc)
WEEK = date(2026, 10, 5)


def _input(
    *,
    kinds=(MealSourceKind.COOK_RECIPE,),
    dates=None,
    member_portions=("3",),
    recipe=None,
):
    recipe = recipe or _detail()
    rice_id = recipe.ingredients[0].food_ingredient_id
    leaf_id = recipe.ingredients[1].food_ingredient_id
    rice = ingredient(
        id=rice_id,
        canonical_code="RICE",
        canonical_name="Рис",
        canonical_name_key="рис",
    )
    leaf = ingredient(
        id=leaf_id,
        canonical_code="BAY_LEAF",
        canonical_name="Лавровый лист",
        canonical_name_key="лавровый лист",
        default_unit=UnitCode.PIECE,
    )
    household = uuid4()
    plan = MealPlan(
        uuid4(), household, WEEK, 1, MealPlanStatus.CONFIRMED, "test-v1", None, AS_OF
    )
    members = [uuid4() for _ in member_portions]
    selections = tuple(
        MealPlanMemberSelection(plan.id, member, uuid4()) for member in members
    )
    events = []
    servings = []
    dates = dates or tuple(WEEK for _ in kinds)
    for index, (kind, event_date) in enumerate(zip(kinds, dates, strict=True)):
        # Positions are contiguous within each calendar date.
        position = sum(e.local_date == event_date for e in events) + 1
        event = HouseholdMealEvent(
            uuid4(),
            plan.id,
            event_date,
            position,
            MealRole.DINNER,
            kind,
            recipe.version.id if kind is MealSourceKind.COOK_RECIPE else None,
            None,
            AS_OF,
        )
        events.append(event)
        servings.extend(
            Serving(uuid4(), event.id, m, Decimal(q), AS_OF)
            for m, q in zip(members, member_portions, strict=True)
        )
    meal = MealPlanDetail(plan, selections, tuple(events), tuple(servings))
    return meal, {recipe.version.id: recipe}, {rice.id: rice, leaf.id: leaf}


def _pantry(
    meal: MealPlanDetail,
    food_id,
    amount,
    *,
    expires_on=date(2026, 10, 12),
    estimated=False,
    location=PantryLocation.PANTRY,
    unit=UnitCode.GRAM,
):
    return PantryItem(
        uuid4(),
        meal.plan.household_id,
        food_id,
        Decimal(amount),
        unit,
        location,
        estimated,
        None,
        None,
        expires_on,
        AS_OF,
        AS_OF,
    )


def _calculate(meal, recipes, foods, pantry=(), **kwargs):
    return calculate_shopping(
        plan=meal,
        recipes=recipes,
        foods=foods,
        pantry_items=tuple(pantry),
        household_timezone=kwargs.get("tz", "Europe/Moscow"),
        captured_at=kwargs.get("clock", AS_OF),
    )


def _amounts(result, food_id):
    item = next(x for x in result.items if x.food_ingredient_id == food_id)
    return (
        item.required_quantity,
        item.pantry_available_quantity,
        item.purchase_quantity,
    )


def test_scaled_per_member_and_base_servings_with_separate_unknown_price():
    meal, recipes, foods = _input(member_portions=("1", "2"))
    result = _calculate(meal, recipes, foods)
    rice_id, leaf_id = tuple(foods)
    assert _amounts(result, rice_id) == (
        Decimal("300.000"),
        Decimal("0.000"),
        Decimal("300.000"),
    )
    assert _amounts(result, leaf_id) == (
        Decimal("0.500"),
        Decimal("0.000"),
        Decimal("1.000"),
    )
    assert result.status is ShoppingStatus.COMPLETE
    assert result.price_status is ShoppingPriceStatus.UNKNOWN
    assert (
        result.pantry_snapshot_hash
        and result.source_fingerprint
        and result.content_fingerprint
    )


@pytest.mark.parametrize(
    ("members", "expected_rice", "expected_leaf_purchase"),
    [
        (("1",), "100.000", "1.000"),
        (("2", "3"), "500.000", "1.000"),
        (("1", "2", "3"), "600.000", "1.000"),
    ],
)
def test_participating_servings_scale_exactly_once(
    members, expected_rice, expected_leaf_purchase
):
    meal, recipes, foods = _input(member_portions=members)
    result = _calculate(meal, recipes, foods)
    rice_id, leaf_id = tuple(foods)
    assert _amounts(result, rice_id)[0] == Decimal(expected_rice)
    assert _amounts(result, leaf_id)[2] == Decimal(expected_leaf_purchase)


def test_two_events_aggregate_once_with_stable_replay_and_read_only_state():
    meal, recipes, foods = _input(
        dates=(WEEK, WEEK.replace(day=6)), kinds=(MealSourceKind.COOK_RECIPE,) * 2
    )
    before = meal, tuple(recipes.items()), tuple(foods.items())
    first = _calculate(meal, recipes, foods)
    second = _calculate(meal, recipes, foods)
    assert first == second
    assert first.content_fingerprint == second.content_fingerprint
    assert len(first.items) == 2
    assert _amounts(first, next(iter(foods)))[0] == Decimal("600.000")
    assert (meal, tuple(recipes.items()), tuple(foods.items())) == before


@pytest.mark.parametrize(
    ("source", "reason"),
    [
        (MealSourceKind.ASSEMBLY, ShoppingUnresolvedReason.ASSEMBLY_UNSUPPORTED),
        (MealSourceKind.LEFTOVER, ShoppingUnresolvedReason.LEFTOVER_SUPPLY_UNVERIFIED),
        (MealSourceKind.PREPARED, ShoppingUnresolvedReason.PREPARED_SUPPLY_UNVERIFIED),
        (MealSourceKind.READY_MEAL, ShoppingUnresolvedReason.READY_MEAL_UNRESOLVED),
    ],
)
def test_non_recipe_supply_is_unresolved_not_silent_zero(source, reason):
    meal, recipes, foods = _input(kinds=(source,))
    result = _calculate(meal, recipes, foods)
    assert result.status is ShoppingStatus.INCOMPLETE
    assert result.price_status is ShoppingPriceStatus.UNKNOWN
    assert not result.items
    assert result.unresolved[0].reason is reason


@pytest.mark.parametrize("source", [MealSourceKind.ORDER_OUT, MealSourceKind.EAT_OUT])
def test_outside_meals_have_no_grocery_demand(source):
    meal, recipes, foods = _input(kinds=(source,))
    result = _calculate(meal, recipes, foods)
    assert result.status is ShoppingStatus.COMPLETE
    assert result.price_status is ShoppingPriceStatus.UNKNOWN
    assert result.items == result.unresolved == ()


def test_mixed_sources_do_not_double_count_leftovers():
    meal, recipes, foods = _input(
        kinds=(
            MealSourceKind.COOK_RECIPE,
            MealSourceKind.LEFTOVER,
            MealSourceKind.EAT_OUT,
        ),
        dates=(WEEK, WEEK.replace(day=6), WEEK.replace(day=7)),
    )
    result = _calculate(meal, recipes, foods)
    assert result.status is ShoppingStatus.INCOMPLETE
    assert _amounts(result, next(iter(foods)))[0] == Decimal("300.000")
    assert len(result.unresolved) == 1


def test_date_aware_expiry_allows_early_meal_but_never_late_meal():
    early, late = date(2026, 10, 9), date(2026, 10, 11)
    meal, recipes, foods = _input(
        kinds=(MealSourceKind.COOK_RECIPE,) * 2, dates=(early, late)
    )
    rice_id = next(iter(foods))
    lot = _pantry(meal, rice_id, "300", expires_on=early)
    before = lot
    result = _calculate(meal, recipes, foods, pantry=(lot,))
    assert _amounts(result, rice_id) == (
        Decimal("600.000"),
        Decimal("300.000"),
        Decimal("300.000"),
    )
    assert len(result.allocations) == 1
    assert result.allocations[0].meal_event_id == meal.events[0].id
    assert lot == before


def test_future_week_lot_cannot_reduce_future_purchase():
    meal, recipes, foods = _input(dates=(date(2026, 10, 11),))
    rice_id = next(iter(foods))
    lot = _pantry(meal, rice_id, "300", expires_on=date(2026, 10, 10))
    result = _calculate(meal, recipes, foods, pantry=(lot,))
    assert _amounts(result, rice_id) == (
        Decimal("300.000"),
        Decimal("0.000"),
        Decimal("300.000"),
    )
    assert not result.allocations
    assert result.status is ShoppingStatus.COMPLETE
    assert [
        (w.code, w.pantry_item_id, w.meal_event_id, w.required_date)
        for w in result.warnings
    ] == [
        (
            "EXPIRES_BEFORE_REQUIRED_DATE",
            lot.id,
            meal.events[0].id,
            date(2026, 10, 11),
        )
    ]


def test_lot_can_cover_early_meal_but_warn_for_unusable_remainder_on_late_meal():
    meal, recipes, foods = _input(
        kinds=(MealSourceKind.COOK_RECIPE,) * 2,
        dates=(date(2026, 10, 9), date(2026, 10, 11)),
    )
    rice_id = next(iter(foods))
    lot = _pantry(meal, rice_id, "450", expires_on=date(2026, 10, 10))
    result = _calculate(meal, recipes, foods, pantry=(lot,))
    assert _amounts(result, rice_id) == (
        Decimal("600.000"),
        Decimal("300.000"),
        Decimal("300.000"),
    )
    assert len(result.allocations) == 1
    assert result.allocations[0].meal_event_id == meal.events[0].id
    assert result.allocations[0].quantity == Decimal(300)
    assert len(result.warnings) == 1
    warning = result.warnings[0]
    assert warning.code == "EXPIRES_BEFORE_REQUIRED_DATE"
    assert warning.pantry_item_id == lot.id
    assert warning.meal_event_id == meal.events[1].id
    assert warning.required_date == date(2026, 10, 11)
    assert result.status is ShoppingStatus.COMPLETE
    assert _calculate(meal, recipes, foods, pantry=(lot,)) == result


def test_fefo_lots_not_reused_and_all_storage_locations_allowed():
    meal, recipes, foods = _input(
        kinds=(MealSourceKind.COOK_RECIPE,) * 2,
        dates=(date(2026, 10, 9), date(2026, 10, 10)),
    )
    rice_id = next(iter(foods))
    first = _pantry(
        meal,
        rice_id,
        "150",
        expires_on=date(2026, 10, 9),
        location=PantryLocation.FRIDGE,
    )
    second = _pantry(
        meal,
        rice_id,
        "350",
        expires_on=date(2026, 10, 12),
        location=PantryLocation.FREEZER,
    )
    result = _calculate(meal, recipes, foods, pantry=(second, first))
    assert _amounts(result, rice_id) == (
        Decimal("600.000"),
        Decimal("500.000"),
        Decimal("100.000"),
    )
    assert sum(a.quantity for a in result.allocations) == Decimal(500)
    assert sum(
        a.quantity for a in result.allocations if a.pantry_item_id == first.id
    ) == Decimal(150)
    assert result.status is ShoppingStatus.COMPLETE


def test_estimated_unknown_expiry_and_expired_are_not_subtracted():
    meal, recipes, foods = _input(dates=(date(2026, 10, 9),))
    rice = next(iter(foods))
    lots = (
        _pantry(meal, rice, "100", estimated=True),
        _pantry(meal, rice, "100", expires_on=None),
        _pantry(meal, rice, "100", expires_on=date(2026, 10, 8)),
    )
    result = _calculate(meal, recipes, foods, pantry=lots)
    assert _amounts(result, rice)[1:] == (Decimal("0.000"), Decimal("300.000"))
    assert result.status is ShoppingStatus.COMPLETE
    assert {w.code for w in result.warnings} == {
        "ESTIMATED_STOCK",
        "EXPIRY_UNKNOWN",
        "EXPIRED_STOCK",
    }


def test_fractional_pieces_round_up_once_and_small_quantity_not_lost():
    recipe = _detail()
    recipe = replace(
        recipe,
        ingredients=(
            replace(recipe.ingredients[0], quantity=Decimal("0.001")),
            recipe.ingredients[1],
        ),
    )
    meal, recipes, foods = _input(recipe=recipe, member_portions=("1",))
    result = _calculate(meal, recipes, foods)
    rice_id, leaf_id = tuple(foods)
    assert _amounts(result, rice_id)[0] == Decimal("0.001")
    assert _amounts(result, leaf_id)[0] == Decimal("0.167")
    assert _amounts(result, leaf_id)[2] == Decimal("1.000")


def test_excess_pantry_never_produces_negative_purchase():
    meal, recipes, foods = _input(dates=(date(2026, 10, 9),))
    rice = next(iter(foods))
    result = _calculate(meal, recipes, foods, pantry=(_pantry(meal, rice, "800"),))
    assert _amounts(result, rice) == (
        Decimal("300.000"),
        Decimal("300.000"),
        Decimal("0.000"),
    )


def test_aggregate_overflow_from_two_valid_events_fails_closed():
    meal, recipes, foods = _input(
        kinds=(MealSourceKind.COOK_RECIPE,) * 2,
        dates=(date(2026, 10, 9), date(2026, 10, 10)),
        member_portions=("6000000000",),
    )
    rice_id = next(iter(foods))
    lot = _pantry(meal, rice_id, "50")
    before = lot
    # Each event requires 600_000_000_000 g (under the limit);
    # the aggregate 1_200_000_000_000 g must not be persisted or returned.
    with pytest.raises(ShoppingCalculationError, match="превышает допустимый предел"):
        _calculate(meal, recipes, foods, pantry=(lot,))
    assert lot == before


def test_pantry_metadata_and_date_change_fingerprints():
    meal, recipes, foods = _input(dates=(date(2026, 10, 9),))
    rice = next(iter(foods))
    stock = _pantry(meal, rice, "150")
    a = _calculate(meal, recipes, foods, pantry=(stock,))
    b = _calculate(
        meal, recipes, foods, pantry=(replace(stock, location=PantryLocation.FRIDGE),)
    )
    assert a.pantry_snapshot_hash != b.pantry_snapshot_hash
    assert a.content_fingerprint != b.content_fingerprint
    midnight = datetime(2026, 10, 9, 21, 10, tzinfo=timezone.utc)
    c = _calculate(meal, recipes, foods, pantry=(stock,), clock=midnight)
    assert c.as_of_date == date(2026, 10, 10)
    assert c.source_fingerprint != a.source_fingerprint


def test_cross_household_pantry_or_missing_recipe_fails_closed():
    meal, recipes, foods = _input()
    rice = next(iter(foods))
    alien = replace(_pantry(meal, rice, "5"), household_id=uuid4())
    with pytest.raises(ShoppingCalculationError):
        _calculate(meal, recipes, foods, pantry=(alien,))
    with pytest.raises(ShoppingCalculationError):
        _calculate(meal, {}, foods)


def test_incompatible_unit_and_optional_ingredient_fail_closed():
    recipe = _detail()
    meal, recipes, foods = _input(recipe=recipe)
    rice_id = next(iter(foods))
    altered = replace(
        recipe,
        ingredients=(
            replace(recipe.ingredients[0], unit=UnitCode.PIECE),
            recipe.ingredients[1],
        ),
    )
    with pytest.raises(ShoppingCalculationError, match="Несовместимые"):
        _calculate(meal, {recipe.version.id: altered}, foods)
    optional = replace(
        recipe,
        ingredients=(
            replace(recipe.ingredients[0], optional=True),
            recipe.ingredients[1],
        ),
    )
    with pytest.raises(ShoppingCalculationError, match="не зафиксирован"):
        _calculate(meal, {recipe.version.id: optional}, foods)
    # Food identity keys must not be silently guessed from similar display names.
    with pytest.raises(ShoppingCalculationError):
        _calculate(
            meal, recipes, {fid: f for fid, f in foods.items() if fid != rice_id}
        )


def test_reject_naive_clock_and_external_float_inputs():
    meal, recipes, foods = _input()
    with pytest.raises(ShoppingCalculationError):
        _calculate(meal, recipes, foods, clock=AS_OF.replace(tzinfo=None))
    # Input domain rejects invalid arithmetic before Shopping ever receives it.
    original = next(iter(recipes.values())).ingredients[0]
    with pytest.raises(DomainValidationError):
        replace(original, quantity=Decimal(0))
    with pytest.raises(DomainValidationError):
        replace(original, quantity=1.0)
