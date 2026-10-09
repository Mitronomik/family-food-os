"""PR9-B SQLite Shopping migration, atomic UoW and application tests."""
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import sqlite3
from uuid import uuid4

import pytest
from sqlalchemy import insert

from app.db.config import DatabaseConfig
from app.db.migrations import (
    MIGRATION_MODULES, apply_migrations, expected_migration_ids,
)
from app.domain.meal_plans import MealSourceKind
from app.domain.shopping_calculation import ShoppingPriceStatus, ShoppingStatus
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
from app.persistence.sqlalchemy_core.meal_plan_uow import SqlAlchemyMealPlanUnitOfWork
from app.persistence.sqlalchemy_core.shopping_repositories import SqlAlchemyShoppingListRepository
from app.persistence.sqlalchemy_core.shopping_tables import shopping_lists_table
from app.persistence.sqlalchemy_core.shopping_uow import (
    SqlAlchemyShoppingReadScope, SqlAlchemyShoppingUnitOfWork,
)
from app.services.shopping import ShoppingService
from app.services.shopping_contracts import ShoppingNotFoundError
from app.tests.persistence.test_meal_plan_repository import (
    NOW, _household, _member, _plan, _seed_household, _selection,
)


@pytest.fixture
def store(tmp_path):
    config = DatabaseConfig(path=tmp_path / "shopping.sqlite")
    apply_migrations(config)
    engine = create_sqlite_engine(config)
    try:
        yield config, engine
    finally:
        engine.dispose()


def _prepare(engine, *, unresolved=False):
    household = _household()
    member = _member(household.id)
    _seed_household(engine, household, member)
    selection = _selection(household.id, member.id)
    plan = _plan(household.id, member.id, selection.selection.id)
    if unresolved:
        events = list(plan.events)
        events[0] = replace(events[0], source_kind=MealSourceKind.PREPARED)
        plan = replace(plan, events=tuple(events))
    with SqlAlchemyMealPlanUnitOfWork(engine) as scope:
        scope.selections.add_detail(selection)
        scope.plans.add_detail(plan)
        scope.commit()
    return household, plan


def _service(engine, instant=NOW):
    return ShoppingService(
        lambda: SqlAlchemyShoppingUnitOfWork(engine),
        lambda: SqlAlchemyShoppingReadScope(engine),
        clock=lambda: instant,
    )


def test_migration_0043_fresh_upgrade_and_lineage(tmp_path):
    config = DatabaseConfig(path=tmp_path / "upgrade.sqlite")
    original = list(MIGRATION_MODULES)
    assert original[-1] == "app.migrations.versions.0043_shopping_engine"
    try:
        MIGRATION_MODULES[:] = original[:-1]
        assert apply_migrations(config)[-1] == "0042_recipe_prepared_output_nutrition"
    finally:
        MIGRATION_MODULES[:] = original
    assert apply_migrations(config) == ["0043_shopping_engine"]
    assert apply_migrations(config) == []
    assert expected_migration_ids()[-1] == "0043_shopping_engine"
    with sqlite3.connect(config.path) as conn:
        for table in ("shopping_lists","shopping_list_items","shopping_unresolved_obligations"):
            assert conn.execute(
                "SELECT 1 FROM sqlite_master WHERE name=? AND type='table'",(table,)
            ).fetchone() is not None
        assert conn.execute("PRAGMA foreign_key_check").fetchall() == []
        assert conn.execute("SELECT COUNT(*) FROM shopping_lists").fetchone()[0] == 0


def test_generation_immutable_roundtrip_idempotent_and_price_unknown(store):
    config, engine = store
    household, plan = _prepare(engine)
    service = _service(engine)
    first = service.generate(household.id, plan.plan.id)
    assert first.shopping_list.status is ShoppingStatus.COMPLETE
    assert first.shopping_list.price_status is ShoppingPriceStatus.UNKNOWN
    assert first.items == first.unresolved == ()
    assert service.get_detail(household.id, first.shopping_list.id) == first
    assert service.generate(household.id, plan.plan.id) == first
    assert service.get_current(household.id, plan.plan.id).stale is False
    assert service.list_history(household.id, plan.plan.id) == [first]
    assert _service(engine, NOW + timedelta(days=1)).get_current(
        household.id, plan.plan.id
    ).stale is True
    with sqlite3.connect(config.path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM shopping_lists").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM pantry_movements").fetchone()[0] == 0
        with pytest.raises(sqlite3.IntegrityError, match="immutable"):
            conn.execute(
                "UPDATE shopping_lists SET status='INCOMPLETE' WHERE id=?",
                (first.shopping_list.id.hex,),
            )


def test_unresolved_obligation_roundtrip_and_foreign_household_hidden(store):
    _, engine = store
    household, plan = _prepare(engine, unresolved=True)
    service = _service(engine)
    record = service.generate(household.id, plan.plan.id)
    assert record.shopping_list.status is ShoppingStatus.INCOMPLETE
    assert record.shopping_list.price_status is ShoppingPriceStatus.UNKNOWN
    assert len(record.unresolved) == 1
    assert record.unresolved[0].meal_event_id == plan.events[0].id
    assert service.get_detail(household.id, record.shopping_list.id) == record
    foreign = _household()
    with pytest.raises(ShoppingNotFoundError):
        service.get_detail(foreign.id, record.shopping_list.id)
    with pytest.raises(ShoppingNotFoundError):
        service.list_history(foreign.id, plan.plan.id)
    with pytest.raises(ShoppingNotFoundError):
        service.generate(foreign.id, plan.plan.id)


def test_physical_begin_immediate_blocks_competing_writer_and_rolls_back(store):
    config, engine = store
    household, plan = _prepare(engine)
    with SqlAlchemyShoppingUnitOfWork(engine) as scope:
        assert scope.plans.get_detail(household.id, plan.plan.id) == plan
        contender = sqlite3.connect(config.path, timeout=0.01)
        try:
            with pytest.raises(sqlite3.OperationalError, match="locked"):
                contender.execute(
                    "UPDATE households SET name='blocked' WHERE id=?",
                    (household.id.hex,),
                )
            contender.rollback()
        finally:
            contender.close()
    # Implicit rollback and release after UoW exit.
    with sqlite3.connect(config.path, timeout=1) as connection:
        connection.execute(
            "UPDATE households SET name='after-release' WHERE id=?",
            (household.id.hex,),
        )
        assert connection.execute(
            "SELECT name FROM households WHERE id=?", (household.id.hex,)
        ).fetchone()[0] == "after-release"


def test_failure_injected_after_header_is_fully_rolled_back(store, monkeypatch):
    config, engine = store
    household, plan = _prepare(engine)

    def partial_insert_then_fail(repo, detail):
        repo._connection.execute(insert(shopping_lists_table).values(
            **{k: getattr(detail.shopping_list,k) for k in
               detail.shopping_list.__dataclass_fields__}
        ))
        raise RuntimeError("injected failure after Shopping header")

    monkeypatch.setattr(SqlAlchemyShoppingListRepository, "add_detail",
                        partial_insert_then_fail)
    with pytest.raises(RuntimeError, match="injected failure"):
        _service(engine).generate(household.id, plan.plan.id)
    with sqlite3.connect(config.path) as connection:
        assert connection.execute("SELECT count(*) FROM shopping_lists").fetchone()[0] == 0
        assert connection.execute("SELECT count(*) FROM shopping_list_items").fetchone()[0] == 0
        assert connection.execute("SELECT count(*) FROM shopping_unresolved_obligations").fetchone()[0] == 0
        assert connection.execute("SELECT count(*) FROM pantry_movements").fetchone()[0] == 0
