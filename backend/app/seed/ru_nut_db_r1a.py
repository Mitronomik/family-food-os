"""R1-A publication of exact RU-NUT-DB authorities for the Planner-capacity batch."""

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

PACKAGE = REPOSITORY_ROOT / "data/curation/r1a-planner-capacity-dependencies"
PUBLICATION_SHA256 = "f83a8bc7c2ab66e685c8887175ba5daca92b3ac2210fdec892e9da2785ddcd32"
EXPECTED = (
    ("ING-0030", "MARGARINE_MILK_TABLE", "Маргарин молочный столовый", "fats_oils", "CREATE_REVIEWED", 1, "1432", 509, "Маргарин молочный столовый", "0018264d8d0e9a181555e62b34684503b7689b4d1d7fddeb848722a287c97a2a"),
    ("ING-0034", "MILK_PASTEURIZED_3_2", "Молоко пастеризованное 3,2%", "dairy", "CREATE_REVIEWED", 1, "929", 549, "Молоко 3,2% жира", "7d99a5fd87f50f471d61df99788d7aa7fe93db22ec1b5d42533733575069333a"),
    ("ING-0047", "SOUR_CREAM_30", "Сметана 30%", "dairy", "CREATE_REVIEWED", 1, "942", 681, "Сметана 30,0% жира", "d5c99fa5365221ef876168887d98d351278b1948bbb820187297ea1a23c12a79"),
    ("ING-0056", "TVOROG_9", "Творог 9%", "dairy", "CREATE_REVIEWED", 1, "968", 813, "Творог полужирный 9,0% жира", "79b770be30bf853021e929f949333838121d65bf5c45a0f3807b90d4cf6a57cb"),
    ("ING-0097", "YEAST_BAKERS_COMPRESSED", "Дрожжи хлебопекарные прессованные", "staples", "CREATE_REVIEWED", 1, "31", 915, "Дрожжи прессованные (*эргостерин)", "6846bc12256db2d75b5329a14279d8d486c9253d3f3db75bf21a3b95e096a386"),
    ("ING-0025", "CHICKEN_CATEGORY_1_RAW", "Курица 1 категории, сырая", "poultry", "CREATE_REVIEWED", 1, "158", 110, "Куры 1 кат", "cd75d00e6781ad32706ee2d6120aad311ed05258cb4a8223a4d6c8bec379f1b9"),
    ("ING-0019", "POTATO", "Картофель", "vegetables", "REUSE_EXISTING", 1, "46", 77, "Картофель сырой (свежий)", "41f284f935466cf22c03fe32dd64f6ac1083f13e5c331520ca26df63f3179de9"),
    ("ING-0028", "ONION_BULB_FRESH", "Лук репчатый свежий", "vegetables", "CREATE_REVIEWED", 1, "1186", 118, "Лук репчатый свежий", "bfd5673766e9061af643423f8f32206de1d7bd331bed50135e449984efb9b55e"),
    ("ING-0036", "FLOUR_WHEAT_HIGH_GRADE", "Мука пшеничная высшего сорта", "grains", "CREATE_REVIEWED", 1, "82", 132, "Мука пшеничная в/с", "f8712b80e2bd18972bf78374fdb6885c9a64c6a6c32ba08d6fa39ffe61b7b332"),
    ("ING-0006", "WATER", "Вода питьевая", "staples", "REUSE_EXISTING", 2, "3000", 360, "Вода питьевая", "efb9ba629e4310c4d75309f01ffe8f6e9566a1f43f3b4f4e5b0f46470c665945"),
    ("ING-0050", "SALT", "Соль поваренная", "staples", "REUSE_EXISTING", 2, "125", 932, "Соль поваренная пищевая", "b7a6d581126d3e02bdc46f7bdb02c73083c4cf9e52e41b67a1e6f10adcee6bb5"),
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
                    f"r1a:{step4.SOURCE_VERSION}:"
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


def load_ru_nut_db_r1a_bundles(
    package: Path = PACKAGE,
    *,
    mapping_path: Path = step4.MAPPING_PATH,
) -> tuple[ReviewedNutritionPublicationBundle, ...]:
    publication = step4._checked_json(package / "publication.json", PUBLICATION_SHA256)
    mappings_raw = step4._checked_json(mapping_path, step4.MAPPING_SHA256)
    if not isinstance(mappings_raw, list) or len(mappings_raw) != 26:
        raise ValueError("R1-A mapping должен содержать ровно 26 source fields.")
    mappings = tuple(mappings_raw)
    approved = tuple(
        row for row in mappings if row["decision"] == "APPROVED_PUBLISHED_VALUE"
    )
    if len(approved) != 18 or len({row["canonical_code"] for row in approved}) != 18:
        raise ValueError("R1-A mapping должен содержать ровно 18 V2 targets.")

    source = publication.get("source")
    if not isinstance(source, dict) or {
        "archive_sha256": source.get("archive_sha256"),
        "raw_html_sha256": source.get("raw_html_sha256"),
        "source_id": source.get("source_id"),
        "source_name": source.get("source_name"),
        "source_version": source.get("source_version"),
    } != {
        "archive_sha256": step4.ARCHIVE_SHA256,
        "raw_html_sha256": step4.RAW_HTML_SHA256,
        "source_id": step4.SOURCE_ID,
        "source_name": step4.SOURCE_NAME,
        "source_version": step4.SOURCE_VERSION,
    }:
        raise ValueError("R1-A source identity расходится с accepted RU-NUT-DB.")
    if publication.get("mapping_contract", {}).get("sha256") != step4.MAPPING_SHA256:
        raise ValueError("R1-A payload ссылается не на frozen Step 4 mapping.")
    if publication.get("authority") != {
        "attribution": step4.ATTRIBUTION,
        "receipt_path": "docs/family-food/fic-nutrition-license-receipt.md",
    }:
        raise ValueError("R1-A authority receipt или attribution изменены.")

    records = publication.get("records")
    if not isinstance(records, list) or len(records) != len(EXPECTED):
        raise ValueError(f"R1-A должен содержать ровно {len(EXPECTED)} source records.")

    mapping_fields = {row["source_field"] for row in mappings}
    verified_at = datetime.fromisoformat("2026-09-27T00:00:00+00:00")
    bundles = []
    source_zero_count = 0
    source_numeric_count = 0

    for record, expected in zip(records, EXPECTED, strict=True):
        (
            dependency_id,
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
        if record.get("r1_dependency_id") != dependency_id:
            raise ValueError(f"R1-A dependency identity изменена для {code}.")
        if record.get("platform") != {
            "action": action,
            "atomic_version": atomic_version,
            "canonical_code": code,
            "canonical_name": canonical_name,
            "category_code": category,
            "default_unit": "g",
            "mass_state": "INPUT",
        }:
            raise ValueError(f"R1-A platform identity изменена для {code}.")
        if record.get("source") != {
            "db_index": db_index,
            "json_pointer": f"/DB/{db_index}",
            "raw_record_sha256": raw_record_sha256,
            "source_code": source_code,
            "source_name": source_name,
        }:
            raise ValueError(f"R1-A source identity изменена для {code}.")

        nutrients = record.get("nutrients")
        if not isinstance(nutrients, dict) or set(nutrients) != mapping_fields:
            raise ValueError(f"R1-A source fields неполны для {code}.")
        for field, literal in nutrients.items():
            if step4._decimal(literal, field=field) == 0:
                source_zero_count += 1
            else:
                source_numeric_count += 1

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
                            "data/curation/r1a-planner-capacity-dependencies/"
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

    if (source_numeric_count, source_zero_count) != (181, 105):
        raise ValueError("R1-A source-state accounting изменилось.")
    if sum(bundle.vector.value_count for bundle in bundles) != 198:
        raise ValueError("R1-A должен публиковать ровно 198 V2 values.")
    return tuple(bundles)


def seed_ru_nut_db_r1a(
    config: DatabaseConfig | None = None,
    *,
    package: Path = PACKAGE,
    mapping_path: Path = step4.MAPPING_PATH,
) -> NutritionBatchPublicationResult:
    bundles = load_ru_nut_db_r1a_bundles(package, mapping_path=mapping_path)
    engine = create_sqlite_engine(config)
    try:
        return create_nutrition_batch_publication_service(engine).publish_batch(bundles)
    finally:
        engine.dispose()


if __name__ == "__main__":
    result = seed_ru_nut_db_r1a()
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
