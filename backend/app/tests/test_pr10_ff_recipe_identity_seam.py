"""Opt-in Recipe persistence seam on disposable SQLite, not PR10 real week proof."""

import hashlib
import json
from dataclasses import replace
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from app.db.config import DatabaseConfig
from app.domain.food_ingredients import normalize_unicode_search_key
from app.domain.food_recipes import Recipe
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
from app.persistence.sqlalchemy_core.food_recipe_composition import (
    create_food_recipe_catalogue_service,
)
from app.persistence.sqlalchemy_core.food_recipe_uow import (
    SqlAlchemyRecipeCatalogueUnitOfWork,
)
from app.persistence.sqlalchemy_core.food_recipe_repositories import (
    SqlAlchemyRecipeVersionRepository,
)
from app.seed.food_ingredients import seed_food_ingredients
from app.seed.food_recipes import load_seed_entries
from app.services.pr10_ff_manifest_loader import (
    SCHEMA_VERSION,
    load_pinned_publication_manifest,
    process_steps_sha256,
    project_trusted_version_seed,
)
from app.services.pr10_ff_typed_ids import (
    FIXTURE_ID,
    NAMESPACE,
    POLICY,
    FixtureIdentityError,
    derive_fixture_uuid,
)


def _original():
    return next(
        x
        for x in load_seed_entries()
        if x.canonical_code == "CACFP6_CORN_EDAMAME_BLEND"
    )


def _version_key(code, version, *, number=1, predecessor=None, correction_sha=None):
    return {
        "canonical_code": code,
        "source_record_key": {
            "canonical_code": code,
            "source_name": version.source_name,
            "source_recipe_id": version.source_recipe_id,
            "source_version": version.source_version,
            "source_document_sha256": version.source_document_sha256,
        },
        "version_number": number,
        "predecessor_version_key": predecessor,
        "publication_kind": "ORIGINAL" if number == 1 else "REVIEWED_CORRECTION",
        "publication_process_sha256": process_steps_sha256(version.steps),
        "correction_revision_sha256": correction_sha,
    }


def _ids_for_version(version_key, version):
    approved = [{"kind": "RECIPE_VERSION", "key": version_key}]
    for pos, row in enumerate(version.ingredients, start=1):
        sha = lambda s: None if s is None else hashlib.sha256(s.encode()).hexdigest()
        approved.append(
            {
                "kind": "RECIPE_INGREDIENT",
                "key": {
                    "recipe_version_key": version_key,
                    "position": pos,
                    "food_ingredient_code": row.food_ingredient_code,
                    "quantity": (
                        "0"
                        if row.quantity.is_zero()
                        else format(row.quantity.normalize(), "f")
                    ),
                    "unit": str(row.unit),
                    "source_amount_text_sha256": sha(row.source_amount_text),
                    "normalization_note_sha256": sha(row.normalization_note),
                    "prep_note_sha256": sha(row.prep_note),
                    "optional": row.optional,
                },
            }
        )
    for pos, instruction in enumerate(version.steps, start=1):
        approved.append(
            {
                "kind": "RECIPE_STEP",
                "key": {
                    "recipe_version_key": version_key,
                    "position": pos,
                    "instruction_sha256": hashlib.sha256(
                        instruction.encode()
                    ).hexdigest(),
                    "stage_code": None,
                },
            }
        )
    return approved


def _provider(tmp_path, original, *, corrected=None):
    v1 = _version_key(original.canonical_code, original.version)
    versions = [(1, v1, original.version)]
    correction_file = None
    correction_sha = None
    correction_blob = None
    if corrected is not None:
        correction_file = tmp_path / "corrections.json"
        correction_file.write_text(
            json.dumps(
                {
                    "recipes": [
                        {
                            "canonical_code": original.canonical_code,
                            "old_steps": list(original.version.steps),
                            "new_steps": list(corrected.steps),
                        }
                    ]
                }
            )
        )
        raw = correction_file.read_bytes()
        correction_sha = hashlib.sha256(raw).hexdigest()
        correction_blob = hashlib.sha1(
            b"blob " + str(len(raw)).encode() + b"\0" + raw
        ).hexdigest()
        v2 = _version_key(
            original.canonical_code,
            corrected,
            number=2,
            predecessor=v1,
            correction_sha=correction_sha,
        )
        versions.append((2, v2, corrected))
    approved = [{"kind": "RECIPE", "key": {"canonical_code": original.canonical_code}}]
    records = []
    members = []
    for number, key, version in versions:
        approved.extend(_ids_for_version(key, version))
        records.append(
            {
                "stage": "synthetic_test",
                "canonical_code": original.canonical_code,
                "version_number": number,
                "version_key": key,
                "seed_projection": json.loads(project_trusted_version_seed(version)),
            }
        )
        members.append(f"{original.canonical_code}@{number}")
    payload = {
        "schema_version": SCHEMA_VERSION,
        "policy": POLICY,
        "namespace": NAMESPACE,
        "fixture_id": FIXTURE_ID,
        "source_commit": "1" * 40,
        "review_reference": "unit-test-only evidence (not accepted real Planner input)",
        "approved_ids": approved,
        "publications": records,
        "stages": {"synthetic_test": members},
    }
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(payload, ensure_ascii=False))
    provider = load_pinned_publication_manifest(
        path,
        expected_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        expected_source_commit="1" * 40,
        expected_stage_membership={"synthetic_test": members},
        correction_path=correction_file,
        expected_correction_sha256=correction_sha,
        expected_correction_blob_sha1=correction_blob,
    )
    return provider, v1


