"""Hash-pinned Step 8 publication of one licensed RU-NUT-DB butter record."""

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

PACKAGE = REPOSITORY_ROOT / "data/curation/ru-nut-db-step8-butter-runtime"
MAPPING_PATH = (
    REPOSITORY_ROOT
    / "data/curation/ru-nut-db-step4-semantic-closure/field-mapping.json"
)
PUBLICATION_SHA256 = "7a9c1ff26fe9accdb1ab22dcb8ee60e9310c8ca5e77a3e2b27dd79c4df98b5bd"
MAPPING_SHA256 = "bf77239d5976e5ec03d01f524726f9c2e8afb5fc4d92a884b62aa63dfe3a9477"
ARCHIVE_SHA256 = "c0d90020798b2998e841328b9081f06f8197efda084b852aa8457fd41a5ce8ea"
ARCHIVE_SIZE_BYTES = 206692075
SCHOOL_PDF_SHA256 = "c9264cf521ae699fb30a964d5668caec8f31ff1efc1f13a3dd055df40ebafb5d"
RAW_HTML_SHA256 = "155107ddb381c14721c77fe995d604a5197982441446b54034e4d84645efbd6d"
RAW_RECORD_SHA256 = "b21345dd5ffa8b1348931808067b116940a252abec6c26b01870c192829a711d"
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
FOOD_CODE = "BUTTER_PEASANT_72_5_UNSALTED"
SOURCE_CODE = "1417"
DB_INDEX = 533
EXPECTED_V2_VALUE_COUNT = 17
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
    record: dict[str, Any], nutrients: dict[str, object]
) -> tuple[ReviewedSourceObservationSpec, ...]:
    values = []
    for profile_field, source_field in LEGACY_FIELDS.items():
        literal = nutrients[source_field]
        if not isinstance(literal, str):
            raise ValueError(f"Legacy profile field {source_field} must be numeric.")
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
                source_literal=literal,
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
                    f"step8:{SOURCE_VERSION}:{SOURCE_CODE}:{field}"
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
                    f"RU-NUT-DB:{SOURCE_VERSION}:{SOURCE_CODE}:{field}"
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
    nutrients: dict[str, object],
) -> str:
    rows = []
    for mapping in sorted(mappings, key=lambda item: item["source_field"]):
        field = mapping["source_field"]
        literal = nutrients[field]
        approved = mapping["decision"] == "APPROVED_PUBLISHED_VALUE"
        if literal is None:
            source_state = "not_reported"
            origin = "SOURCE_NOT_REPORTED"
        else:
            amount = _decimal(literal, field=field)
            source_state = "published_zero" if amount == 0 else "published_numeric"
            origin = "SOURCE_PUBLISHED_VALUE" if approved else "SOURCE_ONLY_DEFERRED"
        observation = {
            "mapping_decision": mapping["decision"],
            "method_code": mapping["method_code"] if approved else None,
            "source_field": field,
            "source_label_ru": mapping["source_label_ru"],
            "source_locator": _locator(record, field),
            "source_state": source_state,
            "source_unit": mapping["source_unit"],
            "source_value": literal,
            "target_nutrient_code": mapping["canonical_code"] if approved else None,
        }
        if field == "salt_ad":
            observation["form_compatibility_role"] = "NO_ADDED_SALT_EVIDENCE"
        rows.append({"origin": origin, "observation": observation})
    return _canonical_json(rows)


