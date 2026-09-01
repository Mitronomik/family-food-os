import sqlite3
from dataclasses import replace
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import Column, ForeignKey, Integer, MetaData, Table, event

from app.db.config import DatabaseConfig
from app.db.migrations import apply_migrations
from app.domain.households import Household, HouseholdMember
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
from app.persistence.sqlalchemy_core.household_uow import (
    SqlAlchemyHouseholdReadScope,
    SqlAlchemyHouseholdUnitOfWork,
)
from app.services.household_contracts import HouseholdPersistenceConflictError

NOW = datetime(2026, 9, 1, 10, 0, 0, 123456, tzinfo=timezone.utc)

terminality_metadata = MetaData()
deferred_parent_table = Table(
    "household_uow_deferred_parent",
    terminality_metadata,
    Column("id", Integer, primary_key=True),
)
deferred_child_table = Table(
    "household_uow_deferred_child",
    terminality_metadata,
    Column("id", Integer, primary_key=True),
    Column(
        "parent_id",
        Integer,
        ForeignKey(
            deferred_parent_table.c.id,
            deferrable=True,
            initially="DEFERRED",
        ),
        nullable=False,
    ),
)


@pytest.fixture
def household_engine(tmp_path):
    config = DatabaseConfig(path=tmp_path / "households.sqlite")
    apply_migrations(config)
    engine = create_sqlite_engine(config)
    with engine.begin() as connection:
        deferred_parent_table.create(connection)
        deferred_child_table.create(connection)
    try:
        yield config, engine
    finally:
        engine.dispose()


def household(**overrides):
    values = {
        "id": uuid4(),
        "name": "Home",
        "timezone": "Europe/Moscow",
        "city": "Saint Petersburg",
        "default_weekly_budget": Decimal("12345.67"),
        "default_cooking_profile": "easy_week",
        "created_at": NOW,
        "updated_at": NOW,
    }
    values.update(overrides)
    return Household(**values)


def member(household_id, **overrides):
    values = {
        "id": uuid4(),
        "household_id": household_id,
        "name": "Anna",
        "active": True,
        "birth_date": date(1990, 5, 20),
        "sex": "female",
        "height_cm": Decimal("168.2"),
        "weight_kg": Decimal("62.346"),
        "activity_level": "moderate",
        "goal": "maintain",
        "created_at": NOW,
        "updated_at": NOW,
    }
    values.update(overrides)
    return HouseholdMember(**values)


def test_household_uuid_utc_and_decimal_roundtrip(household_engine):
    config, engine = household_engine
    expected = household()

    with SqlAlchemyHouseholdUnitOfWork(engine) as scope:
        scope.households.add_household(expected)
        scope.commit()

    with SqlAlchemyHouseholdReadScope(engine) as scope:
        actual = scope.households.get_household(expected.id)

    assert actual == expected
    assert actual is not None
    assert actual.id.version == 4
    assert actual.created_at.tzinfo is timezone.utc
    assert actual.default_weekly_budget == Decimal("12345.67")
    with sqlite3.connect(config.path) as connection:
        stored = connection.execute(
            "SELECT id, default_weekly_budget FROM households WHERE id = ?",
            (expected.id.hex,),
        ).fetchone()
    assert stored == (expected.id.hex, "12345.67")


def test_household_create_read_and_update(household_engine):
    _, engine = household_engine
    original = household()
    changed = replace(
        original,
        name="Updated Home",
        city=None,
        default_weekly_budget=Decimal("9000.00"),
        updated_at=NOW + timedelta(hours=1),
    )

    with SqlAlchemyHouseholdUnitOfWork(engine) as scope:
        scope.households.add_household(original)
        scope.commit()
    with SqlAlchemyHouseholdUnitOfWork(engine) as scope:
        scope.households.update_household(changed)
        scope.commit()
    with SqlAlchemyHouseholdReadScope(engine) as scope:
        assert scope.households.get_household(original.id) == changed


def test_member_create_read_update_list_and_household_scope(household_engine):
    _, engine = household_engine
    first = household(name="First")
    second = household(name="Second")
    first_member = member(first.id, name="Anna")
    second_member = member(second.id, name="Boris")

    with SqlAlchemyHouseholdUnitOfWork(engine) as scope:
        scope.households.add_household(first)
        scope.households.add_household(second)
        scope.members.add_member(first_member)
        scope.members.add_member(second_member)
        scope.commit()

    changed = replace(
        first_member,
        name="Anna Updated",
        active=False,
        updated_at=NOW + timedelta(minutes=1),
    )
    with SqlAlchemyHouseholdUnitOfWork(engine) as scope:
        scope.members.update_member(changed)
        scope.commit()

    with SqlAlchemyHouseholdReadScope(engine) as scope:
        assert scope.members.get_member(first.id, first_member.id) == changed
        assert scope.members.get_member(second.id, first_member.id) is None
        assert scope.members.list_members(first.id) == [changed]
        assert scope.members.list_members(second.id) == [second_member]


def test_foreign_key_failure_is_translated_at_adapter_boundary(household_engine):
    _, engine = household_engine
    orphan = member(uuid4())

    with pytest.raises(HouseholdPersistenceConflictError) as exc_info:
        with SqlAlchemyHouseholdUnitOfWork(engine) as scope:
            scope.members.add_member(orphan)
            scope.commit()

    assert "Household link conflicts" in str(exc_info.value)
    assert exc_info.value.__cause__ is not None


