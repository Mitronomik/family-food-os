"""Synthetic observations test policy semantics, never corpus authority."""

from dataclasses import replace
from decimal import Decimal, ROUND_DOWN, localcontext

import pytest

from app.domain.nutrition_methodology import (
    NutrientKind as Kind,
    ObservationMethod as Method,
    ObservationState as State,
    ObservationSource,
    SourceObservation,
    ObservationContribution,
    RussianNutritionPolicy as Policy,
    aggregate_observations,
    evaluate_observation,
)


def observation(**changes):
    source = ObservationSource(
        "synthetic", "v1", "table 1 row 1", "obs-1", "raw-form", "method section 1"
    )
    return replace(
        SourceObservation(
            Kind.AVAILABLE_CARBOHYDRATE,
            Method.AVAILABLE_PUBLISHED_ROW_UNSPECIFIED,
            State.VALUE,
            Decimal("12"),
            "g",
            Decimal("100"),
            source,
        ),
        **changes,
    )


def contribution(obs, mass="100"):
    return ObservationContribution(obs, Decimal(mass), obs.source.food_form_id)


@pytest.mark.parametrize(
    "method,warning",
    [
        (Method.AVAILABLE_SUMMATION, None),
        (Method.AVAILABLE_BY_DIFFERENCE, "AVAILABLE_BY_DIFFERENCE"),
        (Method.AVAILABLE_PUBLISHED_ROW_UNSPECIFIED, "ROW_METHOD_UNSPECIFIED"),
    ],
)
def test_available_methods_preserve_definition_and_method(method, warning):
    original = observation(method=method)
    result = evaluate_observation(original)
    assert result.amount == Decimal("12")
    assert result.observation is original
    assert not result.estimated
    if warning:
        assert warning in result.warnings


def test_total_is_not_automatically_available():
    result = evaluate_observation(observation(method=Method.TOTAL_BY_DIFFERENCE))
    assert result.amount is None
    assert "UNSUPPORTED_METHOD" in result.warnings
    total = observation(
        nutrient=Kind.TOTAL_CARBOHYDRATE, method=Method.TOTAL_BY_DIFFERENCE
    )
    assert evaluate_observation(total).amount == Decimal("12")
    with pytest.raises(ValueError):
        aggregate_observations((contribution(total), contribution(observation())))


@pytest.mark.parametrize("kind", [Kind.PROTEIN, Kind.FAT, Kind.FIBRE])
def test_independent_macro_components(kind):
    assert evaluate_observation(
        observation(nutrient=kind, method=Method.ANALYTICAL)
    ).amount == Decimal("12")


def test_missing_contribution_does_not_become_partial_total():
    absent = observation(state=State.MISSING, amount=None)
    result = aggregate_observations((contribution(observation()), contribution(absent)))
    assert result.amount is None
    assert "MISSING_OBSERVATION" in result.warnings
    assert result.interpretations[0].amount == Decimal("12")


def test_below_detection_is_unknown_by_default_even_with_printed_zero():
    original = observation(state=State.BELOW_DETECTION, amount=None, source_literal="0")
    assert evaluate_observation(original).amount is None
    estimate = evaluate_observation(original, Policy.PUBLISHED_ZERO_ESTIMATE_V1)
    assert estimate.amount == 0 and estimate.estimated
    assert estimate.observation.amount is None
    assert estimate.observation.state == State.BELOW_DETECTION
    assert "PUBLISHED_ZERO_ESTIMATE" in estimate.warnings


@pytest.mark.parametrize("literal", [None, "следы", "<0.1", "-", "0.01"])
def test_zero_estimate_requires_source_printed_zero(literal):
    original = observation(
        state=State.BELOW_DETECTION, amount=None, source_literal=literal
    )
    assert (
        evaluate_observation(original, Policy.PUBLISHED_ZERO_ESTIMATE_V1).amount is None
    )


def test_policy_cannot_make_unsupported_method_available():
    original = observation(
        method=Method.UNSUPPORTED,
        state=State.BELOW_DETECTION,
        amount=None,
        source_literal="0",
    )
    assert (
        evaluate_observation(original, Policy.PUBLISHED_ZERO_ESTIMATE_V1).amount is None
    )


def test_actual_numeric_zero_retains_source_state():
    result = evaluate_observation(observation(amount=Decimal("0")))
    assert result.amount == 0 and not result.estimated


def test_aggregate_basis_scaling_isolated_from_caller_decimal_context():
    original = observation(amount=Decimal("1"), basis_g=Decimal("3"))
    rows = tuple(contribution(original, "1") for _ in range(3))
    with localcontext() as ctx:
        ctx.prec, ctx.rounding = 2, ROUND_DOWN
        result = aggregate_observations(rows)
    assert result.amount == Decimal("1.000000")
    assert result.contributions[0].observation.source.locator == "table 1 row 1"
    assert result.policy == Policy.STRICT_V1
    assert (
        result.interpretations[0].observation.method
        == Method.AVAILABLE_PUBLISHED_ROW_UNSPECIFIED
    )


