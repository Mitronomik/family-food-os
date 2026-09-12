"""VECTOR-B: real upgrades, entire audited zero set, sparse reads and sealing."""

from copy import deepcopy
from dataclasses import asdict, replace
from decimal import Decimal, localcontext
from importlib import import_module
import json
import sqlite3
from uuid import uuid4

import pytest
from sqlalchemy import insert
from sqlalchemy.exc import IntegrityError
from app.persistence.sqlalchemy_core.uow import SqlAlchemyUnitOfWork

from app.db import migrations
from app.db.config import DatabaseConfig
from app.domain.nutrient_vector import NutrientVectorUnavailableError
from app.domain.nutrient_vector_backfill_v1 import (
    disposition,
    prepare_profile,
    value_set_digest,
)
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
from app.persistence.sqlalchemy_core.food_ingredient_uow import (
    SqlAlchemyFoodCatalogueUnitOfWork,
)
from app.persistence.sqlalchemy_core.nutrition_read_scope import (
    SqlAlchemyNutritionReadScope,
)
from app.persistence.sqlalchemy_core.nutrient_vector_tables import nutrient_values
from app.seed.food_ingredients import seed_food_ingredients
from scripts.audit_pr6_nutrient_vector_b import measure, seed_previous, snapshot

MIGRATION = import_module("app.migrations.versions.0028_normalized_nutrient_vector")


@pytest.fixture(scope="module")
def bundle():
    return MIGRATION.load_bundle()


@pytest.fixture(scope="module")
def database(tmp_path_factory):
    config = DatabaseConfig(path=tmp_path_factory.mktemp("vectors") / "fresh.sqlite")
    seed_food_ingredients(config)
    engine = create_sqlite_engine(config)
    yield config, engine
    engine.dispose()


def vector(engine, food="AGAVE_SYRUP"):
    with SqlAlchemyNutritionReadScope(engine) as read:
        ingredient = read.ingredients.get_by_code(food)
        profile = read.nutrition_profiles.get_current(ingredient.id)
        return read.nutrient_vectors.get(profile.id)


def test_real_upgrade_readiness_all_historical_bindings_and_values(tmp_path):
    report = measure(DatabaseConfig(path=tmp_path / "upgrade.sqlite"))
    assert report["canonical_nutrient_definitions"] == 51
    assert report["profiles_examined"] == report["profiles_backfilled"] == 183
    assert report["normalized_nutrient_value_rows"] == 806
    assert report["audited_unresolved_zero_observations"] == 64
    assert report["authoritative_rows_from_unresolved_zeros"] == 0
    assert report["readiness_before"] == report["readiness_after"]


def test_registry_matches_all_approved_definitions(database, bundle):
    config, _ = database
    with sqlite3.connect(config.path) as db:
        rows = db.execute(
            "SELECT code, display_name_ru, unit, definition_json FROM nutrient_definitions"
        ).fetchall()
        assert len(rows) == len({r[0] for r in rows}) == 51
        assert {r[0] for r in rows} == {
            d["canonical_code"] for d in bundle["nutrient-registry.json"]["entries"]
        }
        for code, name, unit, payload in rows:
            assert any("А" <= ch <= "я" for ch in name)
            assert unit in ("kcal", "g", "mg", "µg")
            assert not code.isdigit()
            assert json.loads(payload) in bundle["nutrient-registry.json"]["entries"]
        stored = db.execute(
            "SELECT bundle_json FROM nutrient_registry_snapshots"
        ).fetchone()[0]
        assert json.loads(stored) == bundle
    assert migrations.expected_migration_ids()[-1] == MIGRATION.MIGRATION_ID


def test_all_64_zeros_preserve_evidence_and_v1_but_never_numeric_rows(database, bundle):
    _, engine = database
    zeros = [
        r
        for r in bundle["legacy-v1-crosswalk.json"]["rows"]
        if r["source_value_state"] == "ZERO_REPORTED"
    ]
    assert len(zeros) == 64
    for row in zeros:
        result = vector(engine, row["food_ingredient_code"])
        assert result.amount(row["target_nutrient_code"]) is None
        assert getattr(result.profile, row["legacy_field"]) == Decimal(0)
        preserved = next(
            r
            for r in json.loads(result.observations_json)
            if r["observation"]["audit_identity"] == row["audit_identity"]
        )
        assert preserved["origin"] == "UNRESOLVED_ZERO"
        assert preserved["observation"] == row
        assert row["source_observation"] is not None


