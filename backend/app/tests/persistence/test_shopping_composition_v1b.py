"""Approved #293: diagnostic v1b compound demand, isolation and immutable replay."""

import json
import sqlite3
import subprocess
import sys
from dataclasses import replace
from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

import app.main as main_module
import pytest
from app.db.config import DATABASE_PATH_ENV
from app.domain.shopping_calculation import ShoppingCalculationError, ShoppingStatus
from app.domain.shopping_composition_calculation import (
    ENGINE_VERSION,
    SCHEMA_V2,
    calculate_shopping_composition,
)
from app.domain.pantry import PantryItem, PantryLocation
from app.persistence.sqlalchemy_core.pantry_uow import SqlAlchemyPantryUnitOfWork
from app.main import create_app
from app.persistence.sqlalchemy_core.shopping_uow import (
    SqlAlchemyShoppingReadScope,
    SqlAlchemyShoppingUnitOfWork,
)
from app.services.shopping_contracts import (
    ShoppingNotFoundError,
    ShoppingPersistenceConflictError,
    ShoppingPersistenceError,
)
from app.services.shopping_diagnostic import DiagnosticCompositionShoppingService
from app.tests.persistence.test_meal_plan_composition_persistence import (
    _compose,
    _setup,
    _write,
)
from app.tests.persistence.test_meal_plan_full_week_composition import _week_21_42
from app.tests.persistence.test_shopping_persistence import _service
from fastapi.testclient import TestClient

NOW = datetime(2026, 11, 16, 12, 0, tzinfo=UTC)


def _internal(engine):
    return DiagnosticCompositionShoppingService(
        lambda: SqlAlchemyShoppingUnitOfWork(engine),
        lambda: SqlAlchemyShoppingReadScope(engine),
        clock=lambda: NOW,
    )


@pytest.mark.parametrize(
    "member_count,expected",
    [
        (1, Decimal("250.000")),
        (2, Decimal("487.500")),
    ],
)
def test_component_demand_is_exact_deduplicated_and_private(
    tmp_path, member_count, expected
):
    config, engine, home, people, old, recipes, selections = _setup(
        tmp_path, members=member_count
    )
    try:
        draft = _compose(old, people, recipes, selections)
        _write(engine, draft, people)
        diagnostic = _internal(engine)
        result = diagnostic.generate_diagnostic(home.id, draft.plan.id)
        assert result.shopping_list.engine_version == ENGINE_VERSION
        assert result.shopping_list.status is ShoppingStatus.COMPLETE
        assert result.unresolved == ()
        assert len(result.items) == 1
        assert result.items[0].required_quantity == expected
        assert result.items[0].purchase_quantity == expected
        source = json.loads(result.shopping_list.provenance_json)
        assert source["schema"] == SCHEMA_V2
        assert len(source["component_contributions"]) == 3
        assert len(source["compositions"][0]["components"]) == 3
        assert len(source["event_demands"]) == 7
        assert sum(
            Decimal(row["unrounded_contribution"])
            for row in source["component_contributions"]
        ) == (Decimal("62.500") if member_count == 1 else Decimal("112.500"))
        assert (
            diagnostic.get_diagnostic_detail(home.id, result.shopping_list.id) == result
        )
        assert diagnostic.generate_diagnostic(home.id, draft.plan.id) == result

        public = _service(engine, NOW)
        with pytest.raises(ShoppingNotFoundError):
            public.get_detail(home.id, result.shopping_list.id)
        assert public.list_history(home.id, draft.plan.id) == []
        with pytest.raises(ShoppingCalculationError):
            public.get_current(home.id, draft.plan.id)
        with pytest.raises(ShoppingCalculationError):
            public.generate(home.id, draft.plan.id)
        with pytest.raises(ShoppingCalculationError):
            public.regenerate(home.id, draft.plan.id)
        with SqlAlchemyShoppingReadScope(engine) as scope:
            assert scope.shopping.get_detail(home.id, result.shopping_list.id) == result
        with sqlite3.connect(config.path) as db:
            assert db.execute("SELECT count(*) FROM shopping_lists").fetchone() == (1,)
            assert db.execute("SELECT count(*) FROM pantry_movements").fetchone() == (
                0,
            )
    finally:
        engine.dispose()


