"""Augment existing nutrition identities with the audited, sealed VECTOR-A set."""

import hashlib
import json
from pathlib import Path

from app.domain.nutrient_vector_backfill_v1 import (
    REGISTRY_VERSION,
    canonical_json,
    prepare_profile,
    value_set_digest,
)

MIGRATION_ID = "0028_normalized_nutrient_vector"
ARTIFACT_DIRECTORY = (
    Path(__file__).resolve().parents[4] / "data/curation/pr6-nutrient-vector-a"
)
# Exact merged VECTOR-A bytes. A future registry requires its own reviewed version.
ARTIFACT_HASHES = {
    "nutrient-registry.json": "de0012d02e31d4eb23b7e4d5c9c4144fa3a12895893470b2100e5dd595ad2492",
    "source-mappings.json": "4e90afd12d8f98aab6b667014329dd0e66473408320f432bdcfe826ce2f49e63",
    "legacy-v1-crosswalk.json": "13853abac3589a308551a3f8544409e8b92e387115ef4ba81774f57909983eea",
    "source-manifest.json": "398d36cf901bed5701ded3dc7a8bd40e7bc03c3e995867d1b5930e09e0af5535",
}

STATEMENTS = (
    """CREATE TABLE nutrient_registry_snapshots (
        version TEXT NOT NULL PRIMARY KEY,
        bundle_json TEXT NOT NULL CHECK(json_valid(bundle_json)),
        bundle_sha256 TEXT NOT NULL CHECK(length(bundle_sha256) = 64)
    )""",
    """CREATE TABLE nutrient_definitions (
        code TEXT NOT NULL PRIMARY KEY CHECK(code GLOB '[A-Z]*' AND code NOT GLOB '*[^A-Z0-9_]*'),
        display_name_ru TEXT NOT NULL CHECK(length(trim(display_name_ru)) > 0),
        unit TEXT NOT NULL CHECK(unit IN ('kcal', 'g', 'mg', 'µg')),
        registry_version TEXT NOT NULL REFERENCES nutrient_registry_snapshots(version) ON DELETE RESTRICT,
        definition_json TEXT NOT NULL CHECK(json_valid(definition_json))
    )""",
    """CREATE TABLE nutrition_vector_seals (
        profile_id CHAR(32) NOT NULL PRIMARY KEY REFERENCES food_nutrition_profiles(id) ON DELETE RESTRICT,
        registry_version TEXT NOT NULL REFERENCES nutrient_registry_snapshots(version) ON DELETE RESTRICT,
        value_count INTEGER NOT NULL CHECK(typeof(value_count) = 'integer' AND value_count >= 0),
        value_sha256 TEXT NOT NULL CHECK(length(value_sha256) = 64),
        observations_json TEXT NOT NULL CHECK(json_valid(observations_json))
    )""",
    """CREATE TABLE nutrient_values (
        profile_id CHAR(32) NOT NULL REFERENCES nutrition_vector_seals(profile_id) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED,
        nutrient_code TEXT NOT NULL REFERENCES nutrient_definitions(code) ON DELETE RESTRICT,
        amount TEXT NOT NULL CHECK(typeof(amount) = 'text' AND length(amount) BETWEEN 1 AND 160
            AND amount NOT GLOB '*[^0-9.]*' AND amount GLOB '*[0-9]*'
            AND length(amount) - length(replace(amount, '.', '')) <= 1),
        provenance_json TEXT NOT NULL CHECK(json_valid(provenance_json)),
        PRIMARY KEY(profile_id, nutrient_code)
    )""",
    """CREATE TRIGGER nutrient_values_no_late_insert BEFORE INSERT ON nutrient_values
        WHEN EXISTS(SELECT 1 FROM nutrition_vector_seals WHERE profile_id = NEW.profile_id)
        BEGIN SELECT RAISE(ABORT, 'Набор нутриентов профиля уже зафиксирован.'); END""",
    """CREATE TRIGGER nutrition_vector_seals_complete BEFORE INSERT ON nutrition_vector_seals
        WHEN NEW.value_count != (SELECT count(*) FROM nutrient_values WHERE profile_id = NEW.profile_id)
        OR EXISTS(SELECT 1 FROM nutrient_values v JOIN nutrient_definitions d ON d.code = v.nutrient_code
                  WHERE v.profile_id = NEW.profile_id AND d.registry_version != NEW.registry_version)
        BEGIN SELECT RAISE(ABORT, 'Набор нутриентов не соответствует снимку.'); END""",
)


