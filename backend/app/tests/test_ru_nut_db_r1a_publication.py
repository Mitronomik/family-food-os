"""R1-A exact dependency publication for the Planner-capacity recipe batch."""

from dataclasses import replace
from datetime import datetime, timezone
import json
import shutil
import sqlite3

import pytest
from sqlalchemy import event

from app.db import migrations
from app.db.config import DatabaseConfig
from app.domain.food_composition import MassState
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
from app.persistence.sqlalchemy_core.nutrition_publication import (
    SqlAlchemyNutritionPublicationUnitOfWork,
)
from app.persistence.sqlalchemy_core.nutrition_read_scope import (
    SqlAlchemyNutritionReadScope,
)
from app.seed.food_ingredients import seed_food_ingredients
from app.seed.ru_food_data import seed_ru_food_data
from app.seed.ru_nut_db_r1a import (
    EXPECTED,
    PACKAGE,
    load_ru_nut_db_r1a_bundles,
)
from app.seed.ru_nut_db_step4 import seed_ru_nut_db_step4
from app.services.nutrition_publication import (
    NutritionPublicationConflictError,
    ReviewedNutritionBatchPublicationService,
    ReviewedNutritionPublicationService,
)

NOW = datetime(2026, 9, 27, 12, tzinfo=timezone.utc)
R1A_CODES = tuple(item[1] for item in EXPECTED)
NEW_CODES = tuple(item[1] for item in EXPECTED if item[4] == "CREATE_REVIEWED")
GENERIC_CODES = (
    "MARGARINE",
    "MILK_WHOLE",
    "SOUR_CREAM_FULL_FAT",
    "COTTAGE_CHEESE_FULL_FAT",
    "CHICKEN_BREAST",
    "CHICKEN_THIGH",
    "ONION_YELLOW",
    "FLOUR_WHEAT",
    "POTATO",
)


@pytest.fixture(scope="module")
def baseline(tmp_path_factory):
    config = DatabaseConfig(path=tmp_path_factory.mktemp("r1a-base") / "base.sqlite")
    migrations.apply_migrations(config)
    seed_food_ingredients(config)
    seed_ru_food_data(config)
    seed_ru_nut_db_step4(config)
    return config


@pytest.fixture
def database(baseline, tmp_path):
    config = DatabaseConfig(path=tmp_path / "r1a.sqlite")
    shutil.copyfile(baseline.path, config.path)
    return config


def db_dump(config: DatabaseConfig) -> str:
    with sqlite3.connect(config.path) as db:
        return "\n".join(db.iterdump())


def assert_fk_clean(config: DatabaseConfig) -> None:
    with sqlite3.connect(config.path) as db:
        assert db.execute("PRAGMA foreign_key_check").fetchall() == []


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


def current_profile_ids(config: DatabaseConfig, codes: tuple[str, ...]) -> dict[str, str]:
    placeholders = ",".join("?" for _ in codes)
    with sqlite3.connect(config.path) as db:
        rows = db.execute(
            f"""
            SELECT i.canonical_code, p.id
            FROM food_ingredients i
            JOIN food_nutrition_profiles p ON p.food_ingredient_id = i.id
            WHERE p.is_current = 1 AND i.canonical_code IN ({placeholders})
            ORDER BY i.canonical_code
            """,
            codes,
        ).fetchall()
    return dict(rows)


