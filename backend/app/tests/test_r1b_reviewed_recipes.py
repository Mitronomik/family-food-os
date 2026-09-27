from dataclasses import replace
from decimal import Decimal
import shutil
import sqlite3

import pytest
from sqlalchemy import event

from app.db import migrations
from app.db.config import DatabaseConfig
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
from app.persistence.sqlalchemy_core.food_recipe_composition import (
    create_food_recipe_catalogue_service,
)
from app.seed.food_ingredients import seed_food_ingredients
from app.seed.r1b_reviewed_recipes import (
    BLOCKED_IDS,
    PUBLISH_IDS,
    load_r1b_recipe_seeds,
    seed_r1b_recipes,
)
from app.seed.ru_food_data import seed_ru_food_data
from app.seed.ru_nut_db_r1a import seed_ru_nut_db_r1a
from app.seed.ru_nut_db_step4 import seed_ru_nut_db_step4
from app.services.food_recipes import RecipeCatalogueConflictError


@pytest.fixture(scope="module")
def baseline(tmp_path_factory):
    config = DatabaseConfig(path=tmp_path_factory.mktemp("r1b-base") / "base.sqlite")
    migrations.apply_migrations(config)
    seed_food_ingredients(config)
    seed_ru_food_data(config)
    seed_ru_nut_db_step4(config)
    seed_ru_nut_db_r1a(config)
    return config


@pytest.fixture
def database(baseline, tmp_path):
    config = DatabaseConfig(path=tmp_path / "r1b.sqlite")
    shutil.copyfile(baseline.path, config.path)
    return config


def db_dump(config: DatabaseConfig) -> str:
    with sqlite3.connect(config.path) as db:
        return "\n".join(db.iterdump())


def test_r1b_package_freezes_three_publish_and_two_process_blockers():
    seeds, package = load_r1b_recipe_seeds()

    assert tuple(seed.version.source_recipe_id for seed in seeds) == PUBLISH_IDS
    assert tuple(
        row["source_recipe_id"]
        for row in package["candidates"]
        if row["disposition"] == "BLOCKED"
    ) == BLOCKED_IDS
    assert {
        row["source_recipe_id"]: row["reason"]
        for row in package["candidates"]
        if row["disposition"] == "BLOCKED"
    } == {
        "USSR82-467": "UNQUANTIFIED_PROCESS_INGREDIENT_SALT",
        "USSR82-492": "UNQUANTIFIED_PROCESS_INGREDIENT_SALT",
    }

    assert [seed.version.source_output_g for seed in seeds] == [
        Decimal("40.000000"),
        Decimal("160.000000"),
        Decimal("75.000000"),
    ]
    assert [len(seed.version.ingredients) for seed in seeds] == [1, 7, 2]
    assert [len(seed.version.steps) for seed in seeds] == [2, 4, 2]
    assert all(seed.initial_is_active is False for seed in seeds)
    published = [
        row for row in package["candidates"] if row["disposition"] == "PUBLISH"
    ]
    assert all(
        row["activation"] == "INACTIVE_PENDING_TRANSFORMATION_AUTHORITY"
        for row in published
    )
    assert all(
        isinstance(row["activation_reason"], str) and row["activation_reason"].strip()
        for row in published
    )


