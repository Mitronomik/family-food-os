"""Persisted non-medical member ingredient exclusions and Planner admission."""

import sqlite3
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import timedelta
from importlib import import_module
from threading import Barrier
from uuid import uuid4

import pytest
from app.db.config import DATABASE_PATH_ENV, DatabaseConfig
from app.db.migrations import (
    MIGRATION_MODULES,
    apply_migrations,
    expected_migration_ids,
)
from app.domain.meal_plans import MealSourceKind
from app.domain.planner import PlannerSuccess
from app.main import create_app
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
from app.persistence.sqlalchemy_core.food_ingredient_composition import (
    create_food_catalogue_service,
)
from app.persistence.sqlalchemy_core.food_recipe_composition import (
    create_food_recipe_catalogue_service,
)
from app.persistence.sqlalchemy_core.household_composition import (
    create_household_service,
)
from app.persistence.sqlalchemy_core.household_uow import SqlAlchemyHouseholdUnitOfWork
from app.persistence.sqlalchemy_core.nutrition_composition import (
    create_nutrition_service,
)
from app.persistence.sqlalchemy_core.pantry_composition import create_pantry_service
from app.persistence.sqlalchemy_core.recipe_nutrition_v2 import (
    create_recipe_nutrition_v2_service,
)
from app.persistence.sqlalchemy_core.shopping_uow import SqlAlchemyShoppingReadScope
from app.persistence.sqlalchemy_core.uow import SqlAlchemyUnitOfWork
from app.services.household_contracts import (
    HouseholdPersistenceConflictError,
    HouseholdPersistenceError,
)
from app.services.households import (
    HouseholdExclusionInputError,
    HouseholdMemberNotFoundError,
    HouseholdNotFoundError,
    HouseholdService,
)
from app.services.meal_plans import MealPlanValidationError
from app.services.planner import PlannerService
from app.tests.test_prep_read_only_integration import WEEK, _db_dump
from app.tests.test_r2c_breakfast_grain_diversity import meal_plan_service
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

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

    # A new engine/scope on the same persisted SQLite file sees the same
    # canonical UUID selection; it is not memory on the Planner object.
    other_engine = create_sqlite_engine(config)
    try:
        reopened = create_household_service(other_engine)
        assert reopened.list_member_excluded_food_ids(household, a) == frozenset(
            {food.id}
        )
    finally:
        other_engine.dispose()

    plain = replace(
        witness.command,
        members=tuple(
            replace(member, excluded_food_ingredient_ids=empty)
            for member in witness.command.members
        ),
    )
    composed = _planner(engine).compose_authoritative_request(plain)
    assert all(
        food.id in member.excluded_food_ingredient_ids
        for member in composed.members
        if member.member_id == a
    )
    assert any(
        not member.excluded_food_ingredient_ids
        for member in composed.members
        if member.member_id == b
    )
    more = create_food_catalogue_service(engine).get_by_code("CARROT")
    supplemented = replace(
        plain,
        members=tuple(
            replace(member, excluded_food_ingredient_ids=frozenset({more.id}))
            if member.member_id == a
            else member
            for member in plain.members
        ),
    )
    result = _planner(engine).compose_authoritative_request(supplemented)
    assert next(
        member for member in result.members if member.member_id == a
    ).excluded_food_ingredient_ids == frozenset({food.id, more.id})


