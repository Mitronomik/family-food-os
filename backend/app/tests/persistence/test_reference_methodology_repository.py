import sqlite3
from dataclasses import replace
from datetime import date, datetime, timedelta, timezone
from uuid import uuid4

import pytest

from app.db.config import DatabaseConfig
from app.db.migrations import apply_migrations
from app.domain.households import Household, HouseholdMember
from app.domain.reference_methodology import MemberReferenceMethodologySelection
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
from app.persistence.sqlalchemy_core.household_uow import SqlAlchemyHouseholdUnitOfWork
from app.persistence.sqlalchemy_core.reference_methodology_uow import (
    SqlAlchemyReferenceMethodologyReadScope,
    SqlAlchemyReferenceMethodologyUnitOfWork,
)
from app.services.reference_methodology_contracts import (
    ReferenceMethodologyPersistenceConflictError,
)


NOW = datetime(2026, 9, 23, 10, 0, tzinfo=timezone.utc)


@pytest.fixture
def database(tmp_path):
    config = DatabaseConfig(path=tmp_path / "reference-methodology.sqlite")
    apply_migrations(config)
    engine = create_sqlite_engine(config)
    try:
        yield config, engine
    finally:
        engine.dispose()


def household(name="Home"):
    return Household(
        id=uuid4(),
        name=name,
        timezone="Europe/Moscow",
        city=None,
        default_weekly_budget=None,
        default_cooking_profile=None,
        created_at=NOW,
        updated_at=NOW,
    )


def member(household_id, name="Anna"):
    return HouseholdMember(
        id=uuid4(),
        household_id=household_id,
        name=name,
        active=True,
        birth_date=date(1990, 5, 20),
        sex="female",
        height_cm=None,
        weight_kg=None,
        activity_level="moderate",
        goal="maintain",
        created_at=NOW,
        updated_at=NOW,
    )


def selection(home, person, *, version=1, supersedes=None, request_id=None):
    return MemberReferenceMethodologySelection(
        id=uuid4(),
        household_id=home.id,
        member_id=person.id,
        version_number=version,
        nutrition_config_version="FAMILY_FOOD_NUTRITION_V1",
        group_reference_methodology_version=None,
        accepted_local_date=date(2026, 9, 23),
        household_timezone_at_acceptance=home.timezone,
        member_updated_at_at_acceptance=person.updated_at,
        household_updated_at_at_acceptance=home.updated_at,
        acceptance_request_id=request_id or uuid4(),
        accepted_at=NOW,
        supersedes_selection_id=supersedes,
        created_at=NOW,
    )


def seed_member(engine, home, person):
    with SqlAlchemyHouseholdUnitOfWork(engine) as scope:
        scope.households.add_household(home)
        scope.members.add_member(person)
        scope.commit()


def test_roundtrip_current_request_lookup_and_history(database):
    _, engine = database
    home = household()
    person = member(home.id)
    seed_member(engine, home, person)
    first = selection(home, person)
    second = selection(
        home,
        person,
        version=2,
        supersedes=first.id,
    )

    with SqlAlchemyReferenceMethodologyUnitOfWork(engine) as scope:
        scope.selections.add(first)
        scope.commit()
    with SqlAlchemyReferenceMethodologyUnitOfWork(engine) as scope:
        scope.selections.add(second)
        scope.commit()

    with SqlAlchemyReferenceMethodologyReadScope(engine) as scope:
        assert scope.selections.get(home.id, first.id) == first
        assert (
            scope.selections.get_by_request_id(
                home.id, person.id, second.acceptance_request_id
            )
            == second
        )
        assert scope.selections.get_current(home.id, person.id) == second
        assert scope.selections.list_history(home.id, person.id) == [
            first,
            second,
        ]


