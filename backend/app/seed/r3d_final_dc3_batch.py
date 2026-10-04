"""R3-D final ten-recipe DC3 prepared-output publication batch."""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any
from uuid import UUID

from app.db.config import REPOSITORY_ROOT, DatabaseConfig
from app.db.migrations import apply_migrations
from app.domain.recipe_nutrition_v2 import NUTRIENT_CODES
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
from app.persistence.sqlalchemy_core.food_ingredient_composition import (
    create_food_catalogue_service,
)
from app.persistence.sqlalchemy_core.food_recipe_composition import (
    create_food_recipe_catalogue_service,
)
from app.persistence.sqlalchemy_core.recipe_nutrition_v2 import (
    SqlAlchemyRecipeNutritionV2ReadScope,
    SqlAlchemyRecipeNutritionV2UnitOfWork,
    create_recipe_nutrition_v2_service,
)
from app.seed.r3c_school2022_main_batch import (
    RECIPE_CODES as R3C_RECIPE_CODES,
)
from app.seed.r3c_school2022_main_batch import seed_r3c_school2022_main_batch
from app.services.food_ingredients import (
    FoodIngredientNotFoundError,
    TrustedFoodIngredientIdentitySeed,
)
from app.services.food_recipes import (
    TrustedRecipeIngredientSeed,
    TrustedRecipeSeed,
    TrustedRecipeSeedDisposition,
    TrustedRecipeVersionSeed,
)
from app.services.planner import PlannerService
from app.services.prepared_recipe_activation import activate_prepared_recipe_batch
from app.services.recipe_nutrition_v2 import (
    PreparedPublicationDisposition,
    RecipeNutritionV2ConflictError,
    ReviewedPreparedRecipeNutritionSpec,
)

PACKAGE = REPOSITORY_ROOT / "data/curation/r3d-final-dc3-batch-gate"
FROZEN_BATCH_PATH = PACKAGE / "frozen-batch.json"
SUMMARY_PATH = PACKAGE / "summary.json"
MR_BUNDLE_PATH = (
    REPOSITORY_ROOT / "data/seed/ru_normative_recipe_corpus/mr_2_4_0162_19.bundle.json"
)

FROZEN_BATCH_GIT_BLOB_SHA = "5668323fe8027dcd2cb94c75db8b551cfb525cde"
SUMMARY_GIT_BLOB_SHA = "a9e0316344f236e06fd90579b6cffd2d9bf04604"
MR_BUNDLE_GIT_BLOB_SHA = "9210458b9ad81aa3650eccad7935519f8d375432"

R3D_RUNTIME_ACCEPTED_BASE = "a6c1a0bd203e0ec21fd73eb4107282c2b144ff9a"
R3D_GATE_ACCEPTED_BASE = "1c82f34b960621aed3e1c43780270f8048edfe0f"
MR_SOURCE_NAME = "RU_MR_2_4_0162_19"
MR_SOURCE_VERSION = "2019-12-30"
MR_RAW_BYTES_SHA256 = "973acb53eee7a04c76853dff80988a0f9b70e704495b715639cd8a34a747293e"
MR_RAW_TEXT_SHA256 = "b5a05ffb36d34cd7bd82de71b55319d72ac850064302bf228e1e1ad19fd02062"

