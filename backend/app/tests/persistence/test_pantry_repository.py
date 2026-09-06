import sqlite3
from dataclasses import replace
from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import Column, ForeignKey, Integer, MetaData, Table, event
from sqlalchemy.exc import ResourceClosedError

from app.db.config import DatabaseConfig
from app.db.migrations import apply_migrations
from app.domain.food_ingredients import FoodIngredient
from app.domain.households import Household
from app.domain.pantry import PantryItem, PantryMovement
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
from app.persistence.sqlalchemy_core.pantry_uow import (
    SqlAlchemyPantryReadScope,
    SqlAlchemyPantryUnitOfWork,
)
from app.services.pantry_contracts import (
    PantryPersistenceConflictError,
    PantryPersistenceError,
)

NOW = datetime(2026, 9, 6, 12, 0, 1, 123456, tzinfo=timezone.utc)
metadata = MetaData()
parent_table = Table(
    "pantry_test_parent", metadata, Column("id", Integer, primary_key=True)
)
child_table = Table(
    "pantry_test_child",
    metadata,
    Column("id", Integer, primary_key=True),
    Column(
        "parent_id",
        Integer,
        ForeignKey(parent_table.c.id, deferrable=True, initially="DEFERRED"),
    ),
)


@pytest.fixture
def pantry_store(tmp_path):
    config = DatabaseConfig(path=tmp_path / "pantry.sqlite")
    apply_migrations(config)
    engine = create_sqlite_engine(config)
    household = Household(uuid4(), "Home", "UTC", None, None, None, NOW, NOW)
    other = replace(household, id=uuid4(), name="Other")
    ingredient = FoodIngredient(
        uuid4(),
        "EGGS",
        "Eggs",
        "eggs",
        "eggs",
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
    with engine.begin() as connection:
        parent_table.create(connection)
        child_table.create(connection)
    with SqlAlchemyPantryUnitOfWork(engine) as scope:
        scope.households.add_household(household)
        scope.households.add_household(other)
        scope.food_ingredients.add(ingredient)
        scope.commit()
    try:
        yield config, engine, household.id, other.id, ingredient.id
    finally:
        engine.dispose()


def item(hid, fid, **changes):
    values = dict(
        id=uuid4(),
        household_id=hid,
        food_ingredient_id=fid,
        quantity=Decimal("10"),
        unit="pcs",
        location="PANTRY",
        estimated=False,
        purchased_on=None,
        opened_on=None,
        expires_on=None,
        created_at=NOW,
        updated_at=NOW,
    )
    values.update(changes)
    return PantryItem(**values)


def movement(bucket, **changes):
    values = dict(
        id=uuid4(),
        household_id=bucket.household_id,
        pantry_item_id=bucket.id,
        quantity=bucket.quantity,
        unit=bucket.unit,
        movement_type="ADD",
        occurred_at=NOW,
        created_at=NOW,
    )
    values.update(changes)
    return PantryMovement(**values)


def persist(engine, bucket):
    with SqlAlchemyPantryUnitOfWork(engine) as scope:
        scope.items.add(bucket)
        scope.movements.add(movement(bucket))
        scope.commit()


def assert_revoked(scope, retained, hid, iid):
    for attribute in ("items", "movements", "households", "food_ingredients"):
        with pytest.raises(RuntimeError, match="not active"):
            getattr(scope, attribute)
    with pytest.raises(ResourceClosedError):
        retained.get(hid, iid)


def test_exact_roundtrip_scoping_and_filters(pantry_store):
    config, engine, hid, other, fid = pantry_store
    bucket = item(hid, fid, quantity="999999999999.999", purchased_on=date(2026, 9, 5))
    persist(engine, bucket)
    with SqlAlchemyPantryReadScope(engine) as scope:
        assert scope.items.get(hid, bucket.id) == bucket
        assert scope.items.get(other, bucket.id) is None
        assert scope.items.list_items(other) == []
        assert scope.items.list_items(
            hid, food_ingredient_id=fid, location="PANTRY"
        ) == [bucket]
        assert scope.items.list_items(hid, location="FRIDGE") == []
        assert scope.movements.list_for_item(other, bucket.id) == []
        history = scope.movements.list_for_item(hid, bucket.id)
        assert history[0].quantity == bucket.quantity
        assert history[0].created_at.tzinfo is timezone.utc
    with sqlite3.connect(config.path) as connection:
        assert connection.execute(
            "SELECT quantity, typeof(quantity) FROM pantry_items"
        ).fetchone() == ("999999999999.999", "text")


def test_atomic_decrease_increase_and_stale_cas_fail_closed(pantry_store):
    _, engine, hid, other, fid = pantry_store
    bucket = item(hid, fid)
    persist(engine, bucket)
    with SqlAlchemyPantryUnitOfWork(engine) as scope:
        assert not scope.items.decrease_quantity_if_sufficient(
            other,
            bucket.id,
            Decimal("4"),
            expected_quantity=Decimal("10"),
            updated_at=NOW,
        )
        assert scope.items.decrease_quantity_if_sufficient(
            hid,
            bucket.id,
            Decimal("4"),
            expected_quantity=Decimal("10"),
            updated_at=NOW,
        )
        scope.movements.add(movement(bucket, quantity="4", movement_type="CONSUMPTION"))
        assert not scope.items.decrease_quantity_if_sufficient(
            hid,
            bucket.id,
            Decimal("4"),
            expected_quantity=Decimal("10"),
            updated_at=NOW,
        )
        assert not scope.items.decrease_quantity_if_sufficient(
            hid,
            bucket.id,
            Decimal("10"),
            expected_quantity=Decimal("6"),
            updated_at=NOW,
        )
        assert scope.items.increase_quantity(
            hid,
            bucket.id,
            Decimal("0.001"),
            expected_quantity=Decimal("6"),
            updated_at=NOW,
        )
        scope.movements.add(
            movement(bucket, quantity="0.001", movement_type="ADJUSTMENT_IN")
        )
        scope.commit()
    with SqlAlchemyPantryReadScope(engine) as scope:
        actual = scope.items.get(hid, bucket.id)
        assert actual.quantity == Decimal("6.001")
        assert actual.quantity == sum(
            m.quantity * m.movement_type.direction
            for m in scope.movements.list_for_item(hid, bucket.id)
        )


def test_metadata_updates_never_overwrite_stock_identity_or_balance(pantry_store):
    _, engine, hid, other, fid = pantry_store
    bucket = item(hid, fid)
    persist(engine, bucket)
    with SqlAlchemyPantryUnitOfWork(engine) as scope:
        scope.items.update_metadata(
            replace(
                bucket,
                food_ingredient_id=uuid4(),
                unit="g",
                quantity=Decimal("999"),
                location="FREEZER",
                expires_on=date(2026, 9, 20),
            )
        )
        with pytest.raises(PantryPersistenceError):
            scope.items.update_metadata(replace(bucket, household_id=other))
        scope.commit()
    with SqlAlchemyPantryReadScope(engine) as scope:
        actual = scope.items.get(hid, bucket.id)
        assert (actual.food_ingredient_id, actual.unit, actual.quantity) == (
            fid,
            bucket.unit,
            bucket.quantity,
        )
        assert actual.location == "FREEZER"


def test_fefo_null_expiry_purchase_ties_and_empty_handling(pantry_store):
    _, engine, hid, _, fid = pantry_store
    first = item(hid, fid, expires_on=date(2026, 9, 10), purchased_on=date(2026, 9, 1))
    second = item(hid, fid, expires_on=date(2026, 9, 10), purchased_on=date(2026, 9, 2))
    third = item(hid, fid, expires_on=date(2026, 9, 10))
    fourth = item(hid, fid, expires_on=date(2026, 9, 11))
    last = item(hid, fid)
    for bucket in (last, third, fourth, second, first):
        persist(engine, bucket)
    with SqlAlchemyPantryUnitOfWork(engine) as scope:
        assert scope.items.list_available_for_ingredient_fefo(hid, fid) == [
            first,
            second,
            third,
            fourth,
            last,
        ]
        assert scope.items.list_expiring(hid, date(2026, 9, 10)) == [
            first,
            second,
            third,
        ]
        assert scope.items.decrease_quantity_if_sufficient(
            hid,
            first.id,
            first.quantity,
            expected_quantity=first.quantity,
            updated_at=NOW,
        )
        scope.movements.add(movement(first, movement_type="CONSUMPTION"))
        scope.commit()
    with SqlAlchemyPantryReadScope(engine) as scope:
        assert len(scope.items.list_items(hid)) == 4
        assert len(scope.items.list_items(hid, include_empty=True)) == 5
        assert scope.items.get(hid, first.id).quantity == 0


@pytest.mark.parametrize(
    "change",
    [{"food_ingredient_id": uuid4()}, {"household_id": uuid4()}, {"unit": "g"}],
)
def test_item_references_and_default_unit_are_guarded(pantry_store, change):
    _, engine, hid, _, fid = pantry_store
    with pytest.raises(PantryPersistenceConflictError), SqlAlchemyPantryUnitOfWork(
        engine
    ) as scope:
        scope.items.add(item(hid, fid, **change))


def test_inactive_ingredient_rejects_new_stock_preserves_history(pantry_store):
    _, engine, hid, _, fid = pantry_store
    bucket = item(hid, fid)
    persist(engine, bucket)
    with SqlAlchemyPantryUnitOfWork(engine) as scope:
        scope.food_ingredients.set_active(fid, active=False, updated_at=NOW)
        scope.commit()
    with pytest.raises(PantryPersistenceConflictError), SqlAlchemyPantryUnitOfWork(
        engine
    ) as scope:
        scope.items.add(item(hid, fid))
    with SqlAlchemyPantryReadScope(engine) as scope:
        assert scope.items.get(hid, bucket.id) == bucket
        assert len(scope.movements.list_for_item(hid, bucket.id)) == 1


@pytest.mark.parametrize(
    "change", [{"household_id": uuid4()}, {"unit": "g"}, {"pantry_item_id": uuid4()}]
)
def test_movement_composite_ownership_and_unit_guard(pantry_store, change):
    _, engine, hid, other, fid = pantry_store
    bucket = item(hid, fid)
    persist(engine, bucket)
    if "household_id" in change:
        change = {"household_id": other}
    with pytest.raises(PantryPersistenceConflictError), SqlAlchemyPantryUnitOfWork(
        engine
    ) as scope:
        scope.movements.add(movement(bucket, **change))


@pytest.mark.parametrize(
    "command",
    [
        "UPDATE pantry_movements SET quantity=quantity",
        "DELETE FROM pantry_movements",
        "UPDATE pantry_items SET unit='g'",
        "DELETE FROM pantry_items",
    ],
)
def test_database_immutability_guards(pantry_store, command):
    config, engine, hid, _, fid = pantry_store
    persist(engine, item(hid, fid))
    with sqlite3.connect(config.path) as connection, pytest.raises(
        sqlite3.IntegrityError
    ):
        connection.execute(command)


def test_create_and_initial_movement_failure_rolls_back_both(pantry_store):
    _, engine, hid, other, fid = pantry_store
    bucket = item(hid, fid)
    with pytest.raises(PantryPersistenceConflictError), SqlAlchemyPantryUnitOfWork(
        engine
    ) as scope:
        scope.items.add(bucket)
        scope.movements.add(movement(bucket, household_id=other))
        scope.commit()
    with SqlAlchemyPantryReadScope(engine) as scope:
        assert scope.items.get(hid, bucket.id) is None
        assert scope.movements.list_for_item(hid, bucket.id) == []


def test_multi_item_and_movement_writes_roll_back_on_failure(pantry_store):
    _, engine, hid, _, fid = pantry_store
    buckets = [item(hid, fid), item(hid, fid)]
    for bucket in buckets:
        persist(engine, bucket)
    with pytest.raises(RuntimeError, match="failure"), SqlAlchemyPantryUnitOfWork(
        engine
    ) as scope:
        for bucket in buckets:
            assert scope.items.decrease_quantity_if_sufficient(
                hid,
                bucket.id,
                Decimal("4"),
                expected_quantity=bucket.quantity,
                updated_at=NOW,
            )
            scope.movements.add(
                movement(bucket, quantity="4", movement_type="CONSUMPTION")
            )
        raise RuntimeError("service failure")
    with SqlAlchemyPantryReadScope(engine) as scope:
        for bucket in buckets:
            assert scope.items.get(hid, bucket.id) == bucket
            assert len(scope.movements.list_for_item(hid, bucket.id)) == 1


@pytest.mark.parametrize("operation", ["commit", "rollback"])
def test_terminal_repository_handles(pantry_store, operation):
    _, engine, hid, _, fid = pantry_store
    bucket = item(hid, fid)
    scope = SqlAlchemyPantryUnitOfWork(engine)
    with scope:
        retained = scope.items
        scope.items.add(bucket)
        scope.movements.add(movement(bucket))
        getattr(scope, operation)()
        assert_revoked(scope, retained, hid, bucket.id)
    with SqlAlchemyPantryReadScope(engine) as read:
        assert (read.items.get(hid, bucket.id) is not None) == (operation == "commit")


def test_failed_commit_discards_actual_pantry_writes_and_later_command_is_clean(
    pantry_store,
):
    _, engine, hid, _, fid = pantry_store
    bucket = item(hid, fid)
    scope = SqlAlchemyPantryUnitOfWork(engine)
    with pytest.raises(PantryPersistenceConflictError), scope:
        retained = scope.items
        scope.items.add(bucket)
        scope.movements.add(movement(bucket))
        scope._scope.adapter_connection.execute(
            child_table.insert().values(id=1, parent_id=999)
        )
        scope.commit()
    assert_revoked(scope, retained, hid, bucket.id)
    with SqlAlchemyPantryReadScope(engine) as read:
        assert read.items.get(hid, bucket.id) is None
        assert read.movements.list_for_item(hid, bucket.id) == []
    persist(engine, bucket)


def test_failed_rollback_discards_actual_pantry_writes_and_later_command_is_clean(
    pantry_store,
):
    _, engine, hid, _, fid = pantry_store
    bucket = item(hid, fid)
    scope = SqlAlchemyPantryUnitOfWork(engine)

    def fail(connection):
        raise RuntimeError("simulated rollback failure")

    with pytest.raises(RuntimeError, match="simulated rollback failure"), scope:
        retained = scope.items
        scope.items.add(bucket)
        scope.movements.add(movement(bucket))
        event.listen(engine, "rollback", fail, once=True)
        scope.rollback()
    assert_revoked(scope, retained, hid, bucket.id)
    with SqlAlchemyPantryReadScope(engine) as read:
        assert read.items.get(hid, bucket.id) is None
        assert read.movements.list_for_item(hid, bucket.id) == []
    persist(engine, bucket)


@pytest.mark.parametrize(
    "column,value",
    [
        ("quantity", "-1.000"),
        ("quantity", "NaN"),
        ("quantity", "Infinity"),
        ("quantity", "1e3"),
        ("quantity", "1.000x"),
        ("quantity", "1.0000"),
        ("quantity", "01.000"),
        ("quantity", "1000000000000.000"),
        ("location", "OTHER"),
        ("estimated", 2),
        ("purchased_on", "2026-02-30"),
        ("opened_on", "2026-01-01T00:00:00Z"),
        ("expires_on", "2026-13-01"),
        ("updated_at", "2026-09-06 25:00:00.000000"),
        ("updated_at", "2026-09-06T12:00:00.000000+03:00"),
    ],
)
def test_sqlite_rejects_invalid_stock_facts(pantry_store, column, value):
    config, engine, hid, _, fid = pantry_store
    persist(engine, item(hid, fid))
    with sqlite3.connect(config.path) as connection, pytest.raises(
        sqlite3.IntegrityError
    ):
        connection.execute(f"UPDATE pantry_items SET {column}=?", (value,))


def test_cas_across_independent_scopes_rejects_stale_quantity(pantry_store):
    _, engine, hid, _, fid = pantry_store
    bucket = item(hid, fid)
    persist(engine, bucket)
    with SqlAlchemyPantryReadScope(engine) as reader:
        stale = reader.items.get(hid, bucket.id)
    with SqlAlchemyPantryUnitOfWork(engine) as writer:
        assert writer.items.decrease_quantity_if_sufficient(
            hid,
            bucket.id,
            Decimal("7"),
            expected_quantity=stale.quantity,
            updated_at=NOW,
        )
        writer.movements.add(
            movement(bucket, quantity="7", movement_type="CONSUMPTION")
        )
        writer.commit()
    with SqlAlchemyPantryUnitOfWork(engine) as later:
        assert not later.items.decrease_quantity_if_sufficient(
            hid,
            bucket.id,
            Decimal("7"),
            expected_quantity=stale.quantity,
            updated_at=NOW,
        )
        later.commit()
    with SqlAlchemyPantryReadScope(engine) as reader:
        assert reader.items.get(hid, bucket.id).quantity == Decimal("3.000")
        assert len(reader.movements.list_for_item(hid, bucket.id)) == 2


def test_overlapping_sqlite_writer_fails_closed_and_no_partial_movement(pantry_store):
    _, engine, hid, _, fid = pantry_store
    bucket = item(hid, fid)
    persist(engine, bucket)
    with SqlAlchemyPantryUnitOfWork(engine) as first:
        with SqlAlchemyPantryUnitOfWork(engine) as second:
            snapshot = second.items.get(hid, bucket.id)
            assert first.items.decrease_quantity_if_sufficient(
                hid,
                bucket.id,
                Decimal("7"),
                expected_quantity=bucket.quantity,
                updated_at=NOW,
            )
            first.movements.add(
                movement(bucket, quantity="7", movement_type="CONSUMPTION")
            )
            second._scope.adapter_connection.exec_driver_sql("PRAGMA busy_timeout=1")
            with pytest.raises(PantryPersistenceConflictError):
                second.items.decrease_quantity_if_sufficient(
                    hid,
                    bucket.id,
                    Decimal("7"),
                    expected_quantity=snapshot.quantity,
                    updated_at=NOW,
                )
        first.commit()
    with SqlAlchemyPantryReadScope(engine) as scope:
        assert scope.items.get(hid, bucket.id).quantity == Decimal("3.000")
        assert len(scope.movements.list_for_item(hid, bucket.id)) == 2


@pytest.mark.parametrize("operation", ["commit", "rollback"])
def test_retained_insufficient_decrease_handle_is_terminal(pantry_store, operation):
    _, engine, hid, _, fid = pantry_store
    bucket = item(hid, fid)
    with SqlAlchemyPantryUnitOfWork(engine) as scope:
        retained = scope.items
        getattr(scope, operation)()
        with pytest.raises(ResourceClosedError):
            retained.decrease_quantity_if_sufficient(
                hid,
                bucket.id,
                Decimal("10"),
                expected_quantity=Decimal("0"),
                updated_at=NOW,
            )


@pytest.mark.parametrize(
    "table,changes",
    [
        ("pantry_items", {"id": "g" * 32}),
        ("pantry_items", {"id": "00000000000010008000000000000000"}),
        ("pantry_items", {"quantity": "0.000"}),
        ("pantry_items", {"unit": "kg"}),
        ("pantry_movements", {"id": "g" * 32}),
        ("pantry_movements", {"quantity": "0.000"}),
        ("pantry_movements", {"quantity": "-1.000"}),
        ("pantry_movements", {"movement_type": "OUT"}),
        ("pantry_movements", {"unit": "kg"}),
        ("pantry_movements", {"occurred_at": "2026-09-06 12:00:01.000000Z"}),
    ],
)
def test_database_insert_guards_own_identifiers_initial_balance_and_movements(
    pantry_store, table, changes
):
    config, engine, hid, _, fid = pantry_store
    persist(engine, item(hid, fid))
    with sqlite3.connect(config.path) as connection:
        connection.execute("PRAGMA foreign_keys=ON")
        connection.row_factory = sqlite3.Row
        values = dict(connection.execute(f"SELECT * FROM {table}").fetchone())
        values.update(id=uuid4().hex)
        values.update(changes)
        columns = ",".join(values)
        placeholders = ",".join("?" for _ in values)
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                f"INSERT INTO {table} ({columns}) VALUES ({placeholders})",
                tuple(values.values()),
            )


def test_fefo_equal_date_ties_use_creation_then_uuid(pantry_store):
    _, engine, hid, _, fid = pantry_store
    earlier = item(hid, fid, created_at=NOW.replace(hour=10))
    tied = [item(hid, fid), item(hid, fid)]
    for bucket in reversed([earlier, *tied]):
        persist(engine, bucket)
    with SqlAlchemyPantryReadScope(engine) as scope:
        assert scope.items.list_available_for_ingredient_fefo(hid, fid) == [
            earlier,
            *sorted(tied, key=lambda bucket: bucket.id),
        ]