def test_r1b_fresh_publication_bindings_input_energy_and_inactive_replay(database):
    first = seed_r1b_recipes(database)

    assert first.dependency_bundle_created_count == 0
    assert first.recipe_summary.recipes_inserted == 3
    assert first.recipe_summary.versions_inserted == 3
    assert first.recipe_summary.ingredients_inserted == 10
    assert first.recipe_summary.steps_inserted == 8
    assert first.binding_fresh_count == 10
    assert first.binding_replay_count == 0
    assert first.activated_count == 0
    assert first.input_energy_kcal == (
        ("USSR82-453", Decimal("58.800000")),
        ("USSR82-1081", Decimal("368.114000")),
        ("USSR82-697", Decimal("255.892000")),
    )

    with sqlite3.connect(database.path) as db:
        rows = db.execute(
            """
            SELECT r.canonical_code, r.is_active, v.source_recipe_id,
                   v.source_output_g, v.source_output_text
            FROM food_recipes r
            JOIN food_recipe_versions v ON v.recipe_id = r.id
            WHERE v.source_name = 'USSR82'
              AND v.source_version = ?
            ORDER BY v.source_recipe_id
            """,
            (
                "sha256:6ac7dfb300844fd996aee6d20b4e7e6aa421dd517367ab1f59120812fee104d5",
            ),
        ).fetchall()
        assert rows == [
            (
                "USSR82_1081_BLINI",
                0,
                "USSR82-1081",
                "160.000000",
                "III — с маслом; выход 160 г",
            ),
            (
                "USSR82_453_BOILED_EGGS",
                0,
                "USSR82-453",
                "40.000000",
                "выход 40 г",
            ),
            (
                "USSR82_697_BOILED_CHICKEN",
                0,
                "USSR82-697",
                "75.000000",
                "выход основного отварного продукта 75 г; без гарнира/соуса",
            ),
        ]
        assert db.execute(
            "SELECT COUNT(*) FROM recipe_ingredient_composition_bindings "
            "WHERE registry_version='RU_NUTRIENT_REGISTRY_V2'"
        ).fetchone()[0] >= 10
        for code, source_name, source_id, version in (
            ("EGG", "USDA_FDC", "748967", 1),
            ("BUTTER_UNSALTED", "USDA_FDC", "173430", 1),
        ):
            row = db.execute(
                """
                SELECT p.is_current, v.version
                FROM food_ingredients i
                JOIN food_nutrition_profiles p ON p.food_ingredient_id = i.id
                JOIN food_composition_versions v ON v.profile_id = p.id
                WHERE i.canonical_code = ?
                  AND p.source_name = ?
                  AND p.source_id = ?
                """,
                (code, source_name, source_id),
            ).fetchone()
            assert row == (1, version)
        assert db.execute(
            """
            SELECT COUNT(*)
            FROM food_ingredients i
            JOIN food_nutrition_profiles p ON p.food_ingredient_id = i.id
            WHERE i.canonical_code IN ('EGG', 'BUTTER_UNSALTED')
              AND p.source_name = 'FIC_RU_NUT_DB'
              AND p.source_id IN ('2287', '1418')
            """
        ).fetchone()[0] == 0
        assert db.execute("PRAGMA foreign_key_check").fetchall() == []

    before = db_dump(database)
    replay = seed_r1b_recipes(database)
    assert replay.dependency_bundle_created_count == 0
    assert replay.recipe_summary.recipes_inserted == 0
    assert replay.recipe_summary.versions_existing == 3
    assert replay.binding_fresh_count == 0
    assert replay.binding_replay_count == 10
    assert replay.activated_count == 0
    assert replay.input_energy_kcal == first.input_energy_kcal
    assert db_dump(database) == before


def test_r1b_output_change_conflicts_with_same_provenance(database):
    seed_r1b_recipes(database)
    seeds, _ = load_r1b_recipe_seeds()
    changed = replace(
        seeds[0],
        version=replace(seeds[0].version, source_output_g=Decimal("41")),
    )
    engine = create_sqlite_engine(database)
    try:
        service = create_food_recipe_catalogue_service(engine)
        with pytest.raises(RecipeCatalogueConflictError, match="trusted seed"):
            service.preflight_trusted_seed(changed)
    finally:
        engine.dispose()


def test_r1b_partial_prior_recipe_batch_fails_without_filling(database):
    seeds, _ = load_r1b_recipe_seeds()
    engine = create_sqlite_engine(database)
    try:
        catalogue = create_food_recipe_catalogue_service(engine)
        catalogue.reconcile_seed((seeds[0],), strict_history=True)
    finally:
        engine.dispose()

    before = db_dump(database)
    with pytest.raises(ValueError, match="Частично опубликованный R1-B Recipe batch"):
        seed_r1b_recipes(database)
    assert db_dump(database) == before


def test_r1b_recipe_batch_failure_rolls_back_every_recipe(database):
    seeds, _ = load_r1b_recipe_seeds()
    engine = create_sqlite_engine(database)
    before = db_dump(database)
    state = {"versions": 0}

    def fail_on_second_version(
        connection, cursor, statement, parameters, context, executemany
    ):
        del connection, cursor, parameters, context, executemany
        if statement.strip().startswith("INSERT INTO food_recipe_versions"):
            state["versions"] += 1
            if state["versions"] == 2:
                raise RuntimeError("injected R1-B recipe failure")

    event.listen(engine, "before_cursor_execute", fail_on_second_version)
    try:
        catalogue = create_food_recipe_catalogue_service(engine)
        with pytest.raises(RuntimeError, match="injected R1-B recipe failure"):
            catalogue.reconcile_seed(seeds, strict_history=True)
    finally:
        event.remove(engine, "before_cursor_execute", fail_on_second_version)
        engine.dispose()

    assert state["versions"] == 2
    assert db_dump(database) == before


def test_r1b_does_not_publish_yield_or_retention_authority(database):
    with sqlite3.connect(database.path) as db:
        before = {
            "yield": db.execute("SELECT COUNT(*) FROM food_yield_models").fetchone()[0],
            "retention": db.execute(
                "SELECT COUNT(*) FROM food_retention_profiles"
            ).fetchone()[0],
            "transformations": db.execute(
                "SELECT COUNT(*) FROM food_transformations"
            ).fetchone()[0],
        }

    seed_r1b_recipes(database)

    with sqlite3.connect(database.path) as db:
        after = {
            "yield": db.execute("SELECT COUNT(*) FROM food_yield_models").fetchone()[0],
            "retention": db.execute(
                "SELECT COUNT(*) FROM food_retention_profiles"
            ).fetchone()[0],
            "transformations": db.execute(
                "SELECT COUNT(*) FROM food_transformations"
            ).fetchone()[0],
        }
    assert after == before