def load_ru_nut_db_step8_butter_bundle(
    package: Path = PACKAGE,
    *,
    mapping_path: Path = MAPPING_PATH,
) -> ReviewedNutritionPublicationBundle:
    publication = _checked_json(package / "publication.json", PUBLICATION_SHA256)
    mappings_raw = _checked_json(mapping_path, MAPPING_SHA256)
    if not isinstance(mappings_raw, list) or len(mappings_raw) != 26:
        raise ValueError("Step 8 mapping должен содержать ровно 26 source fields.")
    mappings = tuple(mappings_raw)
    if len({row["source_field"] for row in mappings}) != 26:
        raise ValueError("Step 8 mapping содержит повторный source field.")
    approved = tuple(
        row for row in mappings if row["decision"] == "APPROVED_PUBLISHED_VALUE"
    )
    if len(approved) != 18 or len({row["canonical_code"] for row in approved}) != 18:
        raise ValueError("Step 8 mapping должен содержать ровно 18 approved targets.")
    for row in approved:
        if (
            row["mapping_status"] not in {"EXACT", "METHOD_SPECIFIC"}
            or row["method_code"] != "published_method_unspecified"
            or row["source_unit"] != row["canonical_unit"]
        ):
            raise ValueError("Approved mapping расходится с frozen Step 4B.")

    if not isinstance(publication, dict) or publication.get("schema_version") != 1:
        raise ValueError("Неизвестный Step 8 publication payload.")
    if publication.get("source") != {
        "archive_sha256": ARCHIVE_SHA256,
        "archive_size_bytes": ARCHIVE_SIZE_BYTES,
        "basis_grams": "100",
        "captured_date": "2026-09-20",
        "raw_html_sha256": RAW_HTML_SHA256,
        "source_data_type": SOURCE_DATA_TYPE,
        "source_id": SOURCE_ID,
        "source_name": SOURCE_NAME,
        "source_url": SOURCE_URL,
        "source_version": SOURCE_VERSION,
        "verified_at": "2026-09-24T00:00:00Z",
    }:
        raise ValueError("Step 8 source identity расходится с merged contract.")
    if publication.get("authority") != {
        "attribution": ATTRIBUTION,
        "receipt_path": "docs/family-food/fic-nutrition-license-receipt.md",
    }:
        raise ValueError("Step 8 authority receipt или attribution изменены.")
    if publication.get("mapping_contract") != {
        "approved_field_count": 18,
        "expected_v2_value_count": EXPECTED_V2_VALUE_COUNT,
        "missing_approved_source_field": "water",
        "path": (
            "data/curation/ru-nut-db-step4-semantic-closure/field-mapping.json"
        ),
        "sha256": MAPPING_SHA256,
    }:
        raise ValueError("Step 8 payload ссылается не на frozen mapping.")
    if publication.get("recipe_dependency") != {
        "gross_mass_g": "10",
        "net_mass_g": "10",
        "pdf_page": 18,
        "recipe_id": "ru-school2022:recipe:53-19з",
        "school_pdf_sha256": SCHOOL_PDF_SHA256,
        "scope": "7–11 years institutional school catering",
        "source_id": "ru-school2022",
        "source_recipe_code": "53-19з",
        "thermal_treatment": "none",
        "title": "Масло сливочное (порциями)",
    }:
        raise ValueError("Step 8 recipe dependency изменён.")
    if publication.get("form_binding") != {
        "accepted_role": "NO_ADDED_SALT_FORM_COMPATIBILITY_ONLY",
        "fat_percent": "72.5",
        "fic_source_field": "salt_ad",
        "fic_source_label": "Добавленная соль",
        "fic_source_literal": "0.0",
        "school_requires_unsalted": True,
        "semantic_disposition": "SOURCE_ONLY_NO_V2_TARGET",
        "sodium_inference_forbidden": True,
    }:
        raise ValueError("Step 8 unsalted form binding изменён.")

    record = publication.get("record")
    if not isinstance(record, dict):
        raise ValueError("Step 8 source record должен быть объектом.")
    if record.get("platform") != {
        "action": "CREATE_REVIEWED",
        "allergen_codes": [],
        "allergens_reviewed": False,
        "atomic_version": 1,
        "canonical_code": FOOD_CODE,
        "canonical_name": "Масло сливочное крестьянское 72,5% несолёное",
        "category_code": "fats_oils",
        "default_unit": "g",
        "density_g_per_ml": None,
        "edible_fraction": None,
        "mass_state": "INPUT",
        "storage_profile_code": None,
    }:
        raise ValueError("Step 8 FoodIngredient identity изменена.")
    if record.get("source") != {
        "db_index": DB_INDEX,
        "json_pointer": "/DB/533",
        "raw_record_sha256": RAW_RECORD_SHA256,
        "source_code": SOURCE_CODE,
        "source_name": "Масло сливочное крестьянское, 72,5%",
    }:
        raise ValueError("Step 8 FIC source identity изменена.")
    nutrients = record.get("nutrients")
    mapping_fields = {row["source_field"] for row in mappings}
    if not isinstance(nutrients, dict) or set(nutrients) != mapping_fields:
        raise ValueError("Step 8 source fields неполны или изменены.")
    if nutrients.get("salt_ad") != "0.0":
        raise ValueError("Step 8 unsalted binding требует exact salt_ad=0.0.")
    if nutrients.get("water") is not None:
        raise ValueError("Step 8 WATER должен оставаться source-not-reported.")

    numeric_count = 0
    null_count = 0
    for field, literal in nutrients.items():
        if literal is None:
            null_count += 1
        else:
            _decimal(literal, field=field)
            numeric_count += 1
    if (numeric_count, null_count) != (25, 1):
        raise ValueError("Step 8 source-state accounting изменилось.")

    verified_at = datetime.fromisoformat("2026-09-24T00:00:00+00:00")
    profile = ReviewedNutritionProfileSpec(
        basis_grams=Decimal("100"),
        kcal=_decimal(nutrients["kcal"], field="kcal"),
        protein_g=_decimal(nutrients["prot"], field="prot"),
        fat_g=_decimal(nutrients["fat"], field="fat"),
        carbohydrates_g=None,
        fiber_g=_decimal(nutrients["diet_fibre"], field="diet_fibre"),
        source_name=SOURCE_NAME,
        source_id=SOURCE_CODE,
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
        if nutrients[mapping["source_field"]] is not None
    )
    rows = tuple(
        {
            "nutrient_code": value.nutrient_code,
            "amount": value.amount,
            "provenance_json": value.provenance_json,
        }
        for value in values
    )
    if len(rows) != EXPECTED_V2_VALUE_COUNT or any(
        row["nutrient_code"] == "WATER" for row in rows
    ):
        raise ValueError("Step 8 vector должен содержать 17 values без WATER.")

    return ReviewedNutritionPublicationBundle(
        ingredient=ReviewedIngredientSpec(
            action=PublicationIngredientAction.CREATE_REVIEWED,
            canonical_code=FOOD_CODE,
            canonical_name="Масло сливочное крестьянское 72,5% несолёное",
            category_code="fats_oils",
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
            observations_json=_source_observations(record, mappings, nutrients),
            value_count=EXPECTED_V2_VALUE_COUNT,
            value_sha256=value_set_digest(rows),
        ),
        atomic_composition=ReviewedAtomicCompositionSpec(
            version=1,
            input_state=MassState.INPUT,
            provenance=CompositionProvenance(
                SOURCE_NAME,
                SOURCE_VERSION,
                (
                    "data/curation/ru-nut-db-step8-butter-runtime/"
                    f"publication.json#{FOOD_CODE}"
                ),
                "docs/family-food/recipe-dependency-food-batch-contract.md",
            ),
        ),
    )


def seed_ru_nut_db_step8_butter(
    config: DatabaseConfig | None = None,
    *,
    package: Path = PACKAGE,
    mapping_path: Path = MAPPING_PATH,
) -> NutritionBatchPublicationResult:
    bundle = load_ru_nut_db_step8_butter_bundle(package, mapping_path=mapping_path)
    engine = create_sqlite_engine(config)
    try:
        return create_nutrition_batch_publication_service(engine).publish_batch(
            (bundle,)
        )
    finally:
        engine.dispose()


if __name__ == "__main__":
    result = seed_ru_nut_db_step8_butter()
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
