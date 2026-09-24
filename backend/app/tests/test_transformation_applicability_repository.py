"""Repository/UoW tests for Step 7 registry-aware transformation applicability."""

from datetime import datetime, timezone
from decimal import Decimal
import sqlite3
from uuid import UUID, uuid4

import pytest
from sqlalchemy import insert

from app.db.config import DatabaseConfig
from app.domain.food_composition import (
    CompositionKind,
    CompositionProvenance,
    CompositionStep,
    CompositionUnavailableError,
    FoodCompositionVersion,
    FoodTransformation,
    MassState,
    NutrientRetentionProfile,
    RetentionValue,
    SeasonScope,
    TransformationApplicability,
    snapshot_digest,
)
from app.domain.food_ingredients import FoodNutritionProfile
from app.domain.nutrient_vector import V2_REGISTRY_VERSION
from app.domain.nutrient_vector_backfill_v1 import (
    REGISTRY_VERSION as REGISTRY_V1,
    value_set_digest,
)
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
from app.persistence.sqlalchemy_core.food_composition_scope import (
    SqlAlchemyCompositionReadScope,
    SqlAlchemyCompositionUnitOfWork,
)
from app.persistence.sqlalchemy_core.food_ingredient_uow import (
    SqlAlchemyFoodCatalogueUnitOfWork,
)
from app.persistence.sqlalchemy_core.nutrient_vector_tables import vector_seals
from app.seed.food_ingredients import seed_food_ingredients
from app.tests.test_nutrient_vector import vector

D = Decimal
P = CompositionProvenance(
    "synthetic-step7",
    "1",
    "test-only-evidence",
    "explicit-test-review",
)


@pytest.fixture
def database(tmp_path):
    config = DatabaseConfig(path=tmp_path / "step7.sqlite")
    seed_food_ingredients(config)
    engine = create_sqlite_engine(config)
    yield config, engine
    engine.dispose()


def food_ids(config: DatabaseConfig) -> tuple[UUID, UUID]:
    with sqlite3.connect(config.path) as db:
        rows = db.execute(
            "SELECT id FROM food_ingredients ORDER BY canonical_code LIMIT 2"
        ).fetchall()
    assert len(rows) == 2
    return UUID(hex=rows[0][0]), UUID(hex=rows[1][0])


def next_composition_version(config: DatabaseConfig, food_id: UUID) -> int:
    with sqlite3.connect(config.path) as db:
        row = db.execute(
            """
            SELECT COALESCE(MAX(version), 0)
            FROM food_composition_versions
            WHERE food_ingredient_id = ?
            """,
            (food_id.hex,),
        ).fetchone()
    assert row is not None
    return int(row[0]) + 1


def publish_empty_v2_profile(engine, food_id: UUID) -> FoodNutritionProfile:
    profile = FoodNutritionProfile(
        id=uuid4(),
        food_ingredient_id=food_id,
        basis_grams=D("100"),
        kcal=D("0"),
        protein_g=D("0"),
        fat_g=D("0"),
        carbohydrates_g=D("0"),
        fiber_g=None,
        source_name="synthetic-step7-empty-vector",
        source_id=str(uuid4()),
        source_version="1",
        source_data_type="test",
        verified_at=datetime(2026, 9, 24, tzinfo=timezone.utc),
        estimated=False,
        is_current=False,
        created_at=datetime(2026, 9, 24, tzinfo=timezone.utc),
    )
    with SqlAlchemyFoodCatalogueUnitOfWork(engine) as uow:
        uow.nutrition_profiles.add(profile)
        uow.commit()

    with engine.begin() as connection:
        connection.execute(
            insert(vector_seals).values(
                profile_id=profile.id,
                registry_version=V2_REGISTRY_VERSION,
                value_count=0,
                value_sha256=value_set_digest([]),
                observations_json="[]",
            )
        )
    return profile


