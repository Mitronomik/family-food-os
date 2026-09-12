"""Explicit PR6 RU import of reviewed source observations, independent of v1 backfill."""

from decimal import Decimal
from typing import Any

from app.domain.nutrient_vector_backfill_v1 import canonical_json

LEGACY_COMPONENTS = {
    "kcal": "1008",
    "protein_g": "1003",
    "fat_g": "1004",
    "carbohydrates_g": "1005",
    "fiber_g": "1079",
}


def prepare_reviewed_source(
    source: dict[str, Any], mappings: list[dict[str, Any]]
) -> tuple[dict[str, Decimal | None], list[dict[str, Any]], str]:
    if (
        source["source_data_type"] != "SR Legacy"
        or source["source_version"] != "2018-04"
    ):
        raise ValueError("Источник не входит в проверенную операцию импорта.")
    if source["source_id"] not in {"170398", "168173"}:
        raise ValueError("Профиль не разрешён к импорту этой операцией.")
    if source["basis_grams"] != "100" or source["energy_nutrient_id"] != "1008":
        raise ValueError("Неверный базис или источник энергии.")
    if source["food"]["fdc_id"] != source["source_id"]:
        raise ValueError("Пищевая идентичность источника не совпадает.")
    vocabulary = {r["id"]: r for r in source["nutrients"]}
    rows: dict[str, dict[str, Any]] = {}
    observations, values = [], []
    for raw in source["food_nutrients"]:
        nutrient_id = raw["nutrient_id"]
        if raw["fdc_id"] != source["source_id"] or nutrient_id in rows:
            raise ValueError("Смешение профилей или повторный нутриент источника.")
        rows[nutrient_id] = raw
        amount = Decimal(raw["amount"]) if raw["amount"] else None
        if amount is not None and (not amount.is_finite() or amount < 0):
            raise ValueError("Некорректное исходное значение нутриента.")
        matches = [
            m
            for m in mappings
            if m["source_name"] == source["source_name"]
            and m["source_release"] == source["source_version"]
            and m["source_data_type"] == source["source_data_type"]
            and m["source_nutrient_id"] == nutrient_id
            and m["mapping_status"] in {"EXACT", "METHOD_SPECIFIC"}
        ]
        if len(matches) > 1:
            raise ValueError("Неоднозначное соответствие нутриента.")
        origin = "UNMAPPED_OR_INCOMPATIBLE"
        if amount is None:
            origin = "VALUE_ABSENT"
        elif amount == 0:
            origin = "UNRESOLVED_ZERO"
        elif matches:
            origin = "SOURCE_COMPONENT_CONFIRMED"
        if (
            matches
            and matches[0]["canonical_code"] == "ENERGY_KCAL"
            and nutrient_id != "1008"
        ):
            origin = "UNSELECTED_ENERGY_METHOD"
        observation = {
            "audit_identity": f"PR6-RU-FOOD-DATA:{source['source_id']}:{raw['id']}",
            "profile_source_name": source["source_name"],
            "profile_source_id": source["source_id"],
            "profile_source_version": source["source_version"],
            "profile_source_data_type": source["source_data_type"],
            "source_nutrient_id": nutrient_id,
            "source_nutrient_name": vocabulary[nutrient_id]["name"],
            "source_unit": vocabulary[nutrient_id]["unit_name"],
            "source_value": raw["amount"],
            "source_food_nutrient_id": raw["id"],
            "source_derivation_id": raw["derivation_id"] or None,
            "source_observation": raw,
            "source_review_reference": source["review_reference"],
            "source_archive_id": source["archive_id"],
            "uncertainty": "Source derivation retained; analytical certainty not inferred.",
        }
        observations.append({"origin": origin, "observation": observation})
        if origin != "SOURCE_COMPONENT_CONFIRMED":
            continue
        mapping = matches[0]
        if (
            mapping["source_unit"] != observation["source_unit"]
            or mapping["source_nutrient_name"] != observation["source_nutrient_name"]
            or mapping["source_nutrient_nbr"] != vocabulary[nutrient_id]["nutrient_nbr"]
            or mapping["unit_conversion_required"]
        ):
            raise ValueError("Исходный компонент не соответствует утверждённой карте.")
        values.append(
            {
                "nutrient_code": mapping["canonical_code"],
                "amount": amount,
                "provenance_json": canonical_json(
                    {"observation": observation, "mapping": mapping}
                ),
            }
        )
    if len({v["nutrient_code"] for v in values}) != len(values):
        raise ValueError("Повторное эффективное значение нутриента.")
    legacy: dict[str, Decimal | None] = {}
    for field, component in LEGACY_COMPONENTS.items():
        raw = rows.get(component)
        amount = Decimal(raw["amount"]) if raw and raw["amount"] else None
        # Unlike historical v1, no unapproved zero may establish a required field.
        if field != "fiber_g" and (amount is None or amount == 0):
            raise ValueError("Нет допустимого обязательного значения Nutrition v1.")
        legacy[field] = amount if amount else None
    return (
        legacy,
        sorted(values, key=lambda v: v["nutrient_code"]),
        canonical_json(observations),
    )