def test_full_21_event_week_aggregates_dated_composite_once(tmp_path):
    _, engine, home, people, old, recipes, selections = _week_21_42(tmp_path)
    try:
        draft = _compose(old, people[:1], recipes, selections, target_index=4)
        _write(engine, draft, people)
        result = _internal(engine).generate_diagnostic(home.id, draft.plan.id)
        assert len(draft.events) == 21
        assert len(draft.servings) == 41
        assert len(result.items) == 1
        assert result.items[0].required_quantity == Decimal("1343.750")
        source = json.loads(result.shopping_list.provenance_json)
        assert len(source["event_demands"]) == 21
        assert sum(
            Decimal(row["unrounded_required"]) for row in source["event_demands"]
        ) == Decimal("1343.750")
    finally:
        engine.dispose()


def test_new_shopping_diagnostic_fault_rolls_back_full_snapshot(tmp_path):
    config, engine, home, people, old, recipes, selections = _setup(tmp_path)
    try:
        draft = _compose(old, people, recipes, selections)
        _write(engine, draft, people)
        with sqlite3.connect(config.path) as db:
            db.execute(
                "CREATE TRIGGER test_v1b_item_failure BEFORE INSERT ON shopping_list_items "
                "BEGIN SELECT RAISE(ABORT, 'injected item fault'); END"
            )
        with pytest.raises(ShoppingPersistenceConflictError):
            _internal(engine).generate_diagnostic(home.id, draft.plan.id)
        with sqlite3.connect(config.path) as db:
            for table in (
                "shopping_lists",
                "shopping_list_items",
                "shopping_unresolved_obligations",
            ):
                assert db.execute(f"SELECT count(*) FROM {table}").fetchone() == (0,)
            assert db.execute("SELECT count(*) FROM pantry_movements").fetchone() == (
                0,
            )
    finally:
        engine.dispose()


def test_v1a_history_and_api_projector_do_not_accept_v2(tmp_path):
    from app.api.shopping import _detail_response
    from app.domain.shopping_lists import ShoppingCurrent

    config, engine, home, people, old, recipes, selections = _setup(tmp_path)
    try:
        # The old 7-event current is source-backed and may have its own v1a list.
        legacy = _service(engine, NOW)
        saved_v1 = legacy.generate(home.id, old.plan.id)
        original_hash = saved_v1.shopping_list.source_fingerprint
        draft = _compose(old, people, recipes, selections)
        _write(engine, draft, people)
        v2 = _internal(engine).generate_diagnostic(home.id, draft.plan.id)
        assert legacy.get_detail(home.id, saved_v1.shopping_list.id) == saved_v1
        assert legacy.list_history(home.id, old.plan.id) == [saved_v1]
        assert legacy.get_current(home.id, old.plan.id).stale
        assert saved_v1.shopping_list.source_fingerprint == original_hash
        with pytest.raises(ShoppingPersistenceError):
            _detail_response(v2, ShoppingCurrent(v2, True, "SOURCE_INVALID"))
        with sqlite3.connect(config.path) as db:
            rows = db.execute(
                "SELECT engine_version, count(*) FROM shopping_lists "
                "GROUP BY engine_version ORDER BY engine_version"
            ).fetchall()
            assert rows == [("shopping-v1a", 1), (ENGINE_VERSION, 1)]
    finally:
        engine.dispose()


def test_v1b_read_endpoints_protect_contents_even_on_stale_fallback(
    tmp_path, monkeypatch
):
    config, engine, home, people, old, recipes, selections = _setup(tmp_path)
    try:
        draft = _compose(old, people, recipes, selections)
        _write(engine, draft, people)
        diagnostic = _internal(engine).generate_diagnostic(home.id, draft.plan.id)
        monkeypatch.setenv(DATABASE_PATH_ENV, str(config.path))
        monkeypatch.setattr(
            main_module,
            "create_shopping_service",
            lambda engine: _service(engine, NOW),
        )
        prefix = f"/api/households/{home.id}/meal-plans/{draft.plan.id}/shopping-lists"
        with TestClient(create_app()) as client:
            direct = client.get(
                f"/api/households/{home.id}/shopping-lists/{diagnostic.shopping_list.id}"
            )
            assert direct.status_code == 404
            assert direct.json()["detail"]["code"] == "SHOPPING_NOT_FOUND"
            history = client.get(prefix)
            assert history.status_code == 200
            assert history.json() == {"shopping_lists": []}
            current = client.get(prefix + "/current")
            assert current.status_code == 409
            for url in (prefix, prefix + "/regenerate"):
                response = client.post(url, json={})
                assert response.status_code == 409
                assert "items" not in response.json()
            for response in (direct, history, current):
                assert "component_contributions" not in response.text
                assert "source_fingerprint" not in response.text
                assert str(diagnostic.shopping_list.id) not in response.text
    finally:
        engine.dispose()


