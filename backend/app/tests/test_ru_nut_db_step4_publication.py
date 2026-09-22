"""Step 4 runtime publication of the licensed five-food RU-NUT-DB batch."""

from dataclasses import replace
from datetime import datetime, timezone
from decimal import Decimal
import json
import shutil
import sqlite3

import pytest
from sqlalchemy import event

from app.db import migrations
from app.db.config import DatabaseConfig
from app.domain.food_composition import MassState
from app.domain.food_ingredients import NutritionObservationState
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
from app.persistence.sqlalchemy_core.nutrition_publication import (
    SqlAlchemyNutritionPublicationUnitOfWork,
)
from app.persistence.sqlalchemy_core.nutrition_read_scope import (
    SqlAlchemyNutritionReadScope,
)
from app.seed.food_ingredients import seed_food_ingredients
from app.seed.ru_food_data import seed_ru_food_data
from app.seed.ru_nut_db_step4 import (
    ATTRIBUTION,
    PACKAGE,
    load_ru_nut_db_step4_bundles,
)
from app.services.nutrition_publication import (
    NutritionPublicationConflictError,
    NutritionPublicationContractError,
    ReviewedNutritionBatchPublicationService,
    ReviewedNutritionPublicationService,
)

NOW = datetime(2026, 9, 22, 12, tzinfo=timezone.utc)
STEP4_CODES = (
    "SUGAR",
    "CARROT_RED_RAW",
    "CABBAGE_GREEN",
    "BEET",
    "RICE_GROATS",
)
EXISTING_CURRENT_CODES = ("SUGAR", "CABBAGE_GREEN", "BEET", "CARROT")


@pytest.fixture(scope="module")
def baseline(tmp_path_factory):
    config = DatabaseConfig(path=tmp_path_factory.mktemp("step4-base") / "base.sqlite")
    migrations.apply_migrations(config)
    seed_food_ingredients(config)
    seed_ru_food_data(config)
    return config


@pytest.fixture
def database(baseline, tmp_path):
    config = DatabaseConfig(path=tmp_path / "step4.sqlite")
    shutil.copyfile(baseline.path, config.path)
    return config


def db_dump(config: DatabaseConfig) -> str:
    with sqlite3.connect(config.path) as db:
        return "\n".join(db.iterdump())


def assert_fk_clean(config: DatabaseConfig) -> None:
    with sqlite3.connect(config.path) as db:
        assert db.execute("PRAGMA foreign_key_check").fetchall() == []


def current_profiles(config: DatabaseConfig) -> dict[str, tuple]:
    placeholders = ",".join("?" for _ in EXISTING_CURRENT_CODES)
    with sqlite3.connect(config.path) as db:
        rows = db.execute(
            f"""
            SELECT i.canonical_code, p.id, p.source_name, p.source_id,
                   p.source_version, p.kcal, p.protein_g, p.fat_g,
                   p.carbohydrates_g, p.fiber_g
            FROM food_ingredients i
            JOIN food_nutrition_profiles p ON p.food_ingredient_id = i.id
            WHERE p.is_current = 1
              AND i.canonical_code IN ({placeholders})
            ORDER BY i.canonical_code
            """,
            EXISTING_CURRENT_CODES,
        ).fetchall()
    return {row[0]: row[1:] for row in rows}


def batch_service(engine):
    return ReviewedNutritionBatchPublicationService(
        lambda: SqlAlchemyNutritionPublicationUnitOfWork(engine),
        clock=lambda: NOW,
    )


def single_service(engine):
    return ReviewedNutritionPublicationService(
        lambda: SqlAlchemyNutritionPublicationUnitOfWork(engine),
        clock=lambda: NOW,
    )


def test_runtime_package_is_exact_five_records_and_90_values():
    bundles = load_ru_nut_db_step4_bundles()
    assert tuple(bundle.ingredient.canonical_code for bundle in bundles) == STEP4_CODES
    assert [bundle.vector.value_count for bundle in bundles] == [18] * 5

    rows = [json.loads(bundle.vector.observations_json) for bundle in bundles]
    assert [len(value) for value in rows] == [26] * 5
    assert sum(len(value) for value in rows) == 130
    assert sum(
        row["observation"]["source_state"] == "published_zero"
        for record in rows
        for row in record
    ) == 43
    assert sum(
        row["observation"]["source_state"] == "published_numeric"
        for record in rows
        for row in record
    ) == 87


def test_runtime_package_pins_exact_raw_source_record_hashes():
    publication = json.loads((PACKAGE / "publication.json").read_text())
    assert {
        row["source"]["source_code"]: row["source"]["raw_record_sha256"]
        for row in publication["records"]
    } == {
        "1150": "b869ae0c72ffb850d52d303ab1288e3ec539938f4cd73ba8709b049393a3994f",
        "1187": "a0587cd2f7cf9b49e586f7b188f9164020af1cbbabd2cb36bcf2bccba7622b8d",
        "1184": "db34f8dfb25ec1d0289c78b7863cae3e21dac19365f9d6913b5842c00db3a109",
        "1204": "c241cffe9f38f562812fba3a42d7cb113c7e7e6da7036f976b8aaca5c3078702",
        "66": "08d4a8a374095622d5f5a52f4c8b88ce956a0546ab5ebcaf115c4e4437a71c85",
    }


