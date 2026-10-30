"""QA-only full trusted seed-chain integration; NOT a Planner fixture approval.

Input projections are read from pinned trusted seed source loaders BEFORE any
database writes. The temporary manifest digest is a self-pinned test witness,
not the separately owner-approved current Planner input fixture.
"""

import hashlib
import json
from uuid import uuid4

import pytest

from app.db.config import DatabaseConfig
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
from app.persistence.sqlalchemy_core.food_recipe_repositories import (
    SqlAlchemyRecipeVersionRepository,
)
from app.persistence.sqlalchemy_core.food_recipe_composition import (
    create_food_recipe_catalogue_service,
)
from app.seed import (
    dc4_a3_russian_step_corrections as dc4,
    r1f_prepared_output as r1f,
    r1h_school2022_main as r1h,
    r2_breakfast_capacity as r2,
    r2b_fish_main_diversity as r2b,
    r2c_breakfast_grain_diversity as r2c,
    r2e_cottage_casserole as r2e,
    r2f_cheese_sandwich as r2f,
    r3a_school2022_main_batch as r3a,
    r3b_school2022_breakfast_batch as r3b,
    r3c_school2022_main_batch as r3c,
    r3d_final_dc3_batch as r3d,
)
from app.services.pr10_ff_manifest_loader import (
    SCHEMA_VERSION,
    _expected_recipe_allowlist,
    load_pinned_publication_manifest,
    process_steps_sha256,
    project_trusted_version_seed,
)
from app.services.pr10_ff_typed_ids import (
    FIXTURE_ID,
    NAMESPACE,
    POLICY,
    FixtureIdentityError,
)


def _trusted_source_inventory():
    """Extract real reviewed source seeds, no Recipe DB, UUID or Planner result."""
    stages = [
        ("r1f", r1f._recipe_seeds(r1f._load_evidence())),
        ("r1h", r1h._recipe_seeds_and_specs(r1h._load_contract()[0])[0]),
        ("r2", r2._recipe_seeds_and_specs(r2._load_contract()[2])[0]),
        ("r2b", r2b._recipe_seeds_and_specs(r2b._load_contract()[2])[0]),
        ("r2c", r2c._recipe_seeds_and_specs(r2c._load_contract()[2])[0]),
        ("r2e", (r2e._recipe_seed_and_spec(r2e._load_contract()[-1])[0],)),
        ("r2f", (r2f._recipe_seed_and_spec(r2f._load_contract()[-1])[0],)),
        ("r3a", r3a._recipe_seeds_and_specs(r3a._load_contract()[4])[0]),
        ("r3b", r3b._recipe_seeds_and_specs(r3b._load_contract()[4])[0]),
        ("r3c", r3c._recipe_seeds_and_specs(r3c._load_contract()[0])[0]),
        ("r3d", r3d._recipe_seeds_and_specs(
            r3d._load_contract()[0], r3d._load_contract()[2]
        )[0]),
    ]
    return stages


def _version_key(recipe, *, number=1, predecessor=None, correction_sha=None):
    v = recipe.version
    return {
        "canonical_code": recipe.canonical_code,
        "source_record_key": {
            "canonical_code": recipe.canonical_code,
            "source_name": v.source_name,
            "source_recipe_id": v.source_recipe_id,
            "source_version": v.source_version,
            "source_document_sha256": v.source_document_sha256,
        },
        "version_number": number,
        "predecessor_version_key": predecessor,
        "publication_kind": "ORIGINAL" if number == 1 else "REVIEWED_CORRECTION",
        "publication_process_sha256": process_steps_sha256(v.steps),
        "correction_revision_sha256": correction_sha,
    }