def test_package_and_dependency_manifest_are_exact():
    bundles = load_ru_nut_db_r1a_bundles()
    assert tuple(bundle.ingredient.canonical_code for bundle in bundles) == R1A_CODES
    assert [bundle.vector.value_count for bundle in bundles] == [18] * 9
    assert sum(bundle.vector.value_count for bundle in bundles) == 162

    source_rows = [json.loads(bundle.vector.observations_json) for bundle in bundles]
    assert [len(rows) for rows in source_rows] == [26] * 9
    assert sum(len(rows) for rows in source_rows) == 234
    assert sum(
        row["observation"]["source_state"] == "published_zero"
        for record in source_rows
        for row in record
    ) == 66
    assert sum(
        row["observation"]["source_state"] == "published_numeric"
        for record in source_rows
        for row in record
    ) == 168

    manifest = json.loads((PACKAGE / "dependency-manifest.json").read_text())
    assert manifest["counts"] == {
        "recipe_count": 7,
        "source_relationship_row_count": 32,
        "unique_dependency_count": 20,
        "accepted_reuse_dependency_count": 9,
        "r1a_publication_dependency_count": 9,
        "blocked_dependency_count": 2,
        "dependency_ready_recipe_count_after_r1a": 5,
        "blocked_recipe_count_after_r1a": 2,
    }
    assert {
        item["id"]: item["disposition"] for item in manifest["dependencies"]
    }["ING-0014"] == "BLOCKED"
    assert {
        item["id"]: item["disposition"] for item in manifest["dependencies"]
    }["ING-0038"] == "BLOCKED"
    assert sum(
        item["post_r1a_dependency_status"] == "READY_FOR_R1B"
        for item in manifest["recipes"]
    ) == 5


def test_package_pins_exact_source_records():
    publication = json.loads((PACKAGE / "publication.json").read_text())
    assert {
        row["source"]["source_code"]: row["source"]["raw_record_sha256"]
        for row in publication["records"]
    } == {
        "1432": "0018264d8d0e9a181555e62b34684503b7689b4d1d7fddeb848722a287c97a2a",
        "929": "7d99a5fd87f50f471d61df99788d7aa7fe93db22ec1b5d42533733575069333a",
        "942": "d5c99fa5365221ef876168887d98d351278b1948bbb820187297ea1a23c12a79",
        "968": "79b770be30bf853021e929f949333838121d65bf5c45a0f3807b90d4cf6a57cb",
        "31": "6846bc12256db2d75b5329a14279d8d486c9253d3f3db75bf21a3b95e096a386",
        "158": "cd75d00e6781ad32706ee2d6120aad311ed05258cb4a8223a4d6c8bec379f1b9",
        "46": "41f284f935466cf22c03fe32dd64f6ac1083f13e5c331520ca26df63f3179de9",
        "1186": "bfd5673766e9061af643423f8f32206de1d7bd331bed50135e449984efb9b55e",
        "82": "f8712b80e2bd18972bf78374fdb6885c9a64c6a6c32ba08d6fa39ffe61b7b332",
    }


def test_fresh_batch_replay_and_current_profile_preservation(database):
    bundles = load_ru_nut_db_r1a_bundles()
    before_current = current_profile_ids(database, GENERIC_CODES)
    assert "POTATO" in before_current

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
        assert len(first.results) == 9
        assert first.bundle_created_count == 9
        assert first.ingredient_created_count == 8
        assert first.nutrient_value_count == 162

        with SqlAlchemyNutritionReadScope(engine) as read:
            for bundle, result in zip(bundles, first.results, strict=True):
                food = read.ingredients.get_by_code(bundle.ingredient.canonical_code)
                assert food.id == result.ingredient_id
                profile = read.nutrition_profiles.get_by_provenance(
                    food.id,
                    bundle.profile.source_name,
                    bundle.profile.source_id,
                    bundle.profile.source_version,
                )
                assert profile is not None
                assert profile.id == result.profile_id
                assert profile.is_current is False
                assert profile.carbohydrates_g is None
                vector = read.nutrient_vectors.get(profile.id)
                assert len(vector.values) == 18
                assert len(json.loads(vector.observations_json)) == 26

            for code in NEW_CODES:
                assert read.nutrition_profiles.get_current(
                    read.ingredients.get_by_code(code).id
                ) is None

        assert current_profile_ids(database, GENERIC_CODES) == before_current

        with sqlite3.connect(database.path) as db:
            rows = db.execute(
                """
                SELECT i.canonical_code, v.version, v.input_state
                FROM food_composition_versions v
                JOIN food_ingredients i ON i.id = v.food_ingredient_id
                JOIN food_nutrition_profiles p ON p.id = v.profile_id
                WHERE p.source_name = 'FIC_RU_NUT_DB'
                  AND i.canonical_code IN (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ORDER BY i.canonical_code
                """,
                tuple(sorted(R1A_CODES)),
            ).fetchall()
        assert rows == [
            (code, 1, MassState.INPUT.value) for code in sorted(R1A_CODES)
        ]

        before_replay = db_dump(database)
        replay = batch_service(engine).publish_batch(bundles)
        assert commits == 1
        assert replay.bundle_created_count == 0
        assert replay.ingredient_created_count == 0
        assert db_dump(database) == before_replay
        assert_fk_clean(database)
    finally:
        event.remove(engine, "commit", count_commit)
        engine.dispose()