def test_repository_rejects_cross_household_member_and_invalid_chain(database):
    _, engine = database
    first_home, second_home = household("A"), household("B")
    person = member(first_home.id)
    with SqlAlchemyHouseholdUnitOfWork(engine) as scope:
        scope.households.add_household(first_home)
        scope.households.add_household(second_home)
        scope.members.add_member(person)
        scope.commit()

    cross_scope = MemberReferenceMethodologySelection(
        **{
            **selection(first_home, person).__dict__,
            "id": uuid4(),
            "household_id": second_home.id,
            "acceptance_request_id": uuid4(),
        }
    )
    with pytest.raises(ReferenceMethodologyPersistenceConflictError):
        with SqlAlchemyReferenceMethodologyUnitOfWork(engine) as scope:
            scope.selections.add(cross_scope)

    invalid_v2 = selection(first_home, person, version=2, supersedes=None)
    with pytest.raises(ReferenceMethodologyPersistenceConflictError):
        with SqlAlchemyReferenceMethodologyUnitOfWork(engine) as scope:
            scope.selections.add(invalid_v2)


def test_duplicate_request_identity_conflicts_and_rolls_back(database):
    _, engine = database
    home = household()
    person = member(home.id)
    seed_member(engine, home, person)
    request_id = uuid4()
    first = selection(home, person, request_id=request_id)
    second = selection(
        home,
        person,
        version=2,
        supersedes=first.id,
        request_id=request_id,
    )

    with SqlAlchemyReferenceMethodologyUnitOfWork(engine) as scope:
        scope.selections.add(first)
        scope.commit()

    with pytest.raises(ReferenceMethodologyPersistenceConflictError):
        with SqlAlchemyReferenceMethodologyUnitOfWork(engine) as scope:
            scope.selections.add(second)

    with SqlAlchemyReferenceMethodologyReadScope(engine) as scope:
        assert scope.selections.list_history(home.id, person.id) == [first]


def test_uncommitted_selection_rolls_back(database):
    _, engine = database
    home = household()
    person = member(home.id)
    seed_member(engine, home, person)
    value = selection(home, person)

    with SqlAlchemyReferenceMethodologyUnitOfWork(engine) as scope:
        scope.selections.add(value)

    with SqlAlchemyReferenceMethodologyReadScope(engine) as scope:
        assert scope.selections.get(home.id, value.id) is None


def test_database_triggers_make_selection_history_immutable(database):
    config, engine = database
    home = household()
    person = member(home.id)
    seed_member(engine, home, person)
    value = selection(home, person)
    with SqlAlchemyReferenceMethodologyUnitOfWork(engine) as scope:
        scope.selections.add(value)
        scope.commit()

    with sqlite3.connect(config.path) as connection:
        with pytest.raises(sqlite3.IntegrityError, match="immutable"):
            connection.execute(
                """
                UPDATE member_reference_methodology_selections
                SET nutrition_config_version = 'changed'
                WHERE id = ?
                """,
                (value.id.hex,),
            )
        connection.rollback()
        with pytest.raises(sqlite3.IntegrityError, match="immutable"):
            connection.execute(
                "DELETE FROM member_reference_methodology_selections WHERE id = ?",
                (value.id.hex,),
            )


def test_real_sqlite_concurrent_member_writer_is_conflict_for_state_guard(database):
    _, engine = database
    home = household()
    person = member(home.id)
    seed_member(engine, home, person)

    with SqlAlchemyReferenceMethodologyUnitOfWork(engine) as acceptance_scope:
        accepted_home = acceptance_scope.households.get_household(home.id)
        accepted_member = acceptance_scope.members.get_member(home.id, person.id)
        assert accepted_home is not None
        assert accepted_member is not None

        with SqlAlchemyHouseholdUnitOfWork(engine) as concurrent_scope:
            concurrent_connection = concurrent_scope._scope.adapter_connection
            concurrent_connection.exec_driver_sql("PRAGMA busy_timeout = 50")
            changed_member = replace(
                person,
                goal="lose_weight",
                updated_at=NOW + timedelta(minutes=1),
            )
            concurrent_scope.members.update_member(changed_member)

            acceptance_scope._scope.adapter_connection.exec_driver_sql(
                "PRAGMA busy_timeout = 50"
            )
            with pytest.raises(
                ReferenceMethodologyPersistenceConflictError,
                match="concurrently being changed",
            ):
                acceptance_scope.revalidate_authoritative_state(
                    household_id=home.id,
                    household_updated_at=accepted_home.updated_at,
                    member_id=person.id,
                    member_updated_at=accepted_member.updated_at,
                )

    with SqlAlchemyReferenceMethodologyReadScope(engine) as read_scope:
        assert read_scope.selections.list_history(home.id, person.id) == []
