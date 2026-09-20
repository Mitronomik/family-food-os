"""Synthetic selector fixtures, not published dietary reference values."""

from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest

from app.domain.russian_reference_targets import (
    ReviewedRussianReferenceTable,
    RussianReferenceRow,
    ReferenceSelectionStatus,
    select_russian_reference_targets,
)


def row(**changes):
    values = dict(
        id="test:energy",
        source_id="TEST_ONLY",
        source_version="1",
        locator="synthetic row",
        review_reference="test-review",
        definition_code="ENERGY",
        unit="kcal/day",
        value=Decimal("1000"),
        sex="male",
        age_min_years=18,
        age_max_years_exclusive=30,
        physical_activity_coefficient=Decimal("1.4"),
        life_stage="adult",
    )
    values.update(changes)
    return RussianReferenceRow(**values)


def table(*rows):
    return ReviewedRussianReferenceTable("TEST_RU_V1", "test-review", rows or (row(),))


def select(reference=None, **changes):
    inputs = dict(
        age_years=25,
        sex="male",
        physical_activity_coefficient=Decimal("1.4"),
        life_stage="adult",
        definition_codes=("ENERGY",),
    )
    inputs.update(changes)
    return select_russian_reference_targets(reference or table(), **inputs)


def test_exact_selection_preserves_source_and_group_basis():
    result = select()
    assert result.status == ReferenceSelectionStatus.COMPLETE
    assert result.rows == (row(),)
    assert result.methodology_version == "TEST_RU_V1"
    assert result.basis == "group_reference_daily"
    assert not result.individualized
    with pytest.raises(FrozenInstanceError):
        result.rows[0].value = Decimal("2")


@pytest.mark.parametrize(
    "changes",
    [
        dict(age_years=17),
        dict(age_years=30),
        dict(age_years=None),
        dict(age_years=True),
        dict(sex="female"),
        dict(physical_activity_coefficient=Decimal("1.6")),
        dict(physical_activity_coefficient=None),
        dict(life_stage="pregnancy"),
    ],
)
def test_unsupported_applicability_never_falls_back(changes):
    assert select(**changes).status == ReferenceSelectionStatus.UNSUPPORTED


def test_age_gap_and_boundary():
    reference = table(
        row(age_max_years_exclusive=29),
        row(id="test:older", age_min_years=30, age_max_years_exclusive=45),
    )
    assert (
        select(reference, age_years=29).status == ReferenceSelectionStatus.UNSUPPORTED
    )
    assert select(reference, age_years=30).rows[0].id == "test:older"


def test_no_us_activity_mapping():
    with pytest.raises(ValueError):
        select(physical_activity_coefficient="inactive")


def test_activity_independent_row_and_sparse_result():
    reference = table(
        row(
            id="fibre",
            definition_code="FIBRE",
            unit="g/day",
            physical_activity_coefficient=None,
        )
    )
    result = select(
        reference,
        physical_activity_coefficient=None,
        definition_codes=("FIBRE", "ENERGY"),
    )
    assert result.status == ReferenceSelectionStatus.INCOMPLETE
    assert result.missing_definitions == ("ENERGY",)


@pytest.mark.parametrize(
    "changes",
    [dict(sex="all"), dict(physical_activity_coefficient=None), dict(unit="g/day")],
)
def test_overlapping_rows_are_not_silently_prioritized(changes):
    with pytest.raises(ValueError, match="Перекрывающиеся"):
        table(row(), row(id="test:overlap", **changes))


@pytest.mark.parametrize(
    "changes",
    [
        dict(value=Decimal("NaN")),
        dict(value=1.0),
        dict(review_reference=""),
        dict(age_min_years=True),
        dict(basis="per_100g"),
        dict(applicability="clinical"),
        dict(life_stage="lactation"),
        dict(unit="percent_energy", value=Decimal("101")),
    ],
)
def test_invalid_or_unreviewed_rows_rejected(changes):
    with pytest.raises(ValueError):
        row(**changes)


def test_no_implicit_equivalence_between_nutrient_definitions():
    reference = table(row(definition_code="VITAMIN_A_RE", unit="µg/day"))
    result = select(reference, definition_codes=("VITAMIN_A_RAE",))
    assert result.status == ReferenceSelectionStatus.UNSUPPORTED
    assert result.rows == ()


def test_table_copies_input_collection():
    rows = [row()]
    reference = ReviewedRussianReferenceTable("TEST_V1", "review", rows)
    rows.clear()
    assert len(reference.rows) == 1
