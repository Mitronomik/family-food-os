"""Step 8 publication of the exact School2022 butter dependency from FIC DB/533."""

from copy import deepcopy
from dataclasses import replace
from decimal import Decimal
import hashlib
import json
import shutil
import sqlite3

import pytest
from sqlalchemy import event

from app.db import migrations
from app.db.config import DatabaseConfig
from app.domain.food_composition import CompositionStatus, MassState
from app.domain.food_ingredients import NutritionObservationState
from app.domain.nutrient_method_adapters import REGISTRY_V2
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
from app.persistence.sqlalchemy_core.nutrition_publication import (
    SqlAlchemyNutritionPublicationUnitOfWork,
)
from app.seed.food_ingredients import seed_food_ingredients
from app.seed.ru_food_data import seed_ru_food_data
from app.seed.ru_nut_db_step4 import seed_ru_nut_db_step4
from app.seed import ru_nut_db_step8_butter as step8
from app.services.food_composition import ApplicabilityAwareCompositionCalculator
from app.services.nutrition_publication import (
    NutritionPublicationConflictError,
    ReviewedNutritionBatchPublicationService,
    ReviewedNutritionPublicationService,
)

FOOD_CODE = "BUTTER_PEASANT_72_5_UNSALTED"
GENERIC_CODE = "BUTTER_UNSALTED"


@pytest.fixture(scope="module")
def baseline(tmp_path_factory):
    config = DatabaseConfig(path=tmp_path_factory.mktemp("step8-base") / "base.sqlite")
    migrations.apply_migrations(config)
    seed_food_ingredients(config)
    seed_ru_food_data(config)
    seed_ru_nut_db_step4(config)
    return config


@pytest.fixture
def database(baseline, tmp_path):
    config = DatabaseConfig(path=tmp_path / "step8.sqlite")
    shutil.copyfile(baseline.path, config.path)
    return config


def db_dump(config: DatabaseConfig) -> str:
    with sqlite3.connect(config.path) as db:
        return "\n".join(db.iterdump())


def assert_fk_clean(config: DatabaseConfig) -> None:
    with sqlite3.connect(config.path) as db:
        assert db.execute("PRAGMA foreign_key_check").fetchall() == []


def generic_butter_snapshot(config: DatabaseConfig) -> tuple:
    with sqlite3.connect(config.path) as db:
        return db.execute(
            """
            SELECT i.id, i.canonical_name, i.category_code, i.default_unit,
                   p.id, p.source_name, p.source_id, p.source_version,
                   p.kcal, p.protein_g, p.fat_g, p.carbohydrates_g, p.fiber_g,
                   p.is_current
            FROM food_ingredients i
            JOIN food_nutrition_profiles p ON p.food_ingredient_id = i.id
            WHERE i.canonical_code = ? AND p.is_current = 1
            """,
            (GENERIC_CODE,),
        ).fetchone()


def protected_counts(config: DatabaseConfig) -> dict[str, int]:
    tables = (
        "food_yield_models",
        "food_retention_profiles",
        "food_retention_values",
        "food_transformations",
        "food_transformation_applicability",
        "food_recipe_versions",
    )
    with sqlite3.connect(config.path) as db:
        return {
            table: db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in tables
        }


def publication_service(engine):
    return ReviewedNutritionBatchPublicationService(
        lambda: SqlAlchemyNutritionPublicationUnitOfWork(engine)
    )


def single_service(engine):
    return ReviewedNutritionPublicationService(
        lambda: SqlAlchemyNutritionPublicationUnitOfWork(engine)
    )


def mutate_package(tmp_path, monkeypatch, mutate):
    package = tmp_path / "package"
    shutil.copytree(step8.PACKAGE, package)
    path = package / "publication.json"
    payload = json.loads(path.read_text())
    mutate(payload)
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    path.write_text(raw)
    monkeypatch.setattr(
        step8, "PUBLICATION_SHA256", hashlib.sha256(raw.encode()).hexdigest()
    )
    return package


