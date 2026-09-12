"""Deterministic parsers/import DTOs for Russian normative recipe cards."""

from __future__ import annotations

from hashlib import sha256
import re
from typing import Any

from app.domain.recipe_source_corpus import (
    CorpusCaptureStatus,
    card_from_dict,
    document_from_dict,
)

_CARD = re.compile(
    r"(?im)^\s*Технологическая\s+карта\s+(?:№|N)\s*([^\n]+)"
)
_SECTION = re.compile(r"(?im)^\s*Приложение\s+(\d+)\b")
_NAME = re.compile(
    r"(?im)^\s*Наименование(?:\s+кулинарного\s+изделия\s*\(блюда\)|\s+блюда)\s*:\s*(.+)$"
)
_BASIS = re.compile(r"(?im)^\s*Источник\s+рецептуры\s*:\s*(.+)$")
_TECH = re.compile(
    r"(?is)Технология\s+приготовления(?:\s+кулинарной\s+продукции)?\s*:\s*(.+?)"
    r"(?=\n\s*(?:Сведения\s+о\s+пищевой|Технологическая\s+карта\s+(?:№|N)|Приложение\s+\d+|$))"
)


def split_normative_cards(text: str) -> list[dict[str, Any]]:
    """Capture every card block losslessly; structure enrichment may happen later.

    Repeated card numbers in different normative appendices are distinct source
    occurrences and retain their appendix context.
    """
    matches = list(_CARD.finditer(text))
    sections = list(_SECTION.finditer(text))
    cards: list[dict[str, Any]] = []
    section_index = 0
    current_section = ""
    for index, match in enumerate(matches):
        while (
            section_index < len(sections)
            and sections[section_index].start() < match.start()
        ):
            current_section = f"APPENDIX_{sections[section_index].group(1)}"
            section_index += 1
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        raw = text[start:end].strip()
        code = " ".join(match.group(1).split())
        name_match = _NAME.search(raw)
        basis_match = _BASIS.search(raw)
        tech_match = _TECH.search(raw)
        name = (
            " ".join(name_match.group(1).split())
            if name_match
            else f"Технологическая карта {code}"
        )
        basis = " ".join(basis_match.group(1).split()) if basis_match else None
        technology = " ".join(tech_match.group(1).split()) if tech_match else None
        cards.append(
            {
                "source_section_code": current_section,
                "source_card_code": code,
                "name_ru": name,
                "category_ru": None,
                "source_recipe_basis": basis,
                "technology_text_ru": technology,
                "raw_card_text": raw,
                "raw_card_sha256": sha256(raw.encode("utf-8")).hexdigest(),
                "capture_status": CorpusCaptureStatus.RAW_CAPTURED.value,
                "variants": [],
            }
        )
    return cards


def validate_bundle(bundle: dict[str, Any]):
    document = document_from_dict(bundle["document"])
    cards = tuple(card_from_dict(card) for card in bundle["cards"])
    if not cards:
        raise ValueError("Recipe source corpus bundle must contain at least one card")
    seen: set[tuple[str, str, str]] = set()
    for card in cards:
        key = (
            card.source_section_code,
            card.source_card_code,
            card.raw_card_sha256,
        )
        if key in seen:
            raise ValueError(
                "Duplicate card revision: "
                f"{card.source_section_code}:{card.source_card_code}"
            )
        seen.add(key)
    return document, cards
