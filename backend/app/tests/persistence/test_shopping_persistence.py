"""PR9-B SQLite Shopping migration, atomic UoW and application tests."""

import sqlite3
from dataclasses import replace
from datetime import date, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from app.db.config import DatabaseConfig
from app.db.migrations import (
    MIGRATION_MODULES,
    apply_migrations,
    expected_migration_ids,
)
from app.domain.food_ingredients import FoodIngredient
from app.domain.pantry import PantryItem
from app.domain.meal_plans import MealSourceKind
from app.domain.shopping_calculation import ShoppingPriceStatus, ShoppingStatus
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
from app.persistence.sqlalchemy_core.meal_plan_uow import SqlAlchemyMealPlanUnitOfWork
from app.persistence.sqlalchemy_core.food_recipe_uow import SqlAlchemyRecipeCatalogueUnitOfWork
from app.persistence.sqlalchemy_core.pantry_uow import SqlAlchemyPantryUnitOfWork
from app.persistence.sqlalchemy_core.shopping_repositories import (
    SqlAlchemyShoppingListRepository,
)
from app.persistence.sqlalchemy_core.shopping_tables import shopping_lists_table
from app.persistence.sqlalchemy_core.shopping_uow import (
    SqlAlchemyShoppingReadScope,
    SqlAlchemyShoppingUnitOfWork,
)
from app.services.shopping import ShoppingService
from app.services.shopping_contracts import ShoppingNotFoundError
from app.tests.test_food_recipe_domain import _detail
from app.tests.persistence.test_meal_plan_repository import (
    NOW,
    _household,
    _member,
    _plan,
    _seed_household,
    _selection,
)
from sqlalchemy import insert


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
        for table in (
            "shopping_lists",
            "shopping_list_items",
            "shopping_unresolved_obligations",
        ):
            assert (
                conn.execute(
                    "SELECT 1 FROM sqlite_master WHERE name=? AND type='table'",
                    (table,),
                ).fetchone()
                is not None
            )
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
    assert (
        _service(engine, NOW + timedelta(days=1))
        .get_current(household.id, plan.plan.id)
        .stale
        is True
    )
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
        assert (
            connection.execute(
                "SELECT name FROM households WHERE id=?", (household.id.hex,)
            ).fetchone()[0]
            == "after-release"
        )


def test_failure_injected_after_header_is_fully_rolled_back(store, monkeypatch):
    config, engine = store
    household, plan = _prepare(engine)

    def partial_insert_then_fail(repo, detail):
        repo._connection.execute(
            insert(shopping_lists_table).values(
                **{
                    k: getattr(detail.shopping_list, k)
                    for k in detail.shopping_list.__dataclass_fields__
                }
            )
        )
        raise RuntimeError("injected failure after Shopping header")

    monkeypatch.setattr(
        SqlAlchemyShoppingListRepository, "add_detail", partial_insert_then_fail
    )
    with pytest.raises(RuntimeError, match="injected failure"):
        _service(engine).generate(household.id, plan.plan.id)
    with sqlite3.connect(config.path) as connection:
        assert (
            connection.execute("SELECT count(*) FROM shopping_lists").fetchone()[0] == 0
        )
        assert (
            connection.execute("SELECT count(*) FROM shopping_list_items").fetchone()[0]
            == 0
        )
        assert (
            connection.execute(
                "SELECT count(*) FROM shopping_unresolved_obligations"
            ).fetchone()[0]
            == 0
        )
        assert (
            connection.execute("SELECT count(*) FROM pantry_movements").fetchone()[0]
            == 0
        )


