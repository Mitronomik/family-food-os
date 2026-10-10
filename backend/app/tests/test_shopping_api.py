"""PR9-C TestClient acceptance: immutable Shopping API, source truth and safety."""

import sqlite3
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import date, timedelta
from decimal import Decimal
from threading import Barrier
from uuid import uuid4

import app.main as main_module
import pytest
from app.db.config import DATABASE_PATH_ENV, DatabaseConfig
from app.db.migrations import apply_migrations
from app.domain.food_ingredients import FoodIngredient
from app.domain.meal_plans import MealSourceKind
from app.domain.pantry import PantryItem
from app.main import create_app
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
from app.persistence.sqlalchemy_core.food_recipe_uow import (
    SqlAlchemyRecipeCatalogueUnitOfWork,
)
from app.persistence.sqlalchemy_core.meal_plan_uow import SqlAlchemyMealPlanUnitOfWork
from app.persistence.sqlalchemy_core.pantry_uow import SqlAlchemyPantryUnitOfWork
from app.persistence.sqlalchemy_core.shopping_uow import (
    SqlAlchemyShoppingReadScope,
    SqlAlchemyShoppingUnitOfWork,
)
from app.services.shopping import ShoppingService
from app.services.shopping_contracts import ShoppingPersistenceError
from app.tests.persistence.test_meal_plan_repository import (
    NOW,
    _household,
    _member,
    _plan,
    _seed_household,
    _selection,
)
from app.tests.persistence.test_shopping_persistence import _prepare
from app.tests.test_food_recipe_domain import _detail
from fastapi.testclient import TestClient


@pytest.fixture
def api(monkeypatch, tmp_path):
    config = DatabaseConfig(path=tmp_path / "shopping-api.sqlite")
    monkeypatch.setenv(DATABASE_PATH_ENV, str(config.path))
    apply_migrations(config)
    seed_engine = create_sqlite_engine(config)
    clock = {"now": NOW}

    def composition(engine):
        return ShoppingService(
            lambda: SqlAlchemyShoppingUnitOfWork(engine),
            lambda: SqlAlchemyShoppingReadScope(engine),
            clock=lambda: clock["now"],
        )

    monkeypatch.setattr(main_module, "create_shopping_service", composition)
    try:
        with TestClient(create_app()) as client:
            yield client, seed_engine, clock, config
    finally:
        seed_engine.dispose()


def _urls(household, plan):
    root = f"/api/households/{household.id}"
    prefix = f"{root}/meal-plans/{plan.plan.id}/shopping-lists"
    return root, prefix


def _rows(config, table):
    with sqlite3.connect(config.path) as connection:
        return connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


def _seed_recipe_case(engine):
    recipe = _detail()
    rice = FoodIngredient(
        recipe.ingredients[0].food_ingredient_id,
        "RICE_PR9C",
        "Рис",
        "рис",
        "grains",
        "g",
        None,
        None,
        False,
        (),
        None,
        True,
        NOW,
        NOW,
    )
    leaf = FoodIngredient(
        recipe.ingredients[1].food_ingredient_id,
        "BAY_LEAF_PR9C",
        "Лавровый лист",
        "лавровый лист",
        "spices",
        "pcs",
        None,
        None,
        False,
        (),
        None,
        True,
        NOW,
        NOW,
    )
    with SqlAlchemyRecipeCatalogueUnitOfWork(engine) as scope:
        scope.food_ingredients.add(rice)
        scope.food_ingredients.add(leaf)
        scope.recipes.add(recipe.recipe)
        scope.versions.add_detail(recipe)
        scope.commit()

    household = _household()
    member = _member(household.id)
    _seed_household(engine, household, member)
    selection = _selection(household.id, member.id)
    plan = _plan(household.id, member.id, selection.selection.id)
    events = list(plan.events)
    for index in (3, 6):
        events[index] = replace(
            events[index],
            source_kind=MealSourceKind.COOK_RECIPE,
            recipe_version_id=recipe.version.id,
            source_reference=None,
        )
    plan = replace(plan, events=tuple(events))
    with SqlAlchemyMealPlanUnitOfWork(engine) as scope:
        scope.selections.add_detail(selection)
        scope.plans.add_detail(plan)
        scope.commit()
    stock = PantryItem(
        uuid4(),
        household.id,
        rice.id,
        Decimal("300.000"),
        "g",
        "PANTRY",
        False,
        None,
        None,
        date(2026, 9, 18),
        NOW,
        NOW,
    )
    with SqlAlchemyPantryUnitOfWork(engine) as scope:
        scope.items.add(stock)
        scope.commit()
    return household, plan, rice, leaf, stock