def test_all_legacy_fields_and_unknown_remain_unchanged(database, bundle):
    _, engine = database
    for row in bundle["legacy-v1-crosswalk.json"]["rows"]:
        result = vector(engine, row["food_ingredient_code"])
        legacy = getattr(result.profile, row["legacy_field"])
        expected = None if row["legacy_value"] is None else Decimal(row["legacy_value"])
        assert legacy == expected
        normalized = result.amount(row["target_nutrient_code"])
        assert normalized == (
            expected if disposition(row) == "SOURCE_COMPONENT_CONFIRMED" else None
        )
        assert result.amount("CALCIUM") is None


@pytest.mark.parametrize(
    "status,origin",
    [
        ("SOURCE_COMPONENT_CONFIRMED", "SOURCE_COMPONENT_CONFIRMED"),
        ("LEGACY_PROFILE_VALUE_CONFIRMED_SOURCE_ID_UNAVAILABLE", "LEGACY_PROJECTION"),
        ("VALUE_MISMATCH", "VALUE_MISMATCH"),
        ("DEFINITION_AMBIGUOUS", "DEFINITION_AMBIGUOUS"),
        ("VALUE_ABSENT", "VALUE_ABSENT"),
    ],
)
def test_explicit_legacy_dispositions_preserve_semantics(
    database, bundle, status, origin
):
    _, engine = database
    existing = vector(engine)
    changed = deepcopy(bundle)
    row = next(
        r
        for r in changed["legacy-v1-crosswalk.json"]["rows"]
        if r["food_ingredient_code"] == "AGAVE_SYRUP" and r["legacy_field"] == "kcal"
    )
    row["legacy_mapping_status"] = status
    profile = asdict(existing.profile)
    if origin == "LEGACY_PROJECTION":
        for k in ("source_nutrient_id", "source_nutrient_name", "source_unit"):
            row[k] = None
    if status == "VALUE_MISMATCH":
        row["source_value"] = "999"
        row["numeric_comparison"]["equal"] = False
    if status == "DEFINITION_AMBIGUOUS":
        row["target_nutrient_code"] = None
    if status == "VALUE_ABSENT":
        row["legacy_value"] = row["source_value"] = None
        profile["kcal"] = None
    values, observations = prepare_profile(profile, "AGAVE_SYRUP", changed)
    preserved = next(
        o
        for o in json.loads(observations)
        if o["observation"]["legacy_field"] == "kcal"
    )
    assert preserved == {"origin": origin, "observation": row}
    energy = next((v for v in values if v["nutrient_code"] == "ENERGY_KCAL"), None)
    if status == "SOURCE_COMPONENT_CONFIRMED":
        assert energy["amount"] == Decimal("310")
    else:
        assert energy is None
        assert preserved["observation"]["legacy_value"] == (
            None if status == "VALUE_ABSENT" else "310.000000"
        )


def test_energy_selection_pinned_not_ordered_or_summed(database, bundle):
    _, engine = database
    row = next(
        r
        for r in bundle["legacy-v1-crosswalk.json"]["rows"]
        if r["source_nutrient_id"] == "2048"
    )
    result = vector(engine, row["food_ingredient_code"])
    changed = deepcopy(bundle)
    source = next(
        s
        for s in changed["source-manifest.json"]["fdc_selected_extracts"]
        if s["source_release"] == row["profile_source_version"]
    )
    alternatives = [
        r
        for r in source["food_nutrient_rows"]
        if r["fdc_id"] == row["profile_source_id"]
        and r["nutrient_id"] in ("2047", "2048", "1008")
    ]
    assert len(alternatives) >= 2
    first = prepare_profile(
        asdict(result.profile), row["food_ingredient_code"], changed
    )
    source["food_nutrient_rows"].reverse()
    changed["source-mappings.json"]["mappings"].reverse()
    changed["legacy-v1-crosswalk.json"]["rows"].reverse()
    assert (
        prepare_profile(asdict(result.profile), row["food_ingredient_code"], changed)
        == first
    )
    energy = next(v for v in result.values if v.definition.code == "ENERGY_KCAL")
    assert energy.amount == result.profile.kcal
    assert energy.provenance.source_nutrient_id == "2048"
    assert energy.provenance.source_observation_id == row["source_food_nutrient_id"]
    assert energy.provenance.source_derivation_id == row["source_derivation_id"]