def publish_v2_atomic(config, engine, food_id: UUID) -> FoodCompositionVersion:
    profile = publish_empty_v2_profile(engine, food_id)
    value = FoodCompositionVersion(
        uuid4(),
        food_id,
        next_composition_version(config, food_id),
        CompositionKind.ATOMIC,
        MassState.INPUT,
        P,
        profile_id=profile.id,
    )
    with SqlAlchemyCompositionUnitOfWork(engine) as uow:
        uow.compositions.add_versions_for_registry(
            (value,),
            V2_REGISTRY_VERSION,
        )
        uow.commit()
    return value


def no_retention_transformation() -> FoodTransformation:
    return FoodTransformation(
        uuid4(),
        1,
        "SYNTHETIC_PROCESS",
        MassState.INPUT,
        MassState.COOKED,
        P,
    )


def applicability(
    transformation: FoodTransformation,
    food_id: UUID,
    *,
    registry_version: str | None = None,
    evidence_scope_id: str = "scope-1",
) -> TransformationApplicability:
    return TransformationApplicability(
        transformation.id,
        food_id,
        registry_version,
        SeasonScope.ALL_SEASONS,
        None,
        evidence_scope_id,
        P,
    )


def test_registry_aware_retention_writer_reader_and_snapshot_shape(database):
    config, engine = database
    food_id, _ = food_ids(config)
    profile = NutrientRetentionProfile(
        uuid4(),
        1,
        MassState.INPUT,
        MassState.COOKED,
        P,
        (RetentionValue("PROTEIN", D("0.8"), P),),
    )
    transformation = FoodTransformation(
        uuid4(),
        1,
        "SYNTHETIC_PROCESS",
        MassState.INPUT,
        MassState.COOKED,
        P,
        retention_profile_id=profile.id,
    )
    app = applicability(
        transformation,
        food_id,
        registry_version=V2_REGISTRY_VERSION,
    )

    with SqlAlchemyCompositionUnitOfWork(engine) as uow:
        uow.compositions.add_retention_profile_for_registry(
            profile,
            V2_REGISTRY_VERSION,
        )
        uow.compositions.add_transformation(transformation)
        uow.compositions.add_applicability(app)
        uow.commit()

    with SqlAlchemyCompositionReadScope(engine) as read:
        legacy_shape = read.compositions.retention_profile(profile.id)
        exact = read.compositions.retention_profile_for_registry(
            profile.id,
            V2_REGISTRY_VERSION,
        )
        assert exact == legacy_shape == profile
        assert snapshot_digest(legacy_shape) == snapshot_digest(profile)
        assert read.compositions.applicability(transformation.id) == app

    with sqlite3.connect(config.path) as db:
        row = db.execute(
            """
            SELECT registry_version
            FROM food_retention_values
            WHERE profile_id = ?
            """,
            (profile.id.hex,),
        ).fetchone()
    assert row == (V2_REGISTRY_VERSION,)


def test_registry_aware_reader_detects_persisted_registry_mismatch(database):
    config, engine = database
    food_id, _ = food_ids(config)
    profile = NutrientRetentionProfile(
        uuid4(),
        1,
        MassState.INPUT,
        MassState.COOKED,
        P,
        (RetentionValue("PROTEIN", D("0.8"), P),),
    )
    transformation = FoodTransformation(
        uuid4(),
        1,
        "SYNTHETIC_PROCESS",
        MassState.INPUT,
        MassState.COOKED,
        P,
        retention_profile_id=profile.id,
    )
    with SqlAlchemyCompositionUnitOfWork(engine) as uow:
        uow.compositions.add_retention_profile_for_registry(
            profile,
            V2_REGISTRY_VERSION,
        )
        uow.compositions.add_transformation(transformation)
        uow.compositions.add_applicability(
            applicability(
                transformation,
                food_id,
                registry_version=V2_REGISTRY_VERSION,
            )
        )
        uow.commit()

    with sqlite3.connect(config.path) as db:
        db.execute("DROP TRIGGER food_retention_values_no_update")
        db.execute(
            """
            UPDATE food_retention_values
            SET registry_version = ?
            WHERE profile_id = ?
            """,
            (REGISTRY_V1, profile.id.hex),
        )
        db.commit()

    with SqlAlchemyCompositionReadScope(engine) as read:
        assert read.compositions.retention_profile(profile.id) == profile
        with pytest.raises(CompositionUnavailableError) as error:
            read.compositions.retention_profile_for_registry(
                profile.id,
                V2_REGISTRY_VERSION,
            )
    assert error.value.issue_code == "RETENTION_REGISTRY_MISMATCH"