def test_empty_state_generation_and_idempotent_http_contract(api):
    client, engine, _, config = api
    household, plan = _prepare(engine, unresolved=True)
    root, prefix = _urls(household, plan)

    missing = client.get(prefix + "/current")
    assert missing.status_code == 200
    assert missing.json()["lifecycle"] == "MISSING"
    assert missing.json()["detail"] is None
    assert missing.json()["lifecycle_message"] == "Список покупок пока не сформирован."

    created = client.post(prefix, json={})
    assert created.status_code == 200, created.text
    payload = created.json()
    assert payload["household_id"] == str(household.id)
    assert payload["source_plan_revision_number"] == plan.plan.revision_number
    assert payload["status"] == "INCOMPLETE"
    assert payload["price_status"] == "UNKNOWN"
    assert payload["lifecycle"] == "CURRENT"
    assert payload["unresolved"][0]["reason"] == "PREPARED_SUPPLY_UNVERIFIED"
    assert payload["unresolved"][0]["message"] == "Наличие заготовки не подтверждено."
    assert payload["items"] == []
    assert "provenance_json" not in payload
    assert "recipe_inputs" not in str(payload)

    detail = client.get(root + "/shopping-lists/" + payload["id"])
    assert detail.status_code == 200
    assert detail.json() == payload
    current = client.get(prefix + "/current").json()
    assert current["lifecycle"] == "CURRENT"
    assert current["detail"] == payload

    assert client.post(prefix).json() == payload
    assert client.post(prefix + "/regenerate", json={}).json() == payload
    history = client.get(prefix).json()["shopping_lists"]
    assert history == [payload]
    assert _rows(config, "shopping_lists") == 1
    assert _rows(config, "shopping_unresolved_obligations") == 1
    assert _rows(config, "pantry_movements") == 0


def test_exact_quantities_fefo_evidence_and_no_pantry_write(api):
    client, engine, _, config = api
    household, plan, rice, leaf, stock = _seed_recipe_case(engine)
    _, prefix = _urls(household, plan)
    response = client.post(prefix, json={})
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["status"] == "COMPLETE"
    assert payload["price_status"] == "UNKNOWN"
    rice_item = next(
        x for x in payload["items"] if x["food_ingredient_id"] == str(rice.id)
    )
    leaf_item = next(
        x for x in payload["items"] if x["food_ingredient_id"] == str(leaf.id)
    )
    assert (
        rice_item["required_quantity"],
        rice_item["pantry_available_quantity"],
        rice_item["purchase_quantity"],
    ) == ("250.000", "125.000", "125.000")
    assert leaf_item["unit"] == "pcs"
    assert leaf_item["purchase_quantity"].endswith(".000")
    assert [x["ordinal"] for x in payload["items"]] == [1, 2]
    assert any(
        w["code"] == "EXPIRES_BEFORE_REQUIRED_DATE"
        and w["pantry_item_id"] == str(stock.id)
        and w["meal_event_id"] == str(plan.events[6].id)
        and w["required_date"] == "2026-09-20"
        and w["message"] == "Продукт дома утратит пригодность до нужного дня."
        for w in payload["warnings"]
    )
    assert len(payload["allocations"]) == 1
    assert payload["allocations"][0]["quantity"] == "125.000000"
    assert payload["allocations"][0]["food_ingredient_id"] == str(rice.id)
    assert "pantry_items" not in str(payload)
    with sqlite3.connect(config.path) as connection:
        assert (
            connection.execute(
                "SELECT quantity FROM pantry_items WHERE id=?", (stock.id.hex,)
            ).fetchone()[0]
            == "300.000"
        )
    assert _rows(config, "pantry_movements") == 0