def test_read_profile_history_not_current_substitution(database):
    _, engine = database
    old = vector(engine)
    with SqlAlchemyFoodCatalogueUnitOfWork(engine) as write:
        write.nutrition_profiles.clear_current(old.profile.food_ingredient_id)
        new = replace(old.profile, id=uuid4(), source_version="test-unreviewed")
        write.nutrition_profiles.add(new)
        # Roll back at exit so shared fixture is unchanged.
        with pytest.raises(NutrientVectorUnavailableError):
            from app.persistence.sqlalchemy_core.nutrient_vector_repository import (
                SqlAlchemyNutrientVectorRepository,
            )

            SqlAlchemyNutrientVectorRepository(write._scope.adapter_connection).get(
                new.id
            )
    assert vector(engine) == old


@pytest.mark.parametrize(
    "table,key",
    [
        ("nutrient_registry_snapshots", "version"),
        ("nutrient_definitions", "code"),
        ("nutrition_vector_seals", "profile_id"),
        ("nutrient_values", "profile_id"),
    ],
)
@pytest.mark.parametrize("operation", ["update", "delete", "replace"])
def test_all_snapshot_tables_are_immutable_even_via_replace(
    database, table, key, operation
):
    config, _ = database
    with sqlite3.connect(config.path) as db:
        row_id = db.execute(f"SELECT {key} FROM {table} LIMIT 1").fetchone()[0]
        with pytest.raises(sqlite3.IntegrityError):
            if operation == "update":
                db.execute(
                    f"UPDATE {table} SET {key} = {key} WHERE {key} = ?", (row_id,)
                )
            elif operation == "delete":
                db.execute(f"DELETE FROM {table} WHERE {key} = ?", (row_id,))
            else:
                db.execute(
                    f"INSERT OR REPLACE INTO {table} SELECT * FROM {table} WHERE {key} = ?",
                    (row_id,),
                )


def test_sealed_vector_cannot_append_even_unknown_nutrient(database):
    config, engine = database
    result = vector(engine)
    with sqlite3.connect(config.path) as db:
        with pytest.raises(sqlite3.IntegrityError, match="зафиксирован"):
            db.execute(
                "INSERT INTO nutrient_values VALUES (?, ?, ?, ?)",
                (result.profile_id.hex, "CALCIUM", "1", "{}"),
            )


def test_unsealed_partial_rows_cannot_commit_or_be_read_and_decimal_roundtrip(database):
    _, engine = database
    old = vector(engine)
    profile = replace(
        old.profile, id=uuid4(), is_current=False, source_version="test-precision"
    )
    from app.persistence.sqlalchemy_core.food_ingredient_repositories import (
        SqlAlchemyFoodNutritionProfileRepository,
    )
    from app.persistence.sqlalchemy_core.nutrient_vector_repository import (
        SqlAlchemyNutrientVectorRepository,
    )

    scope = SqlAlchemyUnitOfWork(engine)
    scope.__enter__()
    connection = scope.adapter_connection
    try:
        SqlAlchemyFoodNutritionProfileRepository(connection).add(profile)
        amount = Decimal("0.1234567890123456789012345678901234567890123456789")
        original = old.values[0]
        # Synthetic persistence fixture preserves Decimal without granting import authority.
        row = dict(
            profile_id=profile.id,
            nutrient_code=original.definition.code,
            amount=amount,
            provenance_json=original.provenance.evidence_json,
        )
        connection.execute(insert(nutrient_values).values(**row))
        assert (
            connection.execute(
                nutrient_values.select().where(
                    nutrient_values.c.profile_id == profile.id
                )
            )
            .mappings()
            .one()["amount"]
            == amount
        )
        with pytest.raises(NutrientVectorUnavailableError):
            SqlAlchemyNutrientVectorRepository(connection).get(profile.id)
        with pytest.raises(IntegrityError, match="UNIQUE"):
            connection.execute(insert(nutrient_values).values(**row))
        with pytest.raises(IntegrityError, match="FOREIGN KEY"):
            scope.commit()
    finally:
        scope.__exit__(None, None, None)
    with SqlAlchemyNutritionReadScope(engine) as read:
        assert read.nutrition_profiles.get_nutrition_profile_by_id(profile.id) is None