def test_next_week_persisted_mealplan_excludes_selected_food_in_every_serving(
    scenario,
):
    """Prove the saved second-week RecipeVersion ingredients, not just request."""
    config, engine, _, witness, _ = scenario
    household = witness.command.household_id
    member_a, member_b = (member.member_id for member in witness.command.members)
    beef = create_food_catalogue_service(engine).get_by_code("BEEF_CATEGORY_1_RAW")
    assert beef is not None
    household_service = create_household_service(engine)
    assert household_service.replace_member_excluded_food_ids(
        household, member_a, expected=frozenset(), selected=frozenset({beef.id})
    )
    next_week = WEEK + timedelta(days=7)
    command = replace(
        witness.command,
        week_start=next_week,
        fixed_events=(),
        members=tuple(
            replace(member, excluded_food_ingredient_ids=frozenset())
            for member in witness.command.members
        ),
    )
    result, saved = _planner(engine).generate_authoritative(command)
    assert isinstance(result, PlannerSuccess)
    assert saved is not None
    assert saved.plan.week_start == next_week
    with SqlAlchemyShoppingReadScope(engine) as scope:
        persisted = scope.plans.get_current(household, next_week)
        assert persisted == saved
        assigned = {}
        for serving in persisted.servings:
            assigned.setdefault(serving.event_id, set()).add(serving.member_id)
        checked = 0
        for event in persisted.events:
            if event.source_kind != MealSourceKind.COOK_RECIPE:
                continue
            detail = scope.recipes.get_detail(event.recipe_version_id)
            assert detail is not None
            ingredients = {row.food_ingredient_id for row in detail.ingredients}
            if member_a in assigned.get(event.id, ()):
                assert beef.id not in ingredients
                checked += 1
        assert checked > 0
    assert (
        household_service.list_member_excluded_food_ids(household, member_b)
        == frozenset()
    )


def test_changed_exclusions_after_planning_abort_new_revision_atomically(
    scenario, monkeypatch
):
    """Recreate the P1 interleaving exactly between generate_week and commit."""
    import app.services.planner as planner_module

    config, engine, _, witness, _ = scenario
    household = witness.command.household_id
    member = witness.command.members[0].member_id
    food = create_food_catalogue_service(engine).get_by_code("BEEF_CATEGORY_1_RAW")
    assert food is not None
    households = create_household_service(engine)
    next_week = WEEK + timedelta(days=7)
    command = replace(
        witness.command,
        week_start=next_week,
        fixed_events=(),
        members=tuple(
            replace(item, excluded_food_ingredient_ids=frozenset())
            for item in witness.command.members
        ),
    )
    original_generate = planner_module.generate_week
    observed = []

    def concurrent_preference_save(request, config):
        result = original_generate(request, config)
        assert isinstance(result, PlannerSuccess)
        observed.append("planned")
        assert households.replace_member_excluded_food_ids(
            household, member, expected=frozenset(), selected=frozenset({food.id})
        )
        observed.append("preference_committed")
        return result

    monkeypatch.setattr(planner_module, "generate_week", concurrent_preference_save)
    before = _db_dump(config)
    with pytest.raises(MealPlanValidationError, match="exclusions changed"):
        _planner(engine).generate_authoritative(command)
    assert observed == ["planned", "preference_committed"]
    assert households.list_member_excluded_food_ids(household, member) == frozenset(
        {food.id}
    )
    with SqlAlchemyShoppingReadScope(engine) as scope:
        assert scope.plans.get_current(household, next_week) is None
        assert scope.plans.get_current(household, WEEK) is not None
    assert before != _db_dump(config)


def test_two_independent_transactions_same_snapshot_only_one_cas_wins(scenario):
    """Both readers see empty; separate SQLite connections race to write."""
    config, engine, _, witness, _ = scenario
    household = witness.command.household_id
    member = witness.command.members[0].member_id
    food = create_food_catalogue_service(engine)
    foods = (
        food.get_by_code("CARROT").id,
        food.get_by_code("BEEF_CATEGORY_1_RAW").id,
    )
    with sqlite3.connect(config.path) as connection:
        assert connection.execute("PRAGMA journal_mode=WAL").fetchone()[0] == "wal"
    barrier = Barrier(2, timeout=10)

    def contender(selected_id):
        separate_engine = create_sqlite_engine(config)
        try:
            with SqlAlchemyHouseholdUnitOfWork(separate_engine) as scope:
                original = scope.members.list_excluded_food_ids(household, member)
                assert original == frozenset()
                barrier.wait()
                try:
                    scope.members.replace_excluded_food_ids(
                        household,
                        member,
                        expected=original,
                        selected=frozenset({selected_id}),
                    )
                    scope.commit()
                    return ("committed", selected_id)
                except HouseholdPersistenceConflictError:
                    return ("conflict", selected_id)
        finally:
            separate_engine.dispose()

    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(contender, foods[0])
        second = pool.submit(contender, foods[1])
        outcomes = (first.result(), second.result())
    winners = [food_id for state, food_id in outcomes if state == "committed"]
    assert len(winners) == 1
    assert sorted(state for state, _ in outcomes) == ["committed", "conflict"]
    assert create_household_service(engine).list_member_excluded_food_ids(
        household, member
    ) == frozenset(winners)


