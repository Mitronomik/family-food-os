"""Hash-pinned Step 4 publication of five licensed RU-NUT-DB records."""

from datetime import datetime
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
from typing import Any

from app.db.config import DatabaseConfig, REPOSITORY_ROOT
from app.domain.food_composition import CompositionProvenance, MassState
from app.domain.food_ingredients import NutritionObservationState
from app.domain.nutrient_method_adapters import REGISTRY_V2
from app.domain.nutrient_vector import V2_VALUE_EVIDENCE_SCHEMA
from app.domain.nutrient_vector_backfill_v1 import value_set_digest
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
from app.persistence.sqlalchemy_core.nutrition_publication import (
    create_nutrition_batch_publication_service,
)
from app.services.nutrition_publication import (
    NutritionBatchPublicationResult,
    PublicationIngredientAction,
    ReviewedAtomicCompositionSpec,
    ReviewedIngredientSpec,
    ReviewedNutrientValueSpec,
    ReviewedNutrientVectorSpec,
    ReviewedNutritionProfileSpec,
    ReviewedNutritionPublicationBundle,
    ReviewedSourceObservationSpec,
)

PACKAGE = REPOSITORY_ROOT / "data/curation/ru-nut-db-step4-runtime"
MAPPING_PATH = (
    REPOSITORY_ROOT
    / "data/curation/ru-nut-db-step4-semantic-closure/field-mapping.json"
)
PUBLICATION_SHA256 = "b9a45f9fe22eef6afb91f2e230bd76d8074d4db58ab6c4628240f9f7f0fe2074"
MAPPING_SHA256 = "bf77239d5976e5ec03d01f524726f9c2e8afb5fc4d92a884b62aa63dfe3a9477"
ARCHIVE_SHA256 = "c0d90020798b2998e841328b9081f06f8197efda084b852aa8457fd41a5ce8ea"
RAW_HTML_SHA256 = "155107ddb381c14721c77fe995d604a5197982441446b54034e4d84645efbd6d"
SOURCE_NAME = "FIC_RU_NUT_DB"
SOURCE_ID = "RU-NUT-DB"
SOURCE_VERSION = "snapshot-2026-09-20-155107ddb381c147"
SOURCE_DATA_TYPE = "official_electronic_database_snapshot"
SOURCE_URL = (
    "https://ion.ru/nauka/baza-dannykh-khimicheskogo-sostava/"
    "1-1-baza-dannykh/1.1_baza%20dannih.html"
)
ATTRIBUTION = (
    "Данные о химическом составе продуктов предоставлены ФГБУН «ФИЦ питания "
    "и биотехнологии» (база «Химический состав пищевых продуктов, используемых "
    "в Российской Федерации»)."
)
EXPECTED = (
    (
        "SUGAR", "Сахар-песок", "staples", "REUSE_EXISTING", 2,
        "1150", 252, "Сахар-песок",
        "b869ae0c72ffb850d52d303ab1288e3ec539938f4cd73ba8709b049393a3994f",
    ),
    (
        "CARROT_RED_RAW", "Морковь свежая красная", "vegetables",
        "CREATE_REVIEWED", 1, "1187", 126, "Морковь свежая красная",
        "a0587cd2f7cf9b49e586f7b188f9164020af1cbbabd2cb36bcf2bccba7622b8d",
    ),
    (
        "CABBAGE_GREEN", "Капуста белокочанная", "vegetables",
        "REUSE_EXISTING", 2, "1184", 69, "Капуста белокочанная свежая",
        "db34f8dfb25ec1d0289c78b7863cae3e21dac19365f9d6913b5842c00db3a109",
    ),
    (
        "BEET", "Свёкла", "vegetables", "REUSE_EXISTING", 1,
        "1204", 254, "Свекла свежая",
        "c241cffe9f38f562812fba3a42d7cb113c7e7e6da7036f976b8aaca5c3078702",
    ),
    (
        "RICE_GROATS", "Крупа рисовая", "grains", "CREATE_REVIEWED", 1,
        "66", 103, "Крупа рисовая",
        "08d4a8a374095622d5f5a52f4c8b88ce956a0546ab5ebcaf115c4e4437a71c85",
    ),
)
LEGACY_FIELDS = {
    "kcal": "kcal",
    "protein_g": "prot",
    "fat_g": "fat",
    "carbohydrates_g": "carbh",
    "fiber_g": "diet_fibre",
}


