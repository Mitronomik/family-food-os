from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest

from app.domain.errors import DomainIssueCode, DomainValidationError
from app.domain.food_ingredients import (
    FoodIngredient,
    FoodNutritionProfile,
    IngredientAlias,
    NutritionObservationState,
    NutritionSourceObservation,
    normalize_unicode_search_key,
)
from app.domain.units import UnitCode

NOW = datetime(2026, 9, 2, tzinfo=timezone.utc)


def ingredient(**overrides):
    values = {
        "id": uuid4(),
        "canonical_code": "BUCKWHEAT",
        "canonical_name": " Гречневая   крупа ",
        "canonical_name_key": "гречневая крупа",
        "category_code": "grains",
        "default_unit": UnitCode.GRAM,
        "density_g_per_ml": None,
        "edible_fraction": None,
        "allergens_reviewed": False,
        "allergen_codes": (),
        "storage_profile_code": None,
        "is_active": True,
        "created_at": NOW,
        "updated_at": NOW,
    }
    values.update(overrides)
    return FoodIngredient(**values)


def profile(**overrides):
    values = {
        "id": uuid4(),
        "food_ingredient_id": uuid4(),
        "basis_grams": "100",
        "kcal": "331.6005206",
        "protein_g": "11.06534",
        "fat_g": "3.039",
        "carbohydrates_g": "71.13066",
        "fiber_g": "4.046",
        "source_name": "USDA_FDC",
        "source_id": "2512378",
        "source_version": "2026-04-30",
        "source_data_type": "Foundation",
        "verified_at": NOW,
        "estimated": None,
        "is_current": True,
        "created_at": NOW,
    }
    values.update(overrides)
    return FoodNutritionProfile(**values)


def test_unicode_search_key_is_nfkc_whitespace_casefold_and_yo_safe():
    assert normalize_unicode_search_key("  СВЁКЛА\u00a0 свежая  ") == "свекла свежая"
    assert normalize_unicode_search_key("ГРЕЧНЕВАЯ   КРУПА") == "гречневая крупа"


def test_food_ingredient_normalizes_text_and_exact_decimal_metadata():
    value = ingredient(density_g_per_ml="1.03214", edible_fraction="0.8123456")

    assert value.canonical_name == "Гречневая крупа"
    assert value.canonical_name_key == "гречневая крупа"
    assert value.density_g_per_ml == Decimal("1.0321")
    assert value.edible_fraction == Decimal("0.812346")


@pytest.mark.parametrize("code", ["", "buckwheat", "1_BUCKWHEAT", "BUCK-WHEAT"])
def test_invalid_canonical_code_is_a_stable_domain_error(code):
    with pytest.raises(DomainValidationError) as exc_info:
        ingredient(canonical_code=code)
    assert exc_info.value.issue.code in {
        DomainIssueCode.REQUIRED_FIELD,
        DomainIssueCode.INVALID_CODE,
    }
    assert exc_info.value.issue.field == "canonical_code"


@pytest.mark.parametrize("name", ["", "   ", None])
def test_blank_canonical_name_is_rejected(name):
    with pytest.raises(DomainValidationError) as exc_info:
        ingredient(canonical_name=name, canonical_name_key="unused")
    assert exc_info.value.issue.code == DomainIssueCode.REQUIRED_FIELD
    assert exc_info.value.issue.field == "canonical_name"


def test_name_key_must_be_the_deterministic_python_key():
    with pytest.raises(DomainValidationError) as exc_info:
        ingredient(canonical_name_key="different")
    assert exc_info.value.issue.code == DomainIssueCode.INVALID_CODE


@pytest.mark.parametrize("unit", [UnitCode.PERCENT, "percent", "kg", None])
def test_food_default_unit_rejects_percent_and_unknown_units(unit):
    with pytest.raises(DomainValidationError) as exc_info:
        ingredient(default_unit=unit)
    assert exc_info.value.issue.code == DomainIssueCode.INVALID_UNIT
    assert exc_info.value.issue.field == "default_unit"


@pytest.mark.parametrize(
    "value", ["0", "-0.1", "0.00001", "NaN", "Infinity", "1E+999999", 1.0]
)
def test_density_validation_is_total(value):
    with pytest.raises(DomainValidationError) as exc_info:
        ingredient(density_g_per_ml=value)
    assert exc_info.value.issue.code in {
        DomainIssueCode.ZERO_OR_NEGATIVE_DENSITY,
        DomainIssueCode.INVALID_DECIMAL,
        DomainIssueCode.FLOAT_NOT_ALLOWED,
    }


@pytest.mark.parametrize(
    "value",
    ["0", "-0.1", "0.0000001", "1.000001", "Infinity", "1E+999999", 0.8],
)
def test_edible_fraction_validation_is_total(value):
    with pytest.raises(DomainValidationError):
        ingredient(edible_fraction=value)


