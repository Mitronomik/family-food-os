import json
import sqlite3
from dataclasses import replace
from decimal import Decimal
from importlib import import_module

import pytest

from app.db import migrations
from app.db.config import DatabaseConfig
from app.db.migrations import apply_migrations, current_migrations, expected_migration_ids
from app.domain.nutrient_method_adapters import (
    ADAPTER_VERSION_V2,
    REGISTRY_V2,
    NutrientMethodAdapterError,
    binding_for_kind,
    resolve_method,
)
from app.domain.nutrient_vector_backfill_v1 import REGISTRY_VERSION as REGISTRY_V1
from app.domain.nutrition_methodology import NutrientKind, ObservationMethod
from pathlib import Path
from app.domain.reference_comparison import DailyNutrientAmount, compare_daily_reference
from app.domain.russian_reference_targets import RussianReferenceRow
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
from app.persistence.sqlalchemy_core.nutrition_read_scope import (
    SqlAlchemyNutritionReadScope,
)
from app.seed.food_ingredients import seed_food_ingredients

MIGRATION = import_module(
    "app.migrations.versions.0035_versioned_nutrient_registry"
)
PREVIOUS_HEAD = "0034_partial_nutrition_profiles"


def build_pre_v2(path):
    config = DatabaseConfig(path=path)
    original = list(migrations.MIGRATION_MODULES)
    cutoff = next(
        index
        for index, module_name in enumerate(original)
        if module_name.endswith(PREVIOUS_HEAD)
    )
    try:
        migrations.MIGRATION_MODULES[:] = original[: cutoff + 1]
        seed_food_ingredients(config)
    finally:
        migrations.MIGRATION_MODULES[:] = original
    return config


def legacy_rows(path):
    with sqlite3.connect(path) as db:
        definitions = db.execute(
            """
            SELECT code, display_name_ru, unit, registry_version, definition_json
            FROM nutrient_definitions ORDER BY code
            """
        ).fetchall()
        values = db.execute(
            """
            SELECT profile_id, nutrient_code, amount, provenance_json
            FROM nutrient_values ORDER BY profile_id, nutrient_code
            """
        ).fetchall()
        seals = db.execute(
            """
            SELECT profile_id, registry_version, value_count, value_sha256, observations_json
            FROM nutrition_vector_seals ORDER BY profile_id
            """
        ).fetchall()
        snapshot = db.execute(
            """
            SELECT version, bundle_json, bundle_sha256
            FROM nutrient_registry_snapshots
            WHERE version = ?
            """,
            (REGISTRY_V1,),
        ).fetchone()
    return definitions, values, seals, snapshot


def retention_rows(path, *, versioned):
    with sqlite3.connect(path) as db:
        if versioned:
            return db.execute(
                """
                SELECT profile_id, registry_version, nutrient_code, factor, provenance_json
                FROM food_retention_values
                ORDER BY profile_id, nutrient_code
                """
            ).fetchall()
        return db.execute(
            """
            SELECT profile_id, nutrient_code, factor, provenance_json
            FROM food_retention_values
            ORDER BY profile_id, nutrient_code
            """
        ).fetchall()


@pytest.fixture
def registry_database(tmp_path):
    config = DatabaseConfig(path=tmp_path / "registry-v2.sqlite")
    seed_food_ingredients(config)
    engine = create_sqlite_engine(config)
    yield config, engine
    engine.dispose()


def test_registry_v2_is_additive_and_v1_remains_immutable(registry_database):
    config, engine = registry_database
    with sqlite3.connect(config.path) as db:
        counts = dict(
            db.execute(
                """
                SELECT registry_version, count(*)
                FROM nutrient_definitions
                GROUP BY registry_version
                """
            ).fetchall()
        )
        assert counts == {REGISTRY_V1: 51, REGISTRY_V2: 54}
        same_code = db.execute(
            """
            SELECT registry_version, definition_json
            FROM nutrient_definitions
            WHERE code = 'CARBOHYDRATE_AVAILABLE'
            ORDER BY registry_version
            """
        ).fetchall()
        assert len(same_code) == 2
        assert same_code[0][1] != same_code[1][1]

    with SqlAlchemyNutritionReadScope(engine) as read:
        v1 = read.nutrient_registry.get(REGISTRY_V1, "CARBOHYDRATE_AVAILABLE")
        v2 = read.nutrient_registry.get(REGISTRY_V2, "CARBOHYDRATE_AVAILABLE")
        assert v1.semantic_identity == (REGISTRY_V1, "CARBOHYDRATE_AVAILABLE")
        assert v2.semantic_identity == (REGISTRY_V2, "CARBOHYDRATE_AVAILABLE")
        assert "сумма аналитических масс" in v1.definition_text_ru.lower()
        assert "метод" in v2.definition_text_ru.lower()
        assert v2.definition_kind == "METHOD_INDEPENDENT_COMPONENT"


