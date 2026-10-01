import shutil
import sqlite3
from dataclasses import replace
from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.db.config import DatabaseConfig
from app.db.migrations import MIGRATION_MODULES, apply_migrations
from app.domain.errors import DomainValidationError
from app.domain.food_recipes import (
    MealTypeCode,
    RecipeVersion,
    RightsReviewStatus,
    VerificationStatus,
)
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
from app.persistence.sqlalchemy_core.food_recipe_composition import (
    create_food_recipe_catalogue_service,
)
from app.persistence.sqlalchemy_core.food_recipe_repositories import (
    SqlAlchemyRecipeVersionRepository,
)
from app.seed.food_recipes import load_seed_entries, seed_food_recipes
from app.services.food_recipes import RecipeCatalogueConflictError
from app.services.food_recipe_contracts import RecipeCataloguePersistenceConflictError

NOW = datetime(2026, 9, 27, tzinfo=timezone.utc)


def _migrate_through(database_path, suffix):
    original = list(MIGRATION_MODULES)
    cutoff = next(
        index for index, module in enumerate(original) if module.endswith(suffix)
    )
    try:
        MIGRATION_MODULES[:] = original[: cutoff + 1]
        return apply_migrations(DatabaseConfig(path=database_path))
    finally:
        MIGRATION_MODULES[:] = original


def _version(**changes):
    recipe_id = uuid4()
    values = dict(
        id=uuid4(),
        recipe_id=recipe_id,
        version_number=1,
        base_servings=Decimal("1"),
        meal_type_code=MealTypeCode.MAIN,
        prep_time_minutes=None,
        cook_time_minutes=None,
        total_time_minutes=None,
        difficulty_code=None,
        batch_friendly=None,
        freezable=None,
        storage_days_fridge=None,
        storage_days_freezer=None,
        verification_status=VerificationStatus.SOURCE_VERIFIED,
        verified_at=NOW,
        source_name="USSR82",
        source_recipe_id="USSR82-TEST",
        source_url="https://example.test/recipe",
        source_version="sha256:" + "a" * 64,
        source_retrieved_at=None,
        source_document_sha256="a" * 64,
        source_original_servings=Decimal("1"),
        rights_review_status=RightsReviewStatus.REVIEWED,
        rights_basis="Reviewed normative recipe facts.",
        created_from_version_id=None,
        change_note="Fixture.",
        created_at=NOW,
        source_output_g=Decimal("110"),
        source_output_text="выход 110 г",
    )
    values.update(changes)
    return RecipeVersion(**values)


def test_recipe_version_source_output_is_exact_decimal_truth():
    value = _version(
        source_output_g=Decimal("110.1234564"),
        source_output_text="  выход   110 г  ",
    )

    assert value.source_output_g == Decimal("110.123456")
    assert value.source_output_text == "выход 110 г"


@pytest.mark.parametrize(
    "value",
    [
        0,
        1.5,
        "110",
        Decimal("0"),
        Decimal("-1"),
        Decimal("0.0000004"),
        Decimal("NaN"),
        Decimal("Infinity"),
    ],
)
def test_recipe_version_rejects_invalid_source_output_mass(value):
    with pytest.raises(DomainValidationError):
        _version(source_output_g=value)


def test_recipe_version_allows_unknown_or_text_only_source_output():
    unknown = _version(source_output_g=None, source_output_text=None)
    text_only = _version(source_output_g=None, source_output_text="выход не оцифрован")

    assert unknown.source_output_g is None
    assert unknown.source_output_text is None
    assert text_only.source_output_g is None
    assert text_only.source_output_text == "выход не оцифрован"

    with pytest.raises(DomainValidationError):
        _version(source_output_g=None, source_output_text="   ")