def test_full_recipe_pantry_generation_roundtrip_provenance_and_stale(store):
    config, engine = store
    recipe = _detail()
    rice = FoodIngredient(
        recipe.ingredients[0].food_ingredient_id, "RICE_SHOPPING",
        "Rice", "rice", "grains", "g", None, None, False, (),
        None, True, NOW, NOW,
    )
    leaf = FoodIngredient(
        recipe.ingredients[1].food_ingredient_id, "BAY_SHOPPING",
        "Bay leaf", "bay leaf", "spices", "pcs", None, None, False, (),
        None, True, NOW, NOW,
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
    selected = _selection(household.id, member.id)
    plan = _plan(household.id, member.id, selected.selection.id)
    events = list(plan.events)
    for idx in (3, 6):
        events[idx] = replace(
            events[idx], source_kind=MealSourceKind.COOK_RECIPE,
            recipe_version_id=recipe.version.id, source_reference=None,
        )
    plan = replace(plan, events=tuple(events))
    with SqlAlchemyMealPlanUnitOfWork(engine) as scope:
        scope.selections.add_detail(selected)
        scope.plans.add_detail(plan)
        scope.commit()
    stock = PantryItem(
        uuid4(), household.id, rice.id, Decimal("300.000"), "g",
        "PANTRY", False, None, None, date(2026, 9, 18), NOW, NOW,
    )
    with SqlAlchemyPantryUnitOfWork(engine) as scope:
        scope.items.add(stock)
        scope.commit()

    service = _service(engine)
    saved = service.generate(household.id, plan.plan.id)
    rice_item = next(x for x in saved.items if x.food_ingredient_id == rice.id)
    # 2 events * 600g / 6 source servings * 1.25 participating servings.
    assert rice_item.required_quantity == Decimal("250.000")
    assert rice_item.pantry_available_quantity == Decimal("125.000")
    assert rice_item.purchase_quantity == Decimal("125.000")
    import json
    evidence = json.loads(saved.shopping_list.provenance_json)
    warnings = evidence["warnings"]
    assert any(
        w["code"] == "EXPIRES_BEFORE_REQUIRED_DATE"
        and w["pantry_item_id"] == str(stock.id)
        and w["meal_event_id"] == str(plan.events[6].id)
        and w["required_date"] == "2026-09-20"
        for w in warnings
    )
    assert len(evidence["allocations"]) == 1
    assert service.get_detail(household.id, saved.shopping_list.id) == saved
    assert not service.get_current(household.id, plan.plan.id).stale
    with sqlite3.connect(config.path) as connection:
        assert connection.execute(
            "SELECT quantity FROM pantry_items WHERE id=?", (stock.id.hex,)
        ).fetchone()[0] == "300.000"
        assert connection.execute(
            "SELECT COUNT(*) FROM pantry_movements"
        ).fetchone()[0] == 0

    with SqlAlchemyPantryUnitOfWork(engine) as scope:
        scope.items.update_metadata(
            replace(stock, estimated=True, updated_at=NOW + timedelta(days=1))
        )
        scope.commit()
    current = service.get_current(household.id, plan.plan.id)
    assert current.stale is True
    assert current.detail == saved
    newer = service.regenerate(household.id, plan.plan.id)
    assert newer.shopping_list.supersedes_list_id == saved.shopping_list.id
    assert newer.shopping_list.id != saved.shopping_list.id
    assert newer.shopping_list.source_pantry_snapshot_hash != saved.shopping_list.source_pantry_snapshot_hash
    assert service.get_detail(household.id, saved.shopping_list.id) == saved
    assert len(service.list_history(household.id, plan.plan.id)) == 2


def test_0043_failure_rolls_back_tables_and_marker(tmp_path, monkeypatch):
    from importlib import import_module

    config = DatabaseConfig(path=tmp_path / "migration-failure.sqlite")
    original = list(MIGRATION_MODULES)
    try:
        MIGRATION_MODULES[:] = original[:-1]
        apply_migrations(config)
    finally:
        MIGRATION_MODULES[:] = original
    module = import_module("app.migrations.versions.0043_shopping_engine")
    upgrade = module.upgrade

    def fail(conn):
        conn.execute("CREATE TABLE aborted_shopping_probe(id INTEGER)")
        raise RuntimeError("injected migration failure")

    monkeypatch.setattr(module, "upgrade", fail)
    with pytest.raises(RuntimeError, match="injected migration failure"):
        apply_migrations(config)
    with sqlite3.connect(config.path) as db:
        assert db.execute(
            "SELECT 1 FROM sqlite_master WHERE name='aborted_shopping_probe'"
        ).fetchone() is None
        assert db.execute(
            "SELECT 1 FROM schema_migrations WHERE migration_id='0043_shopping_engine'"
        ).fetchone() is None
    monkeypatch.setattr(module, "upgrade", upgrade)
    assert apply_migrations(config) == ["0043_shopping_engine"]
