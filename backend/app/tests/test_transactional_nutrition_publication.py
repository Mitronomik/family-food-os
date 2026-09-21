"""Step 3: transactional reviewed V2 profile/vector/ATOMIC publication."""

from copy import deepcopy
from dataclasses import replace
from datetime import datetime, timezone
from decimal import Decimal
import json
import sqlite3
from uuid import uuid4

import pytest
from sqlalchemy import event

from app.db import migrations
from app.db.config import DatabaseConfig
from app.domain.food_composition import (
    CompositionProvenance,
    CompositionUnavailableError,
    MassState,
)
from app.domain.food_ingredients import NutritionObservationState
from app.domain.nutrient_method_adapters import REGISTRY_V2
from app.domain.nutrient_vector import (
    V2_VALUE_EVIDENCE_SCHEMA,
    NutrientValueEvidenceError,
    decode_v2_value_evidence,
)
from app.domain.nutrient_vector_backfill_v1 import (
    REGISTRY_VERSION as REGISTRY_V1,
    value_set_digest,
)
from app.domain.nutrition_methodology import (
    NutrientKind,
    ObservationMethod,
    RussianNutritionPolicy,
)
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
from app.persistence.sqlalchemy_core.food_composition_scope import (
    SqlAlchemyCompositionReadScope,
)
from app.persistence.sqlalchemy_core.food_ingredient_composition import (
    create_food_catalogue_service,
)
from app.persistence.sqlalchemy_core.food_ingredient_uow import (
    SqlAlchemyFoodCatalogueReadScope,
)
from app.persistence.sqlalchemy_core.nutrition_publication import (
    SqlAlchemyNutritionPublicationUnitOfWork,
    create_nutrition_publication_service,
)
from app.persistence.sqlalchemy_core.nutrition_read_scope import (
    SqlAlchemyNutritionReadScope,
)
from app.seed.food_ingredients import seed_food_ingredients
from app.services.food_composition import CompositionCalculator
from app.services.food_ingredients import (
    TrustedFoodIngredientSeed,
    TrustedNutritionSeed,
)
from app.services.nutrition_methodology import NutritionMethodologyService
from app.services.nutrition_publication import (
    NutritionPublicationConflictError,
    NutritionPublicationContractError,
    PublicationIngredientAction,
    ReviewedAtomicCompositionSpec,
    ReviewedIngredientSpec,
    ReviewedNutrientValueSpec,
    ReviewedNutrientVectorSpec,
    ReviewedNutritionProfileSpec,
    ReviewedNutritionPublicationBundle,
    ReviewedNutritionPublicationService,
    ReviewedSourceObservationSpec,
)

NOW = datetime(2026, 9, 21, 12, tzinfo=timezone.utc)
VERIFIED = datetime(2026, 9, 20, 9, tzinfo=timezone.utc)


@pytest.fixture
def database(tmp_path):
    config = DatabaseConfig(path=tmp_path / "step3.sqlite")
    migrations.apply_migrations(config)
    engine = create_sqlite_engine(config)
    try:
        yield config, engine
    finally:
        engine.dispose()


def profile_spec(*, partial=False, source_id="STEP3-001"):
    values = {
        "kcal": Decimal("120"),
        "protein_g": None if partial else Decimal("8"),
        "fat_g": Decimal("4"),
        "carbohydrates_g": None if partial else Decimal("12"),
        "fiber_g": Decimal("2"),
    }
    observations = []
    for field, amount in values.items():
        if amount is None:
            state = (
                NutritionObservationState.METHOD_INCOMPATIBLE
                if field == "carbohydrates_g"
                else NutritionObservationState.MISSING
            )
            literal = "12" if field == "carbohydrates_g" else None
            method = "source-native available carbohydrate" if literal else None
        else:
            state = NutritionObservationState.VALUE
            literal = format(amount, "f")
            method = "reviewed source row"
        observations.append(
            ReviewedSourceObservationSpec(
                source_field=field,
                state=state,
                source_literal=literal,
                method_reference=method,
                source_locator=f"synthetic:{source_id}:{field}",
            )
        )
    return ReviewedNutritionProfileSpec(
        basis_grams=Decimal("100"),
        kcal=values["kcal"],
        protein_g=values["protein_g"],
        fat_g=values["fat_g"],
        carbohydrates_g=values["carbohydrates_g"],
        fiber_g=values["fiber_g"],
        source_name="STEP3_SYNTHETIC",
        source_id=source_id,
        source_version="2026-09-21",
        source_data_type="reviewed_synthetic_fixture",
        verified_at=VERIFIED,
        estimated=None,
        observations=tuple(observations),
    )


