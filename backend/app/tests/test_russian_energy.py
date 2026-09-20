from decimal import Decimal, localcontext
import pytest
from app.domain.russian_energy import (
    EnergyComponent as C,
    EnergyTerm,
    GENERIC_PARTITION,
    calculate_russian_energy,
)


def term(k, value):
    return EnergyTerm(
        k,
        None if value is None else Decimal(value),
        "synthetic:" + k,
        "test-method",
        Decimal(100),
        "raw",
    )


def test_fibre_and_published_energy_are_separate():
    terms = tuple(
        term(
            k,
            {
                C.PROTEIN: "10",
                C.FAT: "5",
                C.AVAILABLE_CARBOHYDRATE: "20",
                C.FIBRE: "3",
            }.get(k, "0"),
        )
        for k in sorted(GENERIC_PARTITION)
    )
    result = calculate_russian_energy(
        terms,
        basis_g=Decimal(100),
        food_form_id="raw",
        published_kcal=Decimal(170),
        published_observation_id="published-test",
        disjoint_partition_review="test-reviewed-partition",
    )
    assert result.computed_kcal == Decimal(171)
    assert result.published_kcal == Decimal(170)
    assert result.difference_from_published_kcal == Decimal(1)


def test_unknown_is_not_zero_and_subtotal_is_not_full_energy():
    result = calculate_russian_energy(
        (term(C.PROTEIN, "10"), term(C.FAT, None)),
        basis_g=Decimal(100),
        food_form_id="raw",
    )
    assert result.computed_kcal is None
    assert result.known_components_subtotal_kcal == Decimal(40)
    assert C.FAT in result.missing_components


def test_no_double_carbohydrates():
    with pytest.raises(ValueError, match="дважды"):
        calculate_russian_energy(
            (term(C.AVAILABLE_CARBOHYDRATE, "10"), term(C.EXPERIMENTAL_SUGARS, "5")),
            basis_g=Decimal(100),
            food_form_id="raw",
        )


def test_experimental_factors_not_generic_and_not_complete():
    result = calculate_russian_energy(
        (term(C.EXPERIMENTAL_SUGARS, "10"), term(C.EXPERIMENTAL_STARCH, "10")),
        basis_g=Decimal(100),
        food_form_id="raw",
    )
    assert result.known_components_subtotal_kcal == Decimal(79)
    assert result.computed_kcal is None


def test_duplicate_terms_rejected():
    with pytest.raises(ValueError, match="Повтор"):
        calculate_russian_energy(
            (term(C.FAT, "1"), term(C.FAT, "1")),
            basis_g=Decimal(100),
            food_form_id="raw",
        )


def test_total_carbohydrate_cannot_be_mislabeled_by_code():
    with pytest.raises(TypeError):
        EnergyTerm("total_carbohydrate", Decimal(10), "s", "m", Decimal(100), "raw")


@pytest.mark.parametrize(
    "value", [float("nan"), Decimal("NaN"), Decimal("-1"), Decimal("Infinity")]
)
def test_bad_amount(value):
    with pytest.raises((ValueError, TypeError)):
        EnergyTerm(C.FAT, value, "s", "m", Decimal(100), "raw")


def test_decimal_context_independence():
    with localcontext() as ctx:
        ctx.prec = 3
        r = calculate_russian_energy(
            (term(C.FAT, "123.456789"),), basis_g=Decimal(100), food_form_id="raw"
        )
    assert r.known_components_subtotal_kcal == Decimal("1111.111101")


def test_unreviewed_partition_not_full_energy():
    terms = tuple(term(k, "0") for k in sorted(GENERIC_PARTITION))
    result = calculate_russian_energy(terms, basis_g=Decimal(100), food_form_id="raw")
    assert result.computed_kcal is None
    assert not result.missing_components


def test_mixed_basis_rejected():
    with pytest.raises(ValueError, match="База"):
        calculate_russian_energy(
            (term(C.FAT, "1"),), basis_g=Decimal(200), food_form_id="raw"
        )