def test_stale_successor_revert_and_historical_detail(api):
    client, engine, _, config = api
    household, plan, _, _, stock = _seed_recipe_case(engine)
    root, prefix = _urls(household, plan)
    first = client.post(prefix).json()
    with SqlAlchemyPantryUnitOfWork(engine) as scope:
        scope.items.update_metadata(replace(stock, estimated=True))
        scope.commit()
    stale = client.get(prefix + "/current").json()
    assert stale["lifecycle"] == "STALE"
    assert stale["stale_reason"] == "SOURCE_CHANGED"
    assert stale["detail"]["id"] == first["id"]

    newer = client.post(prefix + "/regenerate").json()
    assert newer["id"] != first["id"]
    assert newer["supersedes_list_id"] == first["id"]
    assert newer["source_fingerprint"] != first["source_fingerprint"]
    assert (
        client.get(root + "/shopping-lists/" + first["id"]).json()["lifecycle"]
        == "STALE"
    )
    assert client.get(prefix).json()["shopping_lists"][0]["id"] == first["id"]

    with SqlAlchemyPantryUnitOfWork(engine) as scope:
        scope.items.update_metadata(replace(stock, estimated=False))
        scope.commit()
    current = client.get(prefix + "/current").json()
    assert current["lifecycle"] == "CURRENT"
    assert current["detail"]["id"] == first["id"]
    assert (
        client.get(root + "/shopping-lists/" + newer["id"]).json()["stale_reason"]
        == "HISTORICAL_SNAPSHOT"
    )
    assert client.post(prefix).json()["id"] == first["id"]
    assert len(client.get(prefix).json()["shopping_lists"]) == 2
    assert _rows(config, "shopping_lists") == 2
    assert _rows(config, "pantry_movements") == 0


def test_calendar_rollover_and_superseded_plan(api):
    client, engine, clock, config = api
    household, plan = _prepare(engine)
    _, prefix = _urls(household, plan)
    first = client.post(prefix).json()
    clock["now"] = NOW + timedelta(days=1)
    assert client.get(prefix + "/current").json()["lifecycle"] == "STALE"
    successor = client.post(prefix + "/regenerate").json()
    assert successor["supersedes_list_id"] == first["id"]
    assert successor["as_of_date"] != first["as_of_date"]

    member = plan.member_selections[0]
    next_plan = _plan(
        household.id,
        member.member_id,
        member.selection_id,
        revision=2,
        supersedes=plan.plan.id,
    )
    with SqlAlchemyMealPlanUnitOfWork(engine) as scope:
        scope.plans.add_detail(next_plan)
        scope.commit()
    assert client.get(prefix + "/current").json()["stale_reason"] == (
        "PLAN_REVISION_CHANGED"
    )
    fail = client.post(prefix, json={})
    assert fail.status_code == 409
    assert fail.json()["detail"]["code"] == "SHOPPING_CONFLICT"
    assert _rows(config, "shopping_lists") == 2


