"""Pinned test-only publication manifest: exact projections, no DB reverse lookups."""

import json
from dataclasses import replace
from decimal import Decimal
from hashlib import sha1, sha256

import pytest
from app.services.food_recipes import TrustedRecipeVersionSeed
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
    derive_fixture_uuid,
)


def seed(*, steps=("Original approved step.",)):
    return TrustedRecipeVersionSeed(
        base_servings=Decimal(2),
        meal_type_code="DINNER",
        prep_time_minutes=5,
        cook_time_minutes=10,
        total_time_minutes=15,
        difficulty_code=None,
        batch_friendly=None,
        freezable=None,
        storage_days_fridge=None,
        storage_days_freezer=None,
        verification_status="SOURCE_VERIFIED",
        verified_at=None,
        source_name="fixture_source",
        source_recipe_id="fixture_item",
        source_url="https://example.test/recipe",
        source_version="fixture_v1",
        source_retrieved_at=None,
        source_document_sha256="a" * 64,
        source_original_servings=Decimal(2),
        rights_review_status="REVIEWED",
        rights_basis="Synthetic fixture test.",
        change_note="original source",
        ingredients=(),
        steps=tuple(steps),
        equipment_codes=(),
    )


def key_v1():
    return {
        "canonical_code": "SYNTHETIC",
        "source_record_key": {
            "canonical_code": "SYNTHETIC",
            "source_name": "fixture_source",
            "source_recipe_id": "fixture_item",
            "source_version": "fixture_v1",
            "source_document_sha256": "a" * 64,
        },
        "version_number": 1,
        "predecessor_version_key": None,
        "publication_kind": "ORIGINAL",
        "publication_process_sha256": process_steps_sha256(seed().steps),
        "correction_revision_sha256": None,
    }


def _entry(code, version, version_key, source_seed):
    return {
        "stage": "synthetic",
        "canonical_code": code,
        "version_number": version,
        "version_key": version_key,
        "seed_projection": json.loads(project_trusted_version_seed(source_seed)),
    }


def make_manifest(tmp_path, *, corrected=False):
    original = seed()
    v1 = key_v1()
    records = [_entry("SYNTHETIC", 1, v1, original)]
    allowed = [{"kind": "RECIPE_VERSION", "key": v1}]
    inventory = {"synthetic": ["SYNTHETIC@1"]}
    correction_file = tmp_path / "corrections.json"
    correction_sha = correction_blob = None
    if corrected:
        correction_data = {
            "recipes": [
                {
                    "canonical_code": "SYNTHETIC",
                    "old_steps": list(original.steps),
                    "new_steps": ["Corrected, reviewed step."],
                }
            ]
        }
        correction_file.write_bytes(json.dumps(correction_data).encode())
        raw = correction_file.read_bytes()
        correction_sha = sha256(raw).hexdigest()
        correction_blob = sha1(
            b"blob " + str(len(raw)).encode() + b"\0" + raw
        ).hexdigest()
        v2 = {
            **v1,
            "version_number": 2,
            "publication_kind": "REVIEWED_CORRECTION",
            "publication_process_sha256": process_steps_sha256(
                ("Corrected, reviewed step.",)
            ),
            "correction_revision_sha256": correction_sha,
            "predecessor_version_key": v1,
        }
        records.append(
            _entry(
                "SYNTHETIC",
                2,
                v2,
                replace(original, steps=("Corrected, reviewed step.",)),
            )
        )
        allowed.append({"kind": "RECIPE_VERSION", "key": v2})
        inventory["synthetic"].append("SYNTHETIC@2")
    allowed = [
        {"kind": row["kind"], "key": row["key"]}
        for row in (
            json.loads(value.decode("utf-8"))
            for value in sorted(_expected_recipe_allowlist(records))
        )
    ]
    payload = {
        "schema_version": SCHEMA_VERSION,
        "policy": POLICY,
        "namespace": NAMESPACE,
        "fixture_id": FIXTURE_ID,
        "source_commit": "1" * 40,
        "review_reference": "synthetic test-reviewed input (not production authority)",
        "approved_ids": allowed,
        "publications": records,
        "stages": inventory,
    }
    path = tmp_path / "manifest.json"
    path.write_bytes(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode())
    return (
        path,
        sha256(path.read_bytes()).hexdigest(),
        inventory,
        correction_file,
        correction_sha,
        correction_blob,
        payload,
    )


