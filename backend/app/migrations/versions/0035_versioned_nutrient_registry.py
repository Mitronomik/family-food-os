"""Version nutrient-definition identity and publish the reviewed V2 registry."""

import hashlib
import json
from pathlib import Path

from app.domain.nutrient_vector_backfill_v1 import (
    REGISTRY_VERSION as REGISTRY_V1,
    canonical_json,
)

MIGRATION_ID = "0035_versioned_nutrient_registry"
SQLITE_MIGRATION_MODE = "foreign_key_rebuild"

REGISTRY_V2 = "RU_NUTRIENT_REGISTRY_V2"
ADAPTER_VERSION_V2 = "RU_NUTRIENT_METHOD_ADAPTER_V2"

ROOT = Path(__file__).resolve().parents[4]
V1_REGISTRY = ROOT / "data/curation/pr6-nutrient-vector-a/nutrient-registry.json"
V2_DIRECTORY = ROOT / "data/curation/nutrient-registry-v2"

ARTIFACT_HASHES = {
    V1_REGISTRY: "de0012d02e31d4eb23b7e4d5c9c4144fa3a12895893470b2100e5dd595ad2492",
    V2_DIRECTORY / "registry.json": "eb335c3d39e27a67681e64c9de4fcb55183e08bcb59f4d93ed1c8b9fa3eab85d",
    V2_DIRECTORY / "method-adapters.json": "17428d4e6ee3e2a26e9b9fd132cc0e1d18e69bdd6ab9025458609f5f30516ebd",
}

NEW_CODES = {
    "VITAMIN_A_RE",
    "NIACIN_EQUIVALENT",
    "VITAMIN_E_TOCOPHEROL_EQUIVALENT",
}
METHOD_INDEPENDENT_REDEFINITION = "CARBOHYDRATE_AVAILABLE"


def _load(path: Path):
    raw = path.read_bytes()
    expected = ARTIFACT_HASHES[path]
    if hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError(f"Изменён утверждённый артефакт реестра: {path.name}")
    return json.loads(raw)


def load_contract():
    v1 = _load(V1_REGISTRY)
    v2 = _load(V2_DIRECTORY / "registry.json")
    adapters = _load(V2_DIRECTORY / "method-adapters.json")

    if (
        v2.get("registry_version") != REGISTRY_V2
        or v2.get("base_registry_version") != REGISTRY_V1
        or v2.get("schema_version") != 2
        or adapters.get("version") != ADAPTER_VERSION_V2
        or adapters.get("registry_version") != REGISTRY_V2
    ):
        raise ValueError("Неверная идентичность V2 реестра или адаптера.")

    v1_entries = {row["canonical_code"]: row for row in v1["entries"]}
    v2_entries = {row["canonical_code"]: row for row in v2["entries"]}
    if len(v1_entries) != 51 or len(v2_entries) != 54:
        raise ValueError("Ожидалось 51 V1 и 54 V2 определения.")
    if set(v2_entries) - set(v1_entries) != NEW_CODES:
        raise ValueError("Набор новых V2 определений не соответствует решению.")
    if set(v1_entries) - set(v2_entries):
        raise ValueError("V2 не может удалять определения V1.")

    for code, old in v1_entries.items():
        new = v2_entries[code]
        if code == METHOD_INDEPENDENT_REDEFINITION:
            if (
                new["canonical_unit"] != old["canonical_unit"]
                or new["display_name_ru"] != old["display_name_ru"]
                or new["definition_kind"] != "METHOD_INDEPENDENT_COMPONENT"
            ):
                raise ValueError("V2 carbohydrate identity drifted unexpectedly.")
        elif new != old:
            raise ValueError(f"V2 unexpectedly changed V1 definition {code}.")

    if any(
        v2_entries[code]["infoods_mapping_status"] != "NO_IMPLICIT_CONVERSION"
        for code in NEW_CODES
    ):
        raise ValueError("Vitamin equivalents must remain conversion-blocked.")

    adapter_codes = {row["canonical_code"] for row in adapters["bindings"]}
    if adapter_codes != {
        "PROTEIN",
        "FAT_TOTAL",
        "FIBER_TOTAL_DIETARY",
        "CARBOHYDRATE_AVAILABLE",
        "CARBOHYDRATE_BY_DIFFERENCE",
        "ENERGY_KCAL",
    }:
        raise ValueError("Unexpected V2 methodology adapter coverage.")

    return v2, adapters


def _drop_rebuild_triggers(connection):
    for name in (
        "nutrient_definitions_no_update",
        "nutrient_definitions_no_delete",
        "nutrient_definitions_no_replace",
        "nutrient_values_no_update",
        "nutrient_values_no_delete",
        "nutrient_values_no_late_insert",
        "nutrition_vector_seals_complete",
        "food_retention_profiles_complete",
        "food_retention_values_no_update",
        "food_retention_values_no_delete",
        "food_retention_values_no_replace",
        "food_retention_values_no_late_insert",
    ):
        connection.execute(f"DROP TRIGGER IF EXISTS {name}")