def test_repositories_do_not_commit_and_uncommitted_writes_are_rolled_back(
    household_engine,
):
    _, engine = household_engine
    uncommitted = household()

    with SqlAlchemyHouseholdUnitOfWork(engine) as scope:
        scope.households.add_household(uncommitted)

    with SqlAlchemyHouseholdReadScope(engine) as scope:
        assert scope.households.get_household(uncommitted.id) is None


def test_failed_multi_repository_uow_leaves_no_partial_state(household_engine):
    _, engine = household_engine
    expected_household = household()
    expected_member = member(expected_household.id)

    with pytest.raises(RuntimeError, match="simulated command failure"):
        with SqlAlchemyHouseholdUnitOfWork(engine) as scope:
            scope.households.add_household(expected_household)
            scope.members.add_member(expected_member)
            raise RuntimeError("simulated command failure")

    with SqlAlchemyHouseholdReadScope(engine) as scope:
        assert scope.households.get_household(expected_household.id) is None
        assert scope.members.list_members(expected_household.id) == []


def test_committed_uow_is_visible_to_independent_later_read_scope(household_engine):
    _, engine = household_engine
    expected_household = household()
    expected_member = member(expected_household.id)

    with SqlAlchemyHouseholdUnitOfWork(engine) as scope:
        scope.households.add_household(expected_household)
        scope.members.add_member(expected_member)
        scope.commit()

    with SqlAlchemyHouseholdReadScope(engine) as independent_scope:
        assert (
            independent_scope.households.get_household(expected_household.id)
            == expected_household
        )
        assert independent_scope.members.list_members(expected_household.id) == [
            expected_member
        ]


def test_read_scope_has_no_commit_operation(household_engine):
    _, engine = household_engine

    with SqlAlchemyHouseholdReadScope(engine) as scope:
        assert not hasattr(scope, "commit")


def assert_household_repositories_revoked(scope):
    with pytest.raises(RuntimeError, match="not active"):
        _ = scope.households
    with pytest.raises(RuntimeError, match="not active"):
        _ = scope.members


def test_successful_commit_revokes_household_repositories(household_engine):
    _, engine = household_engine
    expected = household()
    scope = SqlAlchemyHouseholdUnitOfWork(engine)

    with scope:
        retained_connection = scope._scope.adapter_connection
        scope.households.add_household(expected)
        scope.commit()
        assert retained_connection.closed
        assert_household_repositories_revoked(scope)

    with SqlAlchemyHouseholdReadScope(engine) as read_scope:
        assert read_scope.households.get_household(expected.id) == expected


def test_successful_rollback_revokes_household_repositories(household_engine):
    _, engine = household_engine
    discarded = household()
    scope = SqlAlchemyHouseholdUnitOfWork(engine)

    with scope:
        retained_connection = scope._scope.adapter_connection
        scope.households.add_household(discarded)
        scope.rollback()
        assert retained_connection.closed
        assert_household_repositories_revoked(scope)

    with SqlAlchemyHouseholdReadScope(engine) as read_scope:
        assert read_scope.households.get_household(discarded.id) is None


def test_failed_commit_revokes_repositories_and_later_uow_is_clean(
    household_engine,
):
    _, engine = household_engine
    scope = SqlAlchemyHouseholdUnitOfWork(engine)

    with pytest.raises(HouseholdPersistenceConflictError) as exc_info:
        with scope:
            retained_connection = scope._scope.adapter_connection
            retained_connection.execute(
                deferred_child_table.insert().values(id=1, parent_id=999)
            )
            scope.commit()

    assert exc_info.value.__cause__ is not None
    assert retained_connection.closed
    assert_household_repositories_revoked(scope)

    expected = household()
    with SqlAlchemyHouseholdUnitOfWork(engine) as later_scope:
        later_scope.households.add_household(expected)
        later_scope.commit()
    with SqlAlchemyHouseholdReadScope(engine) as read_scope:
        assert read_scope.households.get_household(expected.id) == expected


def test_failed_rollback_revokes_repositories_and_later_uow_is_clean(
    household_engine,
):
    _, engine = household_engine
    scope = SqlAlchemyHouseholdUnitOfWork(engine)
    discarded = household()

    def fail_rollback(connection):
        del connection
        raise RuntimeError("simulated rollback failure")

    with pytest.raises(RuntimeError, match="simulated rollback failure"):
        with scope:
            retained_connection = scope._scope.adapter_connection
            scope.households.add_household(discarded)
            event.listen(engine, "rollback", fail_rollback, once=True)
            scope.rollback()

    assert retained_connection.closed
    assert_household_repositories_revoked(scope)

    expected = household()
    with SqlAlchemyHouseholdUnitOfWork(engine) as later_scope:
        later_scope.households.add_household(expected)
        later_scope.commit()
    with SqlAlchemyHouseholdReadScope(engine) as read_scope:
        assert read_scope.households.get_household(discarded.id) is None
        assert read_scope.households.get_household(expected.id) == expected


def test_inactive_commit_programming_error_is_not_wrapped(household_engine):
    _, engine = household_engine
    scope = SqlAlchemyHouseholdUnitOfWork(engine)

    with pytest.raises(RuntimeError, match="no active transaction"):
        scope.commit()

    assert_household_repositories_revoked(scope)