def _checked_json(path: Path, digest: str) -> Any:
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != digest:
        raise ValueError(f"Изменён проверенный файл данных: {path.name}.")
    return json.loads(raw)


def _decimal(value: object, *, field: str) -> Decimal:
    if not isinstance(value, str) or not value or value.startswith("-"):
        raise ValueError(f"Поле {field} должно быть исходной Decimal-строкой.")
    try:
        result = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"Поле {field} не является Decimal.") from exc
    if not result.is_finite() or result < 0 or format(result, "f") != value:
        raise ValueError(f"Поле {field} не является канонической Decimal-строкой.")
    return result


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _locator(record: dict[str, Any], field: str) -> str:
    return f"sha256:{RAW_HTML_SHA256}#{record['source']['json_pointer']}/{field}"


def _profile_observations(
    record: dict[str, Any], nutrients: dict[str, str]
) -> tuple[ReviewedSourceObservationSpec, ...]:
    values = []
    for profile_field, source_field in LEGACY_FIELDS.items():
        if profile_field == "carbohydrates_g":
            state = NutritionObservationState.METHOD_INCOMPATIBLE
            method = (
                "ru-nut-db-step4-semantic-closure:"
                "carbh:DEFER_DEFINITION_AMBIGUOUS"
            )
        else:
            state = NutritionObservationState.VALUE
            method = "published_method_unspecified"
        values.append(
            ReviewedSourceObservationSpec(
                source_field=profile_field,
                state=state,
                source_literal=nutrients[source_field],
                method_reference=method,
                source_locator=_locator(record, source_field),
            )
        )
    return tuple(values)


def _evidence(
    record: dict[str, Any],
    mapping: dict[str, Any],
    profile: ReviewedNutritionProfileSpec,
    literal: str,
) -> str:
    field = mapping["source_field"]
    return _canonical_json(
        {
            "schema_version": V2_VALUE_EVIDENCE_SCHEMA,
            "registry_version": REGISTRY_V2,
            "method_code": mapping["method_code"],
            "origin": "SOURCE_COMPONENT_CONFIRMED",
            "observation": {
                "audit_identity": (
                    f"step4:{SOURCE_VERSION}:"
                    f"{record['source']['source_code']}:{field}"
                ),
                "profile_source_name": profile.source_name,
                "profile_source_id": profile.source_id,
                "profile_source_version": profile.source_version,
                "profile_source_data_type": profile.source_data_type,
                "source_component_id": field,
                "source_component_name": mapping["source_label_ru"],
                "source_unit": mapping["source_unit"],
                "source_value": literal,
                "source_observation_id": (
                    f"RU-NUT-DB:{SOURCE_VERSION}:"
                    f"{record['source']['source_code']}:{field}"
                ),
                "source_derivation_id": None,
                "source_locator": _locator(record, field),
                "uncertainty": None,
            },
            "mapping": {
                "canonical_code": mapping["canonical_code"],
                "mapping_status": mapping["mapping_status"],
                "definition_reference": (
                    "data/curation/nutrient-registry-v2/registry.json#"
                    f"{mapping['canonical_code']}"
                ),
            },
        }
    )


def _source_observations(
    record: dict[str, Any],
    mappings: tuple[dict[str, Any], ...],
    nutrients: dict[str, str],
) -> str:
    rows = []
    for mapping in sorted(mappings, key=lambda item: item["source_field"]):
        field = mapping["source_field"]
        amount = _decimal(nutrients[field], field=field)
        approved = mapping["decision"] == "APPROVED_PUBLISHED_VALUE"
        rows.append(
            {
                "origin": (
                    "SOURCE_PUBLISHED_VALUE"
                    if approved
                    else "SOURCE_ONLY_DEFERRED"
                ),
                "observation": {
                    "mapping_decision": mapping["decision"],
                    "method_code": mapping["method_code"] if approved else None,
                    "source_field": field,
                    "source_label_ru": mapping["source_label_ru"],
                    "source_locator": _locator(record, field),
                    "source_state": (
                        "published_zero" if amount == 0 else "published_numeric"
                    ),
                    "source_unit": mapping["source_unit"],
                    "source_value": nutrients[field],
                    "target_nutrient_code": (
                        mapping["canonical_code"] if approved else None
                    ),
                },
            }
        )
    return _canonical_json(rows)


