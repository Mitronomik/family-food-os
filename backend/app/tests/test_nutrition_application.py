from contextlib import contextmanager
from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.domain.nutrition import NutritionStatus
from app.services.nutrition import NutritionInputNotFoundError, NutritionService
from app.tests.test_household_domain import member
from app.tests.test_nutrition_domain import fixture_recipe


class Reader:
    def __init__(self, value, events, name):
        self.value, self.events, self.name = value, events, name

    def get(self, *args):
        self.events.append((self.name, args))
        return self.value

    get_current = get
    get_detail = get
    get_member = get


def setup_service(*, missing=None):
    detail, food, profile = fixture_recipe()
    person = member(uuid4(), activity_level="active")
    events = []
    scope = SimpleNamespace(
        **{
            name: Reader(None if missing == name else value, events, name)
            for name, value in (
                ("versions", detail),
                ("ingredients", food),
                ("nutrition_profiles", profile),
                ("members", person),
            )
        }
    )

    @contextmanager
    def read():
        events.append("enter")
        try:
            yield scope
        finally:
            events.append("exit")

    return NutritionService(read), detail, food, person, events


def test_recipe_uses_one_scope_and_resolves_repeated_food_only_once(monkeypatch):
    monkeypatch.setenv("AI_ENABLED", "false")
    service, detail, food, _, events = setup_service()
    result = service.recipe_version(detail.version.id)
    assert result.required_total.kcal == Decimal(400)
    assert events == [
        "enter",
        ("versions", (detail.version.id,)),
        ("ingredients", (food.id,)),
        ("nutrition_profiles", (food.id,)),
        "exit",
    ]


def test_ingredient_and_household_scoped_member_reads():
    service, _, food, person, events = setup_service()
    result = service.food_ingredient(food.id, Decimal(50))
    assert result.values.kcal == Decimal(100)
    target = service.member_reference_target(
        person.household_id, person.id, as_of_date=date(2026, 9, 6)
    )
    assert target.inputs.household_id == person.household_id
    assert ("members", (person.household_id, person.id)) in events
    assert events.count("enter") == events.count("exit") == 2


@pytest.mark.parametrize("missing", ["ingredients", "nutrition_profiles"])
def test_missing_recipe_child_is_incomplete_not_root_not_found(missing):
    service, detail, _, _, events = setup_service(missing=missing)
    assert (
        service.recipe_version(detail.version.id).status == NutritionStatus.INCOMPLETE
    )
    assert events[-1] == "exit"


@pytest.mark.parametrize("missing", ["versions", "ingredients", "members"])
def test_missing_root_exits_scope(missing):
    service, detail, food, person, events = setup_service(missing=missing)
    with pytest.raises(NutritionInputNotFoundError):
        if missing == "versions":
            service.recipe_version(detail.version.id)
        elif missing == "ingredients":
            service.food_ingredient(food.id, Decimal(50))
        else:
            service.member_reference_target(
                person.household_id, person.id, as_of_date=date(2026, 9, 6)
            )
    assert events[-1] == "exit"


def test_calculation_failure_exits_scope():
    service, _, food, _, events = setup_service()
    with pytest.raises(TypeError):
        service.food_ingredient(food.id, 1.5)
    assert events[-1] == "exit"