def test_allergen_unknown_reviewed_empty_and_reviewed_codes_are_distinct():
    unknown = ingredient(allergens_reviewed=False, allergen_codes=())
    reviewed_empty = ingredient(allergens_reviewed=True, allergen_codes=())
    reviewed_codes = ingredient(
        allergens_reviewed=True, allergen_codes=("MILK", "EGG", "MILK")
    )

    assert unknown.allergens_reviewed is False
    assert reviewed_empty.allergens_reviewed is True
    assert reviewed_empty.allergen_codes == ()
    assert reviewed_codes.allergen_codes == ("EGG", "MILK")

    with pytest.raises(DomainValidationError):
        ingredient(allergens_reviewed=False, allergen_codes=("MILK",))


def test_alias_key_uses_same_unicode_normalization():
    value = IngredientAlias(
        id=uuid4(),
        food_ingredient_id=uuid4(),
        alias="  ГРЕЧКА ",
        alias_key="гречка",
        language_code="ru",
        created_at=NOW,
    )
    assert value.alias == "ГРЕЧКА"
    assert value.alias_key == "гречка"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("kcal", "-0.000001"),
        ("kcal", "1000.000001"),
        ("protein_g", "100.000001"),
        ("fat_g", "Infinity"),
        ("carbohydrates_g", "NaN"),
        ("fiber_g", "-1"),
        ("kcal", "1E+999999"),
        ("protein_g", 12.5),
    ],
)
def test_nutrition_numeric_validation_is_total_and_bounded(field, value):
    with pytest.raises(DomainValidationError) as exc_info:
        profile(**{field: value})
    assert exc_info.value.issue.field == field


def test_nutrition_uses_exact_decimal_basis_and_provenance():
    value = profile()

    assert value.basis_grams == Decimal("100.000")
    assert value.kcal == Decimal("331.600521")
    assert value.provenance_key[1:] == (
        "USDA_FDC",
        "2512378",
        "2026-04-30",
    )

    with pytest.raises(DomainValidationError):
        profile(basis_grams="1")


def source_observation(
    profile_id,
    source_field,
    state,
    *,
    source_literal=None,
    method_reference=None,
):
    return NutritionSourceObservation(
        id=uuid4(),
        profile_id=profile_id,
        source_field=source_field,
        state=state,
        source_literal=source_literal,
        method_reference=method_reference,
        source_locator="book2002:p163:row1",
        created_at=NOW,
    )


def test_partial_profile_requires_explicit_unknown_state_for_legacy_core_fields():
    with pytest.raises(DomainValidationError) as exc_info:
        profile(carbohydrates_g=None)

    assert exc_info.value.issue.field == "carbohydrates_g"
    assert exc_info.value.issue.code == DomainIssueCode.REQUIRED_FIELD


def test_partial_profile_preserves_below_detection_and_method_incompatible_source_truth():
    profile_id = uuid4()
    value = profile(
        id=profile_id,
        protein_g=None,
        fat_g=None,
        carbohydrates_g=None,
        observations=(
            source_observation(
                profile_id,
                "protein_g",
                NutritionObservationState.BELOW_DETECTION,
                source_literal="0",
            ),
            source_observation(
                profile_id,
                "fat_g",
                NutritionObservationState.BELOW_DETECTION,
                source_literal="0",
            ),
            source_observation(
                profile_id,
                "carbohydrates_g",
                NutritionObservationState.METHOD_INCOMPATIBLE,
                source_literal="99.8",
                method_reference="BOOK2002_AVAILABLE_CARBOHYDRATE",
            ),
        ),
    )

    assert value.protein_g is None
    assert value.fat_g is None
    assert value.carbohydrates_g is None
    assert value.legacy_core_complete is False
    assert [item.source_field for item in value.observations] == [
        "carbohydrates_g",
        "fat_g",
        "protein_g",
    ]
    assert value.observations[0].source_literal == "99.8"


def test_complete_legacy_profile_remains_complete_and_compatible():
    value = profile()

    assert value.legacy_core_complete is True
    assert value.observations == ()


def test_numeric_profile_value_cannot_conflict_with_unknown_observation_state():
    profile_id = uuid4()
    with pytest.raises(DomainValidationError) as exc_info:
        profile(
            id=profile_id,
            protein_g="11",
            observations=(
                source_observation(
                    profile_id,
                    "protein_g",
                    NutritionObservationState.BELOW_DETECTION,
                    source_literal="0",
                ),
            ),
        )

    assert exc_info.value.issue.field == "protein_g"


def test_source_observation_preserves_literal_and_requires_method_when_incompatible():
    profile_id = uuid4()
    observation = source_observation(
        profile_id,
        "protein_g",
        NutritionObservationState.BELOW_DETECTION,
        source_literal="0,0",
    )
    assert observation.source_literal == "0,0"

    with pytest.raises(DomainValidationError) as exc_info:
        source_observation(
            profile_id,
            "carbohydrates_g",
            NutritionObservationState.METHOD_INCOMPATIBLE,
            source_literal="71.2",
        )
    assert exc_info.value.issue.field == "method_reference"


def test_partial_profile_cannot_be_current_in_legacy_selector():
    profile_id = uuid4()
    with pytest.raises(DomainValidationError) as exc_info:
        profile(
            id=profile_id,
            protein_g=None,
            is_current=True,
            observations=(
                source_observation(
                    profile_id,
                    "protein_g",
                    NutritionObservationState.BELOW_DETECTION,
                    source_literal="0",
                ),
            ),
        )

    assert exc_info.value.issue.field == "is_current"