def test_real_sqlite_recipe_ids_are_typed_and_providerless_default_is_random(tmp_path):
    original = _original()
    provider, v1 = _provider(tmp_path, original)
    config = DatabaseConfig(path=tmp_path / "typed.sqlite")
    seed_food_ingredients(config)
    engine = create_sqlite_engine(config)
    try:
        service = create_food_recipe_catalogue_service(engine, id_provider=provider)
        detail = service.create_trusted(original)
        assert detail.version.id == derive_fixture_uuid("RECIPE_VERSION", v1)
        assert detail.recipe.id == derive_fixture_uuid(
            "RECIPE", {"canonical_code": original.canonical_code}
        )
        assert len(provider.ledger) == 2 + len(original.version.ingredients) + len(
            original.version.steps
        )
        assert service.get_version_detail(detail.version.id).steps == detail.steps
    finally:
        engine.dispose()

    other = DatabaseConfig(path=tmp_path / "default.sqlite")
    seed_food_ingredients(other)
    engine = create_sqlite_engine(other)
    try:
        normal = create_food_recipe_catalogue_service(engine)
        detail = normal.create_trusted(original)
        assert detail.version.id.version == 4
        assert detail.version.id != derive_fixture_uuid("RECIPE_VERSION", v1)
        assert detail.recipe.id != derive_fixture_uuid(
            "RECIPE", {"canonical_code": original.canonical_code}
        )
    finally:
        engine.dispose()


def test_real_sqlite_v2_lineage_and_wrong_manifest_rollback(tmp_path):
    original = _original()
    changed = replace(
        original.version,
        change_note="Reviewed synthetic correction for test only",
        steps=(*original.version.steps[:-1], "Updated reviewed synthetic step."),
    )
    provider, _ = _provider(tmp_path, original, corrected=changed)
    config = DatabaseConfig(path=tmp_path / "lineage.sqlite")
    seed_food_ingredients(config)
    engine = create_sqlite_engine(config)
    try:
        service = create_food_recipe_catalogue_service(engine, id_provider=provider)
        first = service.create_trusted(original)
        second = service.append_trusted_version(first.recipe.id, changed)
        assert second.version.version_number == 2
        assert second.version.created_from_version_id == first.version.id
        assert second.version.id == derive_fixture_uuid(
            "RECIPE_VERSION",
            provider.recipe_version_key_for(
                canonical_code=original.canonical_code,
                seed=changed,
                version_number=2,
                predecessor_id=first.version.id,
            ),
        )
        unexpected = replace(changed, steps=("Unreviewed!",))
        with pytest.raises(FixtureIdentityError):
            service.append_trusted_version(first.recipe.id, unexpected)
        assert len(service.list_versions(first.recipe.id)) == 2
    finally:
        engine.dispose()


def test_conflicting_explicit_id_factory_is_rejected(tmp_path):
    original = _original()
    provider, _ = _provider(tmp_path, original)
    engine = create_sqlite_engine(DatabaseConfig(path=tmp_path / "test.sqlite"))
    try:
        with pytest.raises(FixtureIdentityError, match="conflicts"):
            from app.services.food_recipes import FoodRecipeCatalogueService

            FoodRecipeCatalogueService(
                lambda: None,
                lambda: None,
                id_factory=lambda: uuid4(),
                id_provider=provider,
            )
    finally:
        engine.dispose()


def test_exact_replay_rejects_persisted_foreign_step_uuid(tmp_path, monkeypatch):
    """Identical Step text with a different persisted PK is NOT fixture replay."""
    original = _original()
    provider, _ = _provider(tmp_path, original)
    config = DatabaseConfig(path=tmp_path / "foreign-step-uuid.sqlite")
    seed_food_ingredients(config)
    engine = create_sqlite_engine(config)
    try:
        catalogue = create_food_recipe_catalogue_service(engine, id_provider=provider)
        detail = catalogue.create_trusted(original)
        old_query = SqlAlchemyRecipeVersionRepository.list_by_provenance

        def fake_readback(repository, *args, **kwargs):
            results = old_query(repository, *args, **kwargs)
            return [
                replace(
                    row,
                    steps=(replace(row.steps[0], id=uuid4()), *row.steps[1:]),
                )
                for row in results
            ]

        # The immutable SQLite schema rightly rejects direct Step PK updates.
        # Inject an adversarial readback instead; the real DB remains untouched.
        monkeypatch.setattr(
            SqlAlchemyRecipeVersionRepository, "list_by_provenance", fake_readback
        )
        with pytest.raises(FixtureIdentityError, match="UUID/position drift"):
            catalogue.preflight_trusted_seed(original)
        with pytest.raises(FixtureIdentityError, match="UUID/position drift"):
            catalogue.reconcile_seed([original])
        assert len(catalogue.list_versions(detail.recipe.id)) == 1
    finally:
        engine.dispose()