def evidence(profile, code, amount, unit, method, *, token=None):
    token = token or code.lower()
    payload = {
        "schema_version": V2_VALUE_EVIDENCE_SCHEMA,
        "registry_version": REGISTRY_V2,
        "method_code": method.value,
        "origin": "SOURCE_COMPONENT_CONFIRMED",
        "observation": {
            "audit_identity": f"step3:{profile.source_id}:{token}",
            "profile_source_name": profile.source_name,
            "profile_source_id": profile.source_id,
            "profile_source_version": profile.source_version,
            "profile_source_data_type": profile.source_data_type,
            "source_component_id": f"component:{token}",
            "source_component_name": f"Компонент {token}",
            "source_unit": unit,
            "source_value": format(amount, "f"),
            "source_observation_id": f"observation:{profile.source_id}:{token}",
            "source_derivation_id": None,
            "source_locator": f"synthetic:{profile.source_id}:{token}",
            "uncertainty": None,
        },
        "mapping": {
            "canonical_code": code,
            "mapping_status": "EXACT",
            "definition_reference": f"synthetic-definition:{code}",
        },
    }
    return json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )


def vector_spec(profile, *, partial=False, mutate=None):
    raw = [
        (
            "ENERGY_KCAL",
            Decimal("120"),
            "kcal",
            ObservationMethod.PUBLISHED,
        ),
        ("FAT_TOTAL", Decimal("4"), "g", ObservationMethod.ANALYTICAL),
        (
            "FIBER_TOTAL_DIETARY",
            Decimal("2"),
            "g",
            ObservationMethod.ANALYTICAL,
        ),
    ]
    if not partial:
        raw.extend(
            [
                ("PROTEIN", Decimal("8"), "g", ObservationMethod.ANALYTICAL),
                (
                    "CARBOHYDRATE_AVAILABLE",
                    Decimal("12"),
                    "g",
                    ObservationMethod.AVAILABLE_BY_DIFFERENCE,
                ),
            ]
        )
    values = [
        ReviewedNutrientValueSpec(
            nutrient_code=code,
            amount=amount,
            provenance_json=evidence(profile, code, amount, unit, method),
        )
        for code, amount, unit, method in raw
    ]
    if mutate is not None:
        values = mutate(values)
    rows = [
        {
            "nutrient_code": value.nutrient_code,
            "amount": value.amount,
            "provenance_json": value.provenance_json,
        }
        for value in values
    ]
    held = (
        [
            {
                "origin": "METHOD_INCOMPATIBLE",
                "observation": {
                    "target_nutrient_code": "CARBOHYDRATE_AVAILABLE",
                    "method_code": ObservationMethod.AVAILABLE_PUBLISHED_ROW_UNSPECIFIED.value,
                    "source_value": "12",
                },
            },
            {
                "origin": "VALUE_ABSENT",
                "observation": {
                    "target_nutrient_code": "PROTEIN",
                    "method_code": ObservationMethod.ANALYTICAL.value,
                },
            },
        ]
        if partial
        else []
    )
    return ReviewedNutrientVectorSpec(
        registry_version=REGISTRY_V2,
        values=tuple(values),
        observations_json=json.dumps(
            held, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ),
        value_count=len(rows),
        value_sha256=value_set_digest(rows),
    )


def bundle(
    code="STEP3_TEST_FOOD",
    name="Тестовый продукт публикации",
    *,
    partial=False,
    action=PublicationIngredientAction.CREATE_REVIEWED,
    source_id="STEP3-001",
    composition_version=1,
):
    profile = profile_spec(partial=partial, source_id=source_id)
    return ReviewedNutritionPublicationBundle(
        ingredient=ReviewedIngredientSpec(
            action=action,
            canonical_code=code,
            canonical_name=name,
            category_code="test_foods",
            default_unit="g",
            density_g_per_ml=None,
            edible_fraction=None,
            allergens_reviewed=False,
            allergen_codes=(),
            storage_profile_code=None,
        ),
        profile=profile,
        vector=vector_spec(profile, partial=partial),
        atomic_composition=ReviewedAtomicCompositionSpec(
            version=composition_version,
            input_state=MassState.RAW,
            provenance=CompositionProvenance(
                "STEP3-SYNTHETIC",
                "1",
                f"synthetic:{code}",
                "STEP3-CONTRACT-TEST",
            ),
        ),
    )