@pytest.mark.parametrize(
    "code,unit",
    [
        ("VITAMIN_A_RE", "µg"),
        ("NIACIN_EQUIVALENT", "mg"),
        ("VITAMIN_E_TOCOPHEROL_EQUIVALENT", "mg"),
    ],
)
def test_russian_equivalent_definitions_are_distinct_registry_concepts(
    registry_database, code, unit
):
    _, engine = registry_database
    with SqlAlchemyNutritionReadScope(engine) as read:
        definition = read.nutrient_registry.get(REGISTRY_V2, code)
    assert definition.code == code
    assert definition.unit == unit
    assert definition.definition_kind == "EQUIVALENT_COMPONENT"
    assert definition.definition_text_ru


@pytest.mark.parametrize(
    "method",
    [
        ObservationMethod.AVAILABLE_SUMMATION,
        ObservationMethod.AVAILABLE_BY_DIFFERENCE,
        ObservationMethod.AVAILABLE_PUBLISHED_ROW_UNSPECIFIED,
    ],
)
def test_v2_available_carbohydrate_requires_explicit_supported_method(method):
    resolved = resolve_method(
        REGISTRY_V2,
        NutrientKind.AVAILABLE_CARBOHYDRATE,
        evidence_json=json.dumps({"method_code": method.value}),
    )
    assert resolved is method


def test_v2_method_adapter_fails_closed_without_method_or_with_wrong_method():
    with pytest.raises(NutrientMethodAdapterError, match="method_code"):
        resolve_method(
            REGISTRY_V2,
            NutrientKind.AVAILABLE_CARBOHYDRATE,
            evidence_json="{}",
        )
    with pytest.raises(NutrientMethodAdapterError, match="несовместим"):
        resolve_method(
            REGISTRY_V2,
            NutrientKind.AVAILABLE_CARBOHYDRATE,
            evidence_json=json.dumps(
                {"method_code": ObservationMethod.TOTAL_BY_DIFFERENCE.value}
            ),
        )

    # Frozen V1 behavior remains exactly the historical summation projection.
    assert (
        resolve_method(
            REGISTRY_V1,
            NutrientKind.AVAILABLE_CARBOHYDRATE,
            evidence_json=None,
        )
        is ObservationMethod.AVAILABLE_SUMMATION
    )


def reference(code, unit, value):
    return RussianReferenceRow(
        id="reference",
        source_id="RU-MR",
        source_version="2021",
        locator="table",
        review_reference="registry-v2-test",
        definition_code=code,
        unit=unit,
        value=value,
        sex="all",
        age_min_years=18,
        age_max_years_exclusive=None,
        physical_activity_coefficient=None,
        life_stage="adult",
    )


@pytest.mark.parametrize(
    "food_code,reference_code,unit",
    [
        ("VITAMIN_A_RAE", "VITAMIN_A_RE", "µg/day"),
        ("NIACIN", "NIACIN_EQUIVALENT", "mg/day"),
        (
            "VITAMIN_E_ALPHA_TOCOPHEROL",
            "VITAMIN_E_TOCOPHEROL_EQUIVALENT",
            "mg/day",
        ),
        ("CARBOHYDRATE_BY_DIFFERENCE", "CARBOHYDRATE_AVAILABLE", "g/day"),
    ],
)
def test_equal_units_never_substitute_incompatible_definitions(
    food_code, reference_code, unit
):
    result = compare_daily_reference(
        DailyNutrientAmount(
            food_code,
            unit,
            Decimal("1"),
            "registry-v2-test",
            ("source",),
        ),
        reference(reference_code, unit, Decimal("1")),
    )
    assert result.status == "INCOMPATIBLE_DEFINITION"
    assert result.percent_of_group_reference is None