def test_0040_adds_nullable_output_columns_and_preserves_historical_row(tmp_path):
    database = tmp_path / "upgrade.sqlite"
    _migrate_through(database, "0039_recipe_ingredient_composition_binding")

    recipe_id = uuid4().hex
    version_id = uuid4().hex
    backup = tmp_path / "pre-0040.sqlite"

    with sqlite3.connect(database) as connection:
        connection.execute(
            """
            INSERT INTO food_recipes
            (id, canonical_code, canonical_name, canonical_name_key,
             is_active, created_at, updated_at)
            VALUES (?, 'HISTORICAL_RECIPE', 'Historical Recipe', 'historical recipe',
                    1, '2026-09-27T00:00:00+00:00', '2026-09-27T00:00:00+00:00')
            """,
            (recipe_id,),
        )
        connection.execute(
            """
            INSERT INTO food_recipe_versions
            (id, recipe_id, version_number, base_servings, meal_type_code,
             prep_time_minutes, cook_time_minutes, total_time_minutes,
             difficulty_code, batch_friendly, freezable, storage_days_fridge,
             storage_days_freezer, verification_status, verified_at,
             source_name, source_recipe_id, source_url, source_version,
             source_retrieved_at, source_document_sha256,
             source_original_servings, rights_review_status, rights_basis,
             created_from_version_id, change_note, created_at)
            VALUES (?, ?, 1, '1', 'main',
                    NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL,
                    'SOURCE_VERIFIED', '2026-09-27T00:00:00+00:00',
                    'fixture', 'fixture-1', 'https://example.test/fixture',
                    'v1', NULL, ?, '1', 'REVIEWED', 'fixture rights',
                    NULL, 'historical row', '2026-09-27T00:00:00+00:00')
            """,
            (version_id, recipe_id, "a" * 64),
        )
        connection.commit()

    engine = create_sqlite_engine(DatabaseConfig(path=database))
    try:
        with engine.begin() as connection:
            repository = SqlAlchemyRecipeVersionRepository(connection)
            with pytest.raises(
                RecipeCataloguePersistenceConflictError,
                match="Migration 0040 is required",
            ):
                repository.add_detail(SimpleNamespace(version=_version()))
    finally:
        engine.dispose()

    shutil.copy2(database, backup)
    before_bytes = backup.read_bytes()

    assert apply_migrations(DatabaseConfig(path=database)) == [
        "0040_recipe_version_source_output",
        "0041_meal_pattern_energy_allocation",
        "0042_recipe_prepared_output_nutrition",
    ]

    with sqlite3.connect(database) as connection:
        columns = {
            row[1]: row
            for row in connection.execute("PRAGMA table_info('food_recipe_versions')")
        }
        assert columns["source_output_g"][3] == 0
        assert columns["source_output_text"][3] == 0

        row = connection.execute(
            """
            SELECT id, recipe_id, source_recipe_id, source_output_g, source_output_text
            FROM food_recipe_versions WHERE id=?
            """,
            (version_id,),
        ).fetchone()
        assert row == (version_id, recipe_id, "fixture-1", None, None)

        trigger_names = {
            r[0]
            for r in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='trigger' "
                "AND tbl_name='food_recipe_versions'"
            )
        }
        assert "trg_food_recipe_versions_no_update" in trigger_names
        assert "trg_food_recipe_versions_no_delete" in trigger_names
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []

    shutil.copy2(backup, database)
    assert database.read_bytes() == before_bytes
    assert apply_migrations(DatabaseConfig(path=database)) == [
        "0040_recipe_version_source_output",
        "0041_meal_pattern_energy_allocation",
        "0042_recipe_prepared_output_nutrition",
    ]
    with sqlite3.connect(database) as connection:
        restored = connection.execute(
            "SELECT source_output_g, source_output_text "
            "FROM food_recipe_versions WHERE id=?",
            (version_id,),
        ).fetchone()
        assert restored == (None, None)
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []


def test_0040_sql_checks_reject_nonpositive_or_blank_output(tmp_path):
    database = tmp_path / "checks.sqlite"
    apply_migrations(DatabaseConfig(path=database))

    recipe_id = uuid4().hex
    with sqlite3.connect(database) as connection:
        connection.execute(
            """
            INSERT INTO food_recipes
            (id, canonical_code, canonical_name, canonical_name_key,
             is_active, created_at, updated_at)
            VALUES (?, 'OUTPUT_CHECK', 'Output Check', 'output check',
                    1, '2026-09-27T00:00:00+00:00', '2026-09-27T00:00:00+00:00')
            """,
            (recipe_id,),
        )
        base = dict(
            recipe_id=recipe_id,
            digest="b" * 64,
        )
        sql = """
            INSERT INTO food_recipe_versions
            (id, recipe_id, version_number, base_servings, meal_type_code,
             verification_status, verified_at, source_name, source_recipe_id,
             source_url, source_version, source_document_sha256,
             source_original_servings, rights_review_status, rights_basis,
             change_note, created_at, source_output_g, source_output_text)
            VALUES (?, ?, 1, '1', 'main', 'SOURCE_VERIFIED',
                    '2026-09-27T00:00:00+00:00', 'fixture', 'fixture-2',
                    'https://example.test/fixture', 'v1', ?, '1',
                    'REVIEWED', 'fixture rights', 'fixture',
                    '2026-09-27T00:00:00+00:00', ?, ?)
        """
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(sql, (uuid4().hex, recipe_id, base["digest"], "0", "x"))
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                sql, (uuid4().hex, recipe_id, base["digest"], "10", "   ")
            )


def test_trusted_recipe_replay_includes_source_output(tmp_path):
    config = DatabaseConfig(path=tmp_path / "recipes.sqlite")
    seed_food_recipes(config)
    engine = create_sqlite_engine(config)
    try:
        service = create_food_recipe_catalogue_service(engine)
        source = load_seed_entries()[0]
        seed = replace(
            source,
            canonical_code="OUTPUT_REPLAY_FIXTURE",
            canonical_name="Output Replay Fixture",
            initial_is_active=False,
            version=replace(
                source.version,
                source_name="USSR82",
                source_recipe_id="USSR82-OUTPUT-TEST",
                source_url="https://example.test/output",
                source_version="sha256:" + "c" * 64,
                source_document_sha256="c" * 64,
                source_output_g=Decimal("110"),
                source_output_text="выход 110 г",
            ),
        )

        first = service.reconcile_seed((seed,), strict_history=True)
        replay = service.reconcile_seed((seed,), strict_history=True)

        assert first.recipes_inserted == 1
        assert first.versions_inserted == 1
        assert replay.recipes_inserted == 0
        assert replay.versions_existing == 1

        recipe = service.get_by_code(seed.canonical_code)
        detail = service.get_version_detail(service.list_versions(recipe.id)[0].id)
        assert detail.version.source_output_g == Decimal("110.000000")
        assert detail.version.source_output_text == "выход 110 г"

        changed = replace(
            seed,
            version=replace(seed.version, source_output_g=Decimal("111")),
        )
        with pytest.raises(RecipeCatalogueConflictError, match="trusted seed"):
            service.reconcile_seed((changed,), strict_history=True)
    finally:
        engine.dispose()