def test_new_retention_profile_cannot_mix_registry_versions(database):
    config, _ = database
    profile_id = uuid4().hex
    provenance = '{"source":"synthetic"}'
    with sqlite3.connect(config.path) as db:
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("BEGIN")
        db.execute(
            """
            INSERT INTO food_retention_values (
                profile_id, registry_version, nutrient_code, factor, provenance_json
            ) VALUES (?, ?, 'PROTEIN', '1', ?)
            """,
            (profile_id, V2_REGISTRY_VERSION, provenance),
        )
        with pytest.raises(sqlite3.IntegrityError, match="смешивать реестры"):
            db.execute(
                """
                INSERT INTO food_retention_values (
                    profile_id, registry_version, nutrient_code, factor, provenance_json
                ) VALUES (?, ?, 'FAT_TOTAL', '1', ?)
                """,
                (profile_id, REGISTRY_V1, provenance),
            )
        db.rollback()


def test_v2_publication_requires_applicability_and_exact_food(database):
    config, engine = database
    food_id, other_food_id = food_ids(config)
    base = publish_v2_atomic(config, engine, food_id)

    missing = no_retention_transformation()
    missing_version = replace_version_with_step(
        config,
        base,
        missing,
    )
    with SqlAlchemyCompositionUnitOfWork(engine) as uow:
        uow.compositions.add_transformation(missing)
        with pytest.raises(CompositionUnavailableError) as error:
            uow.compositions.add_versions_for_registry(
                (missing_version,),
                V2_REGISTRY_VERSION,
            )
        assert error.value.issue_code == "TRANSFORMATION_APPLICABILITY_MISSING"
        uow.rollback()

    wrong = no_retention_transformation()
    wrong_version = replace_version_with_step(
        config,
        base,
        wrong,
    )
    with SqlAlchemyCompositionUnitOfWork(engine) as uow:
        uow.compositions.add_transformation(wrong)
        uow.compositions.add_applicability(
            applicability(wrong, other_food_id)
        )
        with pytest.raises(CompositionUnavailableError) as error:
            uow.compositions.add_versions_for_registry(
                (wrong_version,),
                V2_REGISTRY_VERSION,
            )
        assert (
            error.value.issue_code
            == "TRANSFORMATION_APPLICABILITY_FOOD_MISMATCH"
        )
        uow.rollback()


def replace_version_with_step(
    config: DatabaseConfig,
    base: FoodCompositionVersion,
    transformation: FoodTransformation,
) -> FoodCompositionVersion:
    return FoodCompositionVersion(
        uuid4(),
        base.food_ingredient_id,
        next_composition_version(config, base.food_ingredient_id),
        CompositionKind.ATOMIC,
        MassState.INPUT,
        P,
        profile_id=base.profile_id,
        steps=(CompositionStep(uuid4(), 0, transformation.id),),
    )


def test_applicability_transformation_and_v2_composition_publish_atomically(database):
    config, engine = database
    food_id, _ = food_ids(config)
    base = publish_v2_atomic(config, engine, food_id)
    transformation = no_retention_transformation()
    transformed = replace_version_with_step(config, base, transformation)
    app = applicability(transformation, food_id)

    with SqlAlchemyCompositionUnitOfWork(engine) as uow:
        uow.compositions.add_transformation(transformation)
        uow.compositions.add_applicability(app)
        uow.compositions.add_versions_for_registry(
            (transformed,),
            V2_REGISTRY_VERSION,
        )
        uow.commit()

    with SqlAlchemyCompositionReadScope(engine) as read:
        assert read.compositions.get(transformed.id) == transformed
        assert read.compositions.applicability(transformation.id) == app