def test_policies_explicitly_change_estimation_without_mutating_source():
    obs = observation(state=State.BELOW_DETECTION, amount=None, source_literal="0")
    rows = (contribution(obs),)
    assert aggregate_observations(rows).amount is None
    estimated = aggregate_observations(rows, Policy.PUBLISHED_ZERO_ESTIMATE_V1)
    assert estimated.amount == 0 and estimated.estimated
    assert estimated.policy != Policy.STRICT_V1
    with pytest.raises(TypeError):
        aggregate_observations(rows, "RU_CUSTOM")


def test_published_energy_is_independent_from_computed():
    published = observation(
        nutrient=Kind.PUBLISHED_ENERGY, unit="kcal", method=Method.PUBLISHED
    )
    computed = observation(
        nutrient=Kind.COMPUTED_ENERGY, unit="kcal", method=Method.COMPUTED
    )
    assert evaluate_observation(published).amount == Decimal("12")
    with pytest.raises(ValueError):
        aggregate_observations((contribution(published), contribution(computed)))
    assert (
        evaluate_observation(replace(published, method=Method.COMPUTED)).amount is None
    )


@pytest.mark.parametrize("value", [1.0, 1, "1", True])
def test_non_decimal_numeric_inputs_rejected(value):
    with pytest.raises(TypeError):
        observation(amount=value)
    with pytest.raises(TypeError):
        observation(basis_g=value)
    with pytest.raises(TypeError):
        ObservationContribution(observation(), value, "raw-form")


@pytest.mark.parametrize(
    "value", [Decimal("NaN"), Decimal("Infinity"), Decimal("-1"), Decimal("1e25")]
)
def test_invalid_numeric_values_rejected(value):
    with pytest.raises(ValueError):
        observation(amount=value)


@pytest.mark.parametrize(
    "changes",
    [
        {"basis_g": Decimal("0")},
        {"unit": "mg"},
        {"basis_part": "gross"},
        {"state": State.MISSING},
        {"amount": None},
    ],
)
def test_ambiguous_observation_rejected(changes):
    with pytest.raises(ValueError):
        observation(**changes)


def test_source_and_form_provenance_mandatory():
    with pytest.raises(ValueError):
        replace(observation().source, locator=" ")
    with pytest.raises(ValueError):
        ObservationContribution(observation(), Decimal("100"), "cooked-form")
    with pytest.raises(ValueError):
        aggregate_observations(())


@pytest.mark.parametrize(
    "estimated,warning",
    [
        (True, "SOURCE_ESTIMATED"),
        (None, "SOURCE_ESTIMATION_STATUS_UNKNOWN"),
        (False, None),
    ],
)
def test_source_estimation_preserved(estimated, warning):
    original = observation(source_estimated=estimated)
    result = evaluate_observation(original)
    assert result.estimated is (estimated is True)
    assert result.observation.source_estimated is estimated
    if warning:
        assert warning in result.warnings
    else:
        assert "SOURCE_ESTIMATED" not in result.warnings
        assert "SOURCE_ESTIMATION_STATUS_UNKNOWN" not in result.warnings
    total = aggregate_observations((contribution(original),))
    assert total.estimated is (estimated is True)
    if warning:
        assert warning in total.warnings


@pytest.mark.parametrize("estimated", [0, 1, "true", Decimal("1")])
def test_estimation_flag_is_strict_boolean_or_unknown(estimated):
    with pytest.raises(TypeError):
        observation(source_estimated=estimated)


@pytest.mark.parametrize("policy", list(Policy))
def test_held_source_zero_is_not_missing_or_eligible_for_zero_estimate(policy):
    held = observation(state=State.HELD, amount=None, source_literal="0")
    interpreted = evaluate_observation(held, policy)
    assert interpreted.amount is None
    assert "HELD_SOURCE_OBSERVATION" in interpreted.warnings
    assert "MISSING_OBSERVATION" not in interpreted.warnings
    assert "PUBLISHED_ZERO_ESTIMATE" not in interpreted.warnings
    total = aggregate_observations(
        (contribution(observation()), contribution(held)), policy
    )
    assert total.amount is None
    assert "HELD_SOURCE_OBSERVATION" in total.warnings
    assert total.interpretations[1].observation.state == State.HELD


def test_held_observation_cannot_contain_numeric_placeholder():
    with pytest.raises(ValueError):
        observation(state=State.HELD, amount=Decimal("0"))


def test_held_unsupported_method_retains_both_reasons():
    result = evaluate_observation(
        observation(state=State.HELD, amount=None, method=Method.UNSUPPORTED)
    )
    assert {"HELD_SOURCE_OBSERVATION", "UNSUPPORTED_METHOD"} <= set(result.warnings)
