"""Pinned VECTOR-A compatibility import policy; no general enrichment policy.

Keep this version stable: migration 0028 and initial audited-profile creation
share it. The input bundle is immutable, hash-pinned evidence, not parsed AI data.
"""

from datetime import datetime
from decimal import Decimal
import hashlib
import json
from typing import Any
from collections.abc import Mapping, Sequence

REGISTRY_VERSION = "PR6_NUTRIENT_VECTOR_A_V1"
FIELDS = ("kcal", "protein_g", "fat_g", "carbohydrates_g", "fiber_g")


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def value_set_digest(rows: Sequence[Mapping[str, Any]]) -> str:
    payload = sorted(
        (r["nutrient_code"], format(r["amount"], "f"), r["provenance_json"])
        for r in rows
    )
    return hashlib.sha256(canonical_json(payload).encode()).hexdigest()


def disposition(row: dict) -> str:
    """Mapping agreement and exact-zero authority are independent gates."""
    status = row["legacy_mapping_status"]
    if status == "SOURCE_COMPONENT_CONFIRMED":
        if row["source_value_state"] == "ZERO_REPORTED":
            return "UNRESOLVED_ZERO"  # no approved exact-zero import policy in v1
        if row["source_value_state"] != "NONZERO_REPORTED":
            return row["source_value_state"]
        if row["censoring_evidence_state"] != "NOT_REVIEWED_NONZERO":
            return row["censoring_evidence_state"]
        if Decimal(row["legacy_value"]) == 0 or Decimal(row["source_value"]) == 0:
            return "UNRESOLVED_ZERO"
        return "SOURCE_COMPONENT_CONFIRMED"
    if status == "LEGACY_PROFILE_VALUE_CONFIRMED_SOURCE_ID_UNAVAILABLE":
        return "LEGACY_PROJECTION"
    if status in {"VALUE_MISMATCH", "DEFINITION_AMBIGUOUS", "VALUE_ABSENT"}:
        return status
    raise ValueError("Неизвестный результат аудита нутриента.")


def prepare_profile(
    profile: dict, food_code: str, bundle: dict
) -> tuple[list, str] | None:
    """Return a complete audited initial set, or explicitly unavailable.

    Identity, all legacy amounts and snapshot metadata must agree. Never select
    current profiles, rebind reviews, or select alternative energy components.
    """
    rows = [
        r
        for r in bundle["legacy-v1-crosswalk.json"]["rows"]
        if r["food_ingredient_code"] == food_code
        and all(
            r["profile_" + k] == profile[k]
            for k in ("source_name", "source_id", "source_version")
        )
    ]
    if len(rows) != len(FIELDS) or {r["legacy_field"] for r in rows} != set(FIELDS):
        return None
    for row in rows:
        for field in ("basis_grams", *FIELDS):
            expected = (
                row["profile_basis_grams"]
                if field == "basis_grams"
                else next(r["legacy_value"] for r in rows if r["legacy_field"] == field)
            )
            actual = profile[field]
            if (actual is None) != (expected is None):
                return None
            if actual is not None and Decimal(actual) != Decimal(expected):
                return None
        instant = profile["verified_at"]
        if isinstance(instant, str):
            instant = datetime.fromisoformat(instant)
        expected_instant = datetime.fromisoformat(row["profile_verified_at"])
        if instant.replace(tzinfo=None) != expected_instant.replace(tzinfo=None):
            return None
        if (
            profile["source_data_type"] != row["profile_source_data_type"]
            or profile["estimated"] != row["profile_estimated"]
        ):
            return None
    definitions = {
        d["canonical_code"]: d for d in bundle["nutrient-registry.json"]["entries"]
    }
    values, observations = [], []
    for row in sorted(rows, key=lambda r: r["legacy_field"]):
        origin = disposition(row)
        observations.append({"origin": origin, "observation": row})
        if origin != "SOURCE_COMPONENT_CONFIRMED":
            continue
        code = row["target_nutrient_code"]
        definition = definitions[code]
        mappings = [
            m
            for m in bundle["source-mappings.json"]["mappings"]
            if m["canonical_code"] == code
            and m["source_name"] == row["profile_source_name"]
            and m["source_release"] == row["profile_source_version"]
            and m["source_data_type"] == row["profile_source_data_type"]
            and m["source_nutrient_id"] == row["source_nutrient_id"]
        ]
        if len(mappings) != 1:
            raise ValueError("Не найдено однозначное соответствие нутриента.")
        mapping = mappings[0]
        if (
            mapping["mapping_status"] not in {"EXACT", "METHOD_SPECIFIC"}
            or mapping["canonical_unit"] != definition["canonical_unit"]
            or mapping["source_unit"] != row["source_unit"]
            or mapping["source_nutrient_name"] != row["source_nutrient_name"]
            or not row["numeric_comparison"]["equal"]
        ):
            raise ValueError("Соответствие не допускает точный перенос значения.")
        values.append(
            {
                "nutrient_code": code,
                "amount": Decimal(row["legacy_value"]),
                "provenance_json": canonical_json(
                    {"observation": row, "mapping": mapping}
                ),
            }
        )
    if len({v["nutrient_code"] for v in values}) != len(values):
        raise ValueError("Повторное эффективное значение нутриента.")
    return values, canonical_json(observations)
