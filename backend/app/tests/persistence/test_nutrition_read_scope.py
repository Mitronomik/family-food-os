import sqlite3
from dataclasses import replace
from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import event

from app.db.config import DatabaseConfig
from app.db.migrations import expected_migration_ids
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
from app.persistence.sqlalchemy_core.food_ingredient_uow import (
    SqlAlchemyFoodCatalogueUnitOfWork,
)
from app.persistence.sqlalchemy_core.food_recipe_composition import (
    create_food_recipe_catalogue_service,
)
from app.persistence.sqlalchemy_core.household_composition import (
    create_household_service,
)
from app.persistence.sqlalchemy_core.nutrition_composition import (
    create_nutrition_service,
)
from app.persistence.sqlalchemy_core.nutrition_read_scope import (
    SqlAlchemyNutritionReadScope,
)
from app.seed.food_recipes import seed_food_recipes
from app.seed.nutrition_measure_evidence import seed_nutrition_measure_evidence
from app.services.nutrition import NutritionInputNotFoundError


@pytest.fixture
def nutrition_engine(tmp_path):
    config = DatabaseConfig(path=tmp_path / "nutrition.sqlite")
    seed_food_recipes(config)
    seed_nutrition_measure_evidence(config)
    with sqlite3.connect(config.path, isolation_level=None) as connection:
        connection.execute("PRAGMA journal_mode=WAL")
    engine = create_sqlite_engine(config)
    try:
        yield config, engine
    finally:
        engine.dispose()


def recipe_detail(engine):
    recipes = create_food_recipe_catalogue_service(engine)
    recipe = recipes.get_by_code("CACFP6_CORN_EDAMAME_BLEND")
    return recipes.get_current_verified(recipe.id)


def test_read_scope_is_coherent_across_concurrent_profile_replacement(nutrition_engine):
    _, engine = nutrition_engine
    detail = recipe_detail(engine)
    food_id = detail.ingredients[0].food_ingredient_id
    with SqlAlchemyNutritionReadScope(engine) as read:
        # The recipe SELECT establishes the same snapshot used for every profile.
        assert read.versions.get_detail(detail.version.id) == detail
        old = read.nutrition_profiles.get_current(food_id)
        replacement = replace(
            old, id=uuid4(), source_version="synthetic-test-v2", kcal=Decimal(999)
        )
        with SqlAlchemyFoodCatalogueUnitOfWork(engine) as write:
            write.nutrition_profiles.clear_current(food_id)
            write.nutrition_profiles.add(replacement)
            write.commit()
        assert read.nutrition_profiles.get_current(food_id) == old
    service = create_nutrition_service(engine)
    assert service.food_ingredient(food_id, Decimal(100)).profile == replacement
    with SqlAlchemyNutritionReadScope(engine) as read:
        historical = read.nutrition_profiles.get_by_provenance(
            food_id, old.source_name, old.source_id, old.source_version
        )
        assert historical == replace(old, is_current=False)


def test_recipe_calculation_has_one_connection_no_writes_and_no_schema_change(
    nutrition_engine,
):
    config, engine = nutrition_engine
    detail = recipe_detail(engine)
    statements, connections = [], []
    with sqlite3.connect(config.path) as database:
        before = list(database.iterdump())
    event.listen(engine, "checkout", lambda *args: connections.append(1))
    event.listen(
        engine,
        "before_cursor_execute",
        lambda c, cur, statement, *args: statements.append(statement),
    )
    result = create_nutrition_service(engine).recipe_version(detail.version.id)
    assert result.version == detail.version
    assert len(connections) == 1
    assert statements and all(
        statement.lstrip().upper().startswith("SELECT") for statement in statements
    )
    with sqlite3.connect(config.path) as database:
        assert list(database.iterdump()) == before
        assert (
            database.execute(
                "SELECT migration_id FROM schema_migrations ORDER BY rowid DESC LIMIT 1"
            ).fetchone()[0]
            == "0027_recipe_same_source_revisions"
        )
    assert expected_migration_ids()[-1] == "0027_recipe_same_source_revisions"
    assert len(expected_migration_ids()) == 27


def test_member_lookup_enforces_household_scope(nutrition_engine):
    _, engine = nutrition_engine
    households = create_household_service(engine)
    owner = households.create_household(name="Synthetic A", timezone_name="UTC")
    other = households.create_household(name="Synthetic B", timezone_name="UTC")
    person = households.add_household_member(
        owner.id,
        name="Synthetic member",
        activity_level="active",
        goal="maintain",
        birth_date=date(1990, 1, 1),
        sex="male",
        height_cm="180",
        weight_kg="80",
    )
    service = create_nutrition_service(engine)
    target = service.member_reference_target(
        owner.id, person.id, as_of_date=date(2026, 9, 6)
    )
    assert target.reference_energy_kcal is not None
    assert target.inputs.household_id == owner.id
    for household_id, member_id in ((other.id, person.id), (owner.id, uuid4())):
        with pytest.raises(NutritionInputNotFoundError):
            service.member_reference_target(
                household_id, member_id, as_of_date=date(2026, 9, 6)
            )


@pytest.mark.parametrize("failure", [False, True])
def test_scope_revokes_readers_on_all_exit_paths_and_is_single_use(
    nutrition_engine, failure
):
    _, engine = nutrition_engine
    scope = SqlAlchemyNutritionReadScope(engine)
    names = ("ingredients", "nutrition_profiles", "versions", "members")
    for name in names:
        with pytest.raises(RuntimeError, match="not active"):
            getattr(scope, name)
    try:
        with scope:
            for name in names:
                assert getattr(scope, name) is not None
            if failure:
                raise ValueError("synthetic")
    except ValueError:
        assert failure
    for name in names:
        with pytest.raises(RuntimeError, match="not active"):
            getattr(scope, name)
    with pytest.raises(RuntimeError, match="single-use"):
        with scope:
            pass