def test_atomic_replace_replay_stale_snapshot_and_cross_household(scenario):
    config, engine, households, witness, _ = scenario
    hid = witness.command.household_id
    member = witness.command.members[0].member_id
    food = create_food_catalogue_service(engine).get_by_code("CARROT").id
    service = create_household_service(engine)
    original = _db_dump(config)
    assert (
        service.replace_member_excluded_food_ids(
            hid, member, expected=frozenset(), selected=frozenset()
        )
        is False
    )
    assert _db_dump(config) == original
    assert (
        service.replace_member_excluded_food_ids(
            hid, member, expected=frozenset(), selected=frozenset({food})
        )
        is True
    )
    current = _db_dump(config)
    assert (
        service.replace_member_excluded_food_ids(
            hid, member, expected=frozenset({food}), selected=frozenset({food})
        )
        is False
    )
    assert _db_dump(config) == current
    with pytest.raises(HouseholdPersistenceConflictError, match="changed"):
        service.replace_member_excluded_food_ids(
            hid, member, expected=frozenset(), selected=frozenset()
        )
    with pytest.raises(HouseholdNotFoundError):
        service.list_member_excluded_food_ids(uuid4(), member)
    other = households.create_household(
        name="Другая семья", timezone_name="Europe/Moscow"
    )
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


def test_failed_insert_rolls_back_deleted_preferences(scenario):
    """An insertion failure after DELETE cannot publish a half-empty set."""
    import sqlite3

    config, engine, _, witness, _ = scenario
    household = witness.command.household_id
    member = witness.command.members[0].member_id
    food = create_food_catalogue_service(engine)
    carrot = food.get_by_code("CARROT").id
    beef = food.get_by_code("BEEF_CATEGORY_1_RAW").id
    service = create_household_service(engine)
    assert service.replace_member_excluded_food_ids(
        household, member, expected=frozenset(), selected=frozenset({carrot})
    )
    with sqlite3.connect(config.path) as connection:
        connection.execute("""
            CREATE TRIGGER reject_exclusion_insert
            BEFORE INSERT ON household_member_excluded_food_ingredients
            BEGIN SELECT RAISE(ABORT, 'injected insert failure'); END
        """)
    before = _db_dump(config)
    with pytest.raises(HouseholdPersistenceConflictError):
        service.replace_member_excluded_food_ids(
            household,
            member,
            expected=frozenset({carrot}),
            selected=frozenset({beef}),
        )
    assert service.list_member_excluded_food_ids(household, member) == frozenset(
        {carrot}
    )
    assert _db_dump(config) == before


def test_inactive_selected_food_stays_recorded_but_cannot_be_newly_added(scenario):
    config, engine, _, witness, _ = scenario
    household = witness.command.household_id
    member = witness.command.members[0].member_id
    service = create_household_service(engine)
    foods = create_food_catalogue_service(engine)
    carrot = foods.get_by_code("CARROT")
    service.replace_member_excluded_food_ids(
        household, member, expected=frozenset(), selected=frozenset({carrot.id})
    )
    foods.deactivate(carrot.id)
    assert service.list_member_excluded_food_ids(household, member) == frozenset(
        {carrot.id}
    )
    with pytest.raises(HouseholdPersistenceConflictError, match="inactive"):
        service.replace_member_excluded_food_ids(
            household,
            witness.command.members[1].member_id,
            expected=frozenset(),
            selected=frozenset({carrot.id}),
        )