def test_household_scope_validation_and_unknown_inputs(api):
    client, engine, _, config = api
    household, plan = _prepare(engine, unresolved=True)
    other = _household()
    _seed_household(engine, other, _member(other.id))
    root, prefix = _urls(household, plan)
    second_root = f"/api/households/{other.id}"
    foreign_prefix = f"{second_root}/meal-plans/{plan.plan.id}/shopping-lists"

    missing_id = uuid4()
    assert client.get(root + "/shopping-lists/" + str(missing_id)).status_code == 404
    assert client.get(foreign_prefix + "/current").status_code == 404
    assert client.get(foreign_prefix).status_code == 404
    assert client.post(foreign_prefix, json={}).status_code == 404
    assert client.post(foreign_prefix + "/regenerate", json={}).status_code == 404

    for invalid in (
        {"required_quantity": "999"},
        {"purchase_quantity": 1},
        {"food_ingredient_id": str(uuid4())},
        {"price": 0.0},
        {"household_id": str(other.id)},
        [],
    ):
        response = client.post(prefix, json=invalid)
        assert response.status_code == 422, response.text
        detail = response.json()["detail"]
        assert detail["code"] == "SHOPPING_INVALID_REQUEST"
        assert "message" in detail and "next_action" in detail
    for url in (
        root + "/shopping-lists/no-uuid",
        f"{root}/meal-plans/no-uuid/shopping-lists/current",
    ):
        result = client.get(url)
        assert result.status_code == 422
        assert result.json()["detail"]["code"] == "SHOPPING_INVALID_REQUEST"

    saved = client.post(prefix).json()
    wrong = client.get(second_root + "/shopping-lists/" + saved["id"])
    unknown = client.get(root + "/shopping-lists/" + str(missing_id))
    assert wrong.status_code == unknown.status_code == 404
    assert wrong.json() == unknown.json()
    assert (
        client.get(
            second_root + "/shopping-lists/" + saved["unresolved"][0]["id"]
        ).status_code
        == 404
    )
    assert _rows(config, "shopping_lists") == 1


def test_busy_conflict_maps_to_safe_409_and_no_partial_list(api):
    client, engine, _, config = api
    household, plan = _prepare(engine)
    _, prefix = _urls(household, plan)
    with sqlite3.connect(config.path, timeout=0) as contender:
        contender.execute("BEGIN IMMEDIATE")
        blocked = client.post(prefix, json={})
        assert blocked.status_code == 409
        assert blocked.json()["detail"]["code"] == "SHOPPING_CONFLICT"
    assert _rows(config, "shopping_lists") == 0
    assert _rows(config, "pantry_movements") == 0
    assert client.post(prefix).status_code == 200


def test_two_simultaneous_http_generations_do_not_fork(api):
    client, engine, _, config = api
    household, plan = _prepare(engine, unresolved=True)
    _, prefix = _urls(household, plan)
    barrier = Barrier(2)

    def post_one(http_client):
        barrier.wait(timeout=10)
        return http_client.post(prefix, json={})

    with (
        TestClient(create_app()) as other_client,
        ThreadPoolExecutor(max_workers=2) as pool,
    ):
        a = pool.submit(post_one, client)
        b = pool.submit(post_one, other_client)
        responses = (a.result(timeout=30), b.result(timeout=30))
    assert {response.status_code for response in responses} <= {200, 409}
    successes = [r.json() for r in responses if r.status_code == 200]
    assert successes
    assert len({row["id"] for row in successes}) == 1
    assert len(client.get(prefix).json()["shopping_lists"]) == 1
    assert _rows(config, "shopping_lists") == 1
    assert _rows(config, "pantry_movements") == 0


def test_error_taxonomy_and_openapi(api, monkeypatch):
    client, engine, _, _ = api
    household, plan = _prepare(engine)
    _, prefix = _urls(household, plan)
    paths = client.get("/openapi.json").json()["paths"]
    assert (
        prefix.replace(str(household.id), "{household_id}").replace(
            str(plan.plan.id), "{plan_id}"
        )
        in paths
    )

    def broken_factory(_engine):
        class Broken:
            def generate(self, *_args):
                raise ShoppingPersistenceError("secret sqlite internals")

        return Broken()

    with monkeypatch.context() as patch:
        patch.setattr(main_module, "create_shopping_service", broken_factory)
        with TestClient(create_app()) as failing_client:
            bad = failing_client.post(prefix)
    assert bad.status_code == 503
    assert bad.json()["detail"]["code"] == "SHOPPING_UNAVAILABLE"
    assert "secret sqlite" not in bad.text
    assert _rows(api[3], "shopping_lists") == 0