def load(bundle, *, corrected=False):
    path, rawsha, inventory, correction_file, correction_sha, correction_blob, _ = (
        bundle
    )
    return load_pinned_publication_manifest(
        path,
        expected_sha256=rawsha,
        expected_source_commit="1" * 40,
        expected_stage_membership=inventory,
        correction_path=correction_file if corrected else None,
        expected_correction_sha256=correction_sha,
        expected_correction_blob_sha1=correction_blob,
    )


def test_explicit_pinned_manifest_v1(tmp_path):
    bundle = make_manifest(tmp_path)
    provider = load(bundle)
    key = provider.recipe_version_key_for(
        canonical_code="SYNTHETIC",
        seed=seed(),
        version_number=1,
        predecessor_id=None,
    )
    assert key == key_v1()
    assert provider.id_for("RECIPE_VERSION", key) == derive_fixture_uuid(
        "RECIPE_VERSION", key
    )
    key["canonical_code"] = "TAMPERED"
    assert (
        provider.recipe_version_key_for(
            canonical_code="SYNTHETIC",
            seed=seed(),
            version_number=1,
            predecessor_id=None,
        )
        == key_v1()
    )


def test_real_predecessor_witness_and_corrected_steps(tmp_path):
    bundle = make_manifest(tmp_path, corrected=True)
    provider = load(bundle, corrected=True)
    prior = provider.id_for("RECIPE_VERSION", key_v1())
    corrected_seed = seed(steps=("Corrected, reviewed step.",))
    key = provider.recipe_version_key_for(
        canonical_code="SYNTHETIC",
        seed=corrected_seed,
        version_number=2,
        predecessor_id=prior,
    )
    assert key["predecessor_version_key"] == key_v1()
    with pytest.raises(FixtureIdentityError, match="predecessor"):
        provider.recipe_version_key_for(
            canonical_code="SYNTHETIC",
            seed=corrected_seed,
            version_number=2,
            predecessor_id=None,
        )
    with pytest.raises(FixtureIdentityError, match="frozen publication"):
        provider.recipe_version_key_for(
            canonical_code="SYNTHETIC",
            seed=seed(steps=("Unauthorized mutation.",)),
            version_number=2,
            predecessor_id=prior,
        )


def test_manifest_bytes_source_and_external_coverage_are_independent(tmp_path):
    bundle = make_manifest(tmp_path)
    path, rawsha, inventory, *_ = bundle
    with pytest.raises(FixtureIdentityError, match="source_commit"):
        load_pinned_publication_manifest(
            path,
            expected_sha256=rawsha,
            expected_source_commit="2" * 40,
            expected_stage_membership=inventory,
        )
    with pytest.raises(FixtureIdentityError, match="inventory"):
        load_pinned_publication_manifest(
            path,
            expected_sha256=rawsha,
            expected_source_commit="1" * 40,
            expected_stage_membership={"synthetic": ["OTHER@1"]},
        )
    path.write_bytes(path.read_bytes() + b" ")
    with pytest.raises(FixtureIdentityError, match="bytes"):
        load(bundle)