def test_runtime_package_exact_identity_sparse_vector_and_source_observations():
    bundle = step8.load_ru_nut_db_step8_butter_bundle()
    assert bundle.ingredient.canonical_code == FOOD_CODE
    assert (
        bundle.ingredient.canonical_name
        == "Масло сливочное крестьянское 72,5% несолёное"
    )
    assert bundle.vector.registry_version == REGISTRY_V2
    assert bundle.vector.value_count == 17
    assert len(bundle.vector.values) == 17
    assert {value.nutrient_code for value in bundle.vector.values} == {
        "ENERGY_KCAL",
        "PROTEIN",
        "FAT_TOTAL",
        "FATTY_ACIDS_SATURATED_TOTAL",
        "STARCH",
        "SUGARS_TOTAL",
        "FIBER_TOTAL_DIETARY",
        "VITAMIN_A_RE",
        "THIAMIN",
        "RIBOFLAVIN",
        "VITAMIN_C",
        "SODIUM",
        "POTASSIUM",
        "CALCIUM",
        "PHOSPHORUS",
        "IRON",
        "MAGNESIUM",
    }
    assert "WATER" not in {value.nutrient_code for value in bundle.vector.values}

    rows = json.loads(bundle.vector.observations_json)
    assert len(rows) == 26
    by_field = {row["observation"]["source_field"]: row for row in rows}
    assert by_field["water"]["origin"] == "SOURCE_NOT_REPORTED"
    assert by_field["water"]["observation"]["source_value"] is None
    assert by_field["water"]["observation"]["target_nutrient_code"] == "WATER"
    assert by_field["salt_ad"]["origin"] == "SOURCE_ONLY_DEFERRED"
    assert by_field["salt_ad"]["observation"]["source_value"] == "0.0"
    assert by_field["salt_ad"]["observation"]["target_nutrient_code"] is None
    assert (
        by_field["salt_ad"]["observation"]["form_compatibility_role"]
        == "NO_ADDED_SALT_EVIDENCE"
    )


def test_runtime_packae_pins_exact_sources_rights_and_form_binding():
    publication = json.loads((step8.PACKAGE / "publication.json").read_text())
    assert publication["source"]["archive_size_bytes"] == 206692075
    assert publication["source"]["archive_sha256"] == step8.ARCHIVE_SHA256
    assert (
        publication["recipe_dependency"]["school_pdf_sha256"]
        == step8.SCHOOL_PDF_SHA256
    )
    assert (
        publication["recipe_dependency"]["recipe_id"]
        == "ru-school2022:recipe:53-19з"
    )
    assert publication["record"]["source"] == {
        "db_index": 533,
        "json_pointer": "/DB/533",
        "raw_record_sha256": step8.RAW_RECORD_SHA256,
        "source_code": "1417",
        "source_name": "Масло сливочное крестьянское, 72,5%",
    }
    assert publication["form_binding"] == {
        "accepted_role": "NO_ADDED_SALT_FORM_COMPATIBILITY_ONLY",
        "fat_percent": "72.5",
        "fic_source_field": "salt_ad",
        "fic_source_label": "Добавленная соль",
        "fic_source_literal": "0.0",
        "school_requires_unsalted": True,
        "semantic_disposition": "SOURCE_ONLY_NO_V2_TARGET",
        "sodium_inference_forbidden": True,
    }
    readme = (step8.PACKAGE / "README.md").read_text()
    assert step8.ATTRIBUTION in readme
    assert step8.SOURCE_URL in readme


@pytest.mark.parametrize("replacement", ["1.0", None])
def test_nonzero_or_null_salt_evidence_fails_closed(tmp_path, monkeypatch, replacement):
    package = mutate_package(
        tmp_path,
        monkeypatch,
        lambda payload: payload["record"]["nutrients"].__setitem__(
            "salt_ad", replacement
        ),
    )
    with pytest.raises(ValueError, match="salt_ad=0.0"):
        step8.load_ru_nut_db_step8_butter_bundle(package)


