from dataclasses import asdict, replace
from decimal import Decimal, ROUND_DOWN, localcontext

import pytest

from app.domain.nutrition import (
    NutritionStatus as Status,
    NutritionWarningCode as Code,
    calculate_recipe_nutrition as calculate_reviewed_recipe,
    scale_food_nutrition,
)
from app.tests.test_food_ingredient_domain import ingredient, profile
from app.tests.test_food_recipe_domain import _detail


from app.tests.nutrition_evidence_fixtures import gram_assessments


def calculate_recipe_nutrition(detail, ingredients, profiles):
    # Existing aggregate regressions now explicitly review their synthetic g rows.
    return calculate_reviewed_recipe(
        detail, ingredients, profiles, gram_assessments(detail, profiles)
    )


def fixture_recipe(*, quantity="100", unit="g", optional=False, **profile_changes):
    detail = _detail()
    food = ingredient(edible_fraction="0.5")
    nutrition = profile(
        food_ingredient_id=food.id,
        kcal="200",
        protein_g="10",
        fat_g="5",
        carbohydrates_g="30",
        fiber_g="2",
        estimated=False,
        **profile_changes,
    )
    first = replace(
        detail.ingredients[0],
        food_ingredient_id=food.id,
        quantity=Decimal(quantity),
        unit=unit,
    )
    second = replace(
        detail.ingredients[1],
        food_ingredient_id=food.id,
        quantity=Decimal(quantity),
        unit=unit,
        optional=optional,
    )
    return replace(detail, ingredients=(first, second)), food, nutrition


def codes(result):
    return [warning.code for warning in result.warnings]


@pytest.mark.parametrize(
    "mass,expected",
    [
        ("100", ("200", "10", "5", "30", "2")),
        ("50", ("100", "5", "2.5", "15", "1")),
        ("33.333333", ("66.666666", "3.333333", "1.666667", "10", ".666667")),
    ],
)
def test_scaling_decimal_rounding_and_provenance(mass, expected):
    _, food, nutrition = fixture_recipe()
    result = scale_food_nutrition(food, nutrition, Decimal(mass))
    assert tuple(asdict(result.values).values()) == tuple(map(Decimal, expected))
    assert result.status == Status.COMPLETE
    assert result.profile == nutrition
    assert result.ingredient == food  # Includes exact density and update instant.
    assert result.mass_g == Decimal(mass)  # No edible fraction transformation.
    assert result == scale_food_nutrition(food, nutrition, Decimal(mass))
    assert result.config.version == "FAMILY_FOOD_NUTRITION_V1"


@pytest.mark.parametrize("quantity", [1.5, True, 100, "100", None])
def test_no_float_or_implicit_numeric_coercion(quantity):
    _, food, nutrition = fixture_recipe()
    with pytest.raises(TypeError, match="Decimal"):
        scale_food_nutrition(food, nutrition, quantity)


@pytest.mark.parametrize("quantity", ["0", "-1", "NaN", "Infinity", "1e25", "1e-19"])
def test_invalid_decimal_quantity_is_bounded(quantity):
    _, food, nutrition = fixture_recipe()
    with pytest.raises(ValueError, match="bounds"):
        scale_food_nutrition(food, nutrition, Decimal(quantity))


def test_ml_only_uses_explicit_density_and_pcs_never_invents_egg_mass():
    _, food, nutrition = fixture_recipe()
    result = scale_food_nutrition(
        replace(food, density_g_per_ml=Decimal(".92")), nutrition, Decimal("12.5"), "ml"
    )
    assert result.mass_g == Decimal("11.5")
    assert result.values.kcal == Decimal(23)
    for unit, reason in (
        ("ml", Code.MISSING_DENSITY),
        ("pcs", Code.UNSUPPORTED_PIECE_MASS),
    ):
        result = scale_food_nutrition(food, nutrition, Decimal(6), unit)
        assert result.mass_g is None
        assert all(value is None for value in asdict(result.values).values())
        assert result.status == Status.INCOMPLETE
        assert codes(result) == [reason]


@pytest.mark.parametrize("missing", ["density", "piece_mass", "profile", "ingredient"])
def test_required_failure_never_publishes_partial_total(missing):
    detail, food, nutrition = fixture_recipe()
    other = ingredient()
    row = replace(
        detail.ingredients[1],
        food_ingredient_id=other.id,
        unit={"density": "ml", "piece_mass": "pcs"}.get(missing, "g"),
    )
    detail = replace(detail, ingredients=(detail.ingredients[0], row))
    foods = {food.id: food}
    if missing != "ingredient":
        foods[other.id] = other
    profiles = {food.id: nutrition}
    if missing not in ("profile", "ingredient"):
        profiles[other.id] = replace(nutrition, food_ingredient_id=other.id)
    result = calculate_recipe_nutrition(detail, foods, profiles)
    assert result.status == Status.INCOMPLETE
    assert all(value is None for value in asdict(result.required_total).values())
    assert all(value is None for value in asdict(result.per_base_serving).values())
    assert result.required_contributions[0].nutrition.values.kcal == Decimal(200)