def test_upgrade_0044_to_0045_only_adds_preferences(tmp_path):
    config = DatabaseConfig(path=tmp_path / "upgrade.sqlite")
    modules = list(MIGRATION_MODULES)
    try:
        MIGRATION_MODULES[:] = modules[:-1]
        apply_migrations(config)
    finally:
        MIGRATION_MODULES[:] = modules
    import sqlite3

    household_id = "1" * 32
    member_id = "2" * 32
    with sqlite3.connect(config.path) as db:
        db.execute("PRAGMA foreign_keys=ON")
        db.execute(
            "INSERT INTO households "
            "(id, name, timezone, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            (
                household_id,
                "Историческая семья",
                "Europe/Moscow",
                "2026-11-01T00:00:00Z",
                "2026-11-01T00:00:00Z",
            ),
        )
        db.execute(
            "INSERT INTO household_members "
            "(id, household_id, name, active, activity_level, goal, "
            "created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                member_id,
                household_id,
                "Исторический участник",
                1,
                "active",
                "maintain",
                "2026-11-01T00:00:00Z",
                "2026-11-01T00:00:00Z",
            ),
        )

    with sqlite3.connect(config.path) as db:
        original_rows = (
            db.execute("SELECT * FROM households").fetchall(),
            db.execute("SELECT * FROM household_members").fetchall(),
        )
        old_history = tuple(
            db.execute(
                "SELECT migration_id FROM schema_migrations ORDER BY rowid"
            ).fetchall()
        )
        old_household_sql = db.execute(
            "SELECT sql FROM sqlite_master WHERE name='household_members'"
        ).fetchone()[0]
    assert apply_migrations(config) == ["0045_household_member_food_exclusions"]
    assert apply_migrations(config) == []
    with sqlite3.connect(config.path) as db:
        assert db.execute("PRAGMA foreign_key_check").fetchall() == []
        assert tuple(
            db.execute(
                "SELECT migration_id FROM schema_migrations ORDER BY rowid"
            ).fetchall()
        ) == (*old_history, ("0045_household_member_food_exclusions",))
        assert (
            db.execute(
                "SELECT sql FROM sqlite_master WHERE name='household_members'"
            ).fetchone()[0]
            == old_household_sql
        )
        assert (
            db.execute(
                "SELECT COUNT(*) FROM household_member_excluded_food_ingredients"
            ).fetchone()[0]
            == 0
        )
        assert (
            db.execute("SELECT * FROM households").fetchall(),
            db.execute("SELECT * FROM household_members").fetchall(),
        ) == original_rows
    assert expected_migration_ids()[-1] == "0045_household_member_food_exclusions"


def test_0045_migration_failure_rolls_back_index_and_schema_marker(
    tmp_path, monkeypatch
):
    """The failed schema half-step cannot leave an unmarked composite index."""
    config = DatabaseConfig(path=tmp_path / "migration-injection.sqlite")
    modules = list(MIGRATION_MODULES)
    try:
        MIGRATION_MODULES[:] = modules[:-1]
        apply_migrations(config)
    finally:
        MIGRATION_MODULES[:] = modules

    module = import_module(
        "app.migrations.versions.0045_household_member_food_exclusions"
    )
    original_upgrade = module.upgrade

    def fail_after_index(db):
        db.execute(
            "CREATE UNIQUE INDEX uq_household_member_scope "
            "ON household_members (household_id, id)"
        )
        raise RuntimeError("injected migration failure before association table")

    monkeypatch.setattr(module, "upgrade", fail_after_index)
    with pytest.raises(RuntimeError, match="injected migration failure"):
        apply_migrations(config)
    with sqlite3.connect(config.path) as db:
        assert (
            db.execute(
                "SELECT name FROM sqlite_master WHERE name='uq_household_member_scope'"
            ).fetchone()
            is None
        )
        assert (
            db.execute(
                "SELECT name FROM sqlite_master "
                "WHERE name='household_member_excluded_food_ingredients'"
            ).fetchone()
            is None
        )
        assert (
            db.execute(
                "SELECT migration_id FROM schema_migrations "
                "WHERE migration_id='0045_household_member_food_exclusions'"
            ).fetchone()
            is None
        )
        assert db.execute("PRAGMA foreign_key_check").fetchall() == []

    monkeypatch.setattr(module, "upgrade", original_upgrade)
    assert apply_migrations(config) == ["0045_household_member_food_exclusions"]


