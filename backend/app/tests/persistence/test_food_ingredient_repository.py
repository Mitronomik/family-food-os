import sqlite3
from dataclasses import replace
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import Column, ForeignKey, Integer, MetaData, Table, event

from app.db.config import DatabaseConfig
from app.db.migrations import apply_migrations
from app.domain.food_ingredients import IngredientAlias
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
from app.persistence.sqlalchemy_core.food_ingredient_composition import (
    create_food_catalogue_service,
)
from app.persistence.sqlalchemy_core.food_ingredient_uow import (
    SqlAlchemyFoodCatalogueReadScope,
    SqlAlchemyFoodCatalogueUnitOfWork,
)
from app.services.food_ingredient_contracts import (
    FoodCataloguePersistenceConflictError,
)
from app.services.food_ingredients import (
    FoodCatalogueConflictError,
    TrustedAliasSeed,
    TrustedFoodIngredientSeed,
    TrustedNutritionSeed,
)

NOW = datetime(2026, 9, 2, tzinfo=timezone.utc)

terminality_metadata = MetaData()
deferred_parent_table = Table(
    "food_catalogue_uow_deferred_parent",
    terminality_metadata,
    Column("id", Integer, primary_key=True),
)
deferred_child_table = Table(
    "food_catalogue_uow_deferred_child",
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
def catalogue_engine(tmp_path):
    config = DatabaseConfig(path=tmp_path / "catalogue.sqlite")
    apply_migrations(config)
    engine = create_sqlite_engine(config)
    with engine.begin() as connection:
        deferred_parent_table.create(connection)
        deferred_child_table.create(connection)
    try:
        yield config, engine
    finally:
        engine.dispose()


def seed(
    code="BUCKWHEAT",
    name="Гречневая крупа",
    *,
    aliases=("гречка",),
    source_id="2512378",
    source_version="2026-04-30",
    kcal="331.600521",
):
    return TrustedFoodIngredientSeed(
        canonical_code=code,
        canonical_name=name,
        category_code="grains",
        default_unit="g",
        density_g_per_ml=None,
        edible_fraction=None,
        allergens_reviewed=False,
        allergen_codes=(),
        storage_profile_code=None,
        aliases=tuple(TrustedAliasSeed(value) for value in aliases),
        nutrition=TrustedNutritionSeed(
            basis_grams=Decimal("100"),
            kcal=Decimal(kcal),
            protein_g=Decimal("11.065340"),
            fat_g=Decimal("3.039000"),
            carbohydrates_g=Decimal("71.130660"),
            fiber_g=Decimal("4.046000"),
            source_name="USDA_FDC",
            source_id=source_id,
            source_version=source_version,
            source_data_type="Foundation",
            verified_at=NOW,
            estimated=None,
        ),
    )


def test_multi_table_create_roundtrips_uuid_utc_exact_decimal_and_provenance(
    catalogue_engine,
):
    config, engine = catalogue_engine
    service = create_food_catalogue_service(engine)

    created = service.add_trusted_ingredient(seed())

    with SqlAlchemyFoodCatalogueReadScope(engine) as scope:
        actual = scope.ingredients.get(created.id)
        aliases = scope.aliases.list_for_ingredient(created.id)
        nutrition = scope.nutrition_profiles.get_current(created.id)

    assert actual == created
    assert actual is not None and actual.id.version == 4
    assert aliases[0].alias_key == "гречка"
    assert nutrition is not None
    assert nutrition.kcal == Decimal("331.600521")
    assert nutrition.created_at.tzinfo is timezone.utc
    with sqlite3.connect(config.path) as connection:
        stored = connection.execute(
            "SELECT id, kcal FROM food_nutrition_profiles"
        ).fetchone()
    assert stored == (nutrition.id.hex, "331.600521")


def test_search_supports_code_name_alias_contains_dedup_and_deterministic_order(
    catalogue_engine,
):
    _, engine = catalogue_engine
    service = create_food_catalogue_service(engine)
    buckwheat = service.add_trusted_ingredient(seed())
    yogurt = service.add_trusted_ingredient(
        seed(
            "YOGURT_GREEK_NONFAT",
            "Йогурт греческий обезжиренный",
            aliases=("греческий йогурт",),
            source_id="330137",
            kcal="61",
        )
    )

    assert service.search("BUCKWHEAT") == [buckwheat]
    assert service.search("гречка") == [buckwheat]
    assert service.search("греч")[0] == buckwheat
    assert service.search("греч") == [buckwheat, yogurt]
    assert service.search("круп") == [buckwheat]


def test_alias_and_canonical_name_cross_collisions_are_rejected(catalogue_engine):
    _, engine = catalogue_engine
    service = create_food_catalogue_service(engine)
    buckwheat = service.add_trusted_ingredient(seed())

    with pytest.raises(FoodCatalogueConflictError, match="collides"):
        service.add_trusted_ingredient(
            seed(
                "OTHER_GRAIN",
                "Гречка",
                aliases=(),
                source_id="other",
            )
        )

    rice = service.add_trusted_ingredient(
        seed("RICE_WHITE", "Рис белый", aliases=(), source_id="2512381")
    )
    with pytest.raises(FoodCatalogueConflictError, match="another"):
        service.add_alias(rice.id, alias="гречка")

    assert service.get(buckwheat.id) == buckwheat


def test_nutrition_new_version_becomes_current_and_history_is_immutable(
    catalogue_engine,
):
    _, engine = catalogue_engine
    service = create_food_catalogue_service(engine)
    ingredient = service.add_trusted_ingredient(seed())

    newer = replace(
        seed().nutrition,
        source_version="2027-04-30",
        kcal=Decimal("332.000000"),
    )
    current = service.attach_nutrition_profile(ingredient.id, newer)

    with SqlAlchemyFoodCatalogueReadScope(engine) as scope:
        old = scope.nutrition_profiles.get_by_provenance(
            ingredient.id, "USDA_FDC", "2512378", "2026-04-30"
        )
        assert scope.nutrition_profiles.get_current(ingredient.id) == current
    assert old is not None and old.is_current is False

    conflicting = replace(newer, kcal=Decimal("333"))
    with pytest.raises(FoodCatalogueConflictError, match="different"):
        service.attach_nutrition_profile(ingredient.id, conflicting)


def test_deactivation_hides_search_but_preserves_direct_history(catalogue_engine):
    _, engine = catalogue_engine
    service = create_food_catalogue_service(engine)
    ingredient = service.add_trusted_ingredient(seed())

    deactivated = service.deactivate(ingredient.id)

    assert deactivated.is_active is False
    assert service.search("греч") == []
    assert service.list_active() == []
    assert service.get(ingredient.id) == deactivated
    with SqlAlchemyFoodCatalogueReadScope(engine) as scope:
        assert scope.aliases.list_for_ingredient(ingredient.id)
        assert scope.nutrition_profiles.get_current(ingredient.id) is not None


def test_uncommitted_multi_table_creation_is_atomic(catalogue_engine):
    _, engine = catalogue_engine
    service = create_food_catalogue_service(engine)
    entry = seed()

    with pytest.raises(RuntimeError, match="simulated"):
        with SqlAlchemyFoodCatalogueUnitOfWork(engine) as scope:
            # Reuse the public service's already validated factory path in a nested
            # command would use another UoW, so prove adapter atomicity directly by
            # raising before any explicit terminal operation.
            from app.domain.food_ingredients import FoodIngredient
            from app.domain.food_ingredients import normalize_unicode_search_key
            from uuid import uuid4

            candidate = FoodIngredient(
                id=uuid4(),
                canonical_code=entry.canonical_code,
                canonical_name=entry.canonical_name,
                canonical_name_key=normalize_unicode_search_key(entry.canonical_name),
                category_code=entry.category_code,
                default_unit=entry.default_unit,
                density_g_per_ml=None,
                edible_fraction=None,
                allergens_reviewed=False,
                allergen_codes=(),
                storage_profile_code=None,
                is_active=True,
                created_at=NOW,
                updated_at=NOW,
            )
            scope.ingredients.add(candidate)
            raise RuntimeError("simulated command failure")

    assert service.list_active() == []


def assert_repositories_revoked(scope):
    for attribute in ("ingredients", "aliases", "nutrition_profiles"):
        with pytest.raises(RuntimeError, match="not active"):
            getattr(scope, attribute)


def test_successful_commit_and_rollback_revoke_repository_handles(catalogue_engine):
    _, engine = catalogue_engine
    committed_scope = SqlAlchemyFoodCatalogueUnitOfWork(engine)
    with committed_scope:
        committed_scope.commit()
        assert_repositories_revoked(committed_scope)

    rolled_back_scope = SqlAlchemyFoodCatalogueUnitOfWork(engine)
    with rolled_back_scope:
        rolled_back_scope.rollback()
        assert_repositories_revoked(rolled_back_scope)


def test_failed_commit_revokes_handles_and_later_uow_is_clean(catalogue_engine):
    _, engine = catalogue_engine
    scope = SqlAlchemyFoodCatalogueUnitOfWork(engine)

    with pytest.raises(FoodCataloguePersistenceConflictError):
        with scope:
            retained_connection = scope._scope.adapter_connection
            retained_connection.execute(
                deferred_child_table.insert().values(id=1, parent_id=999)
            )
            scope.commit()

    assert retained_connection.closed
    assert_repositories_revoked(scope)

    service = create_food_catalogue_service(engine)
    expected = service.add_trusted_ingredient(seed())
    assert service.get(expected.id) == expected


def test_failed_rollback_revokes_handles_and_later_uow_is_clean(catalogue_engine):
    _, engine = catalogue_engine
    service = create_food_catalogue_service(engine)
    ingredient = service.add_trusted_ingredient(seed(aliases=()))
    scope = SqlAlchemyFoodCatalogueUnitOfWork(engine)
    uncertain_alias = IngredientAlias(
        id=uuid4(),
        food_ingredient_id=ingredient.id,
        alias="неопределенный откат",
        alias_key="неопределенный откат",
        language_code="ru",
        created_at=NOW,
    )

    def fail_rollback(connection):
        del connection
        raise RuntimeError("simulated rollback failure")

    with pytest.raises(RuntimeError, match="simulated rollback failure"):
        with scope:
            retained_connection = scope._scope.adapter_connection
            scope.aliases.add(uncertain_alias)
            event.listen(engine, "rollback", fail_rollback, once=True)
            scope.rollback()

    assert retained_connection.closed
    assert_repositories_revoked(scope)

    later_alias = replace(
        uncertain_alias,
        id=uuid4(),
        alias="последующая запись",
        alias_key="последующая запись",
    )
    with SqlAlchemyFoodCatalogueUnitOfWork(engine) as later_scope:
        assert later_scope.aliases.get_by_key(uncertain_alias.alias_key) is None
        later_scope.aliases.add(later_alias)
        later_scope.commit()
    with SqlAlchemyFoodCatalogueReadScope(engine) as read_scope:
        assert read_scope.aliases.get_by_key(uncertain_alias.alias_key) is None
        assert read_scope.aliases.get_by_key(later_alias.alias_key) == later_alias


def test_read_scope_has_no_commit_and_committed_write_is_later_visible(
    catalogue_engine,
):
    _, engine = catalogue_engine
    service = create_food_catalogue_service(engine)
    expected = service.add_trusted_ingredient(seed())

    with SqlAlchemyFoodCatalogueReadScope(engine) as scope:
        assert not hasattr(scope, "commit")
        assert scope.ingredients.get(expected.id) == expected