def test_populated_0034_upgrade_preserves_all_v1_rows_and_seals(tmp_path):
    config = build_pre_v2(tmp_path / "upgrade.sqlite")
    before_definitions, before_values, before_seals, before_snapshot = legacy_rows(
        config.path
    )
    before_retention = retention_rows(config.path, versioned=False)

    assert apply_migrations(config) == [
        MIGRATION.MIGRATION_ID,
        "0036_member_reference_methodology_selection",
        "0037_meal_plan_reference_methodology_pins",
        "0038_transformation_applicability",
        "0039_recipe_ingredient_composition_binding",
    ]

    with sqlite3.connect(config.path) as db:
        after_definitions = db.execute(
            """
            SELECT code, display_name_ru, unit, registry_version, definition_json
            FROM nutrient_definitions
            WHERE registry_version = ?
            ORDER BY code
            """,
            (REGISTRY_V1,),
        ).fetchall()
        after_values = db.execute(
            """
            SELECT profile_id, nutrient_code, amount, provenance_json
            FROM nutrient_values
            WHERE registry_version = ?
            ORDER BY profile_id, nutrient_code
            """,
            (REGISTRY_V1,),
        ).fetchall()
        after_seals = db.execute(
            """
            SELECT profile_id, registry_version, value_count, value_sha256, observations_json
            FROM nutrition_vector_seals ORDER BY profile_id
            """
        ).fetchall()
        after_snapshot = db.execute(
            """
            SELECT version, bundle_json, bundle_sha256
            FROM nutrient_registry_snapshots
            WHERE version = ?
            """,
            (REGISTRY_V1,),
        ).fetchone()
        assert db.execute("PRAGMA foreign_key_check").fetchall() == []
        assert db.execute(
            "SELECT count(*) FROM nutrient_definitions WHERE registry_version = ?",
            (REGISTRY_V2,),
        ).fetchone() == (54,)

    assert after_definitions == before_definitions
    assert after_values == before_values
    assert after_seals == before_seals
    assert after_snapshot == before_snapshot
    after_retention = retention_rows(config.path, versioned=True)
    assert [
        (profile_id, nutrient_code, factor, provenance_json)
        for (
            profile_id,
            registry_version,
            nutrient_code,
            factor,
            provenance_json,
        ) in after_retention
        if registry_version == REGISTRY_V1
    ] == before_retention
    assert all(row[1] == REGISTRY_V1 for row in after_retention)


def test_0035_failure_rolls_back_schema_and_marker(tmp_path):
    config = build_pre_v2(tmp_path / "rollback.sqlite")
    before = legacy_rows(config.path)
    with sqlite3.connect(config.path) as db:
        db.execute(
            "INSERT INTO nutrient_registry_snapshots VALUES (?, '{}', ?)",
            (REGISTRY_V2, "0" * 64),
        )
        db.commit()

    with pytest.raises(sqlite3.IntegrityError):
        apply_migrations(config)

    assert MIGRATION.MIGRATION_ID not in current_migrations(config)
    with sqlite3.connect(config.path) as db:
        columns = [row[1] for row in db.execute("PRAGMA table_info(nutrient_values)")]
        definition_pk = {
            row[1]: row[5]
            for row in db.execute("PRAGMA table_info(nutrient_definitions)")
        }
        assert "registry_version" not in columns
        assert definition_pk["code"] == 1
        assert definition_pk["registry_version"] == 0
        assert db.execute("PRAGMA foreign_key_check").fetchall() == []

    after = legacy_rows(config.path)
    # The test's intentionally pre-existing conflicting snapshot is outside the
    # four V1 structures compared here; the migration itself changed none of them.
    assert after == before


def test_migration_chain_advances_without_consuming_reserved_0033():
    expected = expected_migration_ids()
    assert expected[-7:] == [
        "0032_meal_plan_serving",
        "0034_partial_nutrition_profiles",
        "0035_versioned_nutrient_registry",
        "0036_member_reference_methodology_selection",
        "0037_meal_plan_reference_methodology_pins",
        "0038_transformation_applicability",
        "0039_recipe_ingredient_composition_binding",
    ]
    assert not any(value.startswith("0033_") for value in expected)


def test_committed_adapter_contract_matches_runtime_bindings():
    root = Path(__file__).resolve().parents[3]
    contract = json.loads(
        (
            root
            / "data/curation/nutrient-registry-v2/method-adapters.json"
        ).read_text()
    )
    assert contract["version"] == ADAPTER_VERSION_V2
    assert contract["registry_version"] == REGISTRY_V2
    for row in contract["bindings"]:
        kind = NutrientKind(row["nutrient_kind"])
        binding = binding_for_kind(REGISTRY_V2, kind)
        assert binding.nutrient_code == row["canonical_code"]
        assert {method.value for method in binding.allowed_methods} == set(
            row["allowed_methods"]
        )