def _qa_provider(tmp_path):
    from dataclasses import replace

    stages = _trusted_source_inventory()
    expected_codes = [item.canonical_code for _, recipes in stages for item in recipes]
    assert len(stages) == 11  # DC4-A3 is the separate twelfth correction stage.
    assert len(expected_codes) == len(set(expected_codes)) == 51
    originals = {recipe.canonical_code: recipe for _, recipes in stages for recipe in recipes}

    artifact = dc4._load_corrections()  # source Git blob pin verified by real loader
    corrections = {row["canonical_code"]: row for row in artifact["recipes"]}
    assert len(corrections) == 7
    correction_sha = "157f2ce76cc86baae2b288ce80da069154bc6d44ca1620b2b9f0c521b92e7759"
    assert hashlib.sha256(dc4.CORRECTIONS_PATH.read_bytes()).hexdigest() == correction_sha
    records = []
    membership = {}
    for stage, seeds in stages:
        membership[stage] = []
        for recipe in seeds:
            version_key = _version_key(recipe)
            records.append({
                "stage": stage,
                "canonical_code": recipe.canonical_code,
                "version_number": 1,
                "version_key": version_key,
                "seed_projection": json.loads(project_trusted_version_seed(recipe.version)),
            })
            membership[stage].append(f"{recipe.canonical_code}@1")
    membership["dc4_a3"] = []
    for code in dc4.CORRECTION_CODES:
        original = originals[code]
        corrected = replace(
            original,
            version=replace(
                original.version,
                steps=tuple(corrections[code]["new_steps"]),
                change_note=artifact["change_note"],
            ),
        )
        records.append({
            "stage": "dc4_a3",
            "canonical_code": code,
            "version_number": 2,
            "version_key": _version_key(
                corrected, number=2, predecessor=_version_key(original),
                correction_sha=correction_sha,
            ),
            "seed_projection": json.loads(project_trusted_version_seed(corrected.version)),
        })
        membership["dc4_a3"].append(f"{code}@2")
    assert len(records) == 58
    allowed = [
        {"kind": obj["kind"], "key": obj["key"]}
        for obj in (
            json.loads(value) for value in sorted(_expected_recipe_allowlist(records))
        )
    ]
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "policy": POLICY,
        "namespace": NAMESPACE,
        "fixture_id": FIXTURE_ID,
        "source_commit": "dc4f2ff41865ce7721dac90b8bc29e4cdce6a0b1",
        "review_reference": "QA-only source-loader conformance, not accepted fixture",
        "approved_ids": allowed,
        "publications": records,
        "stages": membership,
    }
    path = tmp_path / "qa-only-pre-run-manifest.json"
    path.write_text(json.dumps(manifest, ensure_ascii=False))
    provider = load_pinned_publication_manifest(
        path,
        expected_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        expected_source_commit=manifest["source_commit"],
        expected_stage_membership=membership,
        correction_path=dc4.CORRECTIONS_PATH,
        expected_correction_sha256=correction_sha,
        expected_correction_blob_sha1=dc4.CORRECTIONS_GIT_BLOB_SHA,
    )
    return provider, originals


def test_actual_trusted_chain_fresh_and_repeat_uses_pinned_typed_ids(tmp_path, monkeypatch):
    """Run real R1-F -> R3-A/B -> R3-C/D -> DC4-A3 publication on SQLite twice."""
    provider, originals = _qa_provider(tmp_path)
    config = DatabaseConfig(path=tmp_path / "real-seed-path.sqlite")
    first = dc4.seed_dc4_a3_russian_step_corrections(config, id_provider=provider)
    assert len(first.recipes) == 7
    engine = create_sqlite_engine(config)
    try:
        catalogue = create_food_recipe_catalogue_service(engine, id_provider=provider)
        actual = catalogue.list_all()
        assert len(actual) == len(originals) == 51
        for recipe in actual:
            versions = catalogue.list_versions(recipe.id)
            assert len(versions) == (2 if recipe.canonical_code in dc4.CORRECTION_CODES else 1)
            for version in versions:
                detail = catalogue.get_version_detail(version.id)
                assert version.version_number in (1, 2)
                assert detail.recipe.id == recipe.id
    finally:
        engine.dispose()
    second = dc4.seed_dc4_a3_russian_step_corrections(config, id_provider=provider)
    assert len(second.recipes) == 7
    assert all(row.disposition == "EXACT_REPLAY" for row in second.recipes)
    assert len(provider.ledger) > 58
    # A persisted v2 Step can preserve its Russian instruction while its UUID
    # is swapped. This is NOT an accepted DC4-A3 exact replay.
    original_query = SqlAlchemyRecipeVersionRepository.list_by_provenance

    def fake_corrected_readback(repository, *args, **kwargs):
        rows = original_query(repository, *args, **kwargs)
        return [
            replace(
                row, steps=(replace(row.steps[0], id=uuid4()), *row.steps[1:])
            ) if row.version.version_number == 2 else row
            for row in rows
        ]

    # Check rejection of a content-identical foreign v2 Step ID without
    # bypassing the database's immutable Step triggers.
    monkeypatch.setattr(
        SqlAlchemyRecipeVersionRepository, "list_by_provenance",
        fake_corrected_readback,
    )
    with pytest.raises(FixtureIdentityError, match="UUID/position drift"):
        dc4.seed_dc4_a3_russian_step_corrections(config, id_provider=provider)
