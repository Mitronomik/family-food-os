"""Pantry HTTP acceptance and Household-boundary tests."""

from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from app.db.config import DATABASE_PATH_ENV, DatabaseConfig
from app.db.migrations import apply_migrations
from app.domain.food_ingredients import FoodIngredient
from app.domain.units import UnitCode
from app.main import create_app
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
from app.persistence.sqlalchemy_core.food_ingredient_uow import (
    SqlAlchemyFoodCatalogueUnitOfWork,
)
from app.persistence.sqlalchemy_core.pantry_uow import SqlAlchemyPantryReadScope

NOW = datetime(2026, 9, 6, tzinfo=timezone.utc)


@pytest.fixture
def pantry_api(monkeypatch, tmp_path):
    config = DatabaseConfig(path=tmp_path / "pantry-api.sqlite")
    monkeypatch.setenv(DATABASE_PATH_ENV, str(config.path))
    apply_migrations(config)
    engine = create_sqlite_engine(config)
    ingredient = FoodIngredient(
        uuid4(),
        "EGGS",
        "Eggs",
        "eggs",
        "eggs",
        UnitCode.PIECE,
        None,
        None,
        False,
        (),
        None,
        True,
        NOW,
        NOW,
    )
    inactive = FoodIngredient(
        uuid4(),
        "INACTIVE",
        "Inactive",
        "inactive",
        "eggs",
        UnitCode.PIECE,
        None,
        None,
        False,
        (),
        None,
        False,
        NOW,
        NOW,
    )
    with SqlAlchemyFoodCatalogueUnitOfWork(engine) as scope:
        scope.ingredients.add(ingredient)
        scope.ingredients.add(inactive)
        scope.commit()
    with TestClient(create_app()) as client:
        home = client.post(
            "/api/households", json={"name": "Home", "timezone": "Europe/Moscow"}
        ).json()
        other = client.post(
            "/api/households", json={"name": "Other", "timezone": "UTC"}
        ).json()
        yield (
            client,
            f"/api/households/{home['id']}/pantry",
            f"/api/households/{other['id']}/pantry",
            ingredient,
            inactive,
            engine,
        )
    engine.dispose()


def add(api, **changes):
    client, prefix, _, ingredient, _, _ = api
    return client.post(
        prefix + "/items",
        json={
            "food_ingredient_id": str(ingredient.id),
            "quantity": "10",
            "unit": "pcs",
            **changes,
        },
    )


def assert_ledger(api, item):
    *_, engine = api
    with SqlAlchemyPantryReadScope(engine) as scope:
        current = scope.items.get(UUID(item["household_id"]), UUID(item["id"]))
        rows = scope.movements.list_for_item(current.household_id, current.id)
        assert current.quantity == sum(
            (m.quantity * m.movement_type.direction for m in rows), Decimal(0)
        )
        return rows


def test_full_confirmed_stock_flow(pantry_api):
    client, prefix, _, ingredient, _, _ = pantry_api
    response = add(
        pantry_api,
        location="FRIDGE",
        estimated=True,
        purchased_on="2026-09-01",
        expires_on="2026-09-09",
    )
    assert response.status_code == 201, response.text
    item = response.json()
    assert item["quantity"] == "10.000"
    assert item["created_at"].endswith("Z")
    assert len(assert_ledger(pantry_api, item)) == 1
    payload = {"food_ingredient_id": str(ingredient.id), "quantity": "4", "unit": "pcs"}
    consume = client.post(prefix + "/consume", json=payload)
    assert consume.status_code == 200, consume.text
    assert consume.json()["movements"][0]["quantity"] == "4.000"
    assert len(assert_ledger(pantry_api, item)) == 2
    fail = client.post(prefix + "/consume", json={**payload, "quantity": "10"})
    assert fail.status_code == 409
    assert client.get(prefix + "/items/" + item["id"]).json()["quantity"] == "6.000"
    assert len(assert_ledger(pantry_api, item)) == 2
    waste = client.post(
        prefix + "/items/" + item["id"] + "/waste",
        json={"quantity": "2", "unit": "pcs"},
    )
    assert waste.status_code == 200
    assert waste.json()["quantity"] == "4.000"
    assert assert_ledger(pantry_api, item)[-1].movement_type == "WASTE"
    for target, movement_type in [("3", "ADJUSTMENT_OUT"), ("5", "ADJUSTMENT_IN")]:
        adjusted = client.post(
            prefix + "/items/" + item["id"] + "/adjust",
            json={"target_quantity": target, "unit": "pcs"},
        )
        assert adjusted.status_code == 200
        assert Decimal(adjusted.json()["quantity"]) == Decimal(target)
        assert assert_ledger(pantry_api, item)[-1].movement_type == movement_type
    before = assert_ledger(pantry_api, item)
    assert (
        client.post(
            prefix + "/items/" + item["id"] + "/adjust",
            json={"target_quantity": "5", "unit": "pcs"},
        ).status_code
        == 200
    )
    assert assert_ledger(pantry_api, item) == before
    patched = client.patch(
        prefix + "/items/" + item["id"],
        json={
            "location": "FREEZER",
            "estimated": False,
            "opened_on": "2026-09-06",
            "expires_on": None,
        },
    )
    assert patched.status_code == 200, patched.text
    assert patched.json()["expires_on"] is None
    assert patched.json()["opened_on"] == "2026-09-06"
    assert patched.json()["quantity"] == "5.000"
    assert assert_ledger(pantry_api, item) == before