def publication_service(engine):
    return ReviewedNutritionPublicationService(
        lambda: SqlAlchemyNutritionPublicationUnitOfWork(engine),
        clock=lambda: NOW,
    )


def db_dump(config):
    with sqlite3.connect(config.path) as db:
        return "\n".join(db.iterdump())


def assert_fk_clean(config):
    with sqlite3.connect(config.path) as db:
        assert db.execute("PRAGMA foreign_key_check").fetchall() == []


def test_fresh_complete_v2_bundle_has_no_v1_bootstrap_and_methodology_reads(database):
    config, engine = database
    request = bundle()
    result = publication_service(engine).publish(request)

    assert result.bundle_created is True
    assert result.ingredient_created is True
    assert result.nutrient_value_count == request.vector.value_count

    with sqlite3.connect(config.path) as db:
        seals = db.execute(
            """
            SELECT registry_version, value_count, value_sha256
            FROM nutrition_vector_seals
            WHERE profile_id = ?
            """,
            (result.profile_id.hex,),
        ).fetchall()
        assert seals == [
            (
                REGISTRY_V2,
                request.vector.value_count,
                request.vector.value_sha256,
            )
        ]
        assert db.execute(
            "SELECT is_current FROM food_nutrition_profiles WHERE id = ?",
            (result.profile_id.hex,),
        ).fetchone() == (0,)

    with SqlAlchemyNutritionReadScope(engine) as read:
        vector = read.nutrient_vectors.get(result.profile_id)
        assert vector.registry_version == REGISTRY_V2
        assert vector.amount("PROTEIN") == Decimal("8")
        assert all(v.provenance.source_nutrient_nbr is None for v in vector.values)

    methodology = NutritionMethodologyService(
        lambda: SqlAlchemyCompositionReadScope(engine)
    )
    interpreted = methodology.atomic_input(
        result.composition_version_id,
        mass_g=Decimal("200"),
        mass_state=MassState.RAW,
        nutrients=(NutrientKind.PROTEIN, NutrientKind.AVAILABLE_CARBOHYDRATE),
        policy=RussianNutritionPolicy.STRICT_V1,
    )
    values = {value.nutrient: value for value in interpreted.values}
    assert values[NutrientKind.PROTEIN].amount == Decimal("16.000000")
    assert (
        values[NutrientKind.AVAILABLE_CARBOHYDRATE].amount
        == Decimal("24.000000")
    )

    with SqlAlchemyCompositionReadScope(engine) as read:
        with pytest.raises(CompositionUnavailableError) as exc_info:
            CompositionCalculator(
                read.compositions, read.nutrient_vectors
            ).calculate(result.composition_version_id, nutrient_codes=("PROTEIN",))
    assert exc_info.value.issue_code == "NUTRIENT_DEFINITION_MISMATCH"
    assert_fk_clean(config)


def test_fresh_partial_v2_bundle_keeps_unknowns_without_numeric_zero(database):
    config, engine = database
    request = bundle(
        code="STEP3_PARTIAL_FOOD",
        name="Тестовый частичный продукт",
        partial=True,
        source_id="STEP3-PARTIAL",
    )
    result = publication_service(engine).publish(request)

    with SqlAlchemyNutritionReadScope(engine) as read:
        profile = read.nutrition_profiles.get_by_provenance(
            result.ingredient_id,
            request.profile.source_name,
            request.profile.source_id,
            request.profile.source_version,
        )
        vector = read.nutrient_vectors.get(result.profile_id)
        observations = read.nutrition_profiles.list_observations(result.profile_id)
    assert profile is not None
    assert profile.protein_g is None
    assert profile.carbohydrates_g is None
    assert profile.is_current is False
    assert vector.amount("PROTEIN") is None
    assert vector.amount("CARBOHYDRATE_AVAILABLE") is None
    states = {value.source_field: value.state for value in observations}
    assert states["protein_g"] is NutritionObservationState.MISSING
    assert states["carbohydrates_g"] is NutritionObservationState.METHOD_INCOMPATIBLE
    with sqlite3.connect(config.path) as db:
        assert db.execute(
            """
            SELECT protein_g, carbohydrates_g
            FROM food_nutrition_profiles
            WHERE id = ?
            """,
            (result.profile_id.hex,),
        ).fetchone() == (None, None)
    assert_fk_clean(config)


