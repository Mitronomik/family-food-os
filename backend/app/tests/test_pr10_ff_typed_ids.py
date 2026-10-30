"""Conformance and fail-closed tests; NOT the forward Planner fixture proof."""

import json
import subprocess
import sys

import pytest
from app.services.pr10_ff_typed_ids import (
    FixtureIdentityError,
    ManifestPinnedFixtureIds,
    canonical_envelope,
    derive_fixture_uuid,
)

RECIPE = {"canonical_code": "SCHOOL2022_54_1R_COD_CUTLET"}
MEMBER = {
    "household_key": "pr10-ff-3m-v1",
    "ordinal": 1,
    "profile_sha256": "0123456789abcdef" * 4,
}


def _v1():
    return {
        "canonical_code": "REC1",
        "source_record_key": {
            "canonical_code": "REC1", "source_name": "Reviewed source",
            "source_recipe_id": "original-1", "source_version": "v1",
            "source_document_sha256": "a" * 64,
        },
        "version_number": 1, "predecessor_version_key": None,
        "publication_kind": "ORIGINAL",
        "publication_process_sha256": "b" * 64,
        "correction_revision_sha256": None,
    }


def _v2():
    return {
        **_v1(), "version_number": 2,
        "predecessor_version_key": _v1(),
        "publication_kind": "REVIEWED_CORRECTION",
        "publication_process_sha256": "c" * 64,
        "correction_revision_sha256": "d" * 64,
    }


def test_two_owner_approved_algorithm_vectors():
    assert str(derive_fixture_uuid("RECIPE", RECIPE)) == "82a8de65-1a14-49a3-bb9b-44a30d54675f"
    assert str(derive_fixture_uuid("HOUSEHOLD_MEMBER", MEMBER)) == (
        "a6f0adfa-af9b-4f69-a9dc-cc4220b1c819"
    )
    for kind, key in (("RECIPE", RECIPE), ("HOUSEHOLD_MEMBER", MEMBER)):
        assert derive_fixture_uuid(kind, key).version == 4


def test_independent_python_process_is_stable():
    code = (
        "from app.services.pr10_ff_typed_ids import derive_fixture_uuid; "
        "print(derive_fixture_uuid('RECIPE', "
        "{'canonical_code':'SCHOOL2022_54_1R_COD_CUTLET'}))"
    )
    first = subprocess.check_output([sys.executable, "-c", code], text=True).strip()
    second = subprocess.check_output([sys.executable, "-c", code], text=True).strip()
    assert first == second == "82a8de65-1a14-49a3-bb9b-44a30d54675f"


def test_strict_allowlist_replay_and_ledger():
    manifest = [("RECIPE", RECIPE), ("HOUSEHOLD_MEMBER", MEMBER)]
    provider = ManifestPinnedFixtureIds(manifest)
    one = provider.id_for("RECIPE", RECIPE)
    assert provider.id_for("RECIPE", dict(RECIPE)) == one
    assert len(provider.ledger) == 1
    assert provider.id_for("HOUSEHOLD_MEMBER", MEMBER) != one
    assert len(provider.ledger) == 2
    with pytest.raises(FixtureIdentityError, match="absent"):
        provider.id_for("RECIPE", {"canonical_code": "UNKNOWN"})
    with pytest.raises(FixtureIdentityError, match="duplicate"):
        ManifestPinnedFixtureIds(manifest * 2)


def test_all_six_closed_key_shapes():
    v = _v2()
    cases = [
        ("RECIPE", RECIPE), ("HOUSEHOLD", {"household_key": "demo"}),
        ("HOUSEHOLD_MEMBER", MEMBER), ("RECIPE_VERSION", v),
        ("RECIPE_STEP", {
            "recipe_version_key": v, "position": 1,
            "instruction_sha256": "e" * 64, "stage_code": None,
        }),
        ("RECIPE_INGREDIENT", {
            "recipe_version_key": v, "position": 1, "food_ingredient_code": "EGG",
            "quantity": "100", "unit": "g", "source_amount_text_sha256": "f" * 64,
            "normalization_note_sha256": None, "prep_note_sha256": None,
            "optional": False,
        }),
    ]
    for kind, key in cases:
        data = canonical_envelope(kind, key)
        assert json.loads(data)["key"] == key
        assert derive_fixture_uuid(kind, key).version == 4


@pytest.mark.parametrize("kind,key", [
    ("RECIPE", {"canonical_code": "  ", "extra": 1}),
    ("RECIPE", {"canonical_code": "e\u0301"}),
    ("HOUSEHOLD_MEMBER", {**MEMBER, "ordinal": True}),
    ("HOUSEHOLD_MEMBER", {**MEMBER, "profile_sha256": "ABC"}),
    ("RECIPE_VERSION", {**_v2(), "correction_revision_sha256": None}),
    ("RECIPE_VERSION", {**_v2(), "predecessor_version_key": None}),
    ("RECIPE_VERSION", {**_v1(), "publication_kind": "REVIEWED_CORRECTION"}),
    ("RECIPE_VERSION", {
        **_v2(),
        "source_record_key": {**_v1()["source_record_key"], "canonical_code": "OTHER"},
    }),
    ("RECIPE_INGREDIENT", {
        "recipe_version_key": _v1(), "position": 1, "food_ingredient_code": "EGG",
        "quantity": "1.000", "unit": "g", "source_amount_text_sha256": "e" * 64,
        "normalization_note_sha256": None, "prep_note_sha256": None, "optional": False,
    }),
])
def test_invalid_keys_fail_closed(kind, key):
    with pytest.raises(FixtureIdentityError):
        derive_fixture_uuid(kind, key)


def test_collision_is_rejected_across_different_keys(monkeypatch):
    from app.services import pr10_ff_typed_ids as ids

    other = {"canonical_code": "ANOTHER_RECIPE"}
    provider = ManifestPinnedFixtureIds([("RECIPE", RECIPE), ("RECIPE", other)])
    original = ids.derive_fixture_uuid
    first = provider.id_for("RECIPE", RECIPE)
    monkeypatch.setattr(ids, "derive_fixture_uuid", lambda kind, key: first)
    with pytest.raises(FixtureIdentityError, match="collision"):
        provider.id_for("RECIPE", other)
    monkeypatch.setattr(ids, "derive_fixture_uuid", original)
    assert len(provider.ledger) == 1


def test_approved_manifest_cannot_be_changed_by_mutating_caller_data():
    key = {"canonical_code": "ORIGINAL"}
    provider = ManifestPinnedFixtureIds([("RECIPE", key)])
    key["canonical_code"] = "MUTATED"
    with pytest.raises(FixtureIdentityError, match="absent"):
        provider.id_for("RECIPE", key)
    assert len(provider.ledger) == 0
    assert provider.id_for("RECIPE", {"canonical_code": "ORIGINAL"}).version == 4