def test_runtime_package_retains_license_attribution_and_source_link():
    readme = (PACKAGE / "README.md").read_text()
    assert ATTRIBUTION in readme
    assert (
        "https://ion.ru/nauka/baza-dannykh-khimicheskogo-sostava/"
        "1-1-baza-dannykh/1.1_baza%20dannih.html"
    ) in readme


def test_changed_runtime_payload_fails_before_database_creation(tmp_path):
    package = tmp_path / "package"
    shutil.copytree(PACKAGE, package)
    with (package / "publication.json").open("a") as stream:
        stream.write(" ")
    config = DatabaseConfig(path=tmp_path / "should-not-exist.sqlite")

    from app.seed.ru_nut_db_step4 import seed_ru_nut_db_step4

    with pytest.raises(ValueError, match="Изменён"):
        seed_ru_nut_db_step4(config, package=package)
    assert not config.path.exists()


def test_actual_batch_commits_once_and_exact_replay_is_zero_write(database):
    bundles = load_ru_nut_db_step4_bundles()
    before_current = current_profiles(database)
    assert set(before_current) == set(EXISTING_CURRENT_CODES)

    engine = create_sqlite_engine(database)
    commits = 0

    def count_commit(connection):
        nonlocal commits
        del connection
        commits += 1

    event.listen(engine, "commit", count_commit)
    try:
        first = batch_service(engine).publish_batch(bundles)
        assert commits == 1
        assert len(first.results) == 5
        assert first.bundle_created_count == 5
        assert first.ingredient_created_count == 2
        assert first.nutrient_value_count == 90

        with SqlAlchemyNutritionReadScope(engine) as read:
            values_by_code = {}
            for bundle, result in zip(bundles, first.results, strict=True):
                food = read.ingredients.get_by_code(bundle.ingredient.canonical_code)
                assert food.id == result.ingredient_id
                profile = read.nutrition_profiles.get_by_provenance(
                    food.id,
                    bundle.profile.source_name,
                    bundle.profile.source_id,
                    bundle.profile.source_version,
                )
                assert profile is not None and profile.id == result.profile_id
                assert profile.is_current is False
                assert profile.carbohydrates_g is None
                vector = read.nutrient_vectors.get(profile.id)
                assert len(vector.values) == 18
                assert len(json.loads(vector.observations_json)) == 26
                observations = {
                    item.source_field: item
                    for item in read.nutrition_profiles.list_observations(profile.id)
                }
                assert observations["kcal"].state is NutritionObservationState.VALUE
                assert (
                    observations["carbohydrates_g"].state
                    is NutritionObservationState.METHOD_INCOMPATIBLE
                )
                values_by_code[food.canonical_code] = (profile, vector)

            sugar_profile, sugar_vector = values_by_code["SUGAR"]
            assert sugar_profile.kcal == Decimal("399.200000")
            assert sugar_profile.protein_g == Decimal("0.000000")
            assert sugar_profile.fat_g == Decimal("0.000000")
            assert sugar_profile.fiber_g == Decimal("0.000000")
            assert sugar_vector.amount("PROTEIN") == Decimal("0.0")
            assert sugar_vector.amount("FAT_TOTAL") == Decimal("0.0")
            assert sugar_vector.amount("FIBER_TOTAL_DIETARY") == Decimal("0.0")
            assert sugar_vector.amount("SUGARS_TOTAL") == Decimal("99.8")

            for code in ("CARROT_RED_RAW", "RICE_GROATS"):
                assert read.nutrition_profiles.get_current(
                    read.ingredients.get_by_code(code).id
                ) is None

        assert current_profiles(database) == before_current

        with sqlite3.connect(database.path) as db:
            compositions = db.execute(
                """
                SELECT i.canonical_code, v.version, v.input_state
                FROM food_composition_versions v
                JOIN food_ingredients i ON i.id = v.food_ingredient_id
                JOIN food_nutrition_profiles p ON p.id = v.profile_id
                WHERE p.source_name = 'FIC_RU_NUT_DB'
                ORDER BY i.canonical_code
                """
            ).fetchall()
        assert compositions == [
            ("BEET", 1, MassState.INPUT.value),
            ("CABBAGE_GREEN", 2, MassState.INPUT.value),
            ("CARROT_RED_RAW", 1, MassState.INPUT.value),
            ("RICE_GROATS", 1, MassState.INPUT.value),
            ("SUGAR", 2, MassState.INPUT.value),
        ]

        before_replay = db_dump(database)
        second = batch_service(engine).publish_batch(bundles)
        assert commits == 1
        assert db_dump(database) == before_replay
        assert second.bundle_created_count == 0
        assert second.ingredient_created_count == 0
        assert [item.ingredient_id for item in second.results] == [
            item.ingredient_id for item in first.results
        ]
        assert [item.profile_id for item in second.results] == [
            item.profile_id for item in first.results
        ]
        assert [item.composition_version_id for item in second.results] == [
            item.composition_version_id for item in first.results
        ]
        assert_fk_clean(database)
    finally:
        event.remove(engine, "commit", count_commit)
        engine.dispose()