def test_fefo_and_expiring_queries(pantry_api):
    client, prefix, _, ingredient, _, _ = pantry_api
    b = add(pantry_api, quantity="4", expires_on="2026-09-10").json()
    a = add(pantry_api, quantity="5", expires_on="2026-09-01", location="FRIDGE").json()
    unknown = add(pantry_api, quantity="2").json()
    result = client.get(prefix + "/expiring", params={"on_or_before": "2026-09-10"})
    assert result.status_code == 200
    assert [i["id"] for i in result.json()["items"]] == [a["id"], b["id"]]
    result = client.post(
        prefix + "/consume",
        json={"food_ingredient_id": str(ingredient.id), "quantity": "7", "unit": "pcs"},
    )
    assert result.status_code == 200
    assert [
        (m["pantry_item_id"], m["quantity"]) for m in result.json()["movements"]
    ] == [(a["id"], "5.000"), (b["id"], "2.000")]
    for item in (a, b, unknown):
        assert_ledger(pantry_api, item)
    assert client.get(prefix + "/items/" + a["id"]).json()["quantity"] == "0.000"
    assert [i["id"] for i in client.get(prefix + "/items").json()["items"]] == [
        b["id"],
        unknown["id"],
    ]
    assert (
        len(
            client.get(prefix + "/items", params={"include_empty": True}).json()[
                "items"
            ]
        )
        == 3
    )
    assert (
        len(
            client.get(
                prefix + "/items",
                params={
                    "include_empty": True,
                    "location": "FRIDGE",
                    "food_ingredient_id": str(ingredient.id),
                },
            ).json()["items"]
        )
        == 1
    )
    assert client.get(
        prefix + "/expiring", params={"on_or_before": "2026-09-01"}
    ).json() == {"items": []}


@pytest.mark.parametrize(
    "changes",
    [
        {"food_ingredient_id": "bad"},
        {"quantity": "bad"},
        {"quantity": "NaN"},
        {"quantity": "Infinity"},
        {"quantity": "-Infinity"},
        {"quantity": "1E99999"},
        {"quantity": "-0.0001"},
        {"quantity": "0"},
        {"quantity": "0.0001"},
        {"quantity": 1.5},
        {"quantity": True},
        {"unit": "kg"},
        {"unit": "percent"},
        {"unit": "g"},
        {"location": "WAREHOUSE"},
        {"estimated": 1},
        {"purchased_on": "2026-02-30"},
        {"opened_on": "2026-09-06T00:00:00Z"},
        {"expires_on": 1788652800},
        {"supplier": "test"},
    ],
)
def test_create_rejects_invalid_input(pantry_api, changes):
    response = add(pantry_api, **changes)
    assert response.status_code == 422, response.text
    assert pantry_api[0].get(pantry_api[1] + "/items").json() == {"items": []}


def test_missing_and_inactive_ingredient(pantry_api):
    assert add(pantry_api, food_ingredient_id=str(uuid4())).status_code == 404
    assert add(pantry_api, food_ingredient_id=str(pantry_api[4].id)).status_code == 409


@pytest.mark.parametrize(
    "changes",
    [
        {"quantity": "20"},
        {"unit": "g"},
        {"household_id": str(uuid4())},
        {"food_ingredient_id": str(uuid4())},
        {},
        {"location": None},
        {"estimated": None},
    ],
)
def test_metadata_cannot_change_quantity_identity_or_null_required_fields(
    pantry_api, changes
):
    client, prefix, *_ = pantry_api
    item = add(pantry_api).json()
    result = client.patch(prefix + "/items/" + item["id"], json=changes)
    assert result.status_code == 422, result.text
    assert client.get(prefix + "/items/" + item["id"]).json() == item
    assert len(assert_ledger(pantry_api, item)) == 1


