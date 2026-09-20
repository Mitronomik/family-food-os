from decimal import Decimal
from dataclasses import replace
from app.domain.reference_comparison import DailyNutrientAmount, compare_daily_reference
from app.domain.russian_reference_targets import RussianReferenceRow


def row(code="VITAMIN_A_RE", unit="µg/day"):
    return RussianReferenceRow(
        "test",
        "synthetic",
        "1",
        "table",
        "review",
        code,
        unit,
        Decimal(1000),
        "all",
        18,
        65,
        None,
        "adult",
    )


def amount(code="VITAMIN_A_RE", unit="mg/day", value=Decimal(1)):
    return DailyNutrientAmount(code, unit, value, "synthetic-v1", ("test-source",))


def test_unit_conversion_with_same_definition():
    r = compare_daily_reference(amount(), row())
    assert r.percent_of_group_reference == Decimal(100)
    assert not r.individualized


def test_rae_cannot_satisfy_re_even_same_unit():
    r = compare_daily_reference(amount("VITAMIN_A_RAE", "µg/day"), row())
    assert r.status == "INCOMPATIBLE_DEFINITION"
    assert r.percent_of_group_reference is None


def test_niacin_cannot_satisfy_ne():
    assert (
        compare_daily_reference(
            amount("NIACIN"), row("NIACIN_EQUIVALENT", "mg/day")
        ).status
        == "INCOMPATIBLE_DEFINITION"
    )


def test_unknown_does_not_report_zero_percent():
    assert (
        compare_daily_reference(amount(value=None), row()).percent_of_group_reference
        is None
    )


def test_percent_energy_cannot_be_compared_to_grams():
    assert (
        compare_daily_reference(
            amount("PROTEIN", "g/day"),
            replace(row("PROTEIN"), unit="percent_energy", value=Decimal(15)),
        ).status
        == "INCOMPATIBLE_UNIT"
    )
