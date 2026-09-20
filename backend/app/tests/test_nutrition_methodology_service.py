from contextlib import contextmanager
from dataclasses import replace
from decimal import Decimal
from types import SimpleNamespace
import pytest
from app.domain.food_composition import CompositionUnavailableError, MassState
from app.domain.nutrition_methodology import (
    NutrientKind as N,
    RussianNutritionPolicy as P,
)
from app.services.nutrition_methodology import NutritionMethodologyService
from app.tests.test_food_composition import atomic
from app.tests import test_food_composition as composition_fixtures

from app.tests.test_nutrient_vector import vector

seeded = composition_fixtures.seeded
database = composition_fixtures.database


def service_fixture(database, v=None):
    v = v or vector(database[1])
    c = atomic(v)

    @contextmanager
    def scope():
        yield SimpleNamespace(
            compositions=SimpleNamespace(get=lambda key: c),
            nutrient_vectors=SimpleNamespace(get=lambda key: v),
        )

    return NutritionMethodologyService(scope), c, v


def request(service, c, **kwargs):
    return service.atomic_input(
        c.id,
        mass_g=Decimal(200),
        mass_state=kwargs.pop("mass_state", MassState.RAW),
        nutrients=kwargs.pop(
            "nutrients", (N.TOTAL_CARBOHYDRATE, N.AVAILABLE_CARBOHYDRATE)
        ),
        policy=P.STRICT_V1,
        **kwargs,
    )


def test_total_not_used_as_available_and_receipt_repeats(database):
    service, c, v = service_fixture(database)
    result = request(service, c)
    assert result.nutrition_profile_id == v.profile.id
    values = {r.nutrient: r for r in result.values}
    assert values[N.AVAILABLE_CARBOHYDRATE].amount is None
    assert result.receipt_sha256 == request(service, c).receipt_sha256


def test_mass_stage_mismatch(database):
    service, c, _ = service_fixture(database)
    with pytest.raises(CompositionUnavailableError):
        request(service, c, mass_state=MassState.COOKED)


def test_unregistered_method_rejected(database):
    service, c, _ = service_fixture(database)
    with pytest.raises(ValueError):
        request(service, c, nutrients=(N.COMPUTED_ENERGY,))


def test_caller_must_select_method(database):
    service, c, _ = service_fixture(database)
    with pytest.raises(TypeError):
        service.atomic_input(
            c.id, mass_g=Decimal(1), mass_state=MassState.RAW, nutrients=(N.PROTEIN,)
        )


def test_held_observation_is_not_absence_or_estimated_zero(database):
    import json

    v = vector(database[1])
    held = [
        {
            "origin": "UNRESOLVED_ZERO",
            "observation": {
                "target_nutrient_code": "CARBOHYDRATE_AVAILABLE",
                "source_value": "0",
            },
        }
    ]
    v = replace(v, observations_json=json.dumps(held))
    service, c, _ = service_fixture(database, v)
    r = request(service, c, nutrients=(N.AVAILABLE_CARBOHYDRATE,))
    assert r.values[0].amount is None
    assert "HELD_SOURCE_OBSERVATION" in r.values[0].warnings
    assert "UNRESOLVED_ZERO" in r.source_observations_json
    assert "UNRESOLVED_ZERO" in r.values[0].contributions[0].observation.source.locator


def test_existing_sqlite_ports_with_pinned_profile(database, monkeypatch):
    from app.persistence.sqlalchemy_core.food_composition_scope import (
        SqlAlchemyCompositionReadScope,
        SqlAlchemyCompositionUnitOfWork,
    )

    monkeypatch.setenv("AI_ENABLED", "false")
    _, engine = database
    v = vector(engine)
    c = atomic(v)
    with SqlAlchemyCompositionUnitOfWork(engine) as uow:
        uow.compositions.add_versions((c,))
        uow.commit()
    service = NutritionMethodologyService(
        lambda: SqlAlchemyCompositionReadScope(engine)
    )
    result = request(service, c)
    total = next(r for r in result.values if r.nutrient == N.TOTAL_CARBOHYDRATE)
    assert total.amount == v.amount("CARBOHYDRATE_BY_DIFFERENCE") * 2
    assert result.nutrition_profile_id == v.profile_id
    assert result.receipt_sha256 == request(service, c).receipt_sha256