def test_domain_decimal_and_duplicate_invariants(database):
    _, engine = database
    result = vector(engine)
    original = result.values[0]
    for invalid in (1.1, 1, None, "1"):
        with pytest.raises(TypeError):
            replace(original, amount=invalid)
    for invalid in ("NaN", "Infinity", "-1"):
        with pytest.raises(ValueError):
            replace(original, amount=Decimal(invalid))
    assert replace(original, amount=Decimal("0")).amount == 0
    with pytest.raises(ValueError, match="повторяется"):
        replace(result, values=(original, original))
    with pytest.raises(ValueError, match="Происхождение"):
        replace(
            result,
            values=(
                replace(
                    original,
                    provenance=replace(
                        original.provenance, source_food_id="other-source"
                    ),
                ),
            ),
        )
    with localcontext() as context:
        context.prec = 2
        assert value_set_digest(
            [
                dict(
                    nutrient_code=original.definition.code,
                    amount=original.amount,
                    provenance_json=original.provenance.evidence_json,
                )
            ]
        )


def test_unknown_deployment_profile_aborts_upgrade_without_half_schema(
    tmp_path, monkeypatch
):
    config = DatabaseConfig(path=tmp_path / "unknown.sqlite")
    seed_previous(config)
    engine = create_sqlite_engine(config)
    try:
        with SqlAlchemyFoodCatalogueUnitOfWork(engine) as write:
            ingredient = write.ingredients.get_by_code("AGAVE_SYRUP")
            profile = write.nutrition_profiles.get_current(ingredient.id)
            write.nutrition_profiles.add(
                replace(
                    profile,
                    id=uuid4(),
                    is_current=False,
                    source_version="unaudited-history",
                )
            )
            write.commit()
    finally:
        engine.dispose()
    before = snapshot(config)
    with pytest.raises(ValueError, match="отдельный аудит"):
        migrations.apply_migrations(config)
    assert snapshot(config) == before
    assert migrations.pending_migration_ids(config) == [MIGRATION.MIGRATION_ID]


def test_mid_backfill_failure_rolls_back_and_resume_is_deterministic(
    tmp_path, monkeypatch
):
    config = DatabaseConfig(path=tmp_path / "rollback.sqlite")
    seed_previous(config)
    before = snapshot(config)
    original = MIGRATION.prepare_profile
    calls = []

    def fail(profile, food, bundle):
        calls.append(food)
        if len(calls) == 10:
            raise RuntimeError("injected mid-backfill failure")
        return original(profile, food, bundle)

    with monkeypatch.context() as patch:
        patch.setattr(MIGRATION, "prepare_profile", fail)
        with pytest.raises(RuntimeError, match="mid-backfill"):
            migrations.apply_migrations(config)
    assert len(calls) == 10
    assert snapshot(config) == before
    assert migrations.apply_migrations(config) == [MIGRATION.MIGRATION_ID]
    after = snapshot(config)
    assert all(after[name] == rows for name, rows in before.items())
    assert len(after["nutrient_values"]) == 806
    assert migrations.apply_migrations(config) == []
    assert snapshot(config) == after


def test_filtered_read_is_not_mistaken_for_unknown(database):
    from sqlalchemy import event
    from sqlalchemy.sql import Select

    _, engine = database
    existing = vector(engine)

    def omit_row(connection, clause, multiparams, params, options):
        if isinstance(clause, Select) and "nutrient_values" in str(clause):
            clause = clause.where(
                nutrient_values.c.nutrient_code != existing.values[0].definition.code
            )
        return clause, multiparams, params

    event.listen(engine, "before_execute", omit_row, retval=True)
    try:
        with pytest.raises(NutrientVectorUnavailableError, match="неполон"):
            vector(engine)
    finally:
        event.remove(engine, "before_execute", omit_row)
    assert vector(engine) == existing


@pytest.mark.parametrize("amount", [None, "-1", "NaN", "Infinity", ".", "1.2.3"])
def test_sql_numeric_rows_refuse_unknown_or_invalid_decimal(database, amount):
    config, _ = database
    with sqlite3.connect(config.path) as db:
        with pytest.raises(sqlite3.IntegrityError):
            db.execute(
                "INSERT INTO nutrient_values VALUES (?, ?, ?, ?)",
                (uuid4().hex, "CALCIUM", amount, "{}"),
            )


