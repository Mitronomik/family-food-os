"""Deterministic parsers/import DTOs for Russian normative recipe cards."""

from __future__ import annotations

from hashlib import sha256
from html.parser import HTMLParser
import re
from typing import Any
from urllib.parse import urljoin, urlparse

from app.domain.recipe_source_corpus import (
    CorpusCaptureStatus,
    card_from_dict,
    document_from_dict,
)

_CARD = re.compile(
    r"(?im)^\s*Технологическая(?:\s+карта)?\s+(?:N|№)\s*([^\n]+)"
)
_NAME = re.compile(
    r"(?im)^\s*Наименование(?:\s+кулинарного\s+изделия\s*\(блюда\)|\s+блюда)\s*:\s*(.+)$"
)
_BASIS = re.compile(r"(?im)^\s*Источник\s+рецептуры\s*:\s*(.+)$")
_TECH = re.compile(
    r"(?is)Технология\s+приготовления\s*:\s*(.+?)"
    r"(?=\n\s*(?:Сведения\s+о\s+пищевой|Технологическая(?:\s+карта)?\s+(?:N|№)|Оглавление|$))"
)
_LINK_CODE = re.compile(
    r"(?i)Технологическая(?:\s+карта)?\s+(?:N|№)\s*([0-9]+(?:\.[0-9]+)?[а-яa-z]?)"
)


class _TextHTMLParser(HTMLParser):
    _BREAK_TAGS = {
        "article",
        "br",
        "div",
        "h1",
        "h2",
        "h3",
        "h4",
        "li",
        "p",
        "section",
        "table",
        "td",
        "th",
        "tr",
    }

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag in self._BREAK_TAGS:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in self._BREAK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


class _LinkHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.current_href: str | None = None
        self.current_text: list[str] = []
        self.links: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag != "a":
            return
        self.current_href = dict(attrs).get("href")
        self.current_text = []

    def handle_data(self, data: str) -> None:
        if self.current_href is not None:
            self.current_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self.current_href is not None:
            self.links.append((self.current_href, " ".join(self.current_text)))
            self.current_href = None
            self.current_text = []


def html_to_text(html: str) -> str:
    parser = _TextHTMLParser()
    parser.feed(html)
    lines = [" ".join(line.split()) for line in "".join(parser.parts).splitlines()]
    return "\n".join(line for line in lines if line).strip()


def extract_sudact_card_links(html: str, appendix_url: str) -> dict[str, str]:
    """Return exact card-code -> page URL links within one appendix only."""
    parser = _LinkHTMLParser()
    parser.feed(html)
    appendix_path = urlparse(appendix_url).path.rstrip("/") + "/"
    found: dict[str, str] = {}
    for href, label in parser.links:
        absolute = urljoin(appendix_url, href)
        parsed = urlparse(absolute)
        if not parsed.path.startswith(appendix_path):
            continue
        if "/tekhnologicheskaia-karta-n-" not in parsed.path:
            continue
        match = _LINK_CODE.search(" ".join(label.split()))
        if match is None:
            continue
        code = _canonical_card_code(match.group(1))
        previous = found.get(code)
        if previous is not None and previous != absolute:
            raise ValueError(f"Multiple Sudact URLs for card {code}: {previous} / {absolute}")
        found[code] = absolute
    return found


def split_normative_cards(
    text: str,
    *,
    source_section_code: str = "DOCUMENT",
    source_page_url: str | None = None,
    category_ru: str | None = None,
) -> list[dict[str, Any]]:
    """Capture every card block losslessly; structure enrichment may happen later."""
    matches = list(_CARD.finditer(text))
    cards: list[dict[str, Any]] = []
    for index, match in enumerate(matches):
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        raw = text[start:end].strip()
        code = _canonical_card_code(" ".join(match.group(1).split()))
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
                "source_section_code": source_section_code,
                "source_card_code": code,
                "source_page_url": source_page_url,
                "name_ru": name,
                "category_ru": category_ru,
                "source_recipe_basis": basis,
                "technology_text_ru": technology,
                "raw_card_text": raw,
                "raw_card_sha256": sha256(raw.encode("utf-8")).hexdigest(),
                "capture_status": CorpusCaptureStatus.RAW_CAPTURED.value,
                "variants": [],
            }
        )
    return cards


def extract_single_normative_card(
    text: str,
    *,
    expected_code: str,
    source_section_code: str,
    source_page_url: str,
    category_ru: str,
) -> dict[str, Any]:
    """Extract the card body from an HTML mirror page that also contains navigation."""
    expected = _canonical_card_code(expected_code)
    candidates = split_normative_cards(
        text,
        source_section_code=source_section_code,
        source_page_url=source_page_url,
        category_ru=category_ru,
    )
    matching = [row for row in candidates if row["source_card_code"] == expected]
    if not matching:
        raise ValueError(f"Card {source_section_code}:{expected} not found in page")
    with_name = [row for row in matching if not row["name_ru"].startswith("Технологическая карта ")]
    selected = with_name[-1] if with_name else matching[-1]
    return selected


def validate_manifest(manifest: dict[str, Any]) -> dict[tuple[str, str], str]:
    total = manifest.get("expected_total_cards")
    if not isinstance(total, int) or total <= 0:
        raise ValueError("Manifest expected_total_cards must be positive")
    lookup: dict[tuple[str, str], str] = {}
    counted = 0
    for appendix in manifest.get("appendices", []):
        section = appendix["source_section_code"]
        categories = appendix["categories"]
        codes: list[str] = []
        for category, values in categories.items():
            for value in values:
                code = _canonical_card_code(value)
                key = (section, code)
                if key in lookup:
                    raise ValueError(f"Duplicate manifest card: {section}:{code}")
                lookup[key] = category
                codes.append(code)
        expected = appendix["expected_card_count"]
        if len(codes) != expected:
            raise ValueError(
                f"Manifest count mismatch for {section}: {len(codes)} != {expected}"
            )
        counted += len(codes)
    if counted != total:
        raise ValueError(f"Manifest total mismatch: {counted} != {total}")
    return lookup


def validate_bundle(bundle: dict[str, Any]):
    document = document_from_dict(bundle["document"])
    cards = tuple(card_from_dict(card) for card in bundle["cards"])
    if not cards:
        raise ValueError("Recipe source corpus bundle must contain at least one card")
    seen: set[tuple[str, str, str]] = set()
    for card in cards:
        key = (card.source_section_code, card.source_card_code, card.raw_card_sha256)
        if key in seen:
            raise ValueError(
                f"Duplicate card revision: {card.source_section_code}:{card.source_card_code}"
            )
        seen.add(key)
    return document, cards


def _canonical_card_code(value: str) -> str:
    return "".join(value.strip().lower().replace("a", "а").replace("b", "б").split())
