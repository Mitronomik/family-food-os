"""Production package gates and isolated adversarial fixtures for the RU operation."""

import ast
from copy import deepcopy
from dataclasses import replace
from decimal import Decimal
import json
from pathlib import Path
import shutil
import sqlite3
from uuid import uuid4

import pytest
from sqlalchemy import event, insert
from sqlalchemy.exc import IntegrityError

from app.db.config import DatabaseConfig
from app.domain.nutrient_vector_backfill_v1 import value_set_digest
from app.domain.ru_food_data import (
    BASELINE_CHAINS,
    derive_readiness,
    market_classification,
    russian_display,
)
from app.domain.ru_food_vector_import import prepare_reviewed_source
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
from app.persistence.sqlalchemy_core.nutrient_vector_tables import nutrient_values
from app.persistence.sqlalchemy_core.ru_food_data import SqlAlchemyRuFoodUnitOfWork
from app.seed.ru_food_data import PACKAGE, load_ru_food_entries, seed_ru_food_data
from app.services.food_composition import CompositionCalculator
from scripts.audit_pr6_ru_food_data import measure, seed_baseline, scope_audit
from scripts.audit_pr6_nutrient_vector_b import snapshot

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def baseline(tmp_path_factory):
    config = DatabaseConfig(path=tmp_path_factory.mktemp("ru-base") / "base.sqlite")
    seed_baseline(config)
    return config


@pytest.fixture
def database(baseline, tmp_path):
    config = DatabaseConfig(path=tmp_path / "ru.sqlite")
    shutil.copyfile(baseline.path, config.path)
    return config


@pytest.fixture
def package():
    return {
        name: json.loads((PACKAGE / name).read_text())
        for name in (
            "food-readiness.json",
            "source-manifest.json",
            "market-evidence.json",
        )
    }


@pytest.fixture
def mappings():
    return json.loads(
        (PACKAGE.parent / "pr6-nutrient-vector-a/source-mappings.json").read_text()
    )["mappings"]


def test_actual_production_audit_preservation_full_readiness_and_two_runs(tmp_path):
    result = measure(DatabaseConfig(path=tmp_path / "audit.sqlite"))
    assert result["target_existing_food_count"] == 81
    assert result["promote_count"] == result["new_nutrition_profile_count"] == 2
    assert result["defer_count"] == 5 and result["reject_count"] == 0
    assert result["new_nutrient_value_count"] == 66
    assert result["new_vector_seal_count"] == 2
    assert result["new_atomic_composition_count"] == result["ru_ready_food_count"] == 60
    assert result["readiness_before"] == result["readiness_after"]
    assert (
        result["full_readiness_sha256_before"] == result["full_readiness_sha256_after"]
    )
    assert (
        result["existing_vector_seals_verified_after"]
        == result["existing_food_ingredient_count"]
    )
    assert (
        result["migration_head_before"]
        == result["migration_head_after"]
        == result["registered_migration_head"]
    )
    assert (
        result["readiness_after"]["warning_occurrences"][
            "CONVERSION_ESTIMATE_NOT_ACCEPTED"
        ]
        == 43
    )


def test_package_population_optional_usages_and_no_deferred_production(
    database, package
):
    entries = load_ru_food_entries()
    assert len(entries) == 60
    rows = package["food-readiness.json"]["rows"]
    assert len({r["food_code"] for r in rows}) == len(rows)
    assert sum(len(r["target_usage"]["required"]) for r in rows) == 185
    assert sum(len(r["target_usage"]["optional"]) for r in rows) == 4
    seed_ru_food_data(database)
    with sqlite3.connect(database.path) as db:
        codes = {
            r[0] for r in db.execute("SELECT canonical_code FROM food_ingredients")
        }
        for row in rows:
            if row["decision"] == "DEFER":
                assert row["food_code"] not in codes
            if row["decision"] == "PROMOTE":
                assert row["parent_food_code"] != row["food_code"]
                assert row["parent_food_code"] in codes and row["food_code"] in codes


@pytest.mark.parametrize(
    "filename",
    [
        "food-readiness.json",
        "market-evidence.json",
        "source-manifest.json",
        "research-log.json",
    ],
)
def test_changed_package_fails_before_writes(filename, tmp_path):
    folder = tmp_path / "package"
    shutil.copytree(PACKAGE, folder)
    with (folder / filename).open("a") as stream:
        stream.write(" ")
    config = DatabaseConfig(path=tmp_path / "no-write.sqlite")
    with pytest.raises(ValueError, match="Изменён"):
        seed_ru_food_data(config, package=folder)
    assert not config.path.exists()


def market_row(package):
    return deepcopy(
        next(
            r
            for r in package["market-evidence.json"]["observations"]
            if r["id"] == "FRESH:CAULIFLOWER_FROZEN"
        )
    )