def test_existing_generic_identities_are_not_reused_for_exact_new_forms(database):
    bundles = load_ru_nut_db_r1a_bundles()
    engine = create_sqlite_engine(database)
    try:
        batch_service(engine).publish_batch(bundles)
        with sqlite3.connect(database.path) as db:
            rows = dict(
                db.execute(
                    """
                    SELECT canonical_code, canonical_name
                    FROM food_ingredients
                    WHERE canonical_code IN (
                        'MARGARINE', 'MARGARINE_MILK_TABLE',
                        'MILK_WHOLE', 'MILK_PASTEURIZED_3_2',
                        'SOUR_CREAM_FULL_FAT', 'SOUR_CREAM_30',
                        'COTTAGE_CHEESE_FULL_FAT', 'TVOROG_9',
                        'CHICKEN_THIGH', 'CHICKEN_CATEGORY_1_RAW',
                        'ONION_YELLOW', 'ONION_BULB_FRESH',
                        'FLOUR_WHEAT', 'FLOUR_WHEAT_HIGH_GRADE'
                    )
                    """
                ).fetchall()
            )
        assert rows["MARGARINE_MILK_TABLE"] == "Маргарин молочный столовый"
        assert rows["MILK_PASTEURIZED_3_2"] == "Молоко пастеризованное 3,2%"
        assert rows["SOUR_CREAM_30"] == "Сметана 30%"
        assert rows["TVOROG_9"] == "Творог 9%"
        assert rows["CHICKEN_CATEGORY_1_RAW"] == "Курица 1 категории, сырая"
        assert rows["ONION_BULB_FRESH"] == "Лук репчатый свежий"
        assert rows["FLOUR_WHEAT_HIGH_GRADE"] == "Мука пшеничная высшего сорта"
        assert "MARGARINE" in rows
        assert "MILK_WHOLE" in rows
        assert "SOUR_CREAM_FULL_FAT" in rows
        assert "COTTAGE_CHEESE_FULL_FAT" in rows
        assert "CHICKEN_THIGH" in rows
        assert "ONION_YELLOW" in rows
        assert "FLOUR_WHEAT" in rows
    finally:
        engine.dispose()


@pytest.mark.parametrize("published_prefix", [1, 4, 8])
def test_exact_partial_prior_batch_fails_without_filling_remainder(
    database, published_prefix
):
    bundles = load_ru_nut_db_r1a_bundles()
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


def test_identity_conflict_rolls_back_entire_batch(database):
    bundles = load_ru_nut_db_r1a_bundles()
    engine = create_sqlite_engine(database)
    before = db_dump(database)
    try:
        corrupted = replace(
            bundles[3],
            ingredient=replace(
                bundles[3].ingredient,
                canonical_name="Конфликтный творог",
            ),
        )
        single_service(engine).publish(corrupted)
        partial = db_dump(database)
        with pytest.raises(NutritionPublicationConflictError):
            batch_service(engine).publish_batch(bundles)
        assert db_dump(database) == partial
        assert partial != before
        assert_fk_clean(database)
    finally:
        engine.dispose()


@pytest.mark.parametrize("food_number", [1, 5, 9])
def test_failure_rolls_back_whole_batch(database, food_number):
    bundles = load_ru_nut_db_r1a_bundles()
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


def test_tampered_payload_fails_before_database_creation(tmp_path):
    package = tmp_path / "package"
    shutil.copytree(PACKAGE, package)
    with (package / "publication.json").open("a") as stream:
        stream.write(" ")
    config = DatabaseConfig(path=tmp_path / "should-not-exist.sqlite")

    from app.seed.ru_nut_db_r1a import seed_ru_nut_db_r1a

    with pytest.raises(ValueError, match="Изменён"):
        seed_ru_nut_db_r1a(config, package=package)
    assert not config.path.exists()
