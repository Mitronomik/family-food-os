"""Explicitly pinned, immutable test-only Recipe publication manifest loader.

The external source pin, stage inventory, and correction evidence are supplied
by a reviewer *before* any seed run. This is not an ingestion/pub authority.
"""

from __future__ import annotations

import hashlib
import json
import unicodedata
from collections.abc import Mapping, Sequence
from dataclasses import fields, is_dataclass
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from pathlib import Path
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
_LOADER_TOKEN = object()


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
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
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


def process_steps_sha256(steps: Sequence[str]) -> str:
    """Frozen PR10-FF process witness: exact ordered NFC instruction list only.

    Rights, ingredient forms, metadata and nutrition are separately checked by
    complete seed projections and live repositories; they are not inferred here.
    """
    if not isinstance(steps, (list, tuple)) or not steps:
        raise FixtureIdentityError("empty process Step list")
    if any(
        not isinstance(s, str) or not s or unicodedata.normalize("NFC", s) != s
        for s in steps
    ):
        raise FixtureIdentityError("invalid ordered process Steps")
    return hashlib.sha256(_record_bytes({"steps": list(steps)})).hexdigest()


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
            raw.decode("utf-8"),
            object_pairs_hook=_reject_duplicate_pairs,
            parse_float=_reject_float,
        )
    except FixtureIdentityError:
        raise
    except (UnicodeError, ValueError, TypeError) as exc:
        raise FixtureIdentityError("unreadable correction artifact") from exc


class PublicationManifestIds(ManifestPinnedFixtureIds, FixtureTypedIdProvider):
    """A sealed, independently pinned publication lookup; never a DB scan."""

    def __init__(
        self,
        *,
        approved: Sequence[tuple[str, Mapping[str, object]]],
        records: Sequence[Mapping[str, object]],
        _loader_token: object | None = None,
    ) -> None:
        if _loader_token is not _LOADER_TOKEN:
            raise FixtureIdentityError(
                "publication provider requires pinned manifest loader"
            )
        super().__init__(approved)  # type: ignore[arg-type]
        self._source_path: Path | None = None
        self._expected_sha256: str | None = None
        self._correction_path: Path | None = None
        self._expected_correction_sha256: str | None = None
        self._publication_index: dict[tuple[str, int, bytes], bytes] = {}
        self._predecessors: dict[bytes, UUID | None] = {}
        for entry in records:
            code = entry["canonical_code"]
            version = entry["version_number"]
            key = entry["version_key"]
            projection = entry["seed_projection"]
            if (
                type(code) is not str
                or type(version) is not int
                or not isinstance(key, dict)
            ):
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
                None
                if predecessor is None
                else derive_fixture_uuid("RECIPE_VERSION", predecessor)
            )
            if (
                predecessor is not None
                and canonical_envelope("RECIPE_VERSION", predecessor)
                not in self._approved
            ):
                raise FixtureIdentityError("unapproved predecessor key")
            self._publication_index[identity] = frozen_key
            self._predecessors[frozen_key] = expected_id

    def _assert_files_unchanged(self) -> None:
        if self._source_path is not None and (
            hashlib.sha256(self._source_path.read_bytes()).hexdigest()
            != self._expected_sha256
        ):
            raise FixtureIdentityError("loaded manifest changed after pinning")
        if self._correction_path is not None and (
            hashlib.sha256(self._correction_path.read_bytes()).hexdigest()
            != self._expected_correction_sha256
        ):
            raise FixtureIdentityError("correction file changed after pinning")

    def id_for(self, kind: str, key: Mapping[str, object]) -> UUID:
        self._assert_files_unchanged()
        return super().id_for(kind, key)  # type: ignore[arg-type]

    def recipe_version_key_for(
        self,
        *,
        canonical_code: str,
        seed: object,
        version_number: int,
        predecessor_id: UUID | None,
    ) -> Mapping[str, object]:
        self._assert_files_unchanged()
        projection = project_trusted_version_seed(seed)
        frozen = self._publication_index.get(
            (canonical_code, version_number, projection)
        )
        if frozen is None:
            raise FixtureIdentityError("missing exact frozen publication/seed")
        if self._predecessors[frozen] != predecessor_id:
            raise FixtureIdentityError(
                "real predecessor does not match frozen semantic key"
            )
        # Return a new dictionary; the manifest's internal copy stays sealed.
        return json.loads(frozen.decode("utf-8"))["key"]


