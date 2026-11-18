"""Approved #293: diagnostic v1b compound demand, isolation and immutable replay."""

import json
import sqlite3
from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from app.domain.shopping_calculation import ShoppingCalculationError, ShoppingStatus
from app.domain.shopping_composition_calculation import ENGINE_VERSION, SCHEMA_V2
from app.persistence.sqlalchemy_core.shopping_uow import (
    SqlAlchemyShoppingReadScope,
    SqlAlchemyShoppingUnitOfWork,
)
from app.services.shopping import ShoppingService
from app.services.shopping_contracts import (
    ShoppingNotFoundError,
    ShoppingPersistenceError,
)
from app.services.shopping_diagnostic import DiagnosticCompositionShoppingService
from app.tests.persistence.test_meal_plan_composition_persistence import (
    _compose,
    _setup,
    _write,
)
from app.tests.persistence.test_meal_plan_full_week_composition import _week_21_42
from app.tests.persistence.test_shopping_persistence import _prepare, _service

NOW = datetime(2026, 11, 16, 12, 0, tzinfo=UTC)


def _internal(engine):
    return DiagnosticCompositionShoppingService(
        lambda: SqlAlchemyShoppingUnitOfWork(engine),
        lambda: SqlAlchemyShoppingReadScope(engine),
        clock=lambda: NOW,
    )


@pytest.mark.parametrize("member_count,expected", [
    (1, Decimal("250.000")),
    (2, Decimal("487.500")),
])
def test_component_demand_is_exact_deduplicated_and_private(tmp_path, member_count, expected):
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
        assert diagnostic.get_diagnostic_detail(home.id, result.shopping_list.id) == result
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
            assert db.execute("SELECT count(*) FROM pantry_movements").fetchone() == (0,)
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
        with pytest.raises(Exception):
            _internal(engine).generate_diagnostic(home.id, draft.plan.id)
        with sqlite3.connect(config.path) as db:
            for table in ("shopping_lists", "shopping_list_items", "shopping_unresolved_obligations"):
                assert db.execute(f"SELECT count(*) FROM {table}").fetchone() == (0,)
            assert db.execute("SELECT count(*) FROM pantry_movements").fetchone() == (0,)
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