def test_missing_salt_evidence_fails_closed(tmp_path, monkeypatch):
    package = mutate_package(
        tmp_path,
        monkeypatch,
        lambda payload: payload["record"]["nutrients"].pop("salt_ad"),
    )
    with pytest.raises(ValueError, match="source fields"):
        step8.load_ru_nut_db_step8_butter_bundle(package)


def test_sodium_cannot_substitute_for_salt_form_evidence(tmp_path, monkeypatch):
    def mutate(payload):
        payload["record"]["nutrients"]["salt_ad"] = None
        payload["record"]["nutrients"]["na"] = "0.0"

    package = mutate_package(tmp_path, monkeypatch, mutate)
    with pytest.raises(ValueError, match="salt_ad=0.0"):
        step8.load_ru_nut_db_step8_butter_bundle(package)


def test_water_must_remain_explicit_unknown(tmp_path, monkeypatch):
    package = mutate_package(
        tmp_path,
        monkeypatch,
        lambda payload: payload["record"]["nutrients"].__setitem__("water", "0.0"),
    )
    with pytest.raises(ValueError, match="WATER"):
        step8.load_ru_nut_db_step8_butter_bundle(package)


def test_changed_runtime_payload_fails_before_database_creation(tmp_path):
    package = tmp_path / "package"
    shutil.copytree(step8.PACKAGE, package)
    with (package / "publication.json").open("a") as stream:
        stream.write(" ")
    config = DatabaseConfig(path=tmp_path / "should-not-exist.sqlite")

    with pytest.raises(ValueError, match="Изменён"):
        step8.seed_ru_nut_db_step8_butter(config, package=package)
    assert not config.path.exists()


def test_fresh_publication_replay_and_preservation(database):
    bundle = step8.load_ru_nut_db_step8_butter_bundle()
    generic_before = generic_butter_snapshot(database)
    protected_before = protected_counts(database)
    assert generic_before is not None

    with sqlite3.connect(database.path) as db:
        fic_before = db.execute(
            "SELECT COUNT(*) FROM food_nutrition_profiles WHERE source_name = ?",
            (step8.SOURCE_NAME,),
        ).fetchone()[0]
        assert fic_before == 5
        migrations_before = {
            row[0] for row in db.execute("SELECT migration_id FROM schema_migrations")
        }
        assert "0038_transformation_applicability" in migrations_before
        assert "0033_recipe_template_catalogue" not in migrations_before

    engine = create_sqlite_engine(database)
    commits = 0

    def count_commit(connection):
        nonlocal commits
        del connection
        commits += 1

    event.listen(engine, "commit", count_commit)
    try:
        first = publication_service(engine).publish_batch((bundle,))
        assert commits == 1
        assert first.bundle_created_count == 1
        assert first.ingredient_created_count == 1
        assert first.nutrient_value_count == 17

        with SqlAlchemyNutritionPublicationUnitOfWork(engine) as uow:
            food = uow.ingredients.get_by_code(FOOD_CODE)
            assert food is not None
            assert food.canonical_name == "Масло сливочное крестьянское 72,5% несолёное"
            profile = uow.nutrition_profiles.get_by_provenance(
                food.id, step8.SOURCE_NAME, step8.SOURCE_CODE, step8.SOURCE_VERSION
            )
            assert profile is not None and profile.is_current is False
            assert profile.kcal == Decimal("660.900000")
            assert profile.protein_g == Decimal("0.800000")
            assert profile.fat_g == Decimal("72.500000")
            assert profile.carbohydrates_g is None
            assert profile.fiber_g == Decimal("0.000000")
            observations = {
                value.source_field: value
                for value in uow.nutrition_profiles.list_observations(profile.id)
            }
            assert (
                observations["carbohydrates_g"].state
                is NutritionObservationState.METHOD_INCOMPATIBLE
            )

            vector = uow.nutrient_vectors.get(profile.id)
            assert vector.registry_version == REGISTRY_V2
            assert len(vector.values) == 17
            assert vector.amount("FAT_TOTAL") == Decimal("72.5")
            assert vector.amount("SODIUM") == Decimal("15.0")
            assert vector.amount("WATER") is None

            composition = uow.compositions.find_version(food.id, 1)
            assert composition is not None
            assert composition.input_state is MassState.INPUT
            result = ApplicabilityAwareCompositionCalculator(
                uow.compositions,
                uow.nutrient_vectors,
                uow.nutrient_registry,
            ).calculate(
                composition.id,
                registry_version=REGISTRY_V2,
                nutrient_codes=("FAT_TOTAL",),
            )
            assert result.status is CompositionStatus.COMPLETE
            assert result.nutrients[0].amount == Decimal("72.500000")

        assert generic_butter_snapshot(database) == generic_before
        assert protected_counts(database) == protected_before

        with sqlite3.connect(database.path) as db:
            fic_after = db.execute(
                "SELECT COUNT(*) FROM food_nutrition_profiles WHERE source_name = ?",
                (step8.SOURCE_NAME,),
            ).fetchone()[0]
            assert fic_after == 6
            assert db.execute("PRAGMA foreign_key_check").fetchall() == []

        before_replay = db_dump(database)
        second = publication_service(engine).publish_batch((bundle,))
        assert commits == 1
        assert second.bundle_created_count == 0
        assert second.ingredient_created_count == 0
        assert second.nutrient_value_count == 17
        assert second.results[0].ingredient_id == first.results[0].ingredient_id
        assert second.results[0].profile_id == first.results[0].profile_id
        assert (
            second.results[0].composition_version_id
            == first.results[0].composition_version_id
        )
        assert db_dump(database) == before_replay
    finally:
        event.remove(engine, "commit", count_commit)
        engine.dispose()

    assert_fk_clean(database)