RECIPE_CODES = (
    "MR2019_1_2A_VEGETARIAN_CABBAGE_SOUP",
    "MR2019_1_3_LENINGRAD_RASSOLNIK_SOUR_CREAM",
    "MR2019_1_4_OAT_VEGETABLE_SOUP_SOUR_CREAM",
    "MR2019_1_16_POTATO_SPLIT_PEA_SOUP",
    "MR2019_6_9_VERMICELLI_HARD_CHEESE",
    "MR2019_6_19_BAKED_MACARONI_HARD_CHEESE",
    "MR2019_2_15_STEAMED_CHICKEN_SOUFFLE",
    "MR2019_2_14_BOILED_CHICKEN_CATEGORY_1",
    "MR2019_2_11_BEEF_VEGETABLE_RAGOUT",
    "MR2019_2_9_STEAMED_BEEF_ROLL_OMELET",
)
SOURCE_CARD_CODES = ("1.2а", "1.3", "1.4", "1.16", "6.9", "6.19", "2.15", "2.14", "2.11", "2.9")
SOURCE_RECIPE_IDS = tuple(f"APPENDIX_5_CARD_{code}" for code in SOURCE_CARD_CODES)
IDENTITY_ONLY_FOOD_CODES = (
    "VEGETABLE_OIL_REFINED_UNSPECIFIED",
    "CUCUMBER_PICKLED_CANNED",
    "SOUR_CREAM_20",
    "SPLIT_PEAS_DRY",
    "CHEESE_HARD_UNSPECIFIED",
    "CHICKEN_CATEGORY_1_WHOLE_RAW",
    "MILK_3_2",
    "FLOUR_WHEAT_FIRST_GRADE",
    "CHEESE_DUTCH_HARD",
    "BUTTER_PEASANT_72",
)
MILK_FOOD_CODE = "MILK_2_5"
BEEF_FOOD_CODE = "BEEF_CATEGORY_1_RAW"
FISH_FOOD_CODES = frozenset(
    {
        "COD_FILLET_RAW",
        "PINK_SALMON_FILLET_RAW",
        "POLLOCK_FILLET_RAW",
        "ATLANTIC_SALMON_FILLET_RAW",
    }
)
CHICKEN_FOOD_CODES = frozenset(
    {
        "CHICKEN_CATEGORY_2_RAW",
        "CHICKEN_BREAST",
        "CHICKEN_CATEGORY_1_WHOLE_RAW",
    }
)
MILK_UNAFFECTED_BREAKFAST_CODES = (
    "HARD_BOILED_EGG",
    "SCHOOL2022_54_1T_COTTAGE_CHEESE_CASSEROLE",
    "SAD28_SANDWICH_CHEESE_20_10",
)

_ASCII_WORD_RE = re.compile(r"[A-Za-z]{2,}")


@dataclass(frozen=True)
class R3DPublicationResult:
    identity_food_inserted: int
    identity_food_existing: int
    recipe_version_ids: tuple[tuple[str, UUID], ...]
    authority_dispositions: tuple[tuple[str, str], ...]
    exact_energy_kcal: tuple[tuple[str, Decimal], ...]


@dataclass(frozen=True)
class R3DFinalBatchResult:
    publication: R3DPublicationResult
    activation_changed: bool
    active_recipe_codes: tuple[str, ...]


def _git_blob_sha(raw: bytes) -> str:
    header = f"blob {len(raw)}\0".encode()
    return hashlib.sha1(header + raw).hexdigest()


def _checked_json(path: Path, expected_git_blob_sha: str) -> dict[str, Any]:
    raw = path.read_bytes()
    if _git_blob_sha(raw) != expected_git_blob_sha:
        raise ValueError(f"R3-D frozen artifact changed: {path.name}.")
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise TypeError(f"R3-D artifact must be a JSON object: {path.name}.")
    return payload


def _canonical_sha256(value: object) -> str:
    raw = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _decimal(value: object, *, field: str) -> Decimal:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field} must be a canonical Decimal string.")
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field} is not Decimal.") from exc
    if not parsed.is_finite() or parsed <= 0 or format(parsed, "f") != value:
        raise ValueError(f"{field} must be a canonical positive Decimal.")
    return parsed


def _normalize_number(value: object) -> str:
    return str(value).strip().replace(",", ".")


def _parse_mr_12_plus(card: dict[str, Any]) -> tuple[list[tuple[str, str]], str]:
    raw = card["raw_card_text"]
    lines = [line.strip() for line in raw.splitlines() if line.strip()]
    try:
        start = lines.index("12 лет и старше") + 1
        end = lines.index("Выход готовой продукции", start)
    except ValueError as exc:
        raise ValueError(f"R3-D MR table markers missing: {card['source_card_code']}") from exc

    rows: list[tuple[str, str]] = []
    index = start
    while index < end:
        if index + 3 >= end + 1:
            raise ValueError(f"R3-D MR ingredient row truncated: {card['source_card_code']}.")
        label = lines[index]
        values = lines[index + 1 : index + 4]
        if len(values) != 3:
            raise ValueError(f"R3-D MR ingredient quantities missing: {label}.")
        rows.append((label, _normalize_number(values[2])))
        index += 4
    if index != end:
        raise ValueError(f"R3-D MR ingredient table shape changed: {card['source_card_code']}.")

    output_values = lines[end + 1 : end + 4]
    if len(output_values) != 3:
        raise ValueError(f"R3-D MR output row missing: {card['source_card_code']}.")
    return rows, _normalize_number(output_values[2])