def test_exact_replay_is_zero_write_and_keeps_ids(database):
    config, engine = database
    request = bundle(
        code="STEP3_REPLAY_FOOD",
        name="Тестовый продукт повтора",
        source_id="STEP3-REPLAY",
    )
    first = publication_service(engine).publish(request)
    before = db_dump(config)
    second = publication_service(engine).publish(request)
    after = db_dump(config)

    assert second.bundle_created is False
    assert second.ingredient_created is False
    assert second.ingredient_id == first.ingredient_id
    assert second.profile_id == first.profile_id
    assert second.composition_version_id == first.composition_version_id
    assert after == before
    assert_fk_clean(config)


def test_existing_current_profile_is_never_cleared_by_step3(database):
    _, engine = database
    catalogue = create_food_catalogue_service(engine)
    existing = catalogue.add_trusted_ingredient(
        TrustedFoodIngredientSeed(
            canonical_code="STEP3_EXISTING_FOOD",
            canonical_name="Существующий тестовый продукт",
            category_code="test_foods",
            default_unit="g",
            density_g_per_ml=None,
            edible_fraction=None,
            allergens_reviewed=False,
            allergen_codes=(),
            storage_profile_code=None,
            aliases=(),
            nutrition=TrustedNutritionSeed(
                basis_grams=Decimal("100"),
                kcal=Decimal("100"),
                protein_g=Decimal("5"),
                fat_g=Decimal("2"),
                carbohydrates_g=Decimal("15"),
                fiber_g=Decimal("1"),
                source_name="LEGACY_SYNTHETIC",
                source_id="CURRENT-1",
                source_version="1",
                source_data_type="synthetic",
                verified_at=VERIFIED,
                estimated=None,
            ),
        )
    )
    with SqlAlchemyFoodCatalogueReadScope(engine) as read:
        current_before = read.nutrition_profiles.get_current(existing.id)
    assert current_before is not None

    request = bundle(
        code=existing.canonical_code,
        name=existing.canonical_name,
        action=PublicationIngredientAction.REUSE_EXISTING,
        source_id="STEP3-EXISTING",
        composition_version=1,
    )
    first = publication_service(engine).publish(request)
    second = publication_service(engine).publish(request)
    assert first.ingredient_id == existing.id
    assert second.bundle_created is False

    with SqlAlchemyFoodCatalogueReadScope(engine) as read:
        current_after = read.nutrition_profiles.get_current(existing.id)
    assert current_after == current_before
    assert current_after.id != first.profile_id


@pytest.mark.parametrize(
    "mutator",
    [
        lambda request: replace(
            request,
            profile=replace(request.profile, kcal=Decimal("121")),
        ),
        lambda request: replace(
            request,
            profile=replace(
                request.profile,
                observations=tuple(
                    replace(value, source_locator=value.source_locator + ":changed")
                    if value.source_field == "kcal"
                    else value
                    for value in request.profile.observations
                ),
            ),
        ),
    ],
    ids=["profile-value", "profile-observation"],
)
def test_same_profile_provenance_conflict_is_zero_write(database, mutator):
    config, engine = database
    request = bundle(
        code="STEP3_PROFILE_CONFLICT",
        name="Тестовый конфликт профиля",
        source_id="STEP3-CONFLICT",
    )
    publication_service(engine).publish(request)
    before = db_dump(config)

    with pytest.raises(NutritionPublicationConflictError):
        publication_service(engine).publish(mutator(request))

    assert db_dump(config) == before
    assert_fk_clean(config)