def test_fiber_unknown_estimated_and_unknown_estimation_propagate():
    detail, food, nutrition = fixture_recipe()
    nutrition = replace(nutrition, fiber_g=None, estimated=True)
    result = calculate_recipe_nutrition(detail, {food.id: food}, {food.id: nutrition})
    assert result.required_total.kcal == Decimal(400)
    assert result.required_total.fiber_g is None
    assert result.per_base_serving.fiber_g is None
    assert result.status == Status.COMPLETE_WITH_WARNINGS
    assert codes(result) == [Code.UNKNOWN_FIBER, Code.ESTIMATED_SOURCE] * 2
    assert all(
        item.nutrition.profile.estimated is True
        for item in result.required_contributions
    )
    unknown = scale_food_nutrition(
        food, replace(nutrition, estimated=None), Decimal(100)
    )
    assert Code.ESTIMATION_STATUS_UNKNOWN in codes(unknown)


@pytest.mark.parametrize("unit", ["g", "pcs"])
def test_optional_rows_are_separate_and_conditional_even_when_unresolved(unit):
    detail, food, nutrition = fixture_recipe(optional=True)
    detail = replace(
        detail,
        ingredients=(detail.ingredients[0], replace(detail.ingredients[1], unit=unit)),
    )
    result = calculate_recipe_nutrition(detail, {food.id: food}, {food.id: nutrition})
    assert result.status == Status.CONDITIONAL
    assert result.required_total.kcal == Decimal(200)
    assert result.per_base_serving.kcal == Decimal("33.333333")
    assert len(result.required_contributions) == len(result.optional_contributions) == 1
    assert result.optional_contributions[0].nutrition.values.kcal == (
        Decimal(200) if unit == "g" else None
    )
    assert Code.OPTIONAL_INGREDIENT in codes(result)
    incomplete = calculate_recipe_nutrition(detail, {food.id: food}, {})
    assert (
        incomplete.status == Status.INCOMPLETE
    )  # Required failure wins over optional.


def test_sum_and_division_use_unrounded_values_and_are_context_independent():
    detail, food, nutrition = fixture_recipe(quantity="0.000001")
    nutrition = replace(nutrition, kcal=Decimal(50))
    snapshot = asdict(detail)
    result = calculate_recipe_nutrition(detail, {food.id: food}, {food.id: nutrition})
    assert result.required_total.kcal == Decimal(
        ".000001"
    )  # Two raw .0000005 contributions.
    assert sum(
        item.nutrition.values.kcal for item in result.required_contributions
    ) == Decimal(".000002")
    assert result.per_base_serving.kcal == Decimal("0.000000")
    with localcontext() as caller:
        caller.prec = 2
        caller.rounding = ROUND_DOWN
        assert (
            calculate_recipe_nutrition(detail, {food.id: food}, {food.id: nutrition})
            == result
        )
        assert caller.prec == 2
    assert asdict(detail) == snapshot
    # A rounded recipe total divided again would give .000001, but raw gives zero.
    detail = replace(detail, version=replace(detail.version, base_servings=Decimal(4)))
    nutrition = replace(nutrition, kcal=Decimal(80))
    result = calculate_recipe_nutrition(detail, {food.id: food}, {food.id: nutrition})
    assert result.required_total.kcal == Decimal(".000002")
    assert result.per_base_serving.kcal == Decimal(0)


def test_all_profile_inputs_and_stable_row_warning_order_are_preserved():
    detail, food, nutrition = fixture_recipe(unit="ml")
    other = ingredient()
    second_profile = replace(
        nutrition, id=other.id, food_ingredient_id=other.id, estimated=True
    )
    detail = replace(
        detail,
        ingredients=(
            detail.ingredients[0],
            replace(detail.ingredients[1], food_ingredient_id=other.id),
        ),
    )
    result = calculate_recipe_nutrition(
        detail,
        {food.id: food, other.id: other},
        {food.id: nutrition, other.id: second_profile},
    )
    assert [item.nutrition.profile.id for item in result.required_contributions] == [
        nutrition.id,
        second_profile.id,
    ]
    assert [
        (warning.recipe_ingredient_id, warning.code) for warning in result.warnings
    ] == [
        (detail.ingredients[0].id, Code.MISSING_NUTRITION_ASSESSMENT),
        (detail.ingredients[1].id, Code.MISSING_NUTRITION_ASSESSMENT),
        (detail.ingredients[1].id, Code.ESTIMATED_SOURCE),
    ]


def test_mismatched_or_historical_profile_cannot_supply_current_truth():
    _, food, nutrition = fixture_recipe()
    for wrong in (profile(), replace(nutrition, is_current=False)):
        with pytest.raises(ValueError, match="matching current"):
            scale_food_nutrition(food, wrong, Decimal(100))


def test_multiple_known_profiles_aggregate_all_nutrients():
    detail, food, nutrition = fixture_recipe()
    other = ingredient()
    second = replace(
        nutrition,
        id=other.id,
        food_ingredient_id=other.id,
        kcal=Decimal(300),
        protein_g=Decimal(20),
        fat_g=Decimal(10),
        carbohydrates_g=Decimal(50),
        fiber_g=Decimal(8),
    )
    detail = replace(
        detail,
        ingredients=(
            detail.ingredients[0],
            replace(
                detail.ingredients[1], food_ingredient_id=other.id, quantity=Decimal(50)
            ),
        ),
    )
    result = calculate_recipe_nutrition(
        detail, {food.id: food, other.id: other}, {food.id: nutrition, other.id: second}
    )
    assert tuple(asdict(result.required_total).values()) == tuple(
        map(Decimal, (350, 20, 10, 55, 6))
    )
    assert result.status == Status.COMPLETE
    assert result.per_base_serving.fiber_g == Decimal(1)