def _recreate_triggers(connection):
    connection.execute(
        """CREATE TRIGGER nutrient_definitions_no_update
        BEFORE UPDATE ON nutrient_definitions
        BEGIN SELECT RAISE(ABORT, 'Снимок нутриентов неизменяем.'); END"""
    )
    connection.execute(
        """CREATE TRIGGER nutrient_definitions_no_delete
        BEFORE DELETE ON nutrient_definitions
        BEGIN SELECT RAISE(ABORT, 'Снимок нутриентов неизменяем.'); END"""
    )
    connection.execute(
        """CREATE TRIGGER nutrient_definitions_no_replace
        BEFORE INSERT ON nutrient_definitions
        WHEN EXISTS(
            SELECT 1 FROM nutrient_definitions
            WHERE registry_version = NEW.registry_version AND code = NEW.code
        )
        BEGIN SELECT RAISE(ABORT, 'Снимок нутриентов неизменяем.'); END"""
    )
    connection.execute(
        """CREATE TRIGGER nutrient_values_no_update
        BEFORE UPDATE ON nutrient_values
        BEGIN SELECT RAISE(ABORT, 'Снимок нутриентов неизменяем.'); END"""
    )
    connection.execute(
        """CREATE TRIGGER nutrient_values_no_delete
        BEFORE DELETE ON nutrient_values
        BEGIN SELECT RAISE(ABORT, 'Снимок нутриентов неизменяем.'); END"""
    )
    connection.execute(
        """CREATE TRIGGER nutrient_values_no_late_insert
        BEFORE INSERT ON nutrient_values
        WHEN EXISTS(
            SELECT 1 FROM nutrition_vector_seals
            WHERE profile_id = NEW.profile_id
        )
        BEGIN SELECT RAISE(ABORT, 'Набор нутриентов профиля уже зафиксирован.'); END"""
    )
    connection.execute(
        """CREATE TRIGGER nutrition_vector_seals_complete
        BEFORE INSERT ON nutrition_vector_seals
        WHEN NEW.value_count != (
            SELECT count(*) FROM nutrient_values
            WHERE profile_id = NEW.profile_id
        )
        OR EXISTS(
            SELECT 1
            FROM nutrient_values v
            LEFT JOIN nutrient_definitions d
              ON d.registry_version = v.registry_version
             AND d.code = v.nutrient_code
            WHERE v.profile_id = NEW.profile_id
              AND (
                  v.registry_version != NEW.registry_version
                  OR d.code IS NULL
              )
        )
        BEGIN SELECT RAISE(ABORT, 'Набор нутриентов не соответствует снимку.'); END"""
    )



def _recreate_retention_triggers(connection):
    connection.execute(
        """CREATE TRIGGER food_retention_profiles_complete
        BEFORE INSERT ON food_retention_profiles
        WHEN NEW.value_count != (
            SELECT count(*) FROM food_retention_values
            WHERE profile_id = NEW.id
        )
        BEGIN SELECT RAISE(ABORT, 'Набор факторов неполон.'); END"""
    )
    connection.execute(
        """CREATE TRIGGER food_retention_values_no_update
        BEFORE UPDATE ON food_retention_values
        BEGIN SELECT RAISE(ABORT, 'Исторический состав неизменяем.'); END"""
    )
    connection.execute(
        """CREATE TRIGGER food_retention_values_no_delete
        BEFORE DELETE ON food_retention_values
        BEGIN SELECT RAISE(ABORT, 'Исторический состав неизменяем.'); END"""
    )
    connection.execute(
        """CREATE TRIGGER food_retention_values_no_replace
        BEFORE INSERT ON food_retention_values
        WHEN EXISTS(
            SELECT 1 FROM food_retention_values
            WHERE profile_id = NEW.profile_id
              AND nutrient_code = NEW.nutrient_code
        )
        BEGIN SELECT RAISE(ABORT, 'Исторический состав неизменяем.'); END"""
    )
    connection.execute(
        """CREATE TRIGGER food_retention_values_no_late_insert
        BEFORE INSERT ON food_retention_values
        WHEN EXISTS(
            SELECT 1 FROM food_retention_profiles
            WHERE id = NEW.profile_id
        )
        BEGIN SELECT RAISE(ABORT, 'Снимок уже зафиксирован.'); END"""
    )


