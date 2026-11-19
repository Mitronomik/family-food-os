"""Reconcile one real School2022 54-2м source-card transcription with R1-G.

Bounded RESEARCH ONLY. This does not fetch/re-hash the original PDF, change
RecipeVersions, infer a household Serving, grant a SECOND role or authorize Prep.
Original PDF numerical facts are in the separate human-auditable witness JSON.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = (
    ROOT
    / "data/curation/r1g-catalogue-capacity-expansion/prepared-publication-specs.json"
)
WITNESS = (
    ROOT
    / "data/curation/school2022-goulash-primary-crosscheck/source-card-text-witness.json"
)
RECIPE_CODE = "SCHOOL2022_54_2M_BEEF_GOULASH"
EXPECTED_MANIFEST_GIT_BLOB_SHA = "394b35d3d02c0498a681584a37d36b1d98faf40d"
REPORT_SCHEMA = "SCHOOL2022_GOULASH_SOURCE_CROSSCHECK_V1"
BLOCKED = "NOT_APPROVED_FOR_FAMILY_MULTI_COURSE_USE"


class SourceCrosscheckBlocked(ValueError):
    """Pinned source evidence is contradictory or incomplete; no success receipt."""


def _require(condition: bool, reason: str) -> None:
    if not condition:
        raise SourceCrosscheckBlocked(reason)


def _amount(value: object, field: str) -> Decimal:
    _require(isinstance(value, str), f"{field}: требуется строка с точным числом.")
    try:
        result = Decimal(value)
    except InvalidOperation as exc:
        raise SourceCrosscheckBlocked(f"{field}: число отсутствует.") from exc
    _require(result.is_finite() and result >= 0, f"{field}: некорректная масса.")
    return result


def _blob_sha(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()


def load_sources(
    *, manifest_path: Path = MANIFEST, witness_path: Path = WITNESS
) -> tuple[dict, dict]:
    raw = Path(manifest_path).read_bytes()
    _require(
        _blob_sha(raw) == EXPECTED_MANIFEST_GIT_BLOB_SHA,
        "Неверный Git blob опубликованного R1-G source manifest.",
    )
    manifest = json.loads(raw)
    witness = json.loads(Path(witness_path).read_text(encoding="utf-8"))
    return manifest, witness


def crosscheck(*, manifest: dict, witness: dict) -> dict:
    """Check exact source card facts against the existing frozen publication."""
    _require(
        witness.get("schema") == "SCHOOL2022_PRIMARY_CARD_TEXT_WITNESS_V1",
        "Неподдерживаемая версия текстового свидетельства.",
    )
    _require(
        witness.get("status") == "RESEARCH_ONLY_TEXT_TRANSCRIPTION_NOT_A_FRESH_BINARY_HASH",
        "Текстовое свидетельство ошибочно представлено как авторитетный источник.",
    )
    publication = witness["publication_context"]
    source = witness["recipe"]
    limits = witness["interpretation_limits"]
    _require(
        publication["card_identifier"] == "54-2м"
        and publication["edition_year"] == 2022
        and publication["printed_page"] == 115
        and publication["source_card_age_context"] == "7–11 лет",
        "Свидетельство не относится к указанной первичной рецептурной карте.",
    )
    _require(
        publication["fresh_pdf_binary_downloaded"] is False
        and publication["fresh_pdf_sha256_verified"] is False
        and publication["visual_pdf_screenshot_verified"] is False,
        "Непроверенная внешняя копия PDF представлена как новый байтовый receipt.",
    )
    _require(
        source["identity_code"] == RECIPE_CODE
        and source["source_recipe_id"] == "ru-school2022:recipe:54-2м",
        "Рецептурная карточка не совпадает с проверяемой идентичностью.",
    )
    _require(
        limits["scaled_family_ready_edible_mass_is_verified"] is False
        and limits["course_SECOND_for_family_is_authorized"] is False
        and limits["individual_age_or_goal_portion_policy_is_verified"] is False
        and limits["finished_cooked_batch_storage_freezing_reheat_is_authorized"]
        is False,
        "Свидетельство не может быть разрешением на семейную порцию или Prep.",
    )
    r = manifest["recipes"][RECIPE_CODE]
    receipt = r["source_receipt"]
    seed = r["trusted_recipe_seed"]
    version = seed["version"]
    prepared = r["prepared_spec"]
    _require(
        receipt["source_recipe_id"] == source["source_recipe_id"]
        and version["source_recipe_id"] == source["source_recipe_id"]
        and prepared["source_recipe_id"] == source["source_recipe_id"],
        "Несовпадение идентификаторов исходного рецепта.",
    )
    _require(
        seed["canonical_name"] == source["name_ru"]
        and seed["canonical_code"] == source["identity_code"],
        "Опубликованное русское имя/код рецепта отличаются от первоисточника.",
    )
    _require(
        receipt["source_document_sha256"]
        == version["source_document_sha256"]
        == prepared["source_document_sha256"]
        == publication["retained_pdf_sha256_from_prior_review"],
        "Исторический пин исходного PDF различается между записями.",
    )
    _require(
        receipt["exact_source_card_sha256"]
        == publication["source_card_sha256_from_existing_review"],
        "Зафиксированная identity исходной карточки была подменена.",
    )
    _require(
        receipt["rights_review_status"] == "REVIEWED"
        and version["rights_review_status"] == "REVIEWED"
        and prepared["rights_review_status"] == "REVIEWED",
        "Исторический rights review не соответствует публикации.",
    )
    _require(
        version["verification_status"] == "SOURCE_VERIFIED",
        "Опубликованный RecipeVersion не имеет source verification.",
    )
    _require(
        version["meal_type_code"] == "main",
        "Публикация неожиданно изменила классификацию рецепта.",
    )
    _require(
        _amount(version["base_servings"], "base_servings")
        == _amount(version["source_original_servings"], "source_original_servings")
        == _amount(source["original_base_servings"], "card original_base_servings")
        == Decimal(1),
        "Различаются основания source и RecipeVersion для одной школьной порции.",
    )
    output = _amount(source["source_output_g"], "card output")
    meat = _amount(source["finished_meat_g"], "meat output")
    sauce = _amount(source["finished_sauce_g"], "sauce output")
    _require(
        meat + sauce == output
        == _amount(version["source_output_g"], "RecipeVersion source output")
        == _amount(prepared["output_mass_g"], "prepared authority output"),
        "Выход блюда не совпадает с суммой готовых компонентов и публикацией.",
    )
    energy = _amount(source["energy_kcal_per_source_card"], "source energy")
    _require(
        len(prepared["expected_available_amounts"]) == 1
        and prepared["expected_available_amounts"][0][0] == "ENERGY_KCAL"
        and _amount(
            prepared["expected_available_amounts"][0][1], "prepared energy"
        )
        == energy,
        "Энергетическая ценность из карты и подготовленной публикации расходятся.",
    )
    _require(
        prepared["require_recipe_inactive"] is True
        and seed["initial_is_active"] is False,
        "Публикация неожиданно предполагает активный потребительский рецепт.",
    )
    _require(
        len(prepared["expected_unknown_codes"]) == 53,
        "Подготовленная Nutrition authority не имеет ожидаемых 53 UNKNOWN.",
    )

    card_inputs = source["input_quantities"]
    seed_inputs = version["ingredients"]
    _require(len(card_inputs) == len(seed_inputs) == 7, "Ожидалось семь исходных строк.")
    _require(
        len({r["canonical_food_code"] for r in card_inputs}) == len(card_inputs)
        and len({r["food_ingredient_code"] for r in seed_inputs}) == len(seed_inputs),
        "Повторяющаяся FoodIngredient identity в исходной карте или публикации.",
    )
    seed_map = {r["food_ingredient_code"]: r for r in seed_inputs}
    discrepancies = []
    net_mass = Decimal(0)
    row_results = []
    for item in card_inputs:
        code = item["canonical_food_code"]
        stored = seed_map.get(code)
        _require(stored is not None, f"FoodIngredient {code} отсутствует.")
        gross = _amount(item["gross_g"], f"{code} gross")
        net = _amount(item["net_g"], f"{code} net")
        _require(net <= gross, f"{code} net не может превышать gross.")
        normalized = _amount(stored["quantity"], f"{code} published quantity")
        if stored["unit"] != "g" or stored["optional"] is not False or net != normalized:
            discrepancies.append(code)
        row_results.append(
            {
                "canonical_food_code": code,
                "source_gross_g": str(gross),
                "source_net_g": str(net),
                "published_input_g": str(normalized),
                "amount_matches": net == normalized,
            }
        )
        net_mass += net
    _require(not discrepancies, "RecipeIngredient rows contradict card: " + ",".join(discrepancies))
    _require(
        net_mass > output,
        "Сумма входного сырья не доказывает выход готового блюда.",
    )
    return {
        "schema": REPORT_SCHEMA,
        "recipe_code": RECIPE_CODE,
        "source_card": "School2022 54-2м",
        "source_age_context": publication["source_card_age_context"],
        "original_primary_card_portion_g": str(output),
        "finished_meat_g": str(meat),
        "finished_sauce_g": str(sauce),
        "source_card_energy_kcal": str(energy),
        "input_net_sum_g": str(net_mass),
        "ingredient_rows": row_results,
        "ingredient_rows_reconciled": len(row_results),
        "source_text_numeric_facts_match_manifest": True,
        "historical_source_pdf_sha256": receipt["source_document_sha256"],
        "historical_source_card_sha256": receipt["exact_source_card_sha256"],
        "current_pdf_binary_independently_verified": False,
        "current_persisted_recipe_version_id_verified": False,
        "current_household_meal_plan_id_verified": False,
        "source_role_classification": "main",
        "family_course_suitability": "UNKNOWN",
        "family_scaled_edible_mass": "UNKNOWN",
        "member_physical_portion_policy": "UNKNOWN",
        "source_card_holding_freezing_reheat_permission": "NOT_PROVEN",
        "prepared_nutrition_available_codes": ["ENERGY_KCAL"],
        "prepared_nutrition_unknown_codes": len(prepared["expected_unknown_codes"]),
        "customer_release": BLOCKED,
        "notes": [
            "Текстовые количественные факты первичной школьной карточки совпадают с R1-G manifest.",
            "Актуальный бинарный PDF не был повторно загружен и захеширован.",
            "80 г — выход исходной школьной рецептуры, не доказанная подходящая масса семейной порции.",
            "Классификация main не подтверждает автоматически курс SECOND для любого члена семьи.",
            "Профиль Prepared Nutrition в данном manifest содержит только ENERGY_KCAL; прочие нутриенты остаются UNKNOWN.",
            "Ни заморозка, ни хранение, ни безопасность повторного разогрева этим receipt не разрешены.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Read-only School2022 54-2м primary-card crosscheck"
    )
    parser.add_argument("--manifest", type=Path, default=MANIFEST)
    parser.add_argument("--witness", type=Path, default=WITNESS)
    args = parser.parse_args()
    manifest, witness = load_sources(
        manifest_path=args.manifest, witness_path=args.witness
    )
    report = crosscheck(manifest=manifest, witness=witness)
    print(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
