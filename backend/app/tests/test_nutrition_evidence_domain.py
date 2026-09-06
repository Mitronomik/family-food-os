from dataclasses import FrozenInstanceError, asdict, replace
from decimal import Decimal, localcontext
from uuid import uuid4

import pytest

from app.domain.nutrition import (
    calculate_recipe_nutrition,
    NutritionStatus,
    NutritionWarningCode as W,
)
from app.domain.nutrition_config import calculation_context
from app.domain.nutrition_evidence import RecipeIngredientNutritionAssessment
from app.tests.nutrition_evidence_fixtures import assessment, measure
from app.tests.test_nutrition_domain import fixture_recipe


def calculate(detail, food, profile, review=None, evidence=None):
    return calculate_recipe_nutrition(
        detail,
        {food.id: food},
        {food.id: profile},
        {} if review is None else {review.recipe_ingredient_id: review},
        {} if evidence is None else {evidence.id: evidence},
    )


def one_row(unit="ml"):
    detail, food, profile = fixture_recipe(quantity="11", unit=unit)
    return replace(detail, ingredients=(detail.ingredients[0],)), food, profile


@pytest.mark.parametrize(
    "unit,denominator,grams", [("ml", "3", "7"), ("pcs", "1", "50.3")]
)
def test_exact_measure_uses_unrounded_source_fraction(unit, denominator, grams):
    detail, food, profile = one_row(unit)
    evidence = measure(
        detail.ingredients[0], unit=unit, denominator=denominator, grams=grams
    )
    review = assessment(
        detail.ingredients[0], profile, status="APPROVED_EXACT", evidence=evidence
    )
    before = asdict(detail)
    result = calculate(detail, food, profile, review, evidence)
    contribution = result.required_contributions[0]
    with localcontext(calculation_context()):
        expected_mass = Decimal(11) * Decimal(grams) / Decimal(denominator)
        expected_kcal = (expected_mass * profile.kcal / profile.basis_grams).quantize(
            Decimal(".000001")
        )
    assert contribution.nutrition.mass_g == expected_mass
    assert result.required_total.kcal == expected_kcal
    assert (
        contribution.measure_evidence == evidence and contribution.assessment == review
    )
    assert contribution.assessment_profile == profile
    assert result.status == NutritionStatus.COMPLETE
    with localcontext() as ctx:
        ctx.prec = 2
        assert calculate(detail, food, profile, review, evidence) == result
    assert asdict(detail) == before
    with pytest.raises(FrozenInstanceError):
        evidence.gram_weight = Decimal(1)


@pytest.mark.parametrize("unit", ["g", "ml", "pcs"])
def test_missing_new_row_never_uses_density_or_gram_fallback(unit):
    detail, food, profile = one_row(unit)
    food = replace(food, density_g_per_ml=Decimal(99))
    result = calculate(detail, food, profile)
    assert [w.code for w in result.warnings] == [W.MISSING_NUTRITION_ASSESSMENT]
    assert result.required_contributions[0].nutrition.mass_g is None
    assert result.required_total.kcal is None


@pytest.mark.parametrize(
    "status,semantic,issues",
    [
        ("REVIEW_REQUIRED_ESTIMATE", "MATCH", ("CONVERSION_ESTIMATE_NOT_ACCEPTED",)),
        (
            "BLOCKED",
            "AMBIGUOUS",
            ("CONVERSION_ESTIMATE_NOT_ACCEPTED", "PROFILE_REPRESENTATIVENESS_REVIEW"),
        ),
    ],
)
def test_estimated_candidate_never_contributes(status, semantic, issues):
    detail, food, profile = one_row()
    evidence = measure(detail.ingredients[0], estimated=True)
    review = assessment(
        detail.ingredients[0],
        profile,
        status=status,
        semantic=semantic,
        issues=issues,
        evidence=evidence,
    )
    result = calculate(detail, food, profile, review, evidence)
    contribution = result.required_contributions[0]
    assert contribution.measure_evidence == evidence
    assert contribution.nutrition.mass_g is None
    assert all(
        value is None for value in asdict(contribution.nutrition.values).values()
    )
    assert W.CONVERSION_ESTIMATE_NOT_ACCEPTED in [w.code for w in result.warnings]
    assert W.ESTIMATED_SOURCE not in [w.code for w in result.warnings]
    assert contribution.assessment.issues == tuple(sorted(issues))


def test_semantic_and_source_blockers_prevent_gram_contribution():
    detail, food, profile = one_row("g")
    review = assessment(
        detail.ingredients[0],
        profile,
        status="BLOCKED",
        semantic="FORM_MISMATCH",
        issues=("FOOD_FORM_MISMATCH", "SOURCE_QUANTITY_AMBIGUOUS"),
    )
    result = calculate(detail, food, profile, review)
    assert result.required_total.kcal is None
    assert result.required_contributions[0].nutrition.mass_g is None
    assert [w.code for w in result.warnings] == [W.NUTRITION_ASSESSMENT_BLOCKED]


@pytest.mark.parametrize(
    "failure,warning",
    [
        ("missing", W.MISSING_MEASURE_EVIDENCE),
        ("estimated", W.CONVERSION_ESTIMATE_NOT_ACCEPTED),
        ("unit", W.NUTRITION_ASSESSMENT_BLOCKED),
        ("stale", W.NUTRITION_ASSESSMENT_PROFILE_STALE),
        ("gram_approval", W.NUTRITION_ASSESSMENT_BLOCKED),
    ],
)
def test_invalid_binding_fails_closed(failure, warning):
    detail, food, profile = one_row()
    evidence = measure(detail.ingredients[0])
    review = assessment(
        detail.ingredients[0], profile, status="APPROVED_EXACT", evidence=evidence
    )
    if failure == "missing":
        evidence = None
    elif failure == "estimated":
        evidence = replace(evidence, estimated=True)
    elif failure == "unit":
        evidence = replace(evidence, normalized_input_unit="pcs")
    elif failure == "stale":
        profile = replace(profile, id=uuid4())
    elif failure == "gram_approval":
        review = assessment(detail.ingredients[0], profile)
    result = calculate(detail, food, profile, review, evidence)
    assert [w.code for w in result.warnings] == [warning]
    assert result.required_total.kcal is None


@pytest.mark.parametrize(
    "field,value",
    [
        ("normalized_input_quantity", Decimal(0)),
        ("gram_weight", Decimal(-1)),
        ("gram_weight", Decimal("NaN")),
        ("normalized_input_quantity", 1.2),
        ("normalized_input_unit", "g"),
        ("estimated", None),
        ("evidence_key", ""),
        ("gram_weight", Decimal("1e-19")),
    ],
)
def test_invalid_evidence_domain_values(field, value):
    detail, _, _ = one_row()
    with pytest.raises((TypeError, ValueError)):
        replace(measure(detail.ingredients[0]), **{field: value})


@pytest.mark.parametrize(
    "changes",
    [
        dict(status_code="INVALID"),
        dict(assessment_version=0),
        dict(issues=("NO_ACCEPTABLE_SOURCE",)),
        dict(semantic_compatibility_code="FORM_MISMATCH"),
        dict(status_code="APPROVED_EXACT"),
        dict(status_code="BLOCKED"),
    ],
)
def test_invalid_assessment_domain_values(changes):
    detail, _, profile = one_row("g")
    with pytest.raises((TypeError, ValueError)):
        replace(assessment(detail.ingredients[0], profile), **changes)
    assert RecipeIngredientNutritionAssessment.__dataclass_params__.frozen