def test_changed_v2_value_provenance_conflicts_without_partial_write(database):
    config, engine = database
    request = bundle(
        code="STEP3_VECTOR_CONFLICT",
        name="Тестовый конфликт вектора",
        source_id="STEP3-VECTOR-CONFLICT",
    )
    publication_service(engine).publish(request)
    before = db_dump(config)

    changed_values = list(request.vector.values)
    first = changed_values[0]
    payload = json.loads(first.provenance_json)
    payload["observation"]["source_locator"] += ":changed"
    changed_values[0] = replace(
        first,
        provenance_json=json.dumps(
            payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ),
    )
    rows = [
        {
            "nutrient_code": value.nutrient_code,
            "amount": value.amount,
            "provenance_json": value.provenance_json,
        }
        for value in changed_values
    ]
    changed = replace(
        request,
        vector=replace(
            request.vector,
            values=tuple(changed_values),
            value_sha256=value_set_digest(rows),
        ),
    )

    with pytest.raises(NutritionPublicationConflictError):
        publication_service(engine).publish(changed)
    assert db_dump(config) == before
    assert_fk_clean(config)


def test_occupied_composition_version_with_different_truth_conflicts(database):
    config, engine = database
    request = bundle(
        code="STEP3_COMPOSITION_CONFLICT",
        name="Тестовый конфликт состава",
        source_id="STEP3-COMPOSITION-CONFLICT",
    )
    publication_service(engine).publish(request)
    before = db_dump(config)

    changed = replace(
        request,
        atomic_composition=replace(
            request.atomic_composition,
            provenance=CompositionProvenance(
                "STEP3-SYNTHETIC",
                "2",
                "synthetic:changed",
                "STEP3-CONTRACT-TEST",
            ),
        ),
    )
    with pytest.raises(NutritionPublicationConflictError):
        publication_service(engine).publish(changed)
    assert db_dump(config) == before
    assert_fk_clean(config)


def test_existing_profile_without_full_bundle_is_not_adopted(database):
    config, engine = database
    request = bundle(
        code="STEP3_PARTIAL_STATE",
        name="Тестовое частичное состояние",
        source_id="STEP3-PARTIAL-STATE",
    )
    service = publication_service(engine)
    with SqlAlchemyNutritionPublicationUnitOfWork(engine) as uow:
        ingredient, _ = service._resolve_ingredient(uow, request.ingredient, now=NOW)
        profile, observations = service._build_profile(
            request.profile,
            ingredient.id,
            profile_id=uuid4(),
            created_at=NOW,
            existing_observations=(),
            now=NOW,
        )
        uow.ingredients.add(ingredient)
        uow.nutrition_profiles.add_unsealed(profile, observations)
        uow.commit()

    before = db_dump(config)
    with pytest.raises(NutritionPublicationConflictError):
        service.publish(request)
    assert db_dump(config) == before
    assert_fk_clean(config)


def test_wrong_registry_and_noncanonical_evidence_fail_before_write(database):
    config, engine = database
    request = bundle(
        code="STEP3_BAD_EVIDENCE",
        name="Тестовое плохое доказательство",
        source_id="STEP3-BAD-EVIDENCE",
    )
    before = db_dump(config)

    wrong_registry = replace(
        request, vector=replace(request.vector, registry_version=REGISTRY_V1)
    )
    with pytest.raises(NutritionPublicationContractError):
        publication_service(engine).publish(wrong_registry)
    assert db_dump(config) == before

    first = request.vector.values[0]
    payload = json.loads(first.provenance_json)
    payload["observation"]["method_code"] = payload.pop("method_code")
    broken = replace(
        first,
        provenance_json=json.dumps(
            payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ),
    )
    values = (broken, *request.vector.values[1:])
    rows = [
        {
            "nutrient_code": value.nutrient_code,
            "amount": value.amount,
            "provenance_json": value.provenance_json,
        }
        for value in values
    ]
    nested_only = replace(
        request,
        vector=replace(
            request.vector,
            values=values,
            value_sha256=value_set_digest(rows),
        ),
    )
    with pytest.raises(NutritionPublicationContractError):
        publication_service(engine).publish(nested_only)
    assert db_dump(config) == before