def test_full_persisted_predecessor_projection_rejects_metadata_drift(
    tmp_path, monkeypatch
):
    """A source-identical v1 with different metadata cannot authorize v2 append."""
    original = _original()
    corrected = replace(
        original.version,
        change_note="Reviewed test-only step correction",
        steps=(*original.version.steps[:-1], "Corrected trusted Step text."),
    )
    provider, _ = _provider(tmp_path, original, corrected=corrected)
    config = DatabaseConfig(path=tmp_path / "tampered-predecessor.sqlite")
    seed_food_ingredients(config)
    engine = create_sqlite_engine(config)
    try:
        catalogue = create_food_recipe_catalogue_service(engine, id_provider=provider)
        detail = catalogue.create_trusted(original)
        original_detail = SqlAlchemyRecipeVersionRepository.get_detail

        def fake_predecessor(repository, version_id):
            value = original_detail(repository, version_id)
            if value is None or value.version.version_number != 1:
                return value
            return replace(
                value,
                version=replace(
                    value.version, source_output_text="Unapproved metadata mutation"
                ),
            )

        monkeypatch.setattr(
            SqlAlchemyRecipeVersionRepository, "get_detail", fake_predecessor
        )
        with pytest.raises(FixtureIdentityError, match="frozen publication|projection"):
            catalogue.append_trusted_version(detail.recipe.id, corrected)
        assert len(catalogue.list_versions(detail.recipe.id)) == 1
    finally:
        engine.dispose()


def test_mixed_provider_partial_recipe_rejects_all_fixture_write_paths(tmp_path):
    """A name/code-matching Recipe with a random UUID cannot gain typed Versions."""
    original = _original()
    provider, _ = _provider(tmp_path, original)
    config = DatabaseConfig(path=tmp_path / "mixed-provider-partial.sqlite")
    seed_food_ingredients(config)
    engine = create_sqlite_engine(config)
    try:
        expected = derive_fixture_uuid(
            "RECIPE", {"canonical_code": original.canonical_code}
        )
        random_id = uuid4()
        assert random_id != expected
        now = datetime(2026, 10, 30, tzinfo=timezone.utc)
        with SqlAlchemyRecipeCatalogueUnitOfWork(engine) as scope:
            scope.recipes.add(
                Recipe(
                    id=random_id,
                    canonical_code=original.canonical_code,
                    canonical_name=original.canonical_name,
                    canonical_name_key=normalize_unicode_search_key(
                        original.canonical_name, field="canonical_name"
                    ),
                    is_active=original.initial_is_active,
                    created_at=now,
                    updated_at=now,
                )
            )
            scope.commit()

        fixture_catalogue = create_food_recipe_catalogue_service(
            engine, id_provider=provider
        )
        with pytest.raises(FixtureIdentityError, match="persisted Recipe UUID"):
            fixture_catalogue.reconcile_seed([original])
        with pytest.raises(FixtureIdentityError, match="persisted Recipe UUID"):
            fixture_catalogue.preflight_trusted_seed(original)
        with pytest.raises(FixtureIdentityError, match="persisted Recipe UUID"):
            fixture_catalogue.append_trusted_version(random_id, original.version)
        with SqlAlchemyRecipeCatalogueUnitOfWork(engine) as scope:
            with pytest.raises(FixtureIdentityError, match="persisted Recipe UUID"):
                fixture_catalogue.reconcile_seed_in_scope(scope, [original])
            with pytest.raises(FixtureIdentityError, match="persisted Recipe UUID"):
                fixture_catalogue.append_trusted_version_in_scope(
                    scope, random_id, original.version
                )

        assert fixture_catalogue.get_by_code(original.canonical_code).id == random_id
        assert fixture_catalogue.list_versions(random_id) == []
        assert len(provider.ledger) == 1  # Only the rejected Recipe key was consulted.
        # Ordinary providerless append remains an independent, unchanged operation.
        ordinary_catalogue = create_food_recipe_catalogue_service(engine)
        created = ordinary_catalogue.append_trusted_version(
            random_id, original.version
        )
        assert created.version.version_number == 1
        assert created.recipe.id == random_id
    finally:
        engine.dispose()