def test_uncommitted_step7_state_rolls_back_as_one_unit(database):
    config, engine = database
    food_id, _ = food_ids(config)
    base = publish_v2_atomic(config, engine, food_id)
    profile = NutrientRetentionProfile(
        uuid4(),
        1,
        MassState.INPUT,
        MassState.COOKED,
        P,
        (RetentionValue("PROTEIN", D("0.8"), P),),
    )
    transformation = FoodTransformation(
        uuid4(),
        1,
        "SYNTHETIC_PROCESS",
        MassState.INPUT,
        MassState.COOKED,
        P,
        retention_profile_id=profile.id,
    )
    app = applicability(
        transformation,
        food_id,
        registry_version=V2_REGISTRY_VERSION,
    )
    transformed = replace_version_with_step(config, base, transformation)

    with SqlAlchemyCompositionUnitOfWork(engine) as uow:
        uow.compositions.add_retention_profile_for_registry(
            profile,
            V2_REGISTRY_VERSION,
        )
        uow.compositions.add_transformation(transformation)
        uow.compositions.add_applicability(app)
        uow.compositions.add_versions_for_registry(
            (transformed,),
            V2_REGISTRY_VERSION,
        )
        # No commit: the UoW must revoke all attempted Step 7 state.

    with sqlite3.connect(config.path) as db:
        assert db.execute(
            "SELECT count(*) FROM food_retention_profiles WHERE id = ?",
            (profile.id.hex,),
        ).fetchone() == (0,)
        assert db.execute(
            "SELECT count(*) FROM food_transformations WHERE id = ?",
            (transformation.id.hex,),
        ).fetchone() == (0,)
        assert db.execute(
            """
            SELECT count(*) FROM food_transformation_applicability
            WHERE transformation_id = ?
            """,
            (transformation.id.hex,),
        ).fetchone() == (0,)
        assert db.execute(
            "SELECT count(*) FROM food_composition_versions WHERE id = ?",
            (transformed.id.hex,),
        ).fetchone() == (0,)


def test_legacy_add_versions_needs_no_applicability_and_blocks_late_binding(database):
    config, engine = database
    legacy_vector = vector(engine)
    version_number = next_composition_version(
        config,
        legacy_vector.profile.food_ingredient_id,
    )
    transformation = FoodTransformation(
        uuid4(),
        1,
        "LEGACY_SYNTHETIC_PROCESS",
        MassState.RAW,
        MassState.COOKED,
        P,
    )
    historical = FoodCompositionVersion(
        uuid4(),
        legacy_vector.profile.food_ingredient_id,
        version_number,
        CompositionKind.ATOMIC,
        MassState.RAW,
        P,
        profile_id=legacy_vector.profile_id,
        steps=(CompositionStep(uuid4(), 0, transformation.id),),
    )

    with SqlAlchemyCompositionUnitOfWork(engine) as uow:
        uow.compositions.add_transformation(transformation)
        uow.compositions.add_versions((historical,))
        uow.commit()

    with SqlAlchemyCompositionUnitOfWork(engine) as uow:
        with pytest.raises(CompositionUnavailableError) as error:
            uow.compositions.add_applicability(
                applicability(
                    transformation,
                    legacy_vector.profile.food_ingredient_id,
                )
            )
        assert error.value.issue_code == "TRANSFORMATION_APPLICABILITY_LATE"
        uow.rollback()


def test_applicability_rows_are_immutable(database):
    config, engine = database
    food_id, _ = food_ids(config)
    transformation = no_retention_transformation()
    with SqlAlchemyCompositionUnitOfWork(engine) as uow:
        uow.compositions.add_transformation(transformation)
        uow.compositions.add_applicability(
            applicability(transformation, food_id)
        )
        uow.commit()

    with sqlite3.connect(config.path) as db:
        with pytest.raises(sqlite3.IntegrityError, match="неизменяема"):
            db.execute(
                """
                UPDATE food_transformation_applicability
                SET evidence_scope_id = 'changed'
                WHERE transformation_id = ?
                """,
                (transformation.id.hex,),
            )
        db.rollback()
        with pytest.raises(sqlite3.IntegrityError, match="неизменяема"):
            db.execute(
                """
                DELETE FROM food_transformation_applicability
                WHERE transformation_id = ?
                """,
                (transformation.id.hex,),
            )
        db.rollback()