def _review_commitment(row: dict[str, Any]) -> str:
    return _canonical_sha256(
        {
            "source_card_raw_sha256": row["source_card_raw_sha256"],
            "source_page_url": row["source_page_url"],
            "source_intermediates": row.get("source_intermediates", []),
            "source_alternative_rows": row.get("source_alternative_rows", []),
            "source_branch_selection": row.get("source_branch_selection"),
            "household_applicability": row["household_applicability"],
            "specialized_medical_scope": row["specialized_medical_scope"],
            "household_rationale": row["household_rationale"],
            "quarantined_source_context": row["quarantined_source_context"],
            "prepared_authority": row["prepared_authority"],
        }
    )


def _validate_mr_source(
    frozen: dict[str, Any],
    *,
    bundle_path: Path,
) -> dict[str, Any]:
    raw = bundle_path.read_bytes()
    if _git_blob_sha(raw) != MR_BUNDLE_GIT_BLOB_SHA:
        raise ValueError("R3-D MR bundle changed.")
    bundle = json.loads(raw)
    if not isinstance(bundle, dict):
        raise TypeError("R3-D MR bundle root changed.")
    document = bundle.get("document")
    cards = bundle.get("cards")
    if not isinstance(document, dict) or not isinstance(cards, list):
        raise TypeError("R3-D MR bundle shape changed.")
    if (
        document.get("source_code") != MR_SOURCE_NAME
        or document.get("source_version") != MR_SOURCE_VERSION
        or document.get("raw_bytes_sha256") != MR_RAW_BYTES_SHA256
        or document.get("raw_text_sha256") != MR_RAW_TEXT_SHA256
        or document.get("publication_policy") != "NORMATIVE_BASE_RECIPE_APPROVED"
    ):
        raise ValueError("R3-D MR document receipt changed.")

    by_key = {
        (card.get("source_section_code"), card.get("source_card_code")): card
        for card in cards
        if isinstance(card, dict)
    }

    for row in frozen["selected"]:
        key = (row["source_section_code"], row["source_card_code"])
        card = by_key.get(key)
        if card is None:
            raise ValueError(f"R3-D selected MR card missing: {key}.")
        raw_card = card.get("raw_card_text")
        if not isinstance(raw_card, str) or not raw_card:
            raise ValueError(f"R3-D raw MR card missing: {key}.")
        if hashlib.sha256(raw_card.encode("utf-8")).hexdigest() != row["source_card_raw_sha256"]:
            raise ValueError(f"R3-D MR card hash mismatch: {key}.")
        if row["source_page_url"] != card.get("source_page_url"):
            raise ValueError(f"R3-D MR card URL mismatch: {key}.")

        source_rows, output = _parse_mr_12_plus(card)
        if output != row["source_output_g"]:
            raise ValueError(f"R3-D MR output mismatch: {key}.")

        ingredient_rows = Counter(
            (
                ingredient["source_label"],
                _normalize_number(ingredient["quantity_g"]),
            )
            for ingredient in row["ingredients"]
        )
        intermediate_rows = Counter(
            (
                item["source_label"],
                _normalize_number(item["quantity_g"]),
            )
            for item in row.get("source_intermediates", [])
        )
        alternative_rows = Counter(
            (
                item["source_label"],
                _normalize_number(item["quantity_g"]),
            )
            for item in row.get("source_alternative_rows", [])
        )
        if Counter(source_rows) != ingredient_rows + intermediate_rows + alternative_rows:
            raise ValueError(f"R3-D MR source→frozen partition mismatch: {key}.")

        branch = row.get("source_branch_selection")
        if branch is not None:
            source_counter = Counter(source_rows)
            selected_counter = Counter(
                (
                    item["source_label"],
                    _normalize_number(item["quantity_g"]),
                )
                for item in branch.get("selected_source_rows", [])
            )
            rejected_counter = Counter(
                (
                    item["source_label"],
                    _normalize_number(item["quantity_g"]),
                )
                for item in branch.get("not_selected_source_rows", [])
            )
            if (
                not selected_counter
                or selected_counter - source_counter
                or rejected_counter - source_counter
                or selected_counter - ingredient_rows
                or rejected_counter - alternative_rows
            ):
                raise ValueError(f"R3-D MR branch row binding mismatch: {key}.")

    return bundle