def test_reference_compatibility_matrix_names_exact_v2_concepts():
    root = Path(__file__).resolve().parents[3]
    matrix = json.loads(
        (
            root
            / "data/curation/russian-methodology/reference-compatibility.json"
        ).read_text()
    )
    assert matrix["registry_v2"] == REGISTRY_V2
    by_reference = {
        row["reference_definition"]: row for row in matrix["comparisons"]
    }
    assert (
        by_reference["available_carbohydrate"]["registry_v2_reference_code"]
        == "CARBOHYDRATE_AVAILABLE"
    )
    assert (
        by_reference["vitamin_a_retinol_equivalent"]["registry_v2_reference_code"]
        == "VITAMIN_A_RE"
    )
    assert (
        by_reference["niacin_equivalent"]["registry_v2_reference_code"]
        == "NIACIN_EQUIVALENT"
    )
    assert (
        by_reference["tocopherol_equivalent"]["registry_v2_reference_code"]
        == "VITAMIN_E_TOCOPHEROL_EQUIVALENT"
    )
    assert (
        by_reference["folates_source_unspecified"]["registry_v2_reference_code"]
        is None
    )


def test_0035_version_pins_existing_retention_rows_without_changing_values(tmp_path):
    config = build_pre_v2(tmp_path / "retention-upgrade.sqlite")
    engine = create_sqlite_engine(config)
    try:
        from app.persistence.sqlalchemy_core.food_composition_scope import (
            SqlAlchemyCompositionUnitOfWork,
        )
        from app.domain.food_composition import (
            CompositionProvenance,
            MassState,
            NutrientRetentionProfile,
            RetentionValue,
        )
        from uuid import uuid4

        provenance = CompositionProvenance(
            "synthetic",
            "1",
            "retention-evidence",
            "registry-v2-migration-test",
        )
        profile = NutrientRetentionProfile(
            uuid4(),
            1,
            MassState.RAW,
            MassState.COOKED,
            provenance,
            (RetentionValue("PROTEIN", Decimal("0.8"), provenance),),
        )
        with SqlAlchemyCompositionUnitOfWork(engine) as uow:
            uow.compositions.add_retention_profile(profile)
            uow.commit()
    finally:
        engine.dispose()

    before = retention_rows(config.path, versioned=False)
    assert len(before) == 1

    assert apply_migrations(config) == [
        MIGRATION.MIGRATION_ID,
        "0036_member_reference_methodology_selection",
        "0037_meal_plan_reference_methodology_pins",
        "0038_transformation_applicability",
        "0039_recipe_ingredient_composition_binding",
    ]

    with sqlite3.connect(config.path) as db:
        after = db.execute(
            """
            SELECT profile_id, registry_version, nutrient_code, factor, provenance_json
            FROM food_retention_values
            ORDER BY profile_id, nutrient_code
            """
        ).fetchall()
        assert after == [
            (
                before[0][0],
                REGISTRY_V1,
                before[0][1],
                before[0][2],
                before[0][3],
            )
        ]
        assert db.execute("PRAGMA foreign_key_check").fetchall() == []
        with pytest.raises(sqlite3.IntegrityError, match="неизменяем"):
            db.execute(
                "UPDATE food_retention_values SET factor = factor WHERE profile_id = ?",
                (before[0][0],),
            )


def test_registry_v2_embeds_fail_closed_appendix2_source_receipt():
    root = Path(__file__).resolve().parents[3]
    registry = json.loads(
        (root / "data/curation/nutrient-registry-v2/registry.json").read_text()
    )
    receipt = registry["source_receipts"]["RU-MR-APPENDIX-2"]
    assert receipt["document"] == "МР 2.3.1.0253-21"
    assert (
        receipt["locator"]
        == "Приложение 2 — коэффициенты пересчета для эквивалентов витаминов"
    )
    assert (
        receipt["source_sha256"]
        == "cf96c7ea7fab087d16b478b2c8c097406d7572e495b2beb43405e4fd05917d79"
    )
    assert set(receipt["scope"]) == {
        "VITAMIN_A_RE",
        "NIACIN_EQUIVALENT",
        "VITAMIN_E_TOCOPHEROL_EQUIVALENT",
    }
    by_code = {row["canonical_code"]: row for row in registry["entries"]}
    for code in receipt["scope"]:
        assert by_code[code]["source_evidence_refs"] == ["RU-MR-APPENDIX-2"]