@pytest.fixture
def exclusions_api(scenario, monkeypatch):
    config, _, _, _, _ = scenario
    monkeypatch.setenv(DATABASE_PATH_ENV, str(config.path))
    monkeypatch.setenv("AI_ENABLED", "false")
    with TestClient(create_app()) as client:
        yield client


def _exclusions_url(household, member):
    return f"/api/households/{household}/members/{member}/food-exclusions"


def _selection_payload(expected, selected):
    return {
        "expected_excluded_food_ingredient_ids": [str(item) for item in expected],
        "excluded_food_ingredient_ids": [str(item) for item in selected],
    }


def test_exclusions_http_catalogue_and_persisted_next_week(scenario, exclusions_api):
    config, engine, _, witness, _ = scenario
    household = witness.command.household_id
    member_a, member_b = (entry.member_id for entry in witness.command.members)
    foods = create_food_catalogue_service(engine)
    beef = foods.get_by_code("BEEF_CATEGORY_1_RAW")
    foods.add_alias(beef.id, alias="Тестовый мясной продукт")
    search = exclusions_api.get(
        "/api/food-ingredients", params={"q": "ТЕСТОВЫЙ МЯСНОЙ ПРОДУКТ"}
    )
    assert search.status_code == 200, search.text
    assert [item["id"] for item in search.json()["items"]] == [str(beef.id)]
    assert exclusions_api.get(f"/api/food-ingredients/{beef.id}").json() == {
        "id": str(beef.id),
        "canonical_name": beef.canonical_name,
        "is_active": True,
    }
    with SqlAlchemyShoppingReadScope(engine) as scope:
        previous = scope.plans.get_current(household, WEEK)
    url = _exclusions_url(household, member_a)
    response = exclusions_api.get(url)
    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    assert response.json() == {"excluded_food_ingredient_ids": []}
    response = exclusions_api.put(url, json=_selection_payload([], [beef.id]))
    assert response.status_code == 200, response.text
    assert response.json() == {
        "excluded_food_ingredient_ids": [str(beef.id)],
        "changed": True,
    }
    assert exclusions_api.get(url).json() == {
        "excluded_food_ingredient_ids": [str(beef.id)]
    }
    assert exclusions_api.get(_exclusions_url(household, member_b)).json() == {
        "excluded_food_ingredient_ids": []
    }
    before = _db_dump(config)
    replay = exclusions_api.put(url, json=_selection_payload([beef.id], [beef.id]))
    assert replay.status_code == 200
    assert replay.json()["changed"] is False
    assert _db_dump(config) == before
    stale = exclusions_api.put(url, json=_selection_payload([], []))
    assert stale.status_code == 409
    assert stale.json()["detail"]["code"] == "MEMBER_EXCLUSIONS_CONFLICT"
    assert _db_dump(config) == before

    next_week = WEEK + timedelta(days=7)
    command = replace(
        witness.command,
        week_start=next_week,
        fixed_events=(),
        members=tuple(
            replace(member, excluded_food_ingredient_ids=frozenset())
            for member in witness.command.members
        ),
    )
    result, saved = _planner(engine).generate_authoritative(command)
    assert isinstance(result, PlannerSuccess)
    assert saved is not None
    with SqlAlchemyShoppingReadScope(engine) as scope:
        assert scope.plans.get_current(household, WEEK) == previous
        persisted = scope.plans.get_current(household, next_week)
        assert persisted == saved
        assigned = {
            serving.event_id
            for serving in persisted.servings
            if serving.member_id == member_a
        }
        checked = 0
        for event in persisted.events:
            if (
                event.id not in assigned
                or event.source_kind != MealSourceKind.COOK_RECIPE
            ):
                continue
            detail = scope.recipes.get_detail(event.recipe_version_id)
            assert detail is not None
            assert beef.id not in {row.food_ingredient_id for row in detail.ingredients}
            checked += 1
        assert checked > 0