def test_fifth_food_identity_conflict_rolls_back_first_four(database):
    bundles = load_ru_nut_db_step4_bundles()
    engine = create_sqlite_engine(database)
    try:
        corrupted_fifth = replace(
            bundles[-1],
            ingredient=replace(
                bundles[-1].ingredient,
                canonical_name="Конфликтная рисовая крупа",
            ),
        )
        single_service(engine).publish(corrupted_fifth)
        before = db_dump(database)

        with pytest.raises(NutritionPublicationConflictError):
            batch_service(engine).publish_batch(bundles)

        assert db_dump(database) == before
        assert_fk_clean(database)
    finally:
        engine.dispose()


@pytest.mark.parametrize("food_number", [1, 2, 3, 4, 5])
def test_failure_after_each_food_rolls_back_whole_batch(database, food_number):
    bundles = load_ru_nut_db_step4_bundles()
    engine = create_sqlite_engine(database)
    before = db_dump(database)
    state = {"composition_count": 0, "armed": False}

    def fail_after_food(
        connection, cursor, statement, parameters, context, executemany
    ):
        del connection, cursor, parameters, context, executemany
        sql = statement.strip()
        if sql.startswith("INSERT INTO food_composition_versions"):
            state["composition_count"] += 1
            if state["composition_count"] == food_number:
                state["armed"] = True
            return
        if state["armed"] and sql.startswith("SELECT"):
            raise RuntimeError(f"injected after food {food_number}")

    event.listen(engine, "before_cursor_execute", fail_after_food)
    try:
        with pytest.raises(RuntimeError, match="injected after food"):
            batch_service(engine).publish_batch(bundles)
    finally:
        event.remove(engine, "before_cursor_execute", fail_after_food)
        engine.dispose()

    assert state["composition_count"] == food_number
    assert db_dump(database) == before
    assert_fk_clean(database)


def test_reviewed_create_identity_without_bundle_is_partial_prior_state(database):
    bundles = load_ru_nut_db_step4_bundles()
    engine = create_sqlite_engine(database)
    try:
        service = single_service(engine)
        with SqlAlchemyNutritionPublicationUnitOfWork(engine) as uow:
            ingredient, created = service._resolve_ingredient(
                uow, bundles[1].ingredient, now=NOW
            )
            assert created is True
            uow.ingredients.add(ingredient)
            uow.commit()
        before = db_dump(database)

        with pytest.raises(
            NutritionPublicationConflictError,
            match="уже существует без полного проверенного bundle",
        ):
            batch_service(engine).publish_batch(bundles)

        assert db_dump(database) == before
        assert_fk_clean(database)
    finally:
        engine.dispose()


@pytest.mark.parametrize("published_prefix", [1, 2, 3, 4])
def test_partial_prior_batch_conflicts_without_filling_missing_bundles(
    database, published_prefix
):
    bundles = load_ru_nut_db_step4_bundles()
    engine = create_sqlite_engine(database)
    try:
        for bundle in bundles[:published_prefix]:
            single_service(engine).publish(bundle)
        before = db_dump(database)

        with pytest.raises(
            NutritionPublicationConflictError,
            match="Частично опубликованный batch",
        ):
            batch_service(engine).publish_batch(bundles)

        assert db_dump(database) == before
        assert_fk_clean(database)
    finally:
        engine.dispose()


def test_duplicate_batch_contract_fails_before_write(database):
    bundles = load_ru_nut_db_step4_bundles()
    engine = create_sqlite_engine(database)
    before = db_dump(database)
    try:
        with pytest.raises(NutritionPublicationContractError):
            batch_service(engine).publish_batch((bundles[0], bundles[0]))
    finally:
        engine.dispose()
    assert db_dump(database) == before


def test_no_book2002_values_enter_runtime_payload():
    publication = json.loads((PACKAGE / "publication.json").read_text())
    by_code = {
        row["platform"]["canonical_code"]: row
        for row in publication["records"]
    }
    assert by_code["RICE_GROATS"]["nutrients"]["kcal"] == "322.6"
    assert by_code["RICE_GROATS"]["nutrients"]["carbh"] == "71.4"
    assert by_code["CARROT_RED_RAW"]["nutrients"]["kcal"] == "33.7"
    assert by_code["CABBAGE_GREEN"]["nutrients"]["kcal"] == "26.9"