def upgrade(connection):
    v2, adapters = load_contract()
    _drop_rebuild_triggers(connection)

    connection.execute(
        """CREATE TABLE nutrient_definitions_new (
            registry_version TEXT NOT NULL
                REFERENCES nutrient_registry_snapshots(version) ON DELETE RESTRICT,
            code TEXT NOT NULL
                CHECK(code GLOB '[A-Z]*' AND code NOT GLOB '*[^A-Z0-9_]*'),
            display_name_ru TEXT NOT NULL CHECK(length(trim(display_name_ru)) > 0),
            unit TEXT NOT NULL CHECK(unit IN ('kcal', 'g', 'mg', 'µg')),
            definition_json TEXT NOT NULL CHECK(json_valid(definition_json)),
            PRIMARY KEY(registry_version, code)
        )"""
    )
    connection.execute(
        """INSERT INTO nutrient_definitions_new (
            registry_version, code, display_name_ru, unit, definition_json
        )
        SELECT registry_version, code, display_name_ru, unit, definition_json
        FROM nutrient_definitions"""
    )
    connection.execute("DROP TABLE nutrient_definitions")
    connection.execute(
        "ALTER TABLE nutrient_definitions_new RENAME TO nutrient_definitions"
    )

    # PR6 Composition retention snapshots are historical V1 evidence. Their
    # nutrient-code FK must become version-aware at the same migration boundary
    # without changing domain snapshot digests or reinterpreting any factor.
    connection.execute(
        """CREATE TABLE food_retention_values_new (
            profile_id CHAR(32) NOT NULL
                REFERENCES food_retention_profiles(id)
                ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED,
            registry_version TEXT NOT NULL,
            nutrient_code TEXT NOT NULL,
            factor TEXT NOT NULL
                CHECK(typeof(factor) = 'text'
                    AND factor NOT GLOB '*[^0-9.]*'
                    AND factor GLOB '*[0-9]*'
                    AND length(factor) - length(replace(factor, '.', '')) <= 1),
            provenance_json TEXT NOT NULL CHECK(json_valid(provenance_json)),
            PRIMARY KEY(profile_id, nutrient_code),
            FOREIGN KEY(registry_version, nutrient_code)
                REFERENCES nutrient_definitions(registry_version, code)
                ON DELETE RESTRICT
        )"""
    )
    connection.execute(
        """INSERT INTO food_retention_values_new (
            profile_id, registry_version, nutrient_code, factor, provenance_json
        )
        SELECT
            profile_id, ?, nutrient_code, factor, provenance_json
        FROM food_retention_values""",
        (REGISTRY_V1,),
    )
    connection.execute("DROP TABLE food_retention_values")
    connection.execute(
        "ALTER TABLE food_retention_values_new RENAME TO food_retention_values"
    )

    connection.execute(
        """CREATE TABLE nutrient_values_new (
            profile_id CHAR(32) NOT NULL
                REFERENCES nutrition_vector_seals(profile_id)
                ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED,
            registry_version TEXT NOT NULL,
            nutrient_code TEXT NOT NULL,
            amount TEXT NOT NULL
                CHECK(typeof(amount) = 'text' AND length(amount) BETWEEN 1 AND 160
                    AND amount NOT GLOB '*[^0-9.]*' AND amount GLOB '*[0-9]*'
                    AND length(amount) - length(replace(amount, '.', '')) <= 1),
            provenance_json TEXT NOT NULL CHECK(json_valid(provenance_json)),
            PRIMARY KEY(profile_id, nutrient_code),
            FOREIGN KEY(registry_version, nutrient_code)
                REFERENCES nutrient_definitions(registry_version, code)
                ON DELETE RESTRICT
        )"""
    )
    connection.execute(
        """INSERT INTO nutrient_values_new (
            profile_id, registry_version, nutrient_code, amount, provenance_json
        )
        SELECT
            v.profile_id,
            s.registry_version,
            v.nutrient_code,
            v.amount,
            v.provenance_json
        FROM nutrient_values v
        JOIN nutrition_vector_seals s ON s.profile_id = v.profile_id"""
    )
    connection.execute("DROP TABLE nutrient_values")
    connection.execute("ALTER TABLE nutrient_values_new RENAME TO nutrient_values")

    bundle = {"registry": v2, "method_adapters": adapters}
    encoded = canonical_json(bundle)
    connection.execute(
        "INSERT INTO nutrient_registry_snapshots VALUES (?, ?, ?)",
        (
            REGISTRY_V2,
            encoded,
            hashlib.sha256(encoded.encode()).hexdigest(),
        ),
    )
    for definition in v2["entries"]:
        connection.execute(
            """INSERT INTO nutrient_definitions (
                registry_version, code, display_name_ru, unit, definition_json
            ) VALUES (?, ?, ?, ?, ?)""",
            (
                REGISTRY_V2,
                definition["canonical_code"],
                definition["display_name_ru"],
                definition["canonical_unit"],
                canonical_json(definition),
            ),
        )

    _recreate_triggers(connection)
    _recreate_retention_triggers(connection)
