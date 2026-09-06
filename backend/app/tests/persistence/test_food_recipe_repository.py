from dataclasses import replace
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import text

from app.db.config import DatabaseConfig
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
from app.persistence.sqlalchemy_core.food_recipe_uow import (
    SqlAlchemyRecipeCatalogueReadScope,
    SqlAlchemyRecipeCatalogueUnitOfWork,
)
from app.seed.food_recipes import seed_food_recipes
from app.services.food_recipe_contracts import (
    RecipeCataloguePersistenceConflictError,
)
from app.services.food_recipes import (
    RecipeCatalogueConflictError,
)
from app.domain.food_recipes import RecipeEquipment, RecipeVersionDetail

PRIMARY_RECIPE_CODE = "SPICED_OATMEAL"


@pytest.fixture
def recipe_engine(tmp_path):
    config = DatabaseConfig(path=tmp_path / "recipes.sqlite")
    seed_food_recipes(config)
    engine = create_sqlite_engine(config)
    try:
        yield config, engine
    finally:
        engine.dispose()


def _service(engine):
    from app.persistence.sqlalchemy_core.food_recipe_composition import (
        create_food_recipe_catalogue_service,
    )

    return create_food_recipe_catalogue_service(engine)


def test_repository_round_trip_orders_children_and_resolves_current(recipe_engine):
    _, engine = recipe_engine
    service = _service(engine)
    recipe = service.get_by_code(PRIMARY_RECIPE_CODE)

    current = service.get_current_verified(recipe.id)
    reread = service.get_version_detail(current.version.id)

    assert reread.recipe == recipe
    assert reread.version == current.version
    assert [item.position for item in reread.ingredients] == list(
        range(1, len(reread.ingredients) + 1)
    )
    assert [step.position for step in reread.steps] == list(
        range(1, len(reread.steps) + 1)
    )
    assert [item.position for item in reread.equipment] == list(
        range(1, len(reread.equipment) + 1)
    )
    assert service.list_versions(recipe.id)[-1].id == current.version.id


def test_repository_list_active_is_deterministic(recipe_engine):
    _, engine = recipe_engine
    service = _service(engine)

    active = service.list_active(limit=100)

    assert active == sorted(
        active,
        key=lambda recipe: (
            recipe.canonical_name_key,
            recipe.canonical_code,
            recipe.id,
        ),
    )


def test_repository_rejects_same_provenance_with_changed_structure(recipe_engine):
    _, engine = recipe_engine
    service = _service(engine)
    recipe = service.get_by_code(PRIMARY_RECIPE_CODE)
    current = service.get_current_verified(recipe.id)

    with pytest.raises(RecipeCatalogueConflictError, match="Same-provenance"):
        service.reconcile_seed(
            [
                replace(
                    next(
                        seed
                        for seed in __import__(
                            "app.seed.food_recipes", fromlist=["load_seed_entries"]
                        ).load_seed_entries()
                        if seed.canonical_code == PRIMARY_RECIPE_CODE
                    ),
                    version=replace(
                        next(
                            seed
                            for seed in __import__(
                                "app.seed.food_recipes",
                                fromlist=["load_seed_entries"],
                            ).load_seed_entries()
                            if seed.canonical_code == PRIMARY_RECIPE_CODE
                        ).version,
                        base_servings=current.version.base_servings + Decimal("1"),
                    ),
                )
            ]
        )