def test_duplicate_v2_evidence_keys_fail_closed():
    profile = profile_spec()
    raw = evidence(
        profile,
        "PROTEIN",
        Decimal("8"),
        "g",
        ObservationMethod.ANALYTICAL,
    )
    duplicated = raw.replace(
        '"method_code":"analytical"',
        '"method_code":"analytical","method_code":"published_method_unspecified"',
    )
    from app.domain.food_ingredients import FoodNutritionProfile

    domain_profile = FoodNutritionProfile(
        id=uuid4(),
        food_ingredient_id=uuid4(),
        basis_grams=profile.basis_grams,
        kcal=profile.kcal,
        protein_g=profile.protein_g,
        fat_g=profile.fat_g,
        carbohydrates_g=profile.carbohydrates_g,
        fiber_g=profile.fiber_g,
        source_name=profile.source_name,
        source_id=profile.source_id,
        source_version=profile.source_version,
        source_data_type=profile.source_data_type,
        verified_at=profile.verified_at,
        estimated=profile.estimated,
        is_current=False,
        created_at=NOW,
    )
    with pytest.raises(NutrientValueEvidenceError, match="Повторное поле"):
        decode_v2_value_evidence(
            duplicated,
            profile=domain_profile,
            expected_registry_version=REGISTRY_V2,
            expected_nutrient_code="PROTEIN",
            expected_amount=Decimal("8"),
        )


@pytest.mark.parametrize(
    "stage",
    [
        "after_ingredient",
        "after_profile",
        "after_first_value",
        "after_seal",
        "after_composition",
    ],
)
def test_failure_injection_rolls_back_every_fresh_write_boundary(database, stage):
    config, engine = database
    request = bundle(
        code=f"STEP3_FAIL_{stage.upper()}",
        name=f"Тестовый откат {stage}",
        source_id=f"STEP3-{stage}",
    )
    before = db_dump(config)
    state = {"value_inserts": 0, "composition_inserted": False}

    def fail(connection, cursor, statement, parameters, context, executemany):
        del connection, cursor, parameters, context, executemany
        sql = statement.strip()
        if stage == "after_ingredient" and sql.startswith(
            "INSERT INTO food_nutrition_profiles"
        ):
            raise RuntimeError("injected after ingredient")
        if stage == "after_profile" and sql.startswith("INSERT INTO nutrient_values"):
            raise RuntimeError("injected after profile")
        if stage == "after_first_value" and sql.startswith(
            "INSERT INTO nutrient_values"
        ):
            state["value_inserts"] += 1
            if state["value_inserts"] == 2:
                raise RuntimeError("injected after first nutrient value")
        if sql.startswith("INSERT INTO food_composition_versions"):
            if stage == "after_seal":
                raise RuntimeError("injected after seal")
            state["composition_inserted"] = True
        if (
            stage == "after_composition"
            and state["composition_inserted"]
            and sql.startswith("SELECT")
        ):
            raise RuntimeError("injected after composition")

    event.listen(engine, "before_cursor_execute", fail)
    try:
        with pytest.raises(RuntimeError, match="injected"):
            publication_service(engine).publish(request)
    finally:
        event.remove(engine, "before_cursor_execute", fail)

    assert db_dump(config) == before
    assert_fk_clean(config)


def test_commit_failure_discards_transaction_without_partial_state(database):
    config, engine = database
    request = bundle(
        code="STEP3_COMMIT_FAILURE",
        name="Тестовый отказ commit",
        source_id="STEP3-COMMIT-FAIL",
    )
    before = db_dump(config)

    def fail_commit(connection):
        del connection
        raise RuntimeError("injected commit failure")

    event.listen(engine, "commit", fail_commit, once=True)
    with pytest.raises(RuntimeError, match="injected commit failure"):
        publication_service(engine).publish(request)

    assert db_dump(config) == before
    assert_fk_clean(config)


def test_generic_v1_seed_and_decoder_remain_unchanged(tmp_path):
    config = DatabaseConfig(path=tmp_path / "v1-regression.sqlite")
    seed_food_ingredients(config)
    engine = create_sqlite_engine(config)
    try:
        with SqlAlchemyNutritionReadScope(engine) as read:
            ingredient = read.ingredients.get_by_code("AGAVE_SYRUP")
            profile = read.nutrition_profiles.get_current(ingredient.id)
            vector = read.nutrient_vectors.get(profile.id)
        assert vector.registry_version == REGISTRY_V1
        assert vector.values
        assert all(
            value.provenance.source_nutrient_nbr is not None
            for value in vector.values
        )
        assert migrations.expected_migration_ids()[-1] == (
            "0035_versioned_nutrient_registry"
        )
    finally:
        engine.dispose()
