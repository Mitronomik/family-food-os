"""Bounded Russian food-data evidence gates; no availability runtime context."""

from collections.abc import Sequence
from datetime import date
import re
from typing import Any

BASELINE_CHAINS = ("PYATEROCHKA", "PEREKRESTOK", "LENTA", "OKEY", "MAGNIT")
MARKET_STATUSES = {"AVAILABLE", "NOT_FOUND", "UNCERTAIN"}


def russian_display(name: str, code: str) -> str:
    if not name.strip() or name == code or not re.search(r"[А-Яа-яЁё]", name):
        raise ValueError("Необходимо русское название продукта.")
    # Preserve legitimate percentages, digits and labelled provenance identifiers.
    # The reviewed primary name is returned verbatim, never a fallback.
    return name


def market_classification(
    food_code: str, food_form: str, evidence: Sequence[dict[str, Any]]
) -> str:
    chains = set()
    water_exception = False
    for row in evidence:
        for key in (
            "id",
            "food_code",
            "food_form",
            "retailer",
            "region",
            "source_url",
            "observed_wording_ru",
            "checked_at",
            "notes",
            "review_reference",
        ):
            if not isinstance(row.get(key), str) or not row[key].strip():
                raise ValueError("Неполное доказательство доступности продукта.")
        date.fromisoformat(row["checked_at"])
        if row["region"] != "RU-SPB/LO":
            raise ValueError("Доказательство относится к другому региону.")
        if row["status"] not in MARKET_STATUSES:
            raise ValueError("Неизвестный статус доказательства.")
        if row["food_code"] != food_code or row["food_form"] != food_form:
            raise ValueError("Доказательство относится к другой пищевой форме.")
        if row["retailer"] == "TAP_WATER_EXCEPTION":
            if food_code != "WATER" or row["status"] != "AVAILABLE":
                raise ValueError("Исключение разрешено только для питьевой воды.")
            water_exception = True
        elif row["retailer"] not in (*BASELINE_CHAINS, "VKUSVILL", "RESEARCH"):
            raise ValueError("Источник не входит в панель проверки.")
        elif row["status"] == "AVAILABLE" and row["retailer"] in BASELINE_CHAINS:
            if not row.get("region_evidence_url"):
                raise ValueError("Нет подтверждения присутствия сети в регионе.")
            chains.add(row["retailer"])
    if water_exception or len(chains) >= 3:
        return "RU_MASS_MARKET"
    if chains:
        return "RU_AVAILABLE"
    return "SPECIALTY_OR_UNCLEAR"


def derive_readiness(
    row: dict[str, Any], evidence: Sequence[dict[str, Any]]
) -> dict[str, Any]:
    """Derive machine status from reviewed facts, never trust a manual label."""
    market = market_classification(row["food_code"], row["food_form"], evidence)
    reasons = list(row["review_blockers"])
    try:
        russian_display(row["canonical_name_ru"], row["food_code"])
    except ValueError:
        reasons.append("RUSSIAN_DISPLAY_REQUIRED")
    if market == "SPECIALTY_OR_UNCLEAR":
        reasons.append("MARKET_EVIDENCE_REQUIRED")
    if row["population"] == "RESEARCH_CANDIDATE" and row["decision"] != "PROMOTE":
        reasons.append("CANDIDATE_NOT_PROMOTED")
    if not row.get("nutrition_profile_source"):
        reasons.append("DIRECT_PROFILE_REQUIRED")
    if row["nutrient_vector_status"] != "SEALED_REFERENCE":
        reasons.append("SEALED_VECTOR_REQUIRED")
    if row["composition_status"] != "ATOMIC_REFERENCE":
        reasons.append("ATOMIC_COMPOSITION_REQUIRED")
    reasons = sorted(set(reasons))
    return {
        "market_classification": market,
        "final_readiness": "RU_READY" if not reasons else "NOT_READY",
        "blocking_reasons": reasons,
        "default_pool_eligible": not reasons and market == "RU_MASS_MARKET",
        "default_pool_blocking_reasons": reasons
        or (
            ["REVIEWED_MASS_MARKET_SUBSTITUTION_PATH_REQUIRED"]
            if market == "RU_AVAILABLE"
            else []
        ),
    }