def test_distinct_three_of_five_threshold_and_secondary_evidence(package):
    row = market_row(package)

    def classify(evidence):
        return market_classification(row["food_code"], row["food_form"], evidence)

    assert classify([]) == "SPECIALTY_OR_UNCLEAR"
    assert classify([row, row, row]) == "RU_AVAILABLE"
    panel = [dict(row, retailer=c, id=c) for c in BASELINE_CHAINS[:3]]
    assert classify(panel) == "RU_MASS_MARKET"
    assert classify(panel[:2]) == "RU_AVAILABLE"
    assert classify([dict(row, retailer="VKUSVILL")]) == "SPECIALTY_OR_UNCLEAR"
    assert classify([dict(row, status="UNCERTAIN")]) == "SPECIALTY_OR_UNCLEAR"
    assert classify([dict(row, status="NOT_FOUND")]) == "SPECIALTY_OR_UNCLEAR"


@pytest.mark.parametrize(
    "field,value",
    [
        ("retailer", "OTHER_CHAIN"),
        ("status", "YES"),
        ("region", "RU-MOW"),
        ("checked_at", "2026-02-30"),
        ("source_url", ""),
        ("observed_wording_ru", ""),
        ("review_reference", ""),
        ("region_evidence_url", ""),
        ("food_form", "Cauliflower, raw"),
        ("food_code", "CAULIFLOWER"),
    ],
)
def test_market_metadata_and_changed_forms_fail_closed(package, field, value):
    row = market_row(package)
    damaged = dict(row, **{field: value})
    with pytest.raises(ValueError):
        market_classification(row["food_code"], row["food_form"], [damaged])


def test_manual_readiness_cannot_override_evidence(package):
    row = next(
        r
        for r in package["food-readiness.json"]["rows"]
        if r["food_code"] == "CAULIFLOWER_FROZEN"
    )
    evidence = [market_row(package)]
    assert derive_readiness(row, evidence)["market_classification"] == "RU_AVAILABLE"
    assert not derive_readiness(row, evidence)["default_pool_eligible"]
    assert derive_readiness(row, [])["final_readiness"] == "NOT_READY"
    damaged = dict(
        row, review_blockers=["PROFILE_FORM_UNRESOLVED"], final_readiness="RU_READY"
    )
    assert derive_readiness(damaged, evidence)["final_readiness"] == "NOT_READY"


def test_water_exception_cannot_be_reused_for_another_food(package):
    row = next(
        r
        for r in package["market-evidence.json"]["observations"]
        if r["id"] == "WATER:EXCEPTION"
    )
    assert market_classification("WATER", row["food_form"], [row]) == "RU_MASS_MARKET"
    with pytest.raises(ValueError):
        market_classification("SUGAR", row["food_form"], [dict(row, food_code="SUGAR")])


@pytest.mark.parametrize("name", ["", "   ", "APPLE_PEELED", "Peeled apple"])
def test_russian_primary_display_has_no_fallback(name):
    with pytest.raises(ValueError):
        russian_display(name, "APPLE_PEELED")


@pytest.mark.parametrize(
    "name", ["Сок 100%", "Молоко 1% жирности", "Витамин B12", "Яблоко (FDC 171689)"]
)
def test_russian_text_preserves_digits_and_exact_source_identifiers(name):
    assert russian_display(name, "CODE") == name


@pytest.mark.parametrize("source_id", ["170398", "168173"])
def test_every_compatible_source_nutrient_exact_sparse_and_same_source_projection(
    package, mappings, source_id
):
    source = package["source-manifest.json"]["profiles"][source_id]
    legacy, values, observations = prepare_reviewed_source(source, mappings)
    assert len(values) == 33
    assert len({v["nutrient_code"] for v in values}) == len(values)
    compatible = {
        m["source_nutrient_id"]: m
        for m in mappings
        if m["source_release"] == "2018-04"
        and m["mapping_status"] in {"EXACT", "METHOD_SPECIFIC"}
    }
    raw = {r["nutrient_id"]: r for r in source["food_nutrients"]}
    expected = {
        m["canonical_code"]
        for id, m in compatible.items()
        if id in raw and Decimal(raw[id]["amount"]) > 0
    }
    assert {v["nutrient_code"] for v in values} == expected
    for value in values:
        provenance = json.loads(value["provenance_json"])
        observation = provenance["observation"]
        assert isinstance(value["amount"], Decimal) and value["amount"] > 0
        assert value["amount"] == Decimal(
            raw[observation["source_nutrient_id"]]["amount"]
        )
        assert observation["profile_source_id"] == source_id
        assert (
            observation["source_food_nutrient_id"]
            == raw[observation["source_nutrient_id"]]["id"]
        )
    assert len(json.loads(observations)) == len(source["food_nutrients"])
    assert all(
        r["origin"] == "UNRESOLVED_ZERO"
        for r in json.loads(observations)
        if Decimal(r["observation"]["source_value"]) == 0
    )
    assert all(isinstance(v, Decimal) for v in legacy.values())
    assert value_set_digest(values) == value_set_digest(list(reversed(values)))