def test_v1b_new_process_replay_and_tamper_rejection(tmp_path):
    config, engine, home, people, old, recipes, selections = _setup(tmp_path)
    try:
        draft = _compose(old, people, recipes, selections)
        _write(engine, draft, people)
        v2 = _internal(engine).generate_diagnostic(home.id, draft.plan.id)
        engine.dispose()
        code = """
import sys
from pathlib import Path
from uuid import UUID
from app.db.config import DatabaseConfig
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
from app.persistence.sqlalchemy_core.shopping_uow import SqlAlchemyShoppingReadScope, SqlAlchemyShoppingUnitOfWork
from app.services.shopping_diagnostic import DiagnosticCompositionShoppingService
engine = create_sqlite_engine(DatabaseConfig(path=Path(sys.argv[1])))
try:
    service = DiagnosticCompositionShoppingService(
        lambda: SqlAlchemyShoppingUnitOfWork(engine),
        lambda: SqlAlchemyShoppingReadScope(engine),
    )
    result = service.get_diagnostic_detail(UUID(sys.argv[2]), UUID(sys.argv[3]))
    print(result.shopping_list.content_fingerprint)
finally:
    engine.dispose()
"""
        outcome = subprocess.run(
            [
                sys.executable,
                "-c",
                code,
                str(config.path),
                str(home.id),
                str(v2.shopping_list.id),
            ],
            text=True,
            capture_output=True,
            check=True,
        )
        assert outcome.stdout.strip() == v2.shopping_list.content_fingerprint

        # A malicious local DB rewrite bypassing immutable triggers must still
        # fail deterministic arithmetic/source replay in a new reader.
        engine = __import__(
            "app.persistence.sqlalchemy_core.engine",
            fromlist=["create_sqlite_engine"],
        ).create_sqlite_engine(config)
        with sqlite3.connect(config.path) as db:
            db.execute("DROP TRIGGER trg_shopping_lists_update_immutable")
            raw = json.loads(
                db.execute(
                    "SELECT provenance_json FROM shopping_lists WHERE id=?",
                    (v2.shopping_list.id.hex,),
                ).fetchone()[0]
            )
            raw["component_contributions"][0]["unrounded_contribution"] = "999"
            db.execute(
                "UPDATE shopping_lists SET provenance_json=? WHERE id=?",
                (json.dumps(raw, ensure_ascii=False), v2.shopping_list.id.hex),
            )
        with pytest.raises(ShoppingPersistenceError):
            _internal(engine).get_diagnostic_detail(home.id, v2.shopping_list.id)
    finally:
        engine.dispose()