def test_exclusions_http_invalid_scope_and_input(scenario, exclusions_api):
    config, engine, households, witness, _ = scenario
    household = witness.command.household_id
    member = witness.command.members[0].member_id
    other = households.create_household(name="Другая семья", timezone_name="UTC")
    url = _exclusions_url(household, member)
    foods = create_food_catalogue_service(engine)
    carrot = foods.get_by_code("CARROT")
    foods.deactivate(carrot.id)
    before = _db_dump(config)
    for wrong in (
        _exclusions_url(other.id, member),
        _exclusions_url(uuid4(), member),
        _exclusions_url(household, uuid4()),
    ):
        assert exclusions_api.get(wrong).status_code == 404
        assert (
            exclusions_api.put(wrong, json=_selection_payload([], [])).status_code
            == 404
        )

    invalid_payloads = [
        {},
        {"excluded_food_ingredient_ids": []},
        {"expected_excluded_food_ingredient_ids": []},
        _selection_payload([], ["private-invalid-input"]),
        _selection_payload([], ["00000000-0000-1000-8000-000000000001"]),
        _selection_payload([], [carrot.id, carrot.id]),
        _selection_payload([carrot.id, carrot.id], []),
        _selection_payload([], [uuid4() for _ in range(129)]),
        _selection_payload([uuid4() for _ in range(129)], []),
        {**_selection_payload([], []), "reason": "private-invalid-input"},
    ]
    for payload in invalid_payloads:
        response = exclusions_api.put(url, json=payload)
        assert response.status_code == 422, response.text
        assert response.json()["detail"]["code"] == "FOOD_SELECTION_INVALID_REQUEST"
        assert "private-invalid-input" not in response.text

    for food_id in (uuid4(), carrot.id):
        response = exclusions_api.put(url, json=_selection_payload([], [food_id]))
        assert response.status_code == 409
        assert response.json()["detail"]["code"] == "MEMBER_EXCLUSIONS_CONFLICT"
        assert str(food_id) not in response.text
    assert (
        exclusions_api.get(f"/api/food-ingredients/{carrot.id}").json()["is_active"]
        is False
    )
    assert exclusions_api.get(f"/api/food-ingredients/{uuid4()}").status_code == 404
    assert (
        exclusions_api.get(
            "/api/food-ingredients", params={"q": "морковь", "limit": 201}
        ).status_code
        == 422
    )
    assert all(
        item["id"] != str(carrot.id)
        for item in exclusions_api.get(
            "/api/food-ingredients", params={"q": carrot.canonical_name}
        ).json()["items"]
    )
    assert _db_dump(config) == before


def test_exclusions_http_failed_write_and_inactive_history(scenario, exclusions_api):
    config, engine, _, witness, _ = scenario
    household = witness.command.household_id
    member = witness.command.members[0].member_id
    foods = create_food_catalogue_service(engine)
    carrot = foods.get_by_code("CARROT")
    beef = foods.get_by_code("BEEF_CATEGORY_1_RAW")
    url = _exclusions_url(household, member)
    assert (
        exclusions_api.put(url, json=_selection_payload([], [carrot.id])).status_code
        == 200
    )
    foods.deactivate(carrot.id)
    assert exclusions_api.get(url).json()["excluded_food_ingredient_ids"] == [
        str(carrot.id)
    ]
    with sqlite3.connect(config.path) as connection:
        connection.execute("""
            CREATE TRIGGER reject_http_exclusion_insert
            BEFORE INSERT ON household_member_excluded_food_ingredients
            BEGIN SELECT RAISE(ABORT, 'private injected failure'); END
        """)
    before = _db_dump(config)
    failed = exclusions_api.put(
        url, json=_selection_payload([carrot.id], [carrot.id, beef.id])
    )
    assert failed.status_code == 409
    assert "private injected failure" not in failed.text
    assert _db_dump(config) == before
    assert exclusions_api.get(url).json()["excluded_food_ingredient_ids"] == [
        str(carrot.id)
    ]
    # An explicit empty selection clears the set; omitted fields cannot.
    cleared = exclusions_api.put(url, json=_selection_payload([carrot.id], []))
    assert cleared.status_code == 200
    assert cleared.json() == {"excluded_food_ingredient_ids": [], "changed": True}


