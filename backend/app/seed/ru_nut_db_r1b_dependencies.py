"""R1-B exact FIC V2 dependency closure for EGG and BUTTER_UNSALTED."""

from datetime import datetime
from decimal import Decimal
import json
from pathlib import Path
from typing import Any

from app.db.config import DatabaseConfig, REPOSITORY_ROOT
from app.domain.food_composition import CompositionProvenance, MassState
from app.domain.nutrient_method_adapters import REGISTRY_V2
from app.domain.nutrient_vector import V2_VALUE_EVIDENCE_SCHEMA
from app.domain.nutrient_vector_backfill_v1 import value_set_digest
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
from app.persistence.sqlalchemy_core.nutrition_publication import (
    create_nutrition_batch_publication_service,
)
from app.seed import ru_nut_db_step4 as step4
from app.services.nutrition_publication import (
    NutritionBatchPublicationResult,
    PublicationIngredientAction,
    ReviewedAtomicCompositionSpec,
    ReviewedIngredientSpec,
    ReviewedNutrientValueSpec,
    ReviewedNutrientVectorSpec,
    ReviewedNutritionProfileSpec,
    ReviewedNutritionPublicationBundle,
)

PACKAGE = REPOSITORY_ROOT / "data/curation/r1b-reviewed-recipes"
PUBLICATION_SHA256 = "2837a7dabd6e4a604b02345962853007b8672d33b6bf367edfa4a94b764f038a"
EXPECTED = (
    (
        "EGG",
        "Яйцо куриное целое",
        "eggs",
        "REUSE_EXISTING",
        2,
        "2287",
        316,
        "Яйцо куриное сырое",
        "9c85665d295de25e51d8722ffa6196be6288ee65c2bdc355f108745abfc4e2d1",
    ),
    (
        "BUTTER_UNSALTED",
        "Масло сливочное несолёное",
        "fats_oils",
        "REUSE_EXISTING",
        2,
        "1418",
        534,
        "Масло сливочное несоленое, 82,5%",
        "b36f472a7bac1f31bf8bf6ba8900d1ed6d15c9f4d8f91a8b05138595c457117f",
    ),
)