def test_duplicate_json_keys_and_extra_records_fail_closed(tmp_path):
    bundle = make_manifest(tmp_path)
    path, _, _, _, _, _, payload = bundle
    path.write_text('{"schema_version":"v1","schema_version":"v2"}')
    with pytest.raises(FixtureIdentityError, match="duplicate"):
        load_pinned_publication_manifest(
            path,
            expected_sha256=sha256(path.read_bytes()).hexdigest(),
            expected_source_commit="1" * 40,
            expected_stage_membership={"synthetic": ["SYNTHETIC@1"]},
        )
    payload["publications"].append(payload["publications"][0])
    path.write_text(json.dumps(payload))
    with pytest.raises(FixtureIdentityError, match="coverage|duplicate"):
        load_pinned_publication_manifest(
            path,
            expected_sha256=sha256(path.read_bytes()).hexdigest(),
            expected_source_commit="1" * 40,
            expected_stage_membership={"synthetic": ["SYNTHETIC@1"]},
        )


def test_correction_file_tamper_fails_before_provider(tmp_path):
    bundle = make_manifest(tmp_path, corrected=True)
    path, rawsha, inventory, correction, corrected_sha, blob, _ = bundle
    correction.write_bytes(correction.read_bytes() + b" ")
    with pytest.raises(FixtureIdentityError, match="correction artifact raw"):
        load_pinned_publication_manifest(
            path,
            expected_sha256=rawsha,
            expected_source_commit="1" * 40,
            expected_stage_membership=inventory,
            correction_path=correction,
            expected_correction_sha256=corrected_sha,
            expected_correction_blob_sha1=blob,
        )


def test_seed_field_unknown_or_missing_does_not_match(tmp_path):
    bundle = make_manifest(tmp_path)
    path, _, inventory, _, _, _, payload = bundle
    payload["publications"][0]["seed_projection"].pop("source_version")
    path.write_bytes(json.dumps(payload).encode())
    with pytest.raises(FixtureIdentityError, match="trusted-seed fields"):
        load_pinned_publication_manifest(
            path,
            expected_sha256=sha256(path.read_bytes()).hexdigest(),
            expected_source_commit="1" * 40,
            expected_stage_membership=inventory,
        )


def test_loaded_provider_invalidates_late_manifest_mutation(tmp_path):
    bundle = make_manifest(tmp_path)
    provider = load(bundle)
    path = bundle[0]
    path.write_bytes(path.read_bytes() + b" ")
    with pytest.raises(FixtureIdentityError, match="changed"):
        provider.recipe_version_key_for(
            canonical_code="SYNTHETIC",
            seed=seed(),
            version_number=1,
            predecessor_id=None,
        )


def test_publication_provider_requires_external_loader(tmp_path):
    from app.services.pr10_ff_manifest_loader import PublicationManifestIds

    bundle = make_manifest(tmp_path)
    _, _, _, _, _, _, payload = bundle
    with pytest.raises(FixtureIdentityError, match="requires pinned"):
        PublicationManifestIds(
            approved=[("RECIPE_VERSION", key_v1())],
            records=payload["publications"],
        )


@pytest.mark.parametrize("mutation", ["extra_version", "missing_step", "extra_recipe"])
def test_publication_allowlist_is_closed_and_rejects_unreachable_keys(
    tmp_path, mutation
):
    bundle = make_manifest(tmp_path)
    path, _, stages, _, _, _, payload = bundle
    if mutation == "extra_version":
        changed = dict(key_v1())
        changed["source_record_key"] = {
            **changed["source_record_key"],
            "source_recipe_id": "unapproved-extra",
        }
        payload["approved_ids"].append({"kind": "RECIPE_VERSION", "key": changed})
    elif mutation == "missing_step":
        payload["approved_ids"] = [
            row for row in payload["approved_ids"] if row["kind"] != "RECIPE_STEP"
        ]
    else:
        payload["approved_ids"].append(
            {"kind": "RECIPE", "key": {"canonical_code": "NOT_IN_PUBLISHED_CORPUS"}}
        )
    path.write_text(json.dumps(payload, ensure_ascii=False))
    with pytest.raises(FixtureIdentityError, match="missing/extra/unreachable"):
        load_pinned_publication_manifest(
            path,
            expected_sha256=sha256(path.read_bytes()).hexdigest(),
            expected_source_commit="1" * 40,
            expected_stage_membership=stages,
        )