@pytest.mark.parametrize(
    "fault",
    [
        "cross_source",
        "duplicate",
        "basis",
        "zero_required",
        "negative",
        "wrong_release",
        "wrong_component",
        "unapproved_candidate",
    ],
)
def test_reviewed_source_import_rejects_false_authority(package, mappings, fault):
    source = deepcopy(package["source-manifest.json"]["profiles"]["170398"])
    if fault == "cross_source":
        source["food_nutrients"][0]["fdc_id"] = "168173"
    if fault == "duplicate":
        source["food_nutrients"].append(source["food_nutrients"][0])
    if fault == "basis":
        source["basis_grams"] = "1"
    if fault == "zero_required":
        next(r for r in source["food_nutrients"] if r["nutrient_id"] == "1003")[
            "amount"
        ] = "0"
    if fault == "negative":
        source["food_nutrients"][0]["amount"] = "-1"
    if fault == "wrong_release":
        source["source_version"] = "2026-04-30"
    if fault == "wrong_component":
        next(r for r in source["nutrients"] if r["id"] == "1003")["name"] = (
            "Not protein"
        )
    if fault == "unapproved_candidate":
        source["source_id"] = "171689"
    with pytest.raises(ValueError):
        prepare_reviewed_source(source, mappings)


def test_late_import_failure_rolls_back_all_food_profile_vector_composition_truth(
    database,
):
    before = snapshot(database)
    engine = create_sqlite_engine(database)

    def fail(connection, cursor, statement, parameters, context, executemany):
        if statement.startswith("INSERT INTO nutrition_vector_seals"):
            raise RuntimeError("injected RU seal failure")

    event.listen(engine, "before_cursor_execute", fail)
    from app.services.ru_food_data import reconcile_ru_food_data

    try:
        with pytest.raises(RuntimeError, match="injected"):
            reconcile_ru_food_data(
                lambda: SqlAlchemyRuFoodUnitOfWork(engine), load_ru_food_entries()
            )
    finally:
        engine.dispose()
    assert snapshot(database) == before
    assert seed_ru_food_data(database)["ingredients"] == 2


def test_replay_uses_pinned_profile_after_current_profile_changes(database):
    seed_ru_food_data(database)
    engine = create_sqlite_engine(database)
    try:
        with SqlAlchemyRuFoodUnitOfWork(engine) as uow:
            food = uow.ingredients.get_by_code("CAULIFLOWER_FROZEN")
            version = uow.compositions.find_version(food.id, 1)
            calculator = CompositionCalculator(uow.compositions, uow.nutrient_vectors)
            before = calculator.calculate(
                version.id, nutrient_codes=("ENERGY_KCAL", "PROTEIN", "CALCIUM")
            )
            old = uow.nutrition_profiles.get_current(food.id)
            uow.nutrition_profiles.clear_current(food.id)
            # Explicitly synthetic new current profile; never a production package row.
            uow.nutrition_profiles.add(
                replace(
                    old,
                    id=uuid4(),
                    source_id="SYNTHETIC_TEST_PROFILE",
                    kcal=Decimal("999"),
                )
            )
            uow.commit()
        with SqlAlchemyRuFoodUnitOfWork(engine) as read:
            after = CompositionCalculator(
                read.compositions, read.nutrient_vectors
            ).calculate(
                version.id, nutrient_codes=("ENERGY_KCAL", "PROTEIN", "CALCIUM")
            )
            assert before == after
        assert not any(seed_ru_food_data(database).values())
    finally:
        engine.dispose()


def test_new_vector_cannot_be_appended_after_sealing(database):
    seed_ru_food_data(database)
    engine = create_sqlite_engine(database)
    try:
        with SqlAlchemyRuFoodUnitOfWork(engine) as uow:
            food = uow.ingredients.get_by_code("CAULIFLOWER_FROZEN")
            profile = uow.nutrition_profiles.get_current(food.id)
            vector = uow.nutrient_vectors.get(profile.id)
            assert vector.amount("BIOTIN") is None
            with pytest.raises(IntegrityError):
                uow.adapter_connection.execute(
                    insert(nutrient_values).values(
                        profile_id=profile.id,
                        nutrient_code="BIOTIN",
                        amount=Decimal("1"),
                        provenance_json="{}",
                    )
                )
    finally:
        engine.dispose()


def test_production_scope_and_driver_independent_runtime():
    assert all(value == 0 for value in scope_audit().values())
    runtime = [
        ROOT / "app/domain/ru_food_data.py",
        ROOT / "app/domain/ru_food_vector_import.py",
        ROOT / "app/services/ru_food_data.py",
    ]
    for path in runtime:
        tree = ast.parse(path.read_text())
        imports = [n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]
        imports += [
            a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names
        ]
        assert not any(
            any(
                token in (name or "").lower()
                for token in (
                    "sqlalchemy",
                    "sqlite3",
                    "retail",
                    "planner",
                    "assembly",
                    "openai",
                )
            )
            for name in imports
        )
