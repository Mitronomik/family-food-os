"""Persisted non-medical member ingredient exclusions and Planner admission."""

from dataclasses import replace
from uuid import uuid4

import pytest

from app.db.config import DatabaseConfig
from app.db.migrations import MIGRATION_MODULES, apply_migrations, expected_migration_ids
from app.persistence.sqlalchemy_core.food_ingredient_composition import (
    create_food_catalogue_service,
)
from app.persistence.sqlalchemy_core.household_composition import create_household_service
from app.persistence.sqlalchemy_core.household_uow import SqlAlchemyHouseholdReadScope
from app.services.household_contracts import HouseholdPersistenceConflictError
from app.services.households import (
    HouseholdExclusionInputError,
    HouseholdMemberNotFoundError,
)
from app.services.planner import PlannerService
from app.tests.test_prep_read_only_integration import WEEK, _db_dump
from app.tests.test_r2c_breakfast_grain_diversity import meal_plan_service
from app.persistence.sqlalchemy_core.food_recipe_composition import (
    create_food_recipe_catalogue_service,
)
from app.persistence.sqlalchemy_core.nutrition_composition import create_nutrition_service
from app.persistence.sqlalchemy_core.pantry_composition import create_pantry_service
from app.persistence.sqlalchemy_core.recipe_nutrition_v2 import (
    create_recipe_nutrition_v2_service,
)

pytest_plugins = ("app.tests.test_prep_read_only_integration",)


def _planner(engine):
    return PlannerService(
        meal_plan_service(engine),
        create_household_service(engine),
        create_food_recipe_catalogue_service(engine),
        create_nutrition_service(engine),
        create_pantry_service(engine),
        recipe_nutrition=create_recipe_nutrition_v2_service(engine),
    )


def test_persisted_exclusions_are_automatic_and_caller_can_only_add(scenario):
    config, engine, _, witness, _ = scenario
    household = witness.command.household_id
    a, b = (entry.member_id for entry in witness.command.members)
    food = create_food_catalogue_service(engine).get_by_code("BEEF_CATEGORY_1_RAW")
    assert food.id in witness.command.members[1].excluded_food_ingredient_ids
    service = create_household_service(engine)
    empty = frozenset()
    assert service.list_member_excluded_food_ids(household, a) == empty
    assert service.replace_member_excluded_food_ids(
        household, a, expected=empty, selected=frozenset({food.id})
    )
    assert service.list_member_excluded_food_ids(household, a) == frozenset({food.id})
    assert service.list_member_excluded_food_ids(household, b) == empty

    plain = replace(
        witness.command,
        members=tuple(replace(member, excluded_food_ingredient_ids=empty)
                      for member in witness.command.members),
    )
    composed = _planner(engine).compose_authoritative_request(plain)
    assert all(food.id in member.excluded_food_ingredient_ids for member in composed.members
               if member.member_id == a)
    assert any(not member.excluded_food_ingredient_ids for member in composed.members
               if member.member_id == b)
    more = create_food_catalogue_service(engine).get_by_code("CARROT")
    supplemented = replace(
        plain,
        members=tuple(replace(member, excluded_food_ingredient_ids=frozenset({more.id}))
                      if member.member_id == a else member
                      for member in plain.members),
    )
    result = _planner(engine).compose_authoritative_request(supplemented)
    assert next(member for member in result.members if member.member_id == a).excluded_food_ingredient_ids == frozenset({food.id, more.id})


def test_atomic_replace_replay_stale_snapshot_and_cross_household(scenario):
    config, engine, households, witness, _ = scenario
    hid = witness.command.household_id
    member = witness.command.members[0].member_id
    food = create_food_catalogue_service(engine).get_by_code("CARROT").id
    service = create_household_service(engine)
    original = _db_dump(config)
    assert service.replace_member_excluded_food_ids(
        hid, member, expected=frozenset(), selected=frozenset()
    ) is False
    assert _db_dump(config) == original
    assert service.replace_member_excluded_food_ids(
        hid, member, expected=frozenset(), selected=frozenset({food})
    ) is True
    current = _db_dump(config)
    assert service.replace_member_excluded_food_ids(
        hid, member, expected=frozenset({food}), selected=frozenset({food})
    ) is False
    assert _db_dump(config) == current
    with pytest.raises(HouseholdPersistenceConflictError, match="changed"):
        service.replace_member_excluded_food_ids(
            hid, member, expected=frozenset(), selected=frozenset()
        )
    with pytest.raises(HouseholdMemberNotFoundError):
        service.list_member_excluded_food_ids(uuid4(), member)
    other = households.create_household(name="Другая семья", timezone_name="Europe/Moscow")
    with pytest.raises(HouseholdMemberNotFoundError):
        service.replace_member_excluded_food_ids(
            other.id, member, expected=frozenset(), selected=frozenset({food})
        )
    assert _db_dump(config) != original
    assert service.list_member_excluded_food_ids(hid, member) == frozenset({food})


def test_missing_inactive_and_malformed_food_ids_cannot_publish(scenario):
    config, engine, _, witness, _ = scenario
    hid = witness.command.household_id
    member = witness.command.members[0].member_id
    service = create_household_service(engine)
    before = _db_dump(config)
    with pytest.raises(HouseholdExclusionInputError):
        service.replace_member_excluded_food_ids(
            hid, member, expected=frozenset(), selected=frozenset({"CARROT"})
        )
    with pytest.raises(HouseholdPersistenceConflictError, match="missing"):
        service.replace_member_excluded_food_ids(
            hid, member, expected=frozenset(), selected=frozenset({uuid4()})
        )
    assert _db_dump(config) == before


def test_upgrade_0044_to_0045_only_adds_preferences(tmp_path):
    config = DatabaseConfig(path=tmp_path / "upgrade.sqlite")
    modules = list(MIGRATION_MODULES)
    try:
        MIGRATION_MODULES[:] = modules[:-1]
        apply_migrations(config)
    finally:
        MIGRATION_MODULES[:] = modules
    import sqlite3

    with sqlite3.connect(config.path) as db:
        old_history = tuple(db.execute(
            "SELECT migration_id FROM schema_migrations ORDER BY rowid"
        ).fetchall())
        old_household_sql = db.execute(
            "SELECT sql FROM sqlite_master WHERE name='household_members'"
        ).fetchone()[0]
    assert apply_migrations(config) == ["0045_household_member_food_exclusions"]
    assert apply_migrations(config) == []
    with sqlite3.connect(config.path) as db:
        assert db.execute("PRAGMA foreign_key_check").fetchall() == []
        assert tuple(db.execute(
            "SELECT migration_id FROM schema_migrations ORDER BY rowid"
        ).fetchall()) == (*old_history, ("0045_household_member_food_exclusions",))
        assert db.execute(
            "SELECT sql FROM sqlite_master WHERE name='household_members'"
        ).fetchone()[0] == old_household_sql
        assert db.execute(
            "SELECT COUNT(*) FROM household_member_excluded_food_ingredients"
        ).fetchone()[0] == 0
    assert expected_migration_ids()[-1] == "0045_household_member_food_exclusions"