def load_ru_nut_db_step4_bundles(
    package: Path = PACKAGE,
    *,
    mapping_path: Path = MAPPING_PATH,
) -> tuple[ReviewedNutritionPublicationBundle, ...]:
    publication = _checked_json(package / "publication.json", PUBLICATION_SHA256)
    mappings_raw = _checked_json(mapping_path, MAPPING_SHA256)
    if not isinstance(mappings_raw, list) or len(mappings_raw) != 26:
        raise ValueError("Step 4 mapping должен содержать ровно 26 source fields.")
    mappings = tuple(mappings_raw)
    if len({row["source_field"] for row in mappings}) != 26:
        raise ValueError("Step 4 mapping содержит повторный source field.")
    approved = tuple(
        row for row in mappings
        if row["decision"] == "APPROVED_PUBLISHED_VALUE"
    )
    if (
        len(approved) != 18
        or len({row["canonical_code"] for row in approved}) != 18
    ):
        raise ValueError("Step 4 mapping должен содержать ровно 18 V2 targets.")
    for row in approved:
        if (
            row["mapping_status"] not in {"EXACT", "METHOD_SPECIFIC"}
            or row["method_code"] != "published_method_unspecified"
            or row["source_unit"] != row["canonical_unit"]
        ):
            raise ValueError("Approved mapping расходится с frozen Step 4B.")

    if not isinstance(publication, dict) or publication.get("schema_version") != 1:
        raise ValueError("Неизвестный Step 4 publication payload.")
    source = publication.get("source")
    expected_source = {
        "archive_sha256": ARCHIVE_SHA256,
        "basis_grams": "100",
        "captured_date": "2026-09-20",
        "raw_html_sha256": RAW_HTML_SHA256,
        "source_data_type": SOURCE_DATA_TYPE,
        "source_id": SOURCE_ID,
        "source_name": SOURCE_NAME,
        "source_url": SOURCE_URL,
        "source_version": SOURCE_VERSION,
        "verified_at": "2026-09-22T00:00:00Z",
    }
    if source != expected_source:
        raise ValueError("Step 4 source identity расходится с accepted contract.")
    if publication.get("mapping_contract") != {
        "approved_field_count": 18,
        "path": (
            "data/curation/ru-nut-db-step4-semantic-closure/"
            "field-mapping.json"
        ),
        "sha256": MAPPING_SHA256,
        "v2_rows_per_record": 18,
    }:
        raise ValueError("Step 4 payload ссылается не на frozen mapping.")
    if publication.get("authority") != {
        "attribution": ATTRIBUTION,
        "receipt_path": "docs/family-food/fic-nutrition-license-receipt.md",
    }:
        raise ValueError("Step 4 authority receipt или attribution изменены.")

    records = publication.get("records")
    if not isinstance(records, list) or len(records) != 5:
        raise ValueError("Step 4 должен содержать ровно пять source records.")
    verified_at = datetime.fromisoformat("2026-09-22T00:00:00+00:00")
    bundles = []
    zero_count = 0
    nonzero_count = 0
    mapping_fields = {row["source_field"] for row in mappings}

    for record, expected in zip(records, EXPECTED, strict=True):
        (
            code,
            canonical_name,
            category,
            action,
            atomic_version,
            source_code,
            db_index,
            source_name,
            raw_record_sha256,
        ) = expected
        if not isinstance(record, dict):
            raise ValueError("Step 4 source record должен быть объектом.")
        if record.get("platform") != {
            "action": action,
            "atomic_version": atomic_version,
            "canonical_code": code,
            "canonical_name": canonical_name,
            "category_code": category,
            "default_unit": "g",
            "mass_state": "INPUT",
        }:
            raise ValueError(f"Step 4 identity contract изменён для {code}.")
        if record.get("source") != {
            "db_index": db_index,
            "json_pointer": f"/DB/{db_index}",
            "raw_record_sha256": raw_record_sha256,
            "source_code": source_code,
            "source_name": source_name,
        }:
            raise ValueError(f"Step 4 source identity изменена для {code}.")
        nutrients = record.get("nutrients")
        if not isinstance(nutrients, dict) or set(nutrients) != mapping_fields:
            raise ValueError(f"Step 4 source fields неполны для {code}.")
        for field, literal in nutrients.items():
            if _decimal(literal, field=field) == 0:
                zero_count += 1
            else:
                nonzero_count += 1

        profile = ReviewedNutritionProfileSpec(
            basis_grams=Decimal("100"),
            kcal=_decimal(nutrients["kcal"], field="kcal"),
            protein_g=_decimal(nutrients["prot"], field="prot"),
            fat_g=_decimal(nutrients["fat"], field="fat"),
            carbohydrates_g=None,
            fiber_g=_decimal(nutrients["diet_fibre"], field="diet_fibre"),
            source_name=SOURCE_NAME,
            source_id=source_code,
            source_version=SOURCE_VERSION,
            source_data_type=SOURCE_DATA_TYPE,
            verified_at=verified_at,
            estimated=None,
            observations=_profile_observations(record, nutrients),
        )
        values = tuple(
            ReviewedNutrientValueSpec(
                nutrient_code=mapping["canonical_code"],
                amount=_decimal(
                    nutrients[mapping["source_field"]],
                    field=mapping["source_field"],
                ),
                provenance_json=_evidence(
                    record,
                    mapping,
                    profile,
                    nutrients[mapping["source_field"]],
                ),
            )
            for mapping in approved
        )
        rows = tuple(
            {
                "nutrient_code": value.nutrient_code,
                "amount": value.amount,
                "provenance_json": value.provenance_json,
            }
            for value in values
        )
        if len(rows) != 18:
            raise ValueError("Step 4 vector должен содержать ровно 18 значений.")
        bundles.append(
            ReviewedNutritionPublicationBundle(
                ingredient=ReviewedIngredientSpec(
                    action=PublicationIngredientAction(action),
                    canonical_code=code,
                    canonical_name=canonical_name,
                    category_code=category,
                    default_unit="g",
                    density_g_per_ml=None,
                    edible_fraction=None,
                    allergens_reviewed=False,
                    allergen_codes=(),
                    storage_profile_code=None,
                ),
                profile=profile,
                vector=ReviewedNutrientVectorSpec(
                    registry_version=REGISTRY_V2,
                    values=values,
                    observations_json=_source_observations(
                        record, mappings, nutrients
                    ),
                    value_count=18,
                    value_sha256=value_set_digest(rows),
                ),
                atomic_composition=ReviewedAtomicCompositionSpec(
                    version=atomic_version,
                    input_state=MassState.INPUT,
                    provenance=CompositionProvenance(
                        SOURCE_NAME,
                        SOURCE_VERSION,
                        (
                            "data/curation/ru-nut-db-step4-runtime/"
                            f"publication.json#{code}"
                        ),
                        (
                            "data/curation/ru-nut-db-step4-semantic-closure/"
                            "verification-summary.json:"
                            "MAPPING_FROZEN_RUNTIME_READY"
                        ),
                    ),
                ),
            )
        )

    if (nonzero_count, zero_count) != (87, 43):
        raise ValueError("Step 4 source-state accounting изменилось.")
    if sum(bundle.vector.value_count for bundle in bundles) != 90:
        raise ValueError("Step 4 должен публиковать ровно 90 V2 values.")
    return tuple(bundles)


def seed_ru_nut_db_step4(
    config: DatabaseConfig | None = None,
    *,
    package: Path = PACKAGE,
    mapping_path: Path = MAPPING_PATH,
) -> NutritionBatchPublicationResult:
    bundles = load_ru_nut_db_step4_bundles(
        package, mapping_path=mapping_path
    )
    engine = create_sqlite_engine(config)
    try:
        return create_nutrition_batch_publication_service(engine).publish_batch(
            bundles
        )
    finally:
        engine.dispose()


if __name__ == "__main__":
    result = seed_ru_nut_db_step4()
    print(
        json.dumps(
            {
                "bundle_count": len(result.results),
                "bundle_created_count": result.bundle_created_count,
                "ingredient_created_count": result.ingredient_created_count,
                "nutrient_value_count": result.nutrient_value_count,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
