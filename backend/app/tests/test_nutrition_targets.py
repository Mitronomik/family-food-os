from dataclasses import asdict, replace
from datetime import date, datetime, timedelta
from decimal import Decimal, ROUND_DOWN, localcontext
from uuid import uuid4

import pytest

from app.domain.nutrition import NutritionStatus as Status, NutritionWarningCode as Code
from app.domain.nutrition_targets import calculate_member_reference_target
from app.tests.test_household_domain import member

AS_OF = date(2026, 9, 6)


def person(age=40, sex="male", pal="inactive", height="180", weight="80", **changes):
    values = dict(
        birth_date=date(AS_OF.year - age, 9, 6),
        sex=sex,
        activity_level=pal,
        height_cm=height,
        weight_kg=weight,
    )
    values.update(changes)
    return member(uuid4(), **values)


def calculate(value):
    return calculate_member_reference_target(value, as_of_date=AS_OF)


def codes(result):
    return [warning.code for warning in result.warnings]


# Independently evaluated published NASEM 2023 Tables 5-15/5-16, cm and kg.
# For the first fixture: 753.07 - 10.83*40 + 6.50*180 + 14.10*80 = 2617.87.
@pytest.mark.parametrize(
    "age,sex,height,weight,energies",
    [
        (40, "male", "180", "80", ("2617.87", "2837.47", "3018.02", "3387.52")),
        (40, "female", "165", "60", ("1950.90", "2112.77", "2249.35", "2481.58")),
        (10, "male", "140", "35", ("1895.94", "1997.52", "2162.11", "2357.00")),
        (10, "female", "140", "35", ("1640.74", "1813.31", "1903.45", "2147.46")),
    ],
)
@pytest.mark.parametrize(
    "index,pal", enumerate(("inactive", "low_active", "active", "very_active"))
)
def test_published_equation_fixtures(age, sex, height, weight, energies, index, pal):
    value = person(age, sex, pal, height, weight)
    result = calculate(value)
    assert result.reference_energy_kcal == Decimal(energies[index])
    assert result.equation_table == ("5-15" if age < 19 else "5-16")
    assert result.status == Status.COMPLETE_WITH_WARNINGS
    assert codes(result) == [Code.REFERENCE_ESTIMATE]
    assert calculate(value) == result


@pytest.mark.parametrize(
    "age,male,female",
    [
        (3, 20, 15),
        (4, 15, 15),
        (8, 15, 15),
        (9, 25, 30),
        (13, 25, 30),
        (14, 20, 20),
        (18, 20, 20),
        (19, 0, 0),
    ],
)
@pytest.mark.parametrize("sex", ["male", "female"])
def test_exact_growth_age_bands(age, male, female, sex):
    result = calculate(person(age, sex))
    assert result.age_years == age
    assert result.growth_allowance_kcal == Decimal(male if sex == "male" else female)


@pytest.mark.parametrize("birthday_age", [3, 4, 9, 14, 19])
def test_changes_only_at_birthday(birthday_age):
    value = person(birthday_age)
    before = calculate_member_reference_target(
        value, as_of_date=AS_OF - timedelta(days=1)
    )
    after = calculate(value)
    assert before.age_years == birthday_age - 1
    assert after.age_years == birthday_age
    if birthday_age == 3:
        assert before.reference_energy_kcal is None
        assert after.reference_energy_kcal is not None
    if birthday_age == 19:
        assert before.equation_table == "5-15"
        assert after.equation_table == "5-16"


def test_leap_day_age_policy_waits_until_march_1_in_nonleap_year():
    value = person(birth_date=date(2008, 2, 29))
    assert (
        calculate_member_reference_target(value, as_of_date=date(2027, 2, 28)).age_years
        == 18
    )
    assert (
        calculate_member_reference_target(value, as_of_date=date(2027, 3, 1)).age_years
        == 19
    )


@pytest.mark.parametrize(
    "change,reason",
    [
        ({"birth_date": None}, Code.MISSING_BIRTH_DATE),
        ({"birth_date": AS_OF + timedelta(days=1)}, Code.FUTURE_BIRTH_DATE),
        ({"birth_date": date(2024, 9, 6)}, Code.UNSUPPORTED_AGE),
        ({"height_cm": None}, Code.INVALID_HEIGHT),
        ({"weight_kg": None}, Code.INVALID_WEIGHT),
        ({"sex": None}, Code.UNSUPPORTED_SEX),
        ({"sex": "other"}, Code.UNSUPPORTED_SEX),
        ({"sex": "Male"}, Code.UNSUPPORTED_SEX),
        ({"activity_level": "moderate"}, Code.UNSUPPORTED_ACTIVITY),
        ({"activity_level": "sedentary"}, Code.UNSUPPORTED_ACTIVITY),
    ],
)
def test_unavailable_inputs_fail_closed(change, reason):
    result = calculate(person(**change))
    assert result.status == Status.INCOMPLETE
    assert result.reference_energy_kcal is None
    assert result.carbohydrate is result.protein is result.fat is None
    assert reason in codes(result)
    if reason in (
        Code.MISSING_BIRTH_DATE,
        Code.FUTURE_BIRTH_DATE,
        Code.UNSUPPORTED_AGE,
        Code.UNSUPPORTED_SEX,
    ):
        assert result.fiber_ai_g is None
    else:
        assert result.fiber_ai_g == Decimal(38)


