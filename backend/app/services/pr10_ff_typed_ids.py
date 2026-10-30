"""Strict, predictable PR10-FF fixture UUIDs. NEVER use for production identities.

This opt-in test policy does not participate in normal service composition. A
separately pinned input manifest must authorize every key before ID allocation.
No production API, CLI, environment flag or global singleton selects it.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from collections.abc import Mapping, Sequence
from decimal import Decimal, InvalidOperation
from typing import Literal, Protocol
from uuid import RFC_4122, UUID

POLICY = "PR10_FF_TYPED_ID_POLICY_V1"
NAMESPACE = "familyfoodos/pr10-ff/fixture-only/v1"
FIXTURE_ID = "PR10_FF_FORWARD_3M_7D_V1"
_PREFIX = b"FamilyFoodOS/PR10-FF/typed-id/v1\x00"
_SHA = re.compile(r"[0-9a-f]{64}\Z")

FixtureEntityKind = Literal[
    "RECIPE",
    "RECIPE_VERSION",
    "RECIPE_INGREDIENT",
    "RECIPE_STEP",
    "HOUSEHOLD",
    "HOUSEHOLD_MEMBER",
]
KINDS = frozenset(
    (
        "RECIPE",
        "RECIPE_VERSION",
        "RECIPE_INGREDIENT",
        "RECIPE_STEP",
        "HOUSEHOLD",
        "HOUSEHOLD_MEMBER",
    )
)


class FixtureIdentityError(ValueError):
    """An unapproved, malformed, or colliding fixture identity."""


class FixtureTypedIdProvider(Protocol):
    def id_for(self, kind: FixtureEntityKind, key: Mapping[str, object]) -> UUID: ...

    def recipe_version_key_for(
        self,
        *,
        canonical_code: str,
        seed: object,
        version_number: int,
        predecessor_id: UUID | None,
    ) -> Mapping[str, object]: ...


def _object(value: object, fields: set[str], *, context: str) -> Mapping[str, object]:
    if (
        not isinstance(value, Mapping)
        or set(value) != fields
        or any(not isinstance(k, str) for k in value)
    ):
        raise FixtureIdentityError(f"{context}: fields must match the frozen schema")
    return value


def _string(value: object) -> None:
    if (
        not isinstance(value, str)
        or not value
        or unicodedata.normalize("NFC", value) != value
    ):
        raise FixtureIdentityError("missing or non-NFC fixture string")


def _sha(value: object, *, nullable: bool = False) -> None:
    if nullable and value is None:
        return
    if not isinstance(value, str) or not _SHA.fullmatch(value):
        raise FixtureIdentityError("invalid lowercase SHA-256")


def _positive(value: object) -> None:
    if type(value) is not int or value <= 0:
        raise FixtureIdentityError("expected positive JSON integer")


def _decimal(value: object) -> None:
    if not isinstance(value, str) or not value:
        raise FixtureIdentityError("expected canonical Decimal string")
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise FixtureIdentityError("invalid Decimal") from exc
    if not parsed.is_finite():
        raise FixtureIdentityError("nonfinite Decimal")
    canonical = "0" if parsed.is_zero() else format(parsed.normalize(), "f")
    if value != canonical:
        raise FixtureIdentityError("noncanonical Decimal")


def _source_key(value: object) -> Mapping[str, object]:
    source = _object(
        value,
        {
            "canonical_code",
            "source_name",
            "source_recipe_id",
            "source_version",
            "source_document_sha256",
        },
        context="source_record_key",
    )
    for name in ("canonical_code", "source_name", "source_recipe_id", "source_version"):
        _string(source[name])
    _sha(source["source_document_sha256"])
    return source


def _version_key(value: object, *, depth: int = 0) -> Mapping[str, object]:
    if depth >= 3:
        raise FixtureIdentityError("predecessor lineage too deep for v1 policy")
    v = _object(
        value,
        {
            "canonical_code",
            "source_record_key",
            "version_number",
            "predecessor_version_key",
            "publication_kind",
            "publication_process_sha256",
            "correction_revision_sha256",
        },
        context="RECIPE_VERSION",
    )
    _string(v["canonical_code"])
    source = _source_key(v["source_record_key"])
    if source["canonical_code"] != v["canonical_code"]:
        raise FixtureIdentityError("source/Recipe canonical code mismatch")
    _positive(v["version_number"])
    _sha(v["publication_process_sha256"])
    if v["publication_kind"] == "ORIGINAL":
        if (
            v["version_number"] != 1
            or v["predecessor_version_key"] is not None
            or v["correction_revision_sha256"] is not None
        ):
            raise FixtureIdentityError(
                "original v1 cannot have correction or predecessor"
            )
    elif v["publication_kind"] == "REVIEWED_CORRECTION":
        _sha(v["correction_revision_sha256"])
        predecessor = _version_key(v["predecessor_version_key"], depth=depth + 1)
        if (
            v["version_number"] != 2
            or predecessor["version_number"] != 1
            or predecessor["canonical_code"] != v["canonical_code"]
            or predecessor["source_record_key"] != v["source_record_key"]
        ):
            raise FixtureIdentityError("unapproved correction lineage")
    else:
        raise FixtureIdentityError("unapproved publication kind")
    return v


def _validate_key(kind: str, key: Mapping[str, object]) -> None:
    if kind == "RECIPE":
        obj = _object(key, {"canonical_code"}, context=kind)
        _string(obj["canonical_code"])
    elif kind == "HOUSEHOLD":
        obj = _object(key, {"household_key"}, context=kind)
        _string(obj["household_key"])
    elif kind == "HOUSEHOLD_MEMBER":
        obj = _object(key, {"household_key", "ordinal", "profile_sha256"}, context=kind)
        _string(obj["household_key"])
        _positive(obj["ordinal"])
        _sha(obj["profile_sha256"])
    elif kind == "RECIPE_VERSION":
        _version_key(key)
    elif kind == "RECIPE_STEP":
        obj = _object(
            key,
            {"recipe_version_key", "position", "instruction_sha256", "stage_code"},
            context=kind,
        )
        _version_key(obj["recipe_version_key"])
        _positive(obj["position"])
        _sha(obj["instruction_sha256"])
        if obj["stage_code"] is not None:
            raise FixtureIdentityError("v1 stage_code must be null")
    elif kind == "RECIPE_INGREDIENT":
        obj = _object(
            key,
            {
                "recipe_version_key",
                "position",
                "food_ingredient_code",
                "quantity",
                "unit",
                "source_amount_text_sha256",
                "normalization_note_sha256",
                "prep_note_sha256",
                "optional",
            },
            context=kind,
        )
        _version_key(obj["recipe_version_key"])
        _positive(obj["position"])
        _string(obj["food_ingredient_code"])
        _decimal(obj["quantity"])
        _string(obj["unit"])
        _sha(obj["source_amount_text_sha256"])
        _sha(obj["normalization_note_sha256"], nullable=True)
        _sha(obj["prep_note_sha256"], nullable=True)
        if type(obj["optional"]) is not bool:
            raise FixtureIdentityError("optional must be boolean")
    else:
        raise FixtureIdentityError("unapproved entity kind")


def canonical_envelope(kind: FixtureEntityKind, key: Mapping[str, object]) -> bytes:
    if kind not in KINDS:
        raise FixtureIdentityError("unknown fixture entity kind")
    _validate_key(kind, key)
    envelope = {
        "policy": POLICY,
        "namespace": NAMESPACE,
        "fixture_id": FIXTURE_ID,
        "kind": kind,
        "key": key,
    }
    try:
        return json.dumps(
            envelope,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError, RecursionError) as exc:
        raise FixtureIdentityError("invalid canonical JSON input") from exc


def derive_fixture_uuid(kind: FixtureEntityKind, key: Mapping[str, object]) -> UUID:
    """Shape a *predictable test ID* as UUID version 4; NOT a random UUID4."""
    data = canonical_envelope(kind, key)
    raw = bytearray(hashlib.sha256(_PREFIX + data).digest()[:16])
    raw[6] = (raw[6] & 0x0F) | 0x40
    raw[8] = (raw[8] & 0x3F) | 0x80
    result = UUID(bytes=bytes(raw))
    if result.version != 4 or result.variant != RFC_4122:
        raise FixtureIdentityError("derived UUID validation failed")
    return result


class ManifestPinnedFixtureIds:
    """No ID is emitted unless its complete typed key was approved *before* use.

    A later proof driver must supply a manifest reviewed outside its Planner run.
    This class is not a source of rights, provenance, or published-version truth.
    """

    def __init__(
        self, approved: Sequence[tuple[FixtureEntityKind, Mapping[str, object]]]
    ):
        if not approved:
            raise FixtureIdentityError("empty/unpinned fixture identity manifest")
        self._approved = frozenset(
            canonical_envelope(kind, key) for kind, key in approved
        )
        if len(self._approved) != len(approved):
            raise FixtureIdentityError("duplicate approved typed key")
        self._forward: dict[bytes, UUID] = {}
        self._inverse: dict[UUID, bytes] = {}

    def id_for(self, kind: FixtureEntityKind, key: Mapping[str, object]) -> UUID:
        frozen = canonical_envelope(kind, key)
        if frozen not in self._approved:
            raise FixtureIdentityError(
                "key absent from independently frozen fixture manifest"
            )
        result = derive_fixture_uuid(kind, key)
        seen = self._inverse.get(result)
        if seen is not None and seen != frozen:
            raise FixtureIdentityError("cross-key / cross-kind ID collision")
        self._inverse[result] = frozen
        self._forward[frozen] = result
        return result

    @property
    def ledger(self) -> tuple[tuple[str, str], ...]:
        """Readonly QA witness (canonical JSON, UUID), not a persisted authority."""
        return tuple(
            sorted(
                (key.decode("utf-8"), str(uid)) for key, uid in self._forward.items()
            )
        )
