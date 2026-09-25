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
    "–î–∞–Ω–Ω—ã–µ –æ —Ö–∏–º–∏—á–µ—Å–∫–æ–º —Å–æ—Å—Ç–∞–≤–µ –ø—Ä–æ–¥—É–∫—Ç–æ–≤ –ø—Ä–µ–¥–æ—Å—Ç–∞–≤–ª–µ–Ω—ã –§–ì–ë–£–ù ¬´–§–ò–¶ –ø–∏—Ç–∞–Ω–∏—è "
    "–∏ –±–∏–æ—Ç–µ—Ö–Ω–æ–ª–æ–≥–∏–∏¬ª (–±–∞–∑–∞ ¬´–•–∏–º–∏—á–µ—Å–∫–∏–π —Å–æ—Å—Ç–∞–≤ –ø–∏—â–µ–≤—ã—Ö –ø—Ä–æ–¥—É–∫—Ç–æ–≤, –∏—Å–ø–æ–ª—å–∑—É–µ–º—ã—Ö "
    "–≤ –†–æ—Å—Å–∏–π—Å–∫–æ–π –§–µ–¥–µ—Ä–∞—Ü–∏–∏¬ª)."
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
        raise ValueError(f"–ò–∑–º–µ–Ω—ë–Ω –ø—Ä–æ–≤–µ—Ä–µ–Ω–Ω—ã–π —Ñ–∞–π–ª –¥–∞–Ω–Ω—ã—Ö: {path.name}.")
    return json.loads(raw)