@pytest.mark.parametrize("goal", ["lose_weight", "gain_weight", "future_goal"])
def test_goal_never_changes_reference_energy(goal):
    value = person()
    baseline = calculate(value)
    changed = calculate(replace(value, goal=goal))
    assert changed.reference_energy_kcal == baseline.reference_energy_kcal
    assert changed.carbohydrate == baseline.carbohydrate
    assert changed.inputs.goal == goal
    assert Code.GOAL_ADJUSTMENT_NOT_APPLIED in codes(changed)
    assert Code.GOAL_ADJUSTMENT_NOT_APPLIED not in codes(baseline)


@pytest.mark.parametrize(
    "age,protein,fat",
    [
        (3, (".05", ".20"), (".30", ".40")),
        (4, (".10", ".30"), (".25", ".35")),
        (18, (".10", ".30"), (".25", ".35")),
        (19, (".10", ".35"), (".20", ".35")),
    ],
)
def test_amdr_and_exact_atwater_conversion(age, protein, fat):
    result = calculate(person(age))
    for actual, expected, factor in zip(
        (result.carbohydrate, result.protein, result.fat),
        ((".45", ".65"), protein, fat),
        (4, 4, 9),
        strict=True,
    ):
        low, high = map(Decimal, expected)
        assert (actual.min_energy_fraction, actual.max_energy_fraction) == (low, high)
        assert actual.kcal_per_g == Decimal(factor)
        assert actual.min_g == (
            result.reference_energy_kcal * low / Decimal(factor)
        ).quantize(Decimal(".000001"))
        assert actual.max_g == (
            result.reference_energy_kcal * high / Decimal(factor)
        ).quantize(Decimal(".000001"))


@pytest.mark.parametrize(
    "age,male,female",
    [
        (3, 19, 19),
        (4, 25, 25),
        (8, 25, 25),
        (9, 31, 26),
        (13, 31, 26),
        (14, 38, 26),
        (18, 38, 26),
        (19, 38, 25),
        (30, 38, 25),
        (31, 38, 25),
        (50, 38, 25),
        (51, 30, 21),
        (70, 30, 21),
        (71, 30, 21),
    ],
)
@pytest.mark.parametrize("sex", ["male", "female"])
def test_fiber_ai_exact_table_bands(age, male, female, sex):
    assert calculate(person(age, sex)).fiber_ai_g == Decimal(
        male if sex == "male" else female
    )


def test_fiber_child_band_does_not_need_sex_but_adolescent_band_does():
    assert calculate(person(8, sex=None)).fiber_ai_g == Decimal(25)
    assert calculate(person(9, sex=None)).fiber_ai_g is None


def test_nonpositive_eer_is_not_a_reference_target():
    result = calculate(person(100, height="1", weight="1"))
    assert result.reference_energy_kcal is None
    assert Code.INVALID_REFERENCE_ENERGY in codes(result)


def test_explicit_date_versions_input_provenance_and_context_independence():
    value = person()
    original = asdict(value)
    baseline = calculate(value)
    assert asdict(baseline.config) == {
        "version": "FAMILY_FOOD_NUTRITION_V1",
        "eer_version": "NASEM_EER_2023_V1",
        "amdr_version": "DRI_AMDR_2002_2005_V1",
        "fiber_version": "DRI_TOTAL_FIBER_AI_2002_2005_V1",
        "atwater_version": "ATWATER_GENERAL_4_4_9_V1",
        "age_policy_version": "COMPLETED_CHRONOLOGICAL_YEARS_V1",
        "rounding_version": "DECIMAL_80_HALF_UP_6DP_V1",
    }
    assert len(baseline.sources) == 4
    assert baseline.inputs.member_updated_at == value.updated_at
    assert baseline.inputs.member_id == value.id
    with localcontext() as caller:
        caller.prec = 2
        caller.rounding = ROUND_DOWN
        assert calculate(value) == baseline
    assert asdict(value) == original
    for invalid in (None, "2026-09-06", datetime(2026, 9, 6)):
        with pytest.raises(TypeError, match="explicit date"):
            calculate_member_reference_target(value, as_of_date=invalid)


@pytest.mark.parametrize(
    "family_name,child_ages",
    [
        ("family_2_adults", ()),
        ("family_2_adults_1_child", (10,)),
        ("family_2_adults_2_children", (10, 7)),
    ],
)
def test_canonical_family_fixtures_produce_independent_member_references(
    family_name, child_ages
):
    household_id = uuid4()
    people = [person(40, "male"), person(35, "female", height="165", weight="60")]
    people.extend(
        person(age, "female", height="130", weight="30") for age in child_ages
    )
    people = tuple(replace(value, household_id=household_id) for value in people)
    targets = tuple(calculate(value) for value in people)
    assert len(targets) == 2 + len(child_ages), family_name
    assert {target.inputs.household_id for target in targets} == {household_id}
    assert len({target.inputs.member_id for target in targets}) == len(people)
    assert all(target.reference_energy_kcal is not None for target in targets)
    assert [target.equation_table for target in targets] == ["5-16", "5-16"] + [
        "5-15"
    ] * len(child_ages)