def test_seal_refuses_wrong_count(database):
    config, _ = database
    with sqlite3.connect(config.path) as db:
        with pytest.raises(sqlite3.IntegrityError, match="не соответствует"):
            db.execute(
                "INSERT INTO nutrition_vector_seals VALUES (?, ?, ?, ?, ?)",
                (uuid4().hex, "PR6_NUTRIENT_VECTOR_A_V1", 1, "0" * 64, "[]"),
            )


def test_audited_profile_initialization_rollback(database, monkeypatch):
    from app.persistence.sqlalchemy_core import nutrient_vector_repository as repository

    _, engine = database
    existing = vector(engine)
    profile = replace(
        existing.profile, id=uuid4(), is_current=False, source_version="injected"
    )

    def fail(connection, profile):
        connection.execute(
            insert(nutrient_values).values(
                profile_id=profile.id,
                nutrient_code="PROTEIN",
                amount=Decimal("1"),
                provenance_json="{}",
            )
        )
        raise RuntimeError("injected before seal")

    with monkeypatch.context() as patch:
        patch.setattr(repository, "initialize_audited_profile", fail)
        with pytest.raises(RuntimeError, match="before seal"):
            with SqlAlchemyFoodCatalogueUnitOfWork(engine) as write:
                write.nutrition_profiles.add(profile)
                write.commit()
    with SqlAlchemyNutritionReadScope(engine) as read:
        assert read.nutrition_profiles.get_nutrition_profile_by_id(profile.id) is None


@pytest.mark.parametrize(
    "field,state",
    [
        ("source_value_state", "ABSENT"),
        ("source_value_state", "IMPORT_FAILED"),
        ("source_value_state", "NOT_IMPORTED"),
        ("censoring_evidence_state", "EXPLICIT_CENSORED"),
        ("censoring_evidence_state", "LOQ_METADATA_PRESENT_STATUS_UNSPECIFIED"),
    ],
)
def test_failed_absent_or_censored_observation_cannot_gain_authority(
    database, bundle, field, state
):
    _, engine = database
    result = vector(engine)
    changed = deepcopy(bundle)
    row = next(
        r
        for r in changed["legacy-v1-crosswalk.json"]["rows"]
        if r["food_ingredient_code"] == "AGAVE_SYRUP" and r["legacy_field"] == "kcal"
    )
    row[field] = state
    values, observations = prepare_profile(
        asdict(result.profile), "AGAVE_SYRUP", changed
    )
    assert all(v["nutrient_code"] != "ENERGY_KCAL" for v in values)
    preserved = next(
        r
        for r in json.loads(observations)
        if r["observation"]["legacy_field"] == "kcal"
    )
    assert preserved["origin"] == state
    assert preserved["observation"]["legacy_value"] == "310.000000"


def test_digest_matches_fixed_decimal_storage_independent_of_context():
    scientific = dict(
        nutrient_code="CALCIUM", amount=Decimal("1E+10"), provenance_json="{}"
    )
    restored = dict(scientific, amount=Decimal(format(scientific["amount"], "f")))
    expected = value_set_digest([scientific])
    with localcontext() as context:
        context.prec = 2
        assert value_set_digest([restored]) == expected


def test_migration_includes_noncurrent_audited_history(tmp_path):
    config = DatabaseConfig(path=tmp_path / "historical.sqlite")
    seed_previous(config)
    engine = create_sqlite_engine(config)
    try:
        with SqlAlchemyFoodCatalogueUnitOfWork(engine) as write:
            food = write.ingredients.get_by_code("AGAVE_SYRUP")
            profile = write.nutrition_profiles.get_current(food.id)
            write.nutrition_profiles.clear_current(food.id)
            write.commit()
        before = snapshot(config)
        migrations.apply_migrations(config)
        after = snapshot(config)
        assert all(after[name] == rows for name, rows in before.items())
        with SqlAlchemyNutritionReadScope(engine) as read:
            assert read.nutrition_profiles.get_current(food.id) is None
            historical = read.nutrient_vectors.get(profile.id)
            assert historical.profile == replace(profile, is_current=False)
            assert historical.amount("ENERGY_KCAL") == profile.kcal
    finally:
        engine.dispose()