@pytest.mark.parametrize("operation", ["get", "patch", "waste", "adjust"])
def test_foreign_item_is_indistinguishable_from_missing(pantry_api, operation):
    client, _, other, *_ = pantry_api
    item = add(pantry_api).json()

    def request(item_id):
        url = other + "/items/" + item_id
        if operation == "get":
            return client.get(url)
        if operation == "patch":
            return client.patch(url, json={"estimated": True})
        return client.post(
            url + "/" + operation,
            json={
                "quantity" if operation == "waste" else "target_quantity": "1",
                "unit": "pcs",
            },
        )

    foreign, missing = request(item["id"]), request(str(uuid4()))
    assert foreign.status_code == missing.status_code == 404
    assert foreign.json() == missing.json()
    assert len(assert_ledger(pantry_api, item)) == 1


def test_consumption_cannot_use_other_household_stock(pantry_api):
    client, _, other, ingredient, *_ = pantry_api
    item = add(pantry_api).json()
    response = client.post(
        other + "/consume",
        json={"food_ingredient_id": str(ingredient.id), "quantity": "1", "unit": "pcs"},
    )
    assert response.status_code == 409
    assert client.get(other + "/items").json() == {"items": []}
    assert len(assert_ledger(pantry_api, item)) == 1


@pytest.mark.parametrize(
    "path,method,payload",
    [
        ("/items", "get", None),
        ("/items", "post", "create"),
        ("/items/{item}", "get", None),
        ("/items/{item}", "patch", {"estimated": True}),
        ("/items/{item}/waste", "post", {"quantity": "1", "unit": "pcs"}),
        ("/items/{item}/adjust", "post", {"target_quantity": "1", "unit": "pcs"}),
        ("/consume", "post", "consume"),
        ("/expiring?on_or_before=2026-09-10", "get", None),
    ],
)
def test_missing_household_all_routes(pantry_api, path, method, payload):
    client, _, _, ingredient, *_ = pantry_api
    if isinstance(payload, str):
        payload = {
            "food_ingredient_id": str(ingredient.id),
            "quantity": "1",
            "unit": "pcs",
        }
    result = client.request(
        method,
        f"/api/households/{uuid4()}/pantry" + path.format(item=uuid4()),
        **({"json": payload} if payload is not None else {}),
    )
    assert result.status_code == 404, result.text


@pytest.mark.parametrize(
    "suffix",
    [
        "/items/bad",
        "/items?food_ingredient_id=bad",
        "/items?location=bad",
        "/expiring",
        "/expiring?on_or_before=bad",
        "/expiring?on_or_before=2026-02-30",
    ],
)
def test_invalid_query_or_identifier(pantry_api, suffix):
    assert pantry_api[0].get(pantry_api[1] + suffix).status_code == 422


@pytest.mark.parametrize(
    "operation,payload,status",
    [
        ("waste", {"quantity": "11", "unit": "pcs"}, 409),
        ("waste", {"quantity": "0", "unit": "pcs"}, 422),
        ("waste", {"quantity": "NaN", "unit": "pcs"}, 422),
        ("waste", {"quantity": "1", "unit": "g"}, 422),
        ("adjust", {"target_quantity": "-1", "unit": "pcs"}, 422),
        ("adjust", {"target_quantity": "Infinity", "unit": "pcs"}, 422),
        ("adjust", {"target_quantity": 2.5, "unit": "pcs"}, 422),
        ("adjust", {"quantity": "2", "unit": "pcs"}, 422),
        ("adjust", {"target_quantity": "2", "unit": "g"}, 422),
    ],
)
def test_rejected_item_commands_preserve_ledger(pantry_api, operation, payload, status):
    client, prefix, *_ = pantry_api
    item = add(pantry_api).json()
    response = client.post(
        prefix + "/items/" + item["id"] + "/" + operation, json=payload
    )
    assert response.status_code == status, response.text
    assert client.get(prefix + "/items/" + item["id"]).json() == item
    assert len(assert_ledger(pantry_api, item)) == 1


@pytest.mark.parametrize("value", ["0000000000", "0864000000", "1788652800"])
def test_epoch_strings_are_not_calendar_dates(pantry_api, value):
    assert add(pantry_api, purchased_on=value).status_code == 422
    assert (
        pantry_api[0]
        .get(pantry_api[1] + "/expiring", params={"on_or_before": value})
        .status_code
        == 422
    )


def test_signed_zero_adjustment_is_canonical_zero(pantry_api):
    client, prefix, *_ = pantry_api
    item = add(pantry_api).json()
    response = client.post(
        prefix + "/items/" + item["id"] + "/adjust",
        json={"target_quantity": "-0", "unit": "pcs"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["quantity"] == "0.000"
    assert len(assert_ledger(pantry_api, item)) == 2