def _load_contract(
    package: Path = PACKAGE,
    *,
    bundle_path: Path = MR_BUNDLE_PATH,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    frozen = _checked_json(package / FROZEN_BATCH_PATH.name, FROZEN_BATCH_GIT_BLOB_SHA)
    summary = _checked_json(package / SUMMARY_PATH.name, SUMMARY_GIT_BLOB_SHA)

    if (
        frozen.get("schema_version") != 1
        or frozen.get("operation") != "R3D_FINAL_DC3_FROZEN_BATCH_CONTRACT"
        or frozen.get("accepted_base") != R3D_GATE_ACCEPTED_BASE
        or frozen.get("issue") != 157
        or frozen.get("status") != "FROZEN_FOR_GATE_REVIEW"
        or summary.get("schema_version") != 1
        or summary.get("operation") != "R3D_FINAL_DC3_GATE_SUMMARY"
        or summary.get("accepted_base") != R3D_GATE_ACCEPTED_BASE
        or summary.get("issue") != 157
    ):
        raise ValueError("R3-D contract identity changed.")

    source = frozen.get("source")
    selected = frozen.get("selected")
    identities = frozen.get("new_identity_only_foods")
    if not isinstance(source, dict) or not isinstance(selected, list) or not isinstance(identities, list):
        raise TypeError("R3-D contract collections changed.")

    selected_codes = tuple(row.get("canonical_code") for row in selected)
    selected_cards = tuple(row.get("source_card_code") for row in selected)
    if (
        selected_codes != RECIPE_CODES
        or selected_cards != SOURCE_CARD_CODES
        or len(set(selected_codes)) != 10
        or len(set(selected_cards)) != 10
        or summary.get("r3d", {}).get("selected_count") != 10
        or summary.get("r3d", {}).get("selected_meal_types") != {"main": 10}
    ):
        raise ValueError("R3-D selected Recipe set/order changed.")

    identity_codes = tuple(row.get("canonical_code") for row in identities)
    if (
        identity_codes != IDENTITY_ONLY_FOOD_CODES
        or any(
            row.get("nutrition_profile") is not None
            or row.get("nutrient_vector_authority") is not None
            or row.get("composition_authority") is not None
            for row in identities
        )
    ):
        raise ValueError("R3-D identity-only FoodIngredient contract changed.")

    if (
        source.get("source_name") != MR_SOURCE_NAME
        or source.get("source_version") != MR_SOURCE_VERSION
        or source.get("bundle_git_blob_sha") != MR_BUNDLE_GIT_BLOB_SHA
        or source.get("source_document_raw_bytes_sha256") != MR_RAW_BYTES_SHA256
        or source.get("source_document_raw_text_sha256") != MR_RAW_TEXT_SHA256
        or source.get("rights_review_status") != "REVIEWED"
        or source.get("publication_policy") != "NORMATIVE_BASE_RECIPE_APPROVED"
        or not isinstance(source.get("rights_basis"), str)
        or not source["rights_basis"]
    ):
        raise ValueError("R3-D source/provenance contract changed.")

    for row in selected:
        code = row["canonical_code"]
        prepared = row.get("prepared_authority")
        if (
            row.get("meal_type_code") != "main"
            or row.get("source_section_code") != "APPENDIX_5"
            or row.get("source_variant") != "12_PLUS"
            or row.get("household_applicability") != "REVIEWED_PASS"
            or row.get("specialized_medical_scope") is not False
            or not isinstance(row.get("household_rationale"), str)
            or not row["household_rationale"].strip()
            or not isinstance(row.get("quarantined_source_context"), list)
            or not row["quarantined_source_context"]
            or not isinstance(row.get("ingredients"), list)
            or not row["ingredients"]
            or not isinstance(row.get("consumer_steps_ru"), list)
            or not row["consumer_steps_ru"]
            or any(
                not isinstance(step, str)
                or not step.strip()
                or _ASCII_WORD_RE.search(step) is not None
                for step in row["consumer_steps_ru"]
            )
            or not isinstance(prepared, dict)
            or prepared.get("authority_kind") != "PREPARED_OUTPUT_V1"
            or prepared.get("calculation_version")
            != "RECIPE_PREPARED_OUTPUT_NUTRITION_V1"
            or prepared.get("available") != {"ENERGY_KCAL": row.get("energy_kcal")}
            or prepared.get("unknown_policy")
            != "all other frozen nutrient codes UNKNOWN"
            or prepared.get("require_recipe_inactive") is not True
        ):
            raise ValueError(f"R3-D frozen Recipe contract changed: {code}.")

        _decimal(row["source_output_g"], field=f"{code}.source_output_g")
        _decimal(row["energy_kcal"], field=f"{code}.energy_kcal")
        for ingredient in row["ingredients"]:
            if (
                not isinstance(ingredient.get("source_label"), str)
                or not ingredient["source_label"]
                or not isinstance(ingredient.get("food_code"), str)
                or not ingredient["food_code"]
            ):
                raise ValueError(f"R3-D ingredient mapping changed: {code}.")
            _decimal(ingredient["quantity_g"], field=f"{code}.ingredient.quantity_g")

        for intermediate in row.get("source_intermediates", []):
            _decimal(intermediate["quantity_g"], field=f"{code}.intermediate.quantity_g")
            if not isinstance(intermediate.get("semantic_role"), str) or not intermediate["semantic_role"]:
                raise ValueError(f"R3-D intermediate semantic role missing: {code}.")
        for alternative in row.get("source_alternative_rows", []):
            _decimal(alternative["quantity_g"], field=f"{code}.alternative.quantity_g")
            if (
                alternative.get("disposition") != "NOT_SELECTED_ALTERNATIVE"
                or not isinstance(alternative.get("semantic_role"), str)
                or not alternative["semantic_role"]
            ):
                raise ValueError(f"R3-D alternative source row changed: {code}.")

    bundle = _validate_mr_source(frozen, bundle_path=bundle_path)

    current = summary.get("current_repository_truth")
    projected = summary.get("projected_after_future_runtime")
    product_mix = summary.get("r3d", {}).get("product_mix")
    if (
        not isinstance(current, dict)
        or current.get("active_exact_energy_count") != 41
        or current.get("by_meal_type") != {"breakfast": 17, "main": 23, "sandwich": 1}
        or current.get("hard_milk_2_5", {}).get("unaffected_count") != 3
        or current.get("hard_milk_2_5", {}).get("capacity") != 9
        or current.get("main_family_concentration", {}).get("beef_category_1_count") != 12
        or current.get("main_family_concentration", {}).get("fish_based_count") != 9
        or product_mix != {
            "meat_free_main": 6,
            "chicken_main": 2,
            "beef_main": 2,
            "fish_main": 0,
        }
        or not isinstance(projected, dict)
        or projected.get("active_exact_energy_count") != 51
        or projected.get("by_meal_type") != {"breakfast": 17, "main": 33, "sandwich": 1}
        or projected.get("main_family_concentration", {}).get("beef_category_1_count") != 14
        or projected.get("main_family_concentration", {}).get("fish_based_count") != 9
        or projected.get("main_family_concentration", {}).get("chicken_based_count") != 4
        or projected.get("main_family_concentration", {}).get("meat_free_count") != 6
        or projected.get("main_family_concentration", {}).get(
            "unaffected_after_exact_beef_exclusion"
        )
        != 19
        or projected.get("main_family_concentration", {}).get(
            "capacity_after_exact_beef_exclusion"
        )
        != 57
        or projected.get("gap_to_50") != 0
        or projected.get("dc4_next_planned_operation") is not True
    ):
        raise ValueError("R3-D catalogue projection contract changed.")

    transaction = frozen.get("future_runtime_transaction_contract")
    if (
        not isinstance(transaction, dict)
        or transaction.get("architecture")
        != "reuse merged R3-A/R3-B/R3-C option B; no new activation architecture"
    ):
        raise ValueError("R3-D transaction contract changed.")

    return frozen, summary, bundle


def _identity_seeds(
    frozen: dict[str, Any],
) -> tuple[TrustedFoodIngredientIdentitySeed, ...]:
    return tuple(
        TrustedFoodIngredientIdentitySeed(
            canonical_code=row["canonical_code"],
            canonical_name=row["canonical_name"],
            category_code=row["category_code"],
            default_unit=row["default_unit"],
        )
        for row in frozen["new_identity_only_foods"]
    )


def _source_amount_text(ingredient: dict[str, Any]) -> str:
    return f"{ingredient['source_label']}: {ingredient['quantity_g']} г (12 лет и старше)"


def _normalization_note(row: dict[str, Any], ingredient: dict[str, Any]) -> str:
    branch = row.get("source_branch_selection")
    if branch is None:
        return "R3-D exact 12+ source row; reviewed FoodIngredient mapping."
    key = (ingredient["source_label"], ingredient["quantity_g"])
    selected = {
        (item["source_label"], item["quantity_g"])
        for item in branch.get("selected_source_rows", [])
    }
    if key in selected:
        return (
            "R3-D exact 12+ source row; selected branch semantic: "
            f"{branch['selected_semantic_option']}."
        )
    return "R3-D exact 12+ source row; reviewed FoodIngredient mapping."


def _change_note(row: dict[str, Any]) -> str:
    commitment = _review_commitment(row)
    return (
        "R3-D merged Gate #158; household=REVIEWED_PASS; medical=false; "
        f"card_sha256={row['source_card_raw_sha256']}; "
        f"source_partition_sha256={commitment}; card={row['source_card_code']}."
    )


def _recipe_seed(
    row: dict[str, Any],
    source: dict[str, Any],
    document: dict[str, Any],
) -> TrustedRecipeSeed:
    source_id = f"{row['source_section_code']}_CARD_{row['source_card_code']}"
    return TrustedRecipeSeed(
        canonical_code=row["canonical_code"],
        canonical_name=row["canonical_name"],
        initial_is_active=False,
        version=TrustedRecipeVersionSeed(
            base_servings=Decimal(1),
            meal_type_code="main",
            prep_time_minutes=None,
            cook_time_minutes=None,
            total_time_minutes=None,
            difficulty_code=None,
            batch_friendly=None,
            freezable=None,
            storage_days_fridge=None,
            storage_days_freezer=None,
            verification_status="SOURCE_VERIFIED",
            verified_at=datetime(2026, 10, 4, tzinfo=timezone.utc),
            source_name=source["source_name"],
            source_recipe_id=source_id,
            source_url=row["source_page_url"],
            source_version=f"sha256:{source['source_document_raw_bytes_sha256']}",
            source_retrieved_at=datetime.fromisoformat(document["retrieved_at"]),
            source_document_sha256=source["source_document_raw_bytes_sha256"],
            source_original_servings=Decimal(1),
            rights_review_status=source["rights_review_status"],
            rights_basis=source["rights_basis"],
            change_note=_change_note(row),
            ingredients=tuple(
                TrustedRecipeIngredientSeed(
                    food_ingredient_code=ingredient["food_code"],
                    quantity=_decimal(
                        ingredient["quantity_g"],
                        field=f"{row['canonical_code']}.ingredient.quantity_g",
                    ),
                    unit="g",
                    source_amount_text=_source_amount_text(ingredient),
                    normalization_note=_normalization_note(row, ingredient),
                    prep_note=None,
                    optional=False,
                )
                for ingredient in row["ingredients"]
            ),
            steps=tuple(row["consumer_steps_ru"]),
            equipment_codes=(),
            source_output_g=_decimal(
                row["source_output_g"],
                field=f"{row['canonical_code']}.source_output_g",
            ),
            source_output_text=(
                f"Выход готовой продукции: {row['source_output_g']} г; "
                f"MR {row['source_card_code']}, 12 лет и старше."
            ),
        ),
    )


def _prepared_spec(
    row: dict[str, Any],
    source: dict[str, Any],
    seed: TrustedRecipeSeed,
) -> ReviewedPreparedRecipeNutritionSpec:
    return ReviewedPreparedRecipeNutritionSpec(
        trusted_recipe_seed=seed,
        recipe_code=seed.canonical_code,
        source_name=source["source_name"],
        source_recipe_id=seed.version.source_recipe_id,
        source_version=seed.version.source_version,
        source_document_sha256=source["source_document_raw_bytes_sha256"],
        output_mass_g=_decimal(
            row["source_output_g"],
            field=f"{seed.canonical_code}.output_mass_g",
        ),
        source_locator=row["source_page_url"],
        source_data_type="NORMATIVE_RECIPE_CARD_HTML",
        rights_review_status=source["rights_review_status"],
        rights_basis=source["rights_basis"],
        review_reference=(
            "data/curation/r3d-final-dc3-batch-gate/"
            f"frozen-batch.json#selected.{seed.canonical_code}"
        ),
        expected_available_amounts=(
            (
                "ENERGY_KCAL",
                _decimal(
                    row["energy_kcal"],
                    field=f"{seed.canonical_code}.ENERGY_KCAL",
                ),
            ),
        ),
        expected_unknown_codes=tuple(
            code for code in NUTRIENT_CODES if code != "ENERGY_KCAL"
        ),
        require_recipe_inactive=True,
    )


def _recipe_seeds_and_specs(
    frozen: dict[str, Any],
    bundle: dict[str, Any],
) -> tuple[
    tuple[TrustedRecipeSeed, ...],
    tuple[ReviewedPreparedRecipeNutritionSpec, ...],
]:
    source = frozen["source"]
    document = bundle["document"]
    rows = frozen["selected"]
    seeds = tuple(_recipe_seed(row, source, document) for row in rows)
    specs = tuple(
        _prepared_spec(row, source, seed) for row, seed in zip(rows, seeds, strict=True)
    )
    return seeds, specs


def _ensure_prerequisites(config: DatabaseConfig | None) -> None:
    apply_migrations(config)
    engine = create_sqlite_engine(config)
    try:
        catalogue = create_food_recipe_catalogue_service(engine)
        existing_codes = {recipe.canonical_code for recipe in catalogue.list_all()}
    finally:
        engine.dispose()

    present = set(R3C_RECIPE_CODES) & existing_codes
    if not present:
        seed_r3c_school2022_main_batch(config)
        return
    if present != set(R3C_RECIPE_CODES):
        raise RecipeNutritionV2ConflictError(
            "Partial persisted prerequisite R3-C Recipe batch."
        )


def _assert_existing_food_mappings(food, frozen: dict[str, Any]) -> None:
    frozen_codes = {
        ingredient["food_code"]
        for row in frozen["selected"]
        for ingredient in row["ingredients"]
    }
    new_codes = set(IDENTITY_ONLY_FOOD_CODES)
    for code in sorted(frozen_codes - new_codes):
        try:
            food.get_by_code(code)
        except FoodIngredientNotFoundError as exc:
            raise RecipeNutritionV2ConflictError(
                f"R3-D required accepted FoodIngredient missing: {code}."
            ) from exc


def _assert_replay_not_partial(engine, catalogue, nutrition, seed, spec) -> None:
    disposition = catalogue.preflight_trusted_seed(seed)
    if disposition is TrustedRecipeSeedDisposition.FRESH:
        return
    recipe = catalogue.get_by_code(seed.canonical_code)
    detail = catalogue.get_latest_verified(recipe.id)
    with SqlAlchemyRecipeNutritionV2ReadScope(engine) as scope:
        authority = scope.prepared.get_authority(detail.version.id)
        values = scope.prepared.list_values(detail.version.id)
    if authority is None or not values:
        raise RecipeNutritionV2ConflictError(
            f"Partial persisted R3-D state for {seed.canonical_code}."
        )
    replay = nutrition.publish_prepared(spec)
    if replay.disposition is not PreparedPublicationDisposition.EXACT_REPLAY:
        raise RecipeNutritionV2ConflictError(
            f"Expected exact R3-D prepared replay for {seed.canonical_code}."
        )


def publish_r3d_final_dc3_batch(
    config: DatabaseConfig | None = None,
    *,
    package: Path = PACKAGE,
    bundle_path: Path = MR_BUNDLE_PATH,
) -> R3DPublicationResult:
    frozen, _, bundle = _load_contract(package, bundle_path=bundle_path)
    _ensure_prerequisites(config)

    engine = create_sqlite_engine(config)
    try:
        food = create_food_catalogue_service(engine)
        _assert_existing_food_mappings(food, frozen)
        identity_summary = food.reconcile_identity_seed(_identity_seeds(frozen))
        catalogue = create_food_recipe_catalogue_service(engine)
        nutrition = create_recipe_nutrition_v2_service(engine)
        seeds, specs = _recipe_seeds_and_specs(frozen, bundle)

        for seed, spec in zip(seeds, specs, strict=True):
            _assert_replay_not_partial(engine, catalogue, nutrition, seed, spec)

        dispositions: list[tuple[str, str]] = []
        version_ids: list[tuple[str, UUID]] = []
        energies: list[tuple[str, Decimal]] = []

        for seed, spec in zip(seeds, specs, strict=True):
            fresh = (
                catalogue.preflight_trusted_seed(seed)
                is TrustedRecipeSeedDisposition.FRESH
            )
            if fresh:
                with SqlAlchemyRecipeNutritionV2UnitOfWork(engine) as uow:
                    catalogue.reconcile_seed_in_scope(uow, (seed,))
                    published = nutrition.publish_prepared_in_scope(uow, spec)
                    if published.disposition is not PreparedPublicationDisposition.FRESH:
                        raise RecipeNutritionV2ConflictError(
                            f"Fresh R3-D authority was not fresh: {seed.canonical_code}."
                        )
                    projection = nutrition.prepared_consumption_projection_in_scope(
                        uow,
                        published.authority.recipe_version_id,
                    )
                    if (
                        not projection.exact_energy_ready
                        or projection.per_base_serving.kcal is None
                    ):
                        raise RecipeNutritionV2ConflictError(
                            f"R3-D in-scope exact energy unavailable: "
                            f"{seed.canonical_code}."
                        )
                    uow.commit()
            else:
                published = nutrition.publish_prepared(spec)

            recipe = catalogue.get_by_code(seed.canonical_code)
            detail = catalogue.get_latest_verified(recipe.id)
            projection = nutrition.neutral_consumption_projection(detail.version.id)
            if (
                not projection.exact_energy_ready
                or projection.per_base_serving.kcal is None
            ):
                raise RecipeNutritionV2ConflictError(
                    f"R3-D exact energy unavailable: {seed.canonical_code}."
                )
            dispositions.append((seed.canonical_code, published.disposition.value))
            version_ids.append((seed.canonical_code, detail.version.id))
            energies.append((seed.canonical_code, projection.per_base_serving.kcal))

        return R3DPublicationResult(
            identity_food_inserted=identity_summary.ingredients_inserted,
            identity_food_existing=identity_summary.ingredients_existing,
            recipe_version_ids=tuple(version_ids),
            authority_dispositions=tuple(dispositions),
            exact_energy_kcal=tuple(energies),
        )
    finally:
        engine.dispose()


def activate_r3d_final_dc3_batch(
    config: DatabaseConfig | None = None,
    *,
    package: Path = PACKAGE,
    bundle_path: Path = MR_BUNDLE_PATH,
) -> bool:
    frozen, _, bundle = _load_contract(package, bundle_path=bundle_path)
    _ensure_prerequisites(config)

    engine = create_sqlite_engine(config)
    try:
        catalogue = create_food_recipe_catalogue_service(engine)
        nutrition = create_recipe_nutrition_v2_service(engine)
        seeds, specs = _recipe_seeds_and_specs(frozen, bundle)
        planner = PlannerService(
            None,
            None,
            catalogue,
            None,
            None,
            recipe_nutrition=nutrition,  # type: ignore[arg-type]
        )
        result = activate_prepared_recipe_batch(
            catalogue=catalogue,
            nutrition=nutrition,
            planner=planner,
            specs=specs,
        )
        if result.recipe_version_ids != tuple(
            catalogue.get_latest_verified(
                catalogue.get_by_code(seed.canonical_code).id
            ).version.id
            for seed in seeds
        ):
            raise AssertionError("R3-D activation version ordering drifted.")
        return result.activated
    finally:
        engine.dispose()


def seed_r3d_final_dc3_batch(
    config: DatabaseConfig | None = None,
    *,
    package: Path = PACKAGE,
    bundle_path: Path = MR_BUNDLE_PATH,
) -> R3DFinalBatchResult:
    publication = publish_r3d_final_dc3_batch(
        config,
        package=package,
        bundle_path=bundle_path,
    )
    activation_changed = activate_r3d_final_dc3_batch(
        config,
        package=package,
        bundle_path=bundle_path,
    )

    engine = create_sqlite_engine(config)
    try:
        catalogue = create_food_recipe_catalogue_service(engine)
        active_recipe_codes = tuple(
            code for code in RECIPE_CODES if catalogue.get_by_code(code).is_active
        )
        if active_recipe_codes != RECIPE_CODES:
            raise AssertionError("R3-D final active batch does not match frozen set.")
    finally:
        engine.dispose()

    return R3DFinalBatchResult(
        publication=publication,
        activation_changed=activation_changed,
        active_recipe_codes=active_recipe_codes,
    )


if __name__ == "__main__":
    result = seed_r3d_final_dc3_batch()
    print(
        json.dumps(
            {
                "identity_food_inserted": result.publication.identity_food_inserted,
                "identity_food_existing": result.publication.identity_food_existing,
                "recipe_version_ids": [
                    [code, str(version_id)]
                    for code, version_id in result.publication.recipe_version_ids
                ],
                "authority_dispositions": list(
                    result.publication.authority_dispositions
                ),
                "active_recipe_codes": list(result.active_recipe_codes),
                "activation_changed": result.activation_changed,
                "exact_energy_kcal": [
                    [code, format(value, "f")]
                    for code, value in result.publication.exact_energy_kcal
                ],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