def test_existing_conflicting_food_identity_fails_without_write(database):
    bundle = step8.load_ru_nut_db_step8_butter_bundle()
    engine = create_sqlite_engine(database)
    try:
        wrong = replace(
            bundle,
            ingredient=replace(bundle.ingredient, canonical_name="Конфликтное масло"),
        )
        single_service(engine).publish(wrong)
        before = db_dump(database)
        with pytest.raises(NutritionPublicationConflictError):
            publication_service(engine).publish_batch((bundle,))
        assert db_dump(database) == before
    finally:
        engine.dispose()
    assert_fk_clean(database)


def test_failure_after_vector_before_composition_rolls_back_everything(database):
    bundle = step8.load_ru_nut_db_step8_butter_bundle()
    engine = create_sqlite_engine(database)
    before = db_dump(database)

    def fail_on_composition(
        connection, cursor, statement, parameters, context, executemany
    ):
        del connection, cursor, parameters, context, executemany
        if statement.strip().startswith("INSERT INTO food_composition_versions"):
            raise RuntimeError("injected Step 8 composition failure")

    event.listen(engine, "before_cursor_execute", fail_on_composition)
    try:
        with pytest.raises(RuntimeError, match="injected Step 8"):
            publication_service(engine).publish_batch((bundle,))
    finally:
        event.remove(engine, "before_cursor_execute", fail_on_composition)
        engine.dispose()

    assert db_dump(database) == before
    assert_fk_clean(database)


def test_production_entrypoint_is_idempotent(database):
    first = step8.seed_ru_nut_db_step8_butter(database)
    before = db_dump(database)
    second = step8.seed_ru_nut_db_step8_butter(database)
    assert first.bundle_created_count == 1
    assert first.ingredient_created_count == 1
    assert first.nutrient_value_count == 17
    assert second.bundle_created_count == 0
    assert second.ingredient_created_count == 0
    assert second.nutrient_value_count == 17
    assert db_dump(database) == before
