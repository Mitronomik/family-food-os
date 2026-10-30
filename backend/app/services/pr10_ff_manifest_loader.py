"""Explicitly pinned, immutable test-only Recipe publication manifest loader.

The external source pin, stage inventory, and correction evidence are supplied
by a reviewer *before* any seed run. This is not an ingestion/pub authority.
"""

from __future__ import annotations

import hashlib
import json
import unicodedata
from dataclasses import fields, is_dataclass
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Sequence
from uuid import UUID

from app.services.pr10_ff_typed_ids import (
    FIXTURE_ID,
    NAMESPACE,
    POLICY,
    FixtureIdentityError,
    FixtureTypedIdProvider,
    ManifestPinnedFixtureIds,
    canonical_envelope,
    derive_fixture_uuid,
)

SCHEMA_VERSION = "PR10_FF_PUBLICATION_MANIFEST_V1"


def _reject_duplicate_pairs(items: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in items:
        if key in result:
            raise FixtureIdentityError("duplicate manifest JSON key")
        result[key] = value
    return result


def _reject_float(value: str) -> None:
    raise FixtureIdentityError("manifest JSON floating-point number is prohibited")


def _record_bytes(value: object) -> bytes:
    try:
        return json.dumps(
            value, ensure_ascii=False, sort_keys=True,
            separators=(",", ":"), allow_nan=False,
        ).encode("utf-8")
    except (ValueError, TypeError, UnicodeError) as exc:
        raise FixtureIdentityError("invalid manifest JSON data") from exc


def _normalize(value: object) -> object:
    if isinstance(value, Enum):
        return _normalize(value.value)
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise FixtureIdentityError("nonfinite seed Decimal")
        return "0" if value.is_zero() else format(value.normalize(), "f")
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise FixtureIdentityError("naive seed timestamp")
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    if is_dataclass(value) and not isinstance(value, type):
        return {f.name: _normalize(getattr(value, f.name)) for f in fields(value)}
    if isinstance(value, (tuple, list)):
        return [_normalize(v) for v in value]
    if isinstance(value, dict):
        if not all(isinstance(k, str) for k in value):
            raise FixtureIdentityError("non-string seed projection key")
        return {k: _normalize(v) for k, v in value.items()}
    if value is None or isinstance(value, bool) or type(value) is int:
        return value
    if isinstance(value, str):
        if unicodedata.normalize("NFC", value) != value:
            raise FixtureIdentityError("non-NFC seed text")
        return value
    raise FixtureIdentityError("unsupported seed projection type")


def project_trusted_version_seed(seed: object) -> bytes:
    """Field-complete deterministic serialization, refusing unknown seed types."""
    from app.services.food_recipes import TrustedRecipeVersionSeed

    if type(seed) is not TrustedRecipeVersionSeed:
        raise FixtureIdentityError("expected exact TrustedRecipeVersionSeed")
    return _record_bytes(_normalize(seed))


def _fingerprint_file(path: Path, sha256: str, blob_sha1: str) -> dict[str, object]:
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != sha256:
        raise FixtureIdentityError("correction artifact raw SHA-256 mismatch")
    git_blob = hashlib.sha1(
        b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw
    ).hexdigest()
    if git_blob != blob_sha1:
        raise FixtureIdentityError("correction artifact Git blob mismatch")
    try:
        return json.loads(
            raw.decode("utf-8"), object_pairs_hook=_reject_duplicate_pairs,
            parse_float=_reject_float,
        )
    except (UnicodeError, ValueError, TypeError) as exc:
        raise FixtureIdentityError("unreadable correction artifact") from exc


class PublicationManifestIds(ManifestPinnedFixtureIds, FixtureTypedIdProvider):
    """A sealed, independently pinned publication lookup; never a DB scan."""

    def __init__(
        self,
        *,
        approved: Sequence[tuple[str, Mapping[str, object]]],
        records: Sequence[Mapping[str, object]],
    ) -> None:
        super().__init__(approved)  # type: ignore[arg-type]
        self._publication_index: dict[tuple[str, int, bytes], bytes] = {}
        self._predecessors: dict[bytes, UUID | None] = {}
        for entry in records:
            code = entry["canonical_code"]
            version = entry["version_number"]
            key = entry["version_key"]
            projection = entry["seed_projection"]
            if type(code) is not str or type(version) is not int or not isinstance(key, dict):
                raise FixtureIdentityError("invalid publication record")
            if not isinstance(projection, dict):
                raise FixtureIdentityError("missing complete trusted-seed projection")
            frozen_key = canonical_envelope("RECIPE_VERSION", key)
            if frozen_key not in self._approved:
                raise FixtureIdentityError("unapproved published-version key")
            if key["canonical_code"] != code or key["version_number"] != version:
                raise FixtureIdentityError("publication key/code/version mismatch")
            projection_bytes = _record_bytes(projection)
            identity = (code, version, projection_bytes)
            if identity in self._publication_index:
                raise FixtureIdentityError("ambiguous trusted publication projection")
            predecessor = key["predecessor_version_key"]
            expected_id = (
                None if predecessor is None
                else derive_fixture_uuid("RECIPE_VERSION", predecessor)
            )
            if predecessor is not None:
                if canonical_envelope("RECIPE_VERSION", predecessor) not in self._approved:
                    raise FixtureIdentityError("unapproved predecessor key")
            self._publication_index[identity] = frozen_key
            self._predecessors[frozen_key] = expected_id

    def recipe_version_key_for(
        self,
        *,
        canonical_code: str,
        seed: object,
        version_number: int,
        predecessor_id: UUID | None,
    ) -> Mapping[str, object]:
        projection = project_trusted_version_seed(seed)
        frozen = self._publication_index.get(
            (canonical_code, version_number, projection)
        )
        if frozen is None:
            raise FixtureIdentityError("missing exact frozen publication/seed")
        if self._predecessors[frozen] != predecessor_id:
            raise FixtureIdentityError("real predecessor does not match frozen semantic key")
        # Return a new dictionary; the manifest's internal copy stays sealed.
        return json.loads(frozen.decode("utf-8"))["key"]


def load_pinned_publication_manifest(
    path: Path,
    *,
    expected_sha256: str,
    expected_source_commit: str,
    expected_stage_membership: Mapping[str, Sequence[str]],
    correction_path: Path | None = None,
    expected_correction_sha256: str | None = None,
    expected_correction_blob_sha1: str | None = None,
) -> PublicationManifestIds:
    """Load only independently pinned bytes and independently reviewed coverage.

    The expected digests, source commit and stage membership MUST originate
    outside this artifact; callers must not compute them from the same read.
    """
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise FixtureIdentityError("unapproved fixture manifest bytes")
    try:
        payload = json.loads(
            raw.decode("utf-8"), object_pairs_hook=_reject_duplicate_pairs,
            parse_float=_reject_float,
        )
    except (UnicodeError, ValueError, TypeError) as exc:
        raise FixtureIdentityError("invalid manifest file") from exc
    if not isinstance(payload, dict) or set(payload) != {
        "schema_version", "policy", "namespace", "fixture_id", "source_commit",
        "review_reference", "approved_ids", "publications", "stages",
    }:
        raise FixtureIdentityError("incorrect fixture manifest schema")
    for name, required in (
        ("schema_version", SCHEMA_VERSION), ("policy", POLICY),
        ("namespace", NAMESPACE), ("fixture_id", FIXTURE_ID),
        ("source_commit", expected_source_commit),
    ):
        if payload[name] != required:
            raise FixtureIdentityError(f"manifest {name} conflicts with external pin")
    if not isinstance(payload["review_reference"], str) or not payload["review_reference"]:
        raise FixtureIdentityError("missing external reviewer reference")

    stage_membership = {
        stage: list(identities) for stage, identities in expected_stage_membership.items()
    }
    if not stage_membership or payload["stages"] != stage_membership:
        raise FixtureIdentityError("manifest stage inventory differs from external pin")
    expected_members = [item for codes in stage_membership.values() for item in codes]
    if len(set(expected_members)) != len(expected_members):
        raise FixtureIdentityError("external stage inventory repeats a publication")
    if not isinstance(payload["approved_ids"], list) or not isinstance(
        payload["publications"], list
    ):
        raise FixtureIdentityError("invalid allowlist/publication collections")
    approved: list[tuple[str, Mapping[str, object]]] = []
    for obj in payload["approved_ids"]:
        if not isinstance(obj, dict) or set(obj) != {"kind", "key"}:
            raise FixtureIdentityError("invalid approved kind/key record")
        approved.append((obj["kind"], obj["key"]))
    records = payload["publications"]
    observed_members: list[str] = []
    corrections = [r for r in records if (
        isinstance(r, dict) and isinstance(r.get("version_key"), dict)
        and r["version_key"].get("publication_kind") == "REVIEWED_CORRECTION"
    )]
    correction_source: dict[str, object] | None = None
    if corrections:
        if (
            correction_path is None
            or expected_correction_sha256 is None
            or expected_correction_blob_sha1 is None
        ):
            raise FixtureIdentityError("missing independently pinned correction artifact")
        correction_source = _fingerprint_file(
            correction_path, expected_correction_sha256, expected_correction_blob_sha1
        )
    correction_rows = {}
    if correction_source is not None:
        for row in correction_source.get("recipes", []):
            if not isinstance(row, dict):
                raise FixtureIdentityError("malformed correction row")
            if row.get("canonical_code") in correction_rows:
                raise FixtureIdentityError("duplicate correction code")
            correction_rows[row["canonical_code"]] = row
        if set(correction_rows) != {r["canonical_code"] for r in corrections}:
            raise FixtureIdentityError("missing/extra approved correction")
    for record in records:
        if not isinstance(record, dict) or set(record) != {
            "stage", "canonical_code", "version_number", "version_key",
            "seed_projection",
        }:
            raise FixtureIdentityError("incomplete publication record")
        code = record["canonical_code"]
        version = record["version_number"]
        stage = record["stage"]
        if not isinstance(stage, str) or not isinstance(code, str) or type(version) is not int:
            raise FixtureIdentityError("invalid stage/code/version")
        member = f"{code}@{version}"
        if member not in stage_membership.get(stage, ()):
            raise FixtureIdentityError("unapproved publication stage membership")
        observed_members.append(member)
        key = record["version_key"]
        if not isinstance(key, dict):
            raise FixtureIdentityError("missing published-version key")
        if key.get("publication_kind") == "REVIEWED_CORRECTION":
            if key.get("correction_revision_sha256") != expected_correction_sha256:
                raise FixtureIdentityError("wrong correction revision SHA")
            row = correction_rows.get(code)
            if not isinstance(row, dict):
                raise FixtureIdentityError("unknown correction source")
            steps = record["seed_projection"].get("steps")
            if steps != row.get("new_steps"):
                raise FixtureIdentityError("reviewed successor Steps mismatch")
            predecessor = key.get("predecessor_version_key")
            if not isinstance(predecessor, dict):
                raise FixtureIdentityError("missing correction lineage")
            predecessor_records = [
                r for r in records
                if r["canonical_code"] == code and r["version_number"] == 1
                and r["version_key"] == predecessor
            ]
            if len(predecessor_records) != 1 or (
                predecessor_records[0]["seed_projection"].get("steps") != row.get("old_steps")
            ):
                raise FixtureIdentityError("unverified original predecessor Steps")
    if sorted(observed_members) != sorted(expected_members):
        raise FixtureIdentityError("incomplete/extra publication coverage")
    if len(records) != len(expected_members):
        raise FixtureIdentityError("duplicate publication membership")
    return PublicationManifestIds(approved=approved, records=records)
