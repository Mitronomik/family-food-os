from contextlib import contextmanager
from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4
from dataclasses import replace
import pytest
from app.services.nutrition import NutritionService, NutritionInputNotFoundError
from app.domain.russian_reference_targets import (
    ReviewedRussianReferenceTable,
    RussianReferenceRow,
)
from app.tests.test_household_domain import member


def setup():
    m = replace(member(uuid4()), birth_date=date(2000, 1, 1), sex="male")
    row = RussianReferenceRow(
        "test",
        "synthetic",
        "1",
        "table",
        "review",
        "ENERGY_KCAL",
        "kcal/day",
        Decimal(2000),
        "male",
        18,
        30,
        Decimal("1.4"),
        "adult",
    )
    table = ReviewedRussianReferenceTable("TEST_RU_V1", "test-review", (row,))
    events = []

    def get(hid, mid):
        events.append((hid, mid))
        return m if (hid, mid) == (m.household_id, m.id) else None

    @contextmanager
    def read():
        yield SimpleNamespace(members=SimpleNamespace(get_member=get))

    return NutritionService(read, russian_reference_tables=lambda v: table), m, events


def call(s, m, **kw):
    return s.russian_member_group_reference(
        m.household_id,
        m.id,
        as_of_date=date(2026, 1, 1),
        methodology_version="TEST_RU_V1",
        physical_activity_coefficient=kw.get("kfa", Decimal("1.4")),
        definition_codes=("ENERGY_KCAL",),
    )


def test_explicit_russian_reference_is_not_personalized():
    s, m, events = setup()
    r = call(s, m)
    assert r.rows[0].value == Decimal(2000)
    assert r.individualized is False
    assert events == [(m.household_id, m.id)]


def test_no_activity_fallback():
    s, m, _ = setup()
    r = call(s, m, kfa=None)
    assert r.status == "UNSUPPORTED"


def test_household_isolation():
    s, m, _ = setup()
    with pytest.raises(NutritionInputNotFoundError):
        call(s, replace(m, household_id=uuid4()))


def test_unknown_table_does_not_use_legacy():
    s, m, _ = setup()
    s._russian_reference_tables = None
    with pytest.raises(NutritionInputNotFoundError):
        call(s, m)