def test_repository_update_delete_triggers_guard_immutable_rows(recipe_engine):
    _, engine = recipe_engine
    service = _service(engine)
    recipe = service.get_by_code(PRIMARY_RECIPE_CODE)
    current = service.get_current_verified(recipe.id)

    guarded = (
        ("food_recipe_versions", current.version.id.hex),
        ("food_recipe_ingredients", current.ingredients[0].id.hex),
        ("food_recipe_steps", current.steps[0].id.hex),
    )
    with engine.connect() as connection:
        for table, row_id in guarded:
            with pytest.raises(Exception, match="immutable"):
                connection.execute(
                    text(f"UPDATE {table} SET created_at = created_at WHERE id = :id"),
                    {"id": row_id},
                )
            connection.rollback()
            with pytest.raises(Exception, match="immutable"):
                connection.execute(
                    text(f"DELETE FROM {table} WHERE id = :id"), {"id": row_id}
                )
            connection.rollback()

        if current.equipment:
            with pytest.raises(Exception, match="immutable"):
                connection.execute(
                    text(
                        "UPDATE food_recipe_equipment SET equipment_code = equipment_code "
                        "WHERE recipe_version_id = :id AND position = 1"
                    ),
                    {"id": current.version.id.hex},
                )
            connection.rollback()
            with pytest.raises(Exception, match="immutable"):
                connection.execute(
                    text(
                        "DELETE FROM food_recipe_equipment "
                        "WHERE recipe_version_id = :id AND position = 1"
                    ),
                    {"id": current.version.id.hex},
                )
            connection.rollback()


def test_repository_read_scope_is_read_only(recipe_engine):
    _, engine = recipe_engine
    with SqlAlchemyRecipeCatalogueReadScope(engine) as scope:
        recipe = scope.recipes.list_active(limit=1)[0]
        assert scope.recipes.get(recipe.id) == recipe
        assert scope.versions.get_current_verified(recipe.id) is not None


def test_repository_transaction_rollback_is_atomic(recipe_engine):
    _, engine = recipe_engine
    service = _service(engine)
    recipe = service.get_by_code(PRIMARY_RECIPE_CODE)
    current = service.get_current_verified(recipe.id)
    duplicate_id = uuid4()
    detail = RecipeVersionDetail(
        recipe=current.recipe,
        version=replace(
            current.version,
            id=duplicate_id,
            version_number=current.version.version_number + 1,
            source_version="rollback-test",
            source_document_sha256="d" * 64,
            created_from_version_id=current.version.id,
        ),
        ingredients=tuple(
            replace(item, id=uuid4(), recipe_version_id=duplicate_id)
            for item in current.ingredients
        ),
        steps=tuple(
            replace(step, id=uuid4(), recipe_version_id=duplicate_id)
            for step in current.steps
        ),
        equipment=tuple(
            RecipeEquipment(duplicate_id, item.position, item.equipment_code)
            for item in current.equipment
        ),
    )

    with SqlAlchemyRecipeCatalogueUnitOfWork(engine) as scope:
        scope.versions.add_detail(detail)
        scope.rollback()

    assert service.get_version(detail.version.id) is None


def test_repository_created_from_version_must_be_same_recipe(recipe_engine):
    _, engine = recipe_engine
    service = _service(engine)
    recipes = service.list_active(limit=2)
    first = service.get_current_verified(recipes[0].id)
    second = service.get_current_verified(recipes[1].id)
    version_id = uuid4()
    detail = RecipeVersionDetail(
        recipe=first.recipe,
        version=replace(
            first.version,
            id=version_id,
            version_number=first.version.version_number + 1,
            source_version="wrong-parent",
            source_document_sha256="c" * 64,
            created_from_version_id=second.version.id,
        ),
        ingredients=tuple(
            replace(item, id=uuid4(), recipe_version_id=version_id)
            for item in first.ingredients
        ),
        steps=tuple(
            replace(step, id=uuid4(), recipe_version_id=version_id)
            for step in first.steps
        ),
        equipment=tuple(
            RecipeEquipment(version_id, item.position, item.equipment_code)
            for item in first.equipment
        ),
    )

    with (
        SqlAlchemyRecipeCatalogueUnitOfWork(engine) as scope,
        pytest.raises(RecipeCataloguePersistenceConflictError),
    ):
        scope.versions.add_detail(detail)


def test_repository_maps_duplicate_version_number_to_stable_conflict(recipe_engine):
    _, engine = recipe_engine
    service = _service(engine)
    existing = service.get_current_verified(service.get_by_code(PRIMARY_RECIPE_CODE).id)
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

    with (
        SqlAlchemyRecipeCatalogueUnitOfWork(engine) as scope,
        pytest.raises(RecipeCataloguePersistenceConflictError),
    ):
        scope.versions.add_detail(detail)