def _expected_recipe_allowlist(
    records: Sequence[Mapping[str, object]],
) -> set[bytes]:
    """Every source-bound Recipe/Version/Ingredient/Step key must be reachable."""
    expected: set[bytes] = set()

    def add(kind: str, key: Mapping[str, object]) -> None:
        encoded = canonical_envelope(kind, key)  # type: ignore[arg-type]
        if encoded in expected and kind != "RECIPE":
            raise FixtureIdentityError("duplicate generated publication identity")
        expected.add(encoded)

    def sha_text(value: str | None) -> str | None:
        return None if value is None else hashlib.sha256(value.encode("utf-8")).hexdigest()

    for record in records:
        code = record["canonical_code"]
        key = record["version_key"]
        projection = record["seed_projection"]
        if not isinstance(code, str) or not isinstance(key, dict) or not isinstance(projection, dict):
            raise FixtureIdentityError("invalid publication allowlist projection")
        add("RECIPE", {"canonical_code": code})
        add("RECIPE_VERSION", key)
        ingredients = projection.get("ingredients")
        steps = projection.get("steps")
        if not isinstance(ingredients, list) or not isinstance(steps, list):
            raise FixtureIdentityError("unreviewed ingredient/Step projection")
        for position, item in enumerate(ingredients, start=1):
            if not isinstance(item, dict) or set(item) != {
                "food_ingredient_code", "quantity", "unit", "source_amount_text",
                "normalization_note", "prep_note", "optional",
            }:
                raise FixtureIdentityError("incomplete/extra ingredient seed fields")
            add("RECIPE_INGREDIENT", {
                "recipe_version_key": key,
                "position": position,
                "food_ingredient_code": item["food_ingredient_code"],
                "quantity": item["quantity"],
                "unit": item["unit"],
                "source_amount_text_sha256": sha_text(item["source_amount_text"]),
                "normalization_note_sha256": sha_text(item["normalization_note"]),
                "prep_note_sha256": sha_text(item["prep_note"]),
                "optional": item["optional"],
            })
        for position, instruction in enumerate(steps, start=1):
            if not isinstance(instruction, str):
                raise FixtureIdentityError("non-string source Step")
            add("RECIPE_STEP", {
                "recipe_version_key": key,
                "position": position,
                "instruction_sha256": sha_text(instruction),
                "stage_code": None,
            })
    return expected


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
            raw.decode("utf-8"),
            object_pairs_hook=_reject_duplicate_pairs,
            parse_float=_reject_float,
        )
    except FixtureIdentityError:
        raise
    except (UnicodeError, ValueError, TypeError) as exc:
        raise FixtureIdentityError("invalid manifest file") from exc
    if not isinstance(payload, dict) or set(payload) != {
        "schema_version",
        "policy",
        "namespace",
        "fixture_id",
        "source_commit",
        "review_reference",
        "approved_ids",
        "publications",
        "stages",
    }:
        raise FixtureIdentityError("incorrect fixture manifest schema")
    for name, required in (
        ("schema_version", SCHEMA_VERSION),
        ("policy", POLICY),
        ("namespace", NAMESPACE),
        ("fixture_id", FIXTURE_ID),
        ("source_commit", expected_source_commit),
    ):
        if payload[name] != required:
            raise FixtureIdentityError(f"manifest {name} conflicts with external pin")
    if (
        not isinstance(payload["review_reference"], str)
        or not payload["review_reference"]
    ):
        raise FixtureIdentityError("missing external reviewer reference")

    stage_membership = {
        stage: list(identities)
        for stage, identities in expected_stage_membership.items()
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
    corrections = [
        r
        for r in records
        if (
            isinstance(r, dict)
            and isinstance(r.get("version_key"), dict)
            and r["version_key"].get("publication_kind") == "REVIEWED_CORRECTION"
        )
    ]
    correction_source: dict[str, object] | None = None
    if corrections:
        if (
            correction_path is None
            or expected_correction_sha256 is None
            or expected_correction_blob_sha1 is None
        ):
            raise FixtureIdentityError(
                "missing independently pinned correction artifact"
            )
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
            "stage",
            "canonical_code",
            "version_number",
            "version_key",
            "seed_projection",
        }:
            raise FixtureIdentityError("incomplete publication record")
        code = record["canonical_code"]
        version = record["version_number"]
        stage = record["stage"]
        if (
            not isinstance(stage, str)
            or not isinstance(code, str)
            or type(version) is not int
        ):
            raise FixtureIdentityError("invalid stage/code/version")
        member = f"{code}@{version}"
        if member not in stage_membership.get(stage, ()):
            raise FixtureIdentityError("unapproved publication stage membership")
        observed_members.append(member)
        key = record["version_key"]
        if not isinstance(key, dict):
            raise FixtureIdentityError("missing published-version key")
        projection = record["seed_projection"]
        if not isinstance(projection, dict) or set(projection) != {
            "base_servings",
            "meal_type_code",
            "prep_time_minutes",
            "cook_time_minutes",
            "total_time_minutes",
            "difficulty_code",
            "batch_friendly",
            "freezable",
            "storage_days_fridge",
            "storage_days_freezer",
            "verification_status",
            "verified_at",
            "source_name",
            "source_recipe_id",
            "source_url",
            "source_version",
            "source_retrieved_at",
            "source_document_sha256",
            "source_original_servings",
            "rights_review_status",
            "rights_basis",
            "change_note",
            "ingredients",
            "steps",
            "equipment_codes",
            "source_output_g",
            "source_output_text",
        }:
            raise FixtureIdentityError("incomplete/extra trusted-seed fields")
        source = key.get("source_record_key")
        if not isinstance(source, dict) or any(
            projection.get(attr) != source.get(attr)
            for attr in (
                "source_name",
                "source_recipe_id",
                "source_version",
                "source_document_sha256",
            )
        ):
            raise FixtureIdentityError("version key/source projection mismatch")
        if key.get("publication_process_sha256") != process_steps_sha256(
            projection["steps"]
        ):
            raise FixtureIdentityError("published process/ordered Step SHA mismatch")
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
                r
                for r in records
                if r["canonical_code"] == code
                and r["version_number"] == 1
                and r["version_key"] == predecessor
            ]
            if len(predecessor_records) != 1 or (
                predecessor_records[0]["seed_projection"].get("steps")
                != row.get("old_steps")
            ):
                raise FixtureIdentityError("unverified original predecessor Steps")
    if sorted(observed_members) != sorted(expected_members):
        raise FixtureIdentityError("incomplete/extra publication coverage")
    if len(records) != len(expected_members):
        raise FixtureIdentityError("duplicate publication membership")
    actual_recipe_keys = {
        canonical_envelope(kind, key)  # type: ignore[arg-type]
        for kind, key in approved
        if kind in {"RECIPE", "RECIPE_VERSION", "RECIPE_INGREDIENT", "RECIPE_STEP"}
    }
    expected_recipe_keys = _expected_recipe_allowlist(records)
    if actual_recipe_keys != expected_recipe_keys:
        raise FixtureIdentityError("missing/extra/unreachable approved Recipe keys")
    provider = PublicationManifestIds(
        approved=approved, records=records, _loader_token=_LOADER_TOKEN
    )
    provider._source_path = path
    provider._expected_sha256 = expected_sha256
    provider._correction_path = correction_path if corrections else None
    provider._expected_correction_sha256 = (
        expected_correction_sha256 if corrections else None
    )
    return provider