def test_versioned_component_member_factor_and_repeated_recipe_pin_change_hash(tmp_path):
    _, engine, home, people, old, recipes, selections = _setup(tmp_path)
    try:
        draft = _compose(old, people, recipes, selections)
        source_ids = set(recipes.values())
        with SqlAlchemyShoppingReadScope(engine) as scope:
            recipe_details = {
                rid: scope.recipes.get_detail(rid) for rid in source_ids
            }
            food_id = next(iter(recipe_details.values())).ingredients[0].food_ingredient_id
            foods = {food_id: scope.foods.get(food_id)}
        inputs = {
            "recipes": recipe_details,
            "foods": foods,
            "pantry_items": (),
            "household_timezone": home.timezone,
            "captured_at": NOW,
        }
        first, source = calculate_shopping_composition(plan=draft, **inputs)
        comp = draft.compositions[0]
        changed_servings = tuple(
            replace(item, portion_servings=Decimal("1.125000"))
            if item.component_id == comp.components[0].id
            else item
            for item in comp.servings
        )
        changed = replace(
            draft, compositions=(replace(comp, servings=changed_servings),)
        )
        second, second_source = calculate_shopping_composition(plan=changed, **inputs)
        assert first.source_fingerprint != second.source_fingerprint
        assert second.items[0].required_quantity == first.items[0].required_quantity + Decimal("3.125")
        assert source["component_contributions"] != second_source["component_contributions"]
        same_recipe_parts = (
            replace(comp.components[0], recipe_version_id=comp.components[1].recipe_version_id),
            *comp.components[1:],
        )
        repeated = replace(
            draft, compositions=(replace(comp, components=same_recipe_parts),)
        )
        third, third_source = calculate_shopping_composition(plan=repeated, **inputs)
        assert third.items[0].required_quantity == first.items[0].required_quantity
        assert third.source_fingerprint != first.source_fingerprint
        assert third_source["compositions"][0]["components"][0]["recipe_version_id"] == (
            third_source["compositions"][0]["components"][1]["recipe_version_id"]
        )
        assert len(third_source["component_contributions"]) == 3
    finally:
        engine.dispose()


@pytest.mark.parametrize(
    "stock_quantity,expected_available,expected_purchase,expect_expiry_warning",
    [
        (Decimal("100.000"), Decimal("100.000"), Decimal("150.000"), False),
        (Decimal("140.000"), Decimal("125.000"), Decimal("125.000"), True),
    ],
)
def test_v1b_dated_pantry_fefo_across_composed_and_legacy_events(
    tmp_path, stock_quantity, expected_available, expected_purchase, expect_expiry_warning
):
    config, engine, home, people, old, recipes, selections = _setup(tmp_path)
    try:
        draft = _compose(old, people, recipes, selections)
        _write(engine, draft, people)
        with sqlite3.connect(config.path) as db:
            ingredient_id = UUID(
                hex=db.execute(
                    "SELECT id FROM food_ingredients WHERE canonical_code='TEST_POTATO'"
                ).fetchone()[0]
            )
        stock = PantryItem(
            id=uuid4(), household_id=home.id,
            food_ingredient_id=ingredient_id,
            quantity=stock_quantity, unit="g",
            location=PantryLocation.PANTRY,
            estimated=False, purchased_on=None, opened_on=None,
            expires_on=date(2026, 9, 16),
            created_at=NOW, updated_at=NOW,
        )
        with SqlAlchemyPantryUnitOfWork(engine) as scope:
            scope.items.add(stock)
            scope.commit()
        # The persisted fixture week is 2026-09-14..20, not November.
        day_before_week = datetime(2026, 9, 13, 12, tzinfo=UTC)
        diagnostic = DiagnosticCompositionShoppingService(
            lambda: SqlAlchemyShoppingUnitOfWork(engine),
            lambda: SqlAlchemyShoppingReadScope(engine),
            clock=lambda: day_before_week,
        )
        snapshot = diagnostic.generate_diagnostic(home.id, draft.plan.id)
        only = snapshot.items[0]
        assert only.required_quantity == Decimal("250.000")
        assert only.pantry_available_quantity == expected_available
        assert only.purchase_quantity == expected_purchase
        data = json.loads(snapshot.shopping_list.provenance_json)
        assert len(data["allocations"]) == 3
        assert sum(Decimal(a["quantity"]) for a in data["allocations"]) == expected_available
        # Component demand is combined before FEFO: one allocation per event/lot.
        assert len({
            (a["meal_event_id"], a["pantry_item_id"])
            for a in data["allocations"]
        }) == len(data["allocations"])
        assert (
            any(
                w["code"] == "EXPIRES_BEFORE_REQUIRED_DATE"
                for w in data["warnings"]
            )
            is expect_expiry_warning
        )
        assert diagnostic.get_diagnostic_detail(home.id, snapshot.shopping_list.id) == snapshot
        with sqlite3.connect(config.path) as db:
            assert db.execute("SELECT count(*) FROM pantry_movements").fetchone() == (0,)
            assert db.execute(
                "SELECT quantity FROM pantry_items WHERE id=?", (stock.id.hex,)
            ).fetchone() == (format(stock_quantity, ".3f"),)
    finally:
        engine.dispose()