def _decimal(value: object, *, field: str) -> Decimal:
    if not isinstance(value, str) or not value or value.startswith("-"):
        raise ValueError(f"–ü–æ–ª–µ {field} –¥–æ–ª–∂–Ω–æ –±—ã—Ç—å –∏—Å—Ö–æ–¥–Ω–æ–π Decimal-—Å—Ç—Ä–æ–∫–æ–π.")
    try:
        result = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"–ü–æ–ª–µ {field} –Ω–µ —è–≤–ª—è–µ—Ç—Å—è Decimal.") from exc
    if not result.is_finite() or result < 0 or format(result, "f") != value:
        raise ValueError(f"–ü–æ–ª–µ {field} –Ω–µ —è–≤–ª—è–µ—Ç—Å—è –∫–∞–Ω–æ–Ω–∏—á–µ—Å–∫–æ–π Decimal-—Å—Ç—Ä–æ–∫–æ–π.")
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
    mappings_raw = _checked_json(X\[ô◊‹]PTSë◊‘“LçMäBàYàõ›\⁄[ú›[òŸJX\[ô‹◊‹ò]À\›
H‹à[äX\[ô‹◊‹ò] HOHçéÇàòZ\ŸHò[YQ\úõ‹äî›\X\[ô»4-4/¥.Ù-¥-t/H4`t/¥-4-t`4-¥,4`¥c4`4/¥,¥/t/àçà€›\òŸHöY[ÀàäBàX\[ô‹»H\JX\[ô‹◊‹ò] BàYà[ä‹õ›÷»ú€›\òŸWŸöY[óHõ‹àõ›»[àX\[ô‹ﬂJHOHçéÇàòZ\ŸHò[YQ\úõ‹äî›\X\[ô»4`t/¥-4-t`4-¥.4`à4/Ù/¥,¥`¥/¥`4/tbÙ.H€›\òŸHöY[àäBà\õ›ôYH\Jàõ›»õ‹àõ›»[àX\[ô‹»Yàõ›÷»ôX⁄\⁄[€àóHOHêTì’ëQ‘PìT“Q’êSQHÇà
BàYà[ä\õ›ôY
HOHN‹à[ä‹õ›÷»òÿ[õ€öXÿ[ÿ€ŸHóHõ‹àõ›»[à\õ›ôYJHOHNÇàòZ\ŸHò[YQ\úõ‹äî›\X\[ô»4-4/¥.Ù-¥-t/H4`t/¥-4-t`4-¥,4`¥c4`4/¥,¥/t/àN\õ›ôY\ôŸ]ÀàäBàõ‹àõ›»[à\õ›ôYÇàYà
àõ›÷»õX\[ô◊‹›]\»óHõ›[à»ëVP’ãìQU—‘‘P“QíP»üBà‹àõ›÷»õY]Ÿÿ€ŸHóHOHúXõ\⁄Y€Y]Ÿ›[ú‹X⁄YöYYÇà‹àõ›÷»ú€›\òŸW›[ö]óHOHõ›÷»òÿ[õ€öXÿ[›[ö]óBà
NÇàòZ\ŸHò[YQ\úõ‹äê\õ›ôYX\[ô»4`4,4`tat/¥-4.4`¥`tc»4`túõﬁô[à›\ãàäBÇàYàõ›\⁄[ú›[òŸJXõXÿ][€ãX›
H‹àXõXÿ][€ãôŸ]
úÿ⁄[XW›ô\ú⁄[€àäHOHNÇàòZ\ŸHò[YQ\úõ‹ä¥'t-t.4-Ù,¥-t`t`¥/tbÙ.H›\XõXÿ][€à^[ÿYàäBàYàXõXÿ][€ãôŸ]
ú€›\òŸHäHOH¬àò\ò⁄]ôW‹⁄LçMàéàTê“UëW‘“LçMãàò\ò⁄]ôW‹⁄^ôWÿû]\»éàTê“UëW‘“VëW–ñUTÀàòò\⁄\◊Ÿ‹ò[\»éàåLãàòÿ\\ôYŸ]HéàååçãLKLåãàúò]◊⁄[‹⁄LçMàéàêU◊“S‘“LçMãàú€›\òŸWŸ]W›\Héà”’Tê—W—UW’TKàú€›\òŸW⁄Yéà”’Tê—W“Qàú€›\òŸW€ò[YHéà”’Tê—W”êSQKàú€›\òŸW›\õéà”’Tê—W’Tìàú€›\òŸW›ô\ú⁄[€àéà”’Tê—W’ëTî“S”ãàùô\öYöYYÿ]éàååçãLKLçååàãàNÇàòZ\ŸHò[YQ\úõ‹äî›\€›\òŸHY[ù]H4`4,4`tat/¥-4.4`¥`tc»4`HY\ôŸY€€ùòX›àäBàYàXõXÿ][€ãôŸ]
ò]]‹ö]HäHOH¬àò]öXù][€àéàUíPïUS”ãàúôXŸZ\‹]éàôÿ‹ÀŸò[Z[KYõ€ŸŸöXÀ[ù]ö][€ã[XŸ[úŸK\ôXŸZ\õYãàNÇàòZ\ŸHò[YQ\úõ‹äî›\]]‹ö]HôXŸZ\4.4.Ù. attribution –∏–∑–º–µ–Ω–µ–Ω—ã.")
    if publication.get("mapping_contract") != {
        "approved_field_count": 18,
        "expected_v2_value_count": EXPECTED_V2_VALUE_COUNT,
        "missing_approved_source_field": "water",
        "path": (
            "data/curation/ru-nut-db-step4-semantic-closure/field-mapping.json"
        ),
        "sha256": MAPPING_SHA256,
    }:
        raise ValueError("Step 8 payload —Å—Å—ã–ª–∞–µ—Ç—Å—è —Å–µ –Ω–∞ frozen mapping.")
    if publication.get("recipe_dependency") != {
        "gross_mass_g": "10",
        "net_mass_g": "10",
        "pdf_page": 18,
        "recipe_id": "ru-school2022:recipe:53-19–∑",
        "school_pdf_sha256": SCHOOL_PDF_SHA256,
        "scope": "7‚Äì11 years institutional school catering",
        "source_id": "ru-school2022",
        "source_recipe_code": "53-19–∑",
        "thermal_treatment": "none",
        "title": "–ú–∞—Å–ª–æ —Å–ª–∏–≤–æ—á–Ω–æ–µ (–ø–æ—Ä—Ü–∏—è–º–∏)",
    }:
        raise ValueError("Step 8 recipe dependency –∏–∑–º–µ–Ω—ë–Ω.")
    if publication.get("form_binding") != {
        "accepted_role": "NO_ADDED_SALT_FORM_COMPATIBILITY_ONLY",
        "fat_percent": "72.5",
        "fic_source_field": "salt_ad",
        "fic_source_label": "–î–æ–±–∞–≤–ª–µ–Ω–Ω–∞—è —Å–æ–ª—å",
        "fic_source_literal": "0.0",
        "school_requires_unsalted": True,
        "semantic_disposition": "SOURCE_ONLY_NO_V2_TARGET",
        "sodium_inference_forbidden": True,
    }:
        raise ValueError("Step 8 unsalted form binding –∏–∑–º–µ–Ω–µ–Ω.")

    record = publication.get("record")
    if not isinstance(record, dict):
        raise ValueError("Step 8 source record –¥–æ–ª–∂–µ–Ω –±—ã—Ç—å –æ–±—ä–µ–∫—Ç–æ–º.")
    if record.get("platform") != {
        "action": "CREATE_REVIEWED",
        "allergen_codes": [],
        "allergens_reviewed": False,
        "atomic_version": 1,
        "canonical_code": FOOD_CODE,
        "canonical_name": "–ú–∞—Å–ª–æ —Å–ª–∏–≤–æ—á–Ω–æ–µ –∫—Ä–µ—Å—Ç—å—è–Ω—Å–∫–æ–µ 72,5% –Ω–µ—Å–æ–ª—ë–Ω–æ–µ",
        "category_code": "fats_oils",
        "default_unit": "g",
        "density_g_per_ml": None,
        "edible_fraction": None,
        "mass_state": "INPUT",
        "storage_profile_code": None,
    }:
        raise ValueError("Step 8 FoodIngredient identity –∏–∑–º–µ–Ω–µ–Ω–∞.")
    if record.get("source") != {
        "db_index": DB_INDEX,
        "json_pointer": "/DB/533",
        "raw_record_sha256": RAW_RECORD_SHA256,
        "source_code": SOURCE_CODE,
        "source_name": "–ú–∞—Å–ª–æ —Å–ª–∏–≤–æ—á–Ω–æ–µ –∫—Ä–µ—Å—Ç—å—è–Ω—Å–∫–æ–µ, 72,5%",
    }:
        raise ValueError("Step 8 FIC source identity –∏–∑–º–µ–Ω–µ–Ω–∞.")
    nutrients = record.get("nutrients")
    mapping_fields = {row["source_field"] for row in mappings}
    if not isinstance(nutrients, dict) or set(nutrients) != mapping_fields:
        raise ValueError("Step 8 source fields –Ω–µ–ø–æ–ª–Ω—ã –∏–ª–∏ –∏–∑–º–µ–Ω–µ–Ω—ã.")
    if nutrients.get("salt_ad") != "0.0":
        raise ValueError("Step 8 unsalted binding —Ç—Ä–µ–±—É–µ—Ç exact salt_ad=0.0.")
    if nutrients.get("water") is not None:
        raise ValueError("Step 8 WATER –¥–æ–ª–∂–µ–Ω –æ—Å—Ç–∞–≤–∞—Ç—å—Å—è source-not-reported.")

    numeric_count = 0
    null_count = 0
    for field, literal in nutrients.items():
        if literal is None:
            null_count += 1
        else:
            _decimal(literal, field=field)
            numeric_count += 1
    if (numeric_count, null_count) != (25, 1):
        raise ValueError("Step 8 source-state accounting –∏–∑–º–µ–Ω–∏–ª–æ—Å—å.")

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
        raise ValueError("Step 8 vector –¥–æ–ª–∂–µ–Ω —Å–æ–¥–µ—Ä–∂–∞—Ç—å 17 values –±–µ–∑ WATER.")

    return ReviewedNutritionPublicationBundle(
        ingredient=ReviewedIngredientSpec(
            action=PublicationIngredientAction.CREATE_REVIEWED,
            canonical_code=FOOD_CODE,
            canonical_name="–ú–∞—Å–ª–æ —Å–ª–∏–≤–æ—á–Ω–æ–µ –∫—Ä–µ—Å—Ç—å—è–Ω—Å–∫–æ–µ 72,5% –Ω–µ—Å–æ–ª—ë–Ω–æ–µ",
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