def test_exclusions_http_retains_inactive_food_while_editing(scenario, exclusions_api):
    config, engine, _, witness, _ = scenario
    household = witness.command.household_id
    member, other_member = (item.member_id for item in witness.command.members)
    foods = create_food_catalogue_service(engine)
    carrot = foods.get_by_code("CARROT")
    beef = foods.get_by_code("BEEF_CATEGORY_1_RAW")
    url = _exclusions_url(household, member)

    def put(expected, selected):
        return exclusions_api.put(url, json=_selection_payload(expected, selected))

    assert put([], [carrot.id]).status_code == 200
    foods.deactivate(carrot.id)
    assert put([carrot.id], [carrot.id, beef.id]).status_code == 200
    both = sorted([str(carrot.id), str(beef.id)])
    assert exclusions_api.get(url).json()["excluded_food_ingredient_ids"] == both
    before = _db_dump(config)

    replay = put([carrot.id, beef.id], [beef.id, carrot.id])
    assert replay.status_code == 200
    assert replay.json()["changed"] is False
    assert put([carrot.id], [carrot.id]).status_code == 409
    assert put([carrot.id, beef.id], [carrot.id, beef.id, uuid4()]).status_code == 409
    other_url = _exclusions_url(household, other_member)
    assert (
        exclusions_api.put(
            other_url, json=_selection_payload([], [carrot.id])
        ).status_code
        == 409
    )
    assert _db_dump(config) == before

    assert put([carrot.id, beef.id], [carrot.id]).status_code == 200
    assert put([carrot.id], []).status_code == 200
    assert put([], [carrot.id]).status_code == 409
    assert exclusions_api.get(url).json()["excluded_food_ingredient_ids"] == []


def test_exclusions_http_commit_failure_is_not_cas_conflict(
    scenario, exclusions_api, monkeypatch
):
    config, engine, _, witness, _ = scenario
    household = witness.command.household_id
    member = witness.command.members[0].member_id
    foods = create_food_catalogue_service(engine)
    carrot = foods.get_by_code("CARROT")
    beef = foods.get_by_code("BEEF_CATEGORY_1_RAW")
    url = _exclusions_url(household, member)
    assert (
        exclusions_api.put(url, json=_selection_payload([], [carrot.id])).status_code
        == 200
    )
    before = _db_dump(config)
    observed = []

    def fail_commit(scope):
        # The real Household UoW translates DBAPIError; its context manager
        # rolls back the actual uncommitted replacement on exit.
        observed.append(True)
        raise OperationalError(
            "private SQL", {}, sqlite3.OperationalError("private commit failure")
        )

    with monkeypatch.context() as patch:
        patch.setattr(SqlAlchemyUnitOfWork, "commit", fail_commit)
        response = exclusions_api.put(
            url, json=_selection_payload([carrot.id], [beef.id])
        )
    assert observed == [True]
    assert response.status_code == 503
    assert response.headers["Cache-Control"] == "no-store"
    assert response.json()["detail"]["code"] == (
        "MEMBER_EXCLUSIONS_PERSISTENCE_FAILURE"
    )
    assert response.json()["detail"]["next_action"]
    assert "private" not in response.text
    assert _db_dump(config) == before
    assert exclusions_api.get(url).json()["excluded_food_ingredient_ids"] == [
        str(carrot.id)
    ]
    retry = exclusions_api.put(url, json=_selection_payload([carrot.id], [beef.id]))
    assert retry.status_code == 200


def test_exclusions_http_read_persistence_failure_is_safe(
    scenario, exclusions_api, monkeypatch
):
    _, _, _, witness, _ = scenario
    url = _exclusions_url(
        witness.command.household_id, witness.command.members[0].member_id
    )

    def fail_read(*args, **kwargs):
        raise HouseholdPersistenceError("private storage details")

    monkeypatch.setattr(HouseholdService, "list_member_excluded_food_ids", fail_read)
    response = exclusions_api.get(url)
    assert response.status_code == 503
    assert response.headers["Cache-Control"] == "no-store"
    assert response.json()["detail"]["code"] == (
        "MEMBER_EXCLUSIONS_PERSISTENCE_FAILURE"
    )
    assert "private" not in response.text
