import sqlite3
from dataclasses import replace
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy import Column, ForeignKey, Integer, MetaData, Table, event

from app.db.config import DatabaseConfig
from app.domain.food_recipes import (
    Recipe,
    RecipeEquipment,
    RecipeVersionDetail,
)
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
from app.persistence.sqlalchemy_core.food_recipe_composition import (
    create_food_recipe_catalogue_service,
)
from app.persistence.sqlalchemy_core.food_recipe_uow import (
    SqlAlchemyRecipeCatalogueReadScope,
    SqlAlchemyRecipeCatalogueUnitOfWork,
)
from app.seed.food_recipes import load_seed_entries, seed_food_recipes
from app.services.food_recipe_contracts import RecipeCataloguePersistenceConflictError

NOW = datetime(2026, 9, 4, tzinfo=timezone.utc)

terminality_metadata = MetaData()
deferred_parent_table = Table(
    "recipe_uow_deferred_parent",
    terminality_metadata,
    Column("id", Integer, primary_key=True),
)
deferred_child_table = Table(
    "recipe_uow_deferred_child",
    terminality_metadata,
    Column("id", Integer, primary_key=True),
    Column(
        "parent_id",
        Integer,
        ForeignKey(deferred_parent_table.c.id, deferrable=True, initially="DEFERRED"),
        nullable=False,
    ),
)


@pytest.fixture
def recipe_engine(tmp_path):
    config = DatabaseConfig(path=tmp_path / "recipes.sqlite")
    seed_food_recipes(config)
    engine = create_sqlite_engine(config)
    with engine.begin() as connection:
        deferred_parent_table.create(connection)
        deferred_child_table.create(connection)
    try:
        yield config, engine
    finally:
        engine.dispose()


def _assert_revoked(scope):
    for attribute in ("recipes", "versions", "food_ingredients"):
        with pytest.raises(RuntimeError, match="not active"):
            getattr(scope, attribute)


def test_complete_version_roundtrips_uuid_utc_decimal_and_order(recipe_engine):
    _, engine = recipe_engine
    service = create_food_recipe_catalogue_service(engine)
    recipe = service.get_by_code("SPICED_OATMEAL")
    detail = service.get_current_verified(recipe.id)

    assert recipe.id.version == detail.version.id.version == 4
    assert detail.version.created_at.tzinfo is timezone.utc
    assert [item.position for item in detail.ingredients] == list(
        range(1, len(detail.ingredients) + 1)
    )
    assert [step.position for step in detail.steps] == list(
        range(1, len(detail.steps) + 1)
    )
    assert service.list_versions(recipe.id) == [detail.version]


def test_append_v2_preserves_v1_and_current_verified_advances(recipe_engine):
    _, engine = recipe_engine
    service = create_food_recipe_catalogue_service(engine)
    recipe = service.get_by_code("SPICED_OATMEAL")
    v1 = service.get_current_verified(recipe.id)
    source = next(
        seed.version
        for seed in load_seed_entries()
        if seed.canonical_code == "SPICED_OATMEAL"
    )
    v2_seed = replace(
        source,
        source_version="reviewed-v2",
        source_document_sha256="b" * 64,
        change_note="Reviewed source correction.",
        equipment_codes=("saucepan",),
    )

    v2 = service.append_trusted_version(recipe.id, v2_seed)

    assert v2.version.version_number == 2
    assert v2.version.created_from_version_id == v1.version.id
    assert service.get_version_detail(v1.version.id) == v1
    assert service.get_current_verified(recipe.id) == v2


def test_sqlite_guards_reject_update_and_delete_for_every_version_owned_table(
    recipe_engine,
):
    config, engine = recipe_engine
    service = create_food_recipe_catalogue_service(engine)
    recipe = service.get_by_code("SPICED_OATMEAL")
    source = next(
        seed.version
        for seed in load_seed_entries()
        if seed.canonical_code == "SPICED_OATMEAL"
    )
    v2 = service.append_trusted_version(
        recipe.id,
        replace(
            source,
            source_version="guard-v2",
            source_document_sha256="c" * 64,
            change_note="Guard fixture.",
            equipment_codes=("saucepan",),
        ),
    )
    targets = {
        "food_recipe_versions": ("change_note", "changed", "id", v2.version.id.hex),
        "food_recipe_ingredients": (
            "quantity",
            "999",
            "id",
            v2.ingredients[0].id.hex,
        ),
        "food_recipe_steps": ("instruction", "changed", "id", v2.steps[0].id.hex),
        "food_recipe_equipment": (
            "equipment_code",
            "changed",
            "recipe_version_id",
            v2.version.id.hex,
        ),
    }
    with sqlite3.connect(config.path) as connection:
        for table, (column, value, key, identifier) in targets.items():
            with pytest.raises(sqlite3.IntegrityError, match="immutable"):
                connection.execute(
                    f"UPDATE {table} SET {column}=? WHERE {key}=?", (value, identifier)
                )
            connection.rollback()
            with pytest.raises(sqlite3.IntegrityError, match="immutable"):
                connection.execute(f"DELETE FROM {table} WHERE {key}=?", (identifier,))
            connection.rollback()