def load_bundle():
    bundle = {}
    for name, expected in ARTIFACT_HASHES.items():
        raw = (ARTIFACT_DIRECTORY / name).read_bytes()
        if hashlib.sha256(raw).hexdigest() != expected:
            raise ValueError(f"Изменён утверждённый артефакт VECTOR-A: {name}")
        bundle[name] = json.loads(raw)
    definitions = bundle["nutrient-registry.json"]["entries"]
    zeros = [
        r
        for r in bundle["legacy-v1-crosswalk.json"]["rows"]
        if r["source_value_state"] == "ZERO_REPORTED"
    ]
    if len(definitions) != 51 or len(zeros) != 64:
        raise ValueError(
            "Конфликт VECTOR-A: ожидалось 51 определение и 64 наблюдения нуля."
        )
    return bundle


def upgrade(connection):
    # Standard runner owns COMMIT and the migration marker. Explicit BEGIN also
    # makes DDL transactional when upgrading immediately after a rebuild.
    if not connection.in_transaction:
        connection.execute("BEGIN")
    bundle = load_bundle()
    for statement in STATEMENTS:
        connection.execute(statement)
    for table, key in (
        ("nutrient_registry_snapshots", "version"),
        ("nutrient_definitions", "code"),
        ("nutrition_vector_seals", "profile_id"),
        ("nutrient_values", None),
    ):
        for operation in ("UPDATE", "DELETE"):
            connection.execute(f"""CREATE TRIGGER {table}_no_{operation.lower()}
                BEFORE {operation} ON {table}
                BEGIN SELECT RAISE(ABORT, 'Снимок нутриентов неизменяем.'); END""")
        if key:
            connection.execute(f"""CREATE TRIGGER {table}_no_replace BEFORE INSERT ON {table}
                WHEN EXISTS(SELECT 1 FROM {table} WHERE {key} = NEW.{key})
                BEGIN SELECT RAISE(ABORT, 'Снимок нутриентов неизменяем.'); END""")
    encoded = canonical_json(bundle)
    connection.execute(
        "INSERT INTO nutrient_registry_snapshots VALUES (?, ?, ?)",
        (REGISTRY_VERSION, encoded, hashlib.sha256(encoded.encode()).hexdigest()),
    )
    for definition in bundle["nutrient-registry.json"]["entries"]:
        connection.execute(
            "INSERT INTO nutrient_definitions VALUES (?, ?, ?, ?, ?)",
            (
                definition["canonical_code"],
                definition["display_name_ru"],
                definition["canonical_unit"],
                REGISTRY_VERSION,
                canonical_json(definition),
            ),
        )
    profiles = connection.execute("""SELECT p.*, f.canonical_code FROM food_nutrition_profiles p
        JOIN food_ingredients f ON f.id = p.food_ingredient_id ORDER BY p.id""").fetchall()
    for profile in profiles:
        prepared = prepare_profile(dict(profile), profile["canonical_code"], bundle)
        if prepared is None:
            raise ValueError(
                "Профиль отсутствует в полном аудите VECTOR-A или отличается от него; "
                "перед обновлением нужен отдельный аудит происхождения."
            )
        values, observations = prepared
        for value in values:
            connection.execute(
                "INSERT INTO nutrient_values VALUES (?, ?, ?, ?)",
                (
                    profile["id"],
                    value["nutrient_code"],
                    format(value["amount"], "f"),
                    value["provenance_json"],
                ),
            )
        connection.execute(
            "INSERT INTO nutrition_vector_seals VALUES (?, ?, ?, ?, ?)",
            (
                profile["id"],
                REGISTRY_VERSION,
                len(values),
                value_set_digest(values),
                observations,
            ),
        )