def _evidence(
    record: dict[str, Any],
    mapping: dict[str, Any],
    profile: ReviewedNutritionProfileSpec,
    literal: str,
) -> str:
    field = mapping["source_field"]
    return json.dumps(
        {
            "schema_version": V2_VALUE_EVIDENCE_SCHEMA,
            "registry_version": REGISTRY_V2,
            "method_code": mapping["method_code"],
            "origin": "SOURCE_COMPONENT_CONFIRMED",
            "observation": {
                "audit_identity": (
                    f"r1b-dep:{step4.SOURCE_VERSION}:"
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
                    f"RU-NUT-DB:{step4.SOURCE_VERSION}:"
                    f"{record['source']['source_code']}:{field}"
                ),
                "source_derivation_id": None,
                "source_locator": (
                    f"sha256:{step4.RAW_HTML_SHA256}"
                    f"#{record['source']['json_pointer']}/{field}"
                ),
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
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def load_ru_nut_db_r1b_dependency_bundles(
    package: Path = PACKAGE,
    *,
    mapping_path: Path = step4.MAPPING_PATH,
) -> tuple[ReviewedNutritionPublicationBundle, ...]:
    publication = step4._checked_json(
        package / "nutrition-dependencies.json", PUBLICATION_SHA256
    )
    mappings_raw = step4._checked_json(mapping_path, step4.MAPPING_SHA256)
    if not isinstance(mappings_raw, list) or len(mappings_raw) != 26:
        raise ValueError("R1-B dependency mapping должен содержать 26 source fields.")
    mappings = tuple(mappings_raw)
    approved = tuple(
        row for row in mappings if row["decision"] == "APPROVED_PUBLISHED_VALUE"
    )
    if len(approved) != 18:
        raise ValueError("R1-B dependency mapping должен содержать 18 V2 targets.")

    if publication.get("schema_version") != 1 or publication.get("operation") != (
        "R1B_V2_DEPENDENCY_CLOSURE"
    ):
        raise ValueError("Неизвестный R1-B dependency publication payload.")

    source = publication.get("source")
    if not isinstance(source, dict) or {
        "archive_sha256": source.get("archive_sha256"),
        "raw_html_sha256": source.get("raw_html_sha256"),
        "source_id": source.get("source_id"),
        "source_name": source.get("source_name"),
        "source_version": source.get("source_version"),
        "source_data_type": source.get("source_data_type"),
    } != {
        "archive_sha256": step4.ARCHIVE_SHA256,
        "raw_html_sha256": step4.RAW_HTML_SHA256,
        "source_id": step4.SOURCE_ID,
        "source_name": step4.SOURCE_NAME,
        "source_version": step4.SOURCE_VERSION,
        "source_data_type": step4.SOURCE_DATA_TYPE,
    }:
        raise ValueError("R1-B dependency source identity расходится с accepted FIC.")

    if publication.get("mapping_contract", {}).get("sha256") != step4.MAPPING_SHA256:
        raise ValueError("R1-B dependency payload использует неверный mapping.")
    if publication.get("authority") != {
        "attribution": step4.ATTRIBUTION,
        "receipt_path": "docs/family-food/fic-nutrition-license-receipt.md",
    }:
        raise ValueError("R1-B dependency authority receipt изменён.")

    records = publication.get("records")
    if not isinstance(records, list) or len(records) != len(EXPECTED):
        raise ValueError("R1-B dependency package должен содержать ровно 2 records.")

    mapping_fields = {row["source_field"] for row in mappings}
    verified_at = datetime.fromisoformat("2026-09-27T00:00:00+00:00")
    bundles = []
    zero_count = 0
    nonzero_count = 0

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
        if record.get("r1b_dependency") != code:
            raise ValueError(f"R1-B dependency identity изменена для {code}.")
        if record.get("platform") != {
            "action": action,
            "atomic_version": atomic_version,
            "canonical_code": code,
            "canonical_name": canonical_name,
            "category_code": category,
            "default_unit": "g",
            "mass_state": "INPUT",
        }:
            raise ValueError(f"R1-B platform identity изменена для {code}.")
        if record.get("source") != {
            "db_index": db_index,
            "json_pointer": f"/DB/{db_index}",
            "raw_record_sha256": raw_record_sha256,
            "source_code": source_code,
            "source_name": source_name,
        }:
            raise ValueError(f"R1-B source identity изменена для {code}.")

        nutrients = record.get("nutrients")
        if not isinstance(nutrients, dict) or set(nutrients) != mapping_fields:
            raise ValueError(f"R1-B source fields неполны для {code}.")
        for field, literal in nutrients.items():
            if step4._decimal(literal, field=field) == 0:
                zero_count += 1
            else:
                nonzero_count += 1

        profile = ReviewedNutritionProfileSpec(
            basis_grams=Decimal("100"),
            kcal=step4._decimal(nutrients["kcal"], field="kcal"),
            protein_g=step4._decimal(nutrients["prot"], field="prot"),
            fat_g=step4._decimal(nutrients["fat"], field="fat"),
            carbohydrates_g=None,
            fiber_g=step4._decimal(nutrients["diet_fibre"], field="diet_fibre"),
            source_name=step4.SOURCE_NAME,
            source_id=source_code,
            source_version=step4.SOURCE_VERSION,
            source_data_type=step4.SOURCE_DATA_TYPE,
            verified_at=verified_at,
            estimated=None,
            observations=step4._profile_observations(record, nutrients),
        )
        values = tuple(
            ReviewedNutrientValueSpec(
                nutrient_code=mapping["canonical_code"],
                amount=step4._decimal(
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
                    observations_json=step4._source_observations(
                        record, mappings, nutrients
                    ),
                    value_count=18,
                    value_sha256=value_set_digest(rows),
                ),
                atomic_composition=ReviewedAtomicCompositionSpec(
                    version=atomic_version,
                    input_state=MassState.INPUT,
                    provenance=CompositionProvenance(
                        step4.SOURCE_NAME,
                        step4.SOURCE_VERSION,
                        (
                            "data/curation/r1b-reviewed-recipes/"
                            f"nutrition-dependencies.json#{code}"
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

    if (nonzero_count, zero_count) != (39, 13):
        raise ValueError("R1-B dependency source-state accounting изменилось.")
    if sum(bundle.vector.value_count for bundle in bundles) != 36:
        raise ValueError("R1-B dependencies должны публиковать ровно 36 V2 values.")
    return tuple(bundles)


def seed_ru_nut_db_r1b_dependencies(
    config: DatabaseConfig | None = None,
    *,
    package: Path = PACKAGE,
) -> NutritionBatchPublicationResult:
    bundles = load_ru_nut_db_r1b_dependency_bundles(package)
    engine = create_sqlite_engine(config)
    try:
        return create_nutrition_batch_publication_service(engine).publish_batch(bundles)
    finally:
        engine.dispose()