def test_successful_commit_and_rollback_revoke_repository_handles(recipe_engine):
    _, engine = recipe_engine
    committed = SqlAlchemyRecipeCatalogueUnitOfWork(engine)
    with committed:
        committed.commit()
        _assert_revoked(committed)
    rolled_back = SqlAlchemyRecipeCatalogueUnitOfWork(engine)
    with rolled_back:
        rolled_back.rollback()
        _assert_revoked(rolled_back)


def test_failed_commit_revokes_discards_and_later_uow_is_clean(recipe_engine):
    _, engine = recipe_engine
    scope = SqlAlchemyRecipeCatalogueUnitOfWork(engine)
    with pytest.raises(RecipeCataloguePersistenceConflictError):
        with scope:
            retained = scope._scope.adapter_connection
            retained.execute(deferred_child_table.insert().values(id=1, parent_id=999))
            scope.commit()
    assert retained.closed
    _assert_revoked(scope)
    service = create_food_recipe_catalogue_service(engine)
    assert service.get_by_code("SPICED_OATMEAL").is_active is True


def test_failed_rollback_revokes_discards_and_later_uow_is_clean(recipe_engine):
    _, engine = recipe_engine
    scope = SqlAlchemyRecipeCatalogueUnitOfWork(engine)
    candidate = Recipe(
        uuid4(),
        "ROLLBACK_FIXTURE",
        "Rollback Fixture",
        "rollback fixture",
        True,
        NOW,
        NOW,
    )

    def fail_rollback(connection):
        del connection
        raise RuntimeError("simulated rollback failure")

    with pytest.raises(RuntimeError, match="simulated rollback failure"):
        with scope:
            retained = scope._scope.adapter_connection
            scope.recipes.add(candidate)
            event.listen(engine, "rollback", fail_rollback, once=True)
            scope.rollback()
    assert retained.closed
    _assert_revoked(scope)
    with SqlAlchemyRecipeCatalogueReadScope(engine) as later:
        assert later.recipes.get_by_code("ROLLBACK_FIXTURE") is None
        assert later.recipes.get_by_code("SPICED_OATMEAL") is not None


def test_repository_rejects_cross_recipe_created_from_reference(recipe_engine):
    _, engine = recipe_engine
    service = create_food_recipe_catalogue_service(engine)
    first = service.get_current_verified(service.get_by_code("SPICED_OATMEAL").id)
    second = service.get_current_verified(service.get_by_code("PIZZA_GREEN_BEANS").id)
    new_id = uuid4()
    invalid_version = replace(
        second.version,
        id=new_id,
        version_number=2,
        source_version="cross-recipe-v2",
        source_document_sha256="d" * 64,
        created_from_version_id=first.version.id,
    )
    detail = RecipeVersionDetail(
        recipe=second.recipe,
        version=invalid_version,
        ingredients=tuple(
            replace(item, id=uuid4(), recipe_version_id=new_id)
            for item in second.ingredients
        ),
        steps=tuple(
            replace(step, id=uuid4(), recipe_version_id=new_id) for step in second.steps
        ),
        equipment=tuple(
            RecipeEquipment(new_id, item.position, item.equipment_code)
            for item in second.equipment
        ),
    )
    with SqlAlchemyRecipeCatalogueUnitOfWork(engine) as scope:
        with pytest.raises(
            RecipeCataloguePersistenceConflictError, match="same Recipe"
        ):
            scope.versions.add_detail(detail)


def test_repository_maps_duplicate_version_number_to_stable_conflict(recipe_engine):
    _, engine = recipe_engine
    service = create_food_recipe_catalogue_service(engine)
    existing = service.get_current_verified(service.get_by_code("SPICED_OATMEAL").id)
    duplicate_id = uuid4()
    detail = RecipeVersionDetail(
        recipe=existing.recipe,
        version=replace(
            existing.version,
            id=duplicate_id,
            source_version="duplicate-number",
            source_document_sha256="f" * 64,
        ),
        ingredients=tuple(
            replace(item, id=uuid4(), recipe_version_id=duplicate_id)
            for item in existing.ingredients
        ),
        steps=tuple(
            replace(step, id=uuid4(), recipe_version_id=duplicate_id)
            for step in existing.steps
        ),
        equipment=tuple(
            RecipeEquipment(duplicate_id, item.position, item.equipment_code)
            for item in existing.equipment
        ),
    )

    with SqlAlchemyRecipeCatalogueUnitOfWork(engine) as scope:
        with pytest.raises(RecipeCataloguePersistenceConflictError):
            scope.versions.add_detail(detail)
