"""Versioned source corpus for imported recipe/technology cards.

These objects preserve source truth before FoodIngredient resolution and before
publication into the verified Recipe Catalogue. Source-declared nutrition is
reference evidence, never deterministic Nutrition truth.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from hashlib import sha256
from typing import Any


class CorpusRawFormat(StrEnum):
    TEXT = "TEXT"
    HTML = "HTML"
    PDF_TEXT = "PDF_TEXT"
    JSON = "JSON"


class CorpusPublicationPolicy(StrEnum):
    NORMATIVE_BASE_RECIPE_APPROVED = "NORMATIVE_BASE_RECIPE_APPROVED"


class CorpusCaptureStatus(StrEnum):
    RAW_CAPTURED = "RAW_CAPTURED"
    STRUCTURED = "STRUCTURED"
    PARTIAL = "PARTIAL"


@dataclass(frozen=True)
class SourceDocumentInput:
    source_code: str
    title_ru: str
    authority_ru: str
    source_url: str
    source_version: str
    retrieved_at: str
    raw_format: CorpusRawFormat
    raw_bytes_sha256: str
    raw_text_sha256: str
    publication_policy: CorpusPublicationPolicy

    def __post_init__(self) -> None:
        for value in (
            self.source_code,
            self.title_ru,
            self.authority_ru,
            self.source_version,
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError("Source document text fields must not be empty")
        if not self.source_url.startswith(("https://", "http://", "file://")):
            raise ValueError("source_url must be HTTP(S) or file://")
        try:
            datetime.fromisoformat(self.retrieved_at)
        except ValueError as exc:
            raise ValueError("retrieved_at must be ISO-8601") from exc
        for value in (self.raw_bytes_sha256, self.raw_text_sha256):
            if len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
                raise ValueError("source hashes must be lowercase SHA-256")


@dataclass(frozen=True)
class SourceIngredientInput:
    position: int
    name_ru: str
    gross_g: str | None = None
    net_g: str | None = None
    quantity_text: str | None = None
    source_form_note: str | None = None
    optional: bool = False

    def __post_init__(self) -> None:
        if self.position <= 0 or not self.name_ru.strip():
            raise ValueError("Ingredient position/name are required")
        for field in ("gross_g", "net_g"):
            value = getattr(self, field)
            if value is not None:
                _nonnegative_decimal(value, field)


@dataclass(frozen=True)
class SourceNutrientInput:
    nutrient_code: str
    value: str
    unit: str
    source_label: str

    def __post_init__(self) -> None:
        if not self.nutrient_code or not self.unit or not self.source_label:
            raise ValueError("Declared nutrient code/unit/label are required")
        _nonnegative_decimal(self.value, "value")


@dataclass(frozen=True)
class SourceVariantInput:
    variant_code: str
    label_ru: str
    position: int
    output_g: str | None
    output_text: str | None
    ingredients: tuple[SourceIngredientInput, ...]
    declared_nutrients: tuple[SourceNutrientInput, ...] = ()

    def __post_init__(self) -> None:
        if not self.variant_code or not self.label_ru or self.position <= 0:
            raise ValueError("Variant code/label/position are required")
        if self.output_g is not None:
            _positive_decimal(self.output_g, "output_g")
        positions = [row.position for row in self.ingredients]
        if positions != sorted(set(positions)):
            raise ValueError("Ingredient positions must be unique and sorted")


@dataclass(frozen=True)
class SourceCardInput:
    source_section_code: str
    source_card_code: str
    source_page_url: str | None
    name_ru: str
    category_ru: str | None
    source_recipe_basis: str | None
    technology_text_ru: str | None
    raw_card_text: str
    raw_card_sha256: str
    capture_status: CorpusCaptureStatus
    variants: tuple[SourceVariantInput, ...]

    def __post_init__(self) -> None:
        if not self.source_section_code.strip():
            raise ValueError("source_section_code is required")
        if not self.source_card_code or not self.name_ru or not self.raw_card_text:
            raise ValueError("Card code/name/raw text are required")
        if self.source_page_url is not None and not self.source_page_url.startswith(
            ("https://", "http://", "file://")
        ):
            raise ValueError("source_page_url must be HTTP(S), file://, or null")
        expected = sha256(self.raw_card_text.encode("utf-8")).hexdigest()
        if self.raw_card_sha256 != expected:
            raise ValueError("raw_card_sha256 does not match raw_card_text")
        positions = [row.position for row in self.variants]
        if positions != sorted(set(positions)):
            raise ValueError("Variant positions must be unique and sorted")


def document_from_dict(data: dict[str, Any]) -> SourceDocumentInput:
    return SourceDocumentInput(
        source_code=data["source_code"],
        title_ru=data["title_ru"],
        authority_ru=data["authority_ru"],
        source_url=data["source_url"],
        source_version=data["source_version"],
        retrieved_at=data["retrieved_at"],
        raw_format=CorpusRawFormat(data["raw_format"]),
        raw_bytes_sha256=data["raw_bytes_sha256"],
        raw_text_sha256=data["raw_text_sha256"],
        publication_policy=CorpusPublicationPolicy(data["publication_policy"]),
    )


def card_from_dict(data: dict[str, Any]) -> SourceCardInput:
    variants: list[SourceVariantInput] = []
    for variant in data.get("variants", []):
        ingredients = tuple(
            SourceIngredientInput(**row) for row in variant.get("ingredients", [])
        )
        nutrients = tuple(
            SourceNutrientInput(**row)
            for row in variant.get("declared_nutrients", [])
        )
        variants.append(
            SourceVariantInput(
                variant_code=variant["variant_code"],
                label_ru=variant["label_ru"],
                position=variant["position"],
                output_g=variant.get("output_g"),
                output_text=variant.get("output_text"),
                ingredients=ingredients,
                declared_nutrients=nutrients,
            )
        )
    raw_text = data["raw_card_text"]
    return SourceCardInput(
        source_section_code=data.get("source_section_code", "BOOTSTRAP"),
        source_card_code=data["source_card_code"],
        source_page_url=data.get("source_page_url"),
        name_ru=data["name_ru"],
        category_ru=data.get("category_ru"),
        source_recipe_basis=data.get("source_recipe_basis"),
        technology_text_ru=data.get("technology_text_ru"),
        raw_card_text=raw_text,
        raw_card_sha256=sha256(raw_text.encode("utf-8")).hexdigest(),
        capture_status=CorpusCaptureStatus(data["capture_status"]),
        variants=tuple(variants),
    )


def _positive_decimal(value: str, field: str) -> Decimal:
    parsed = _decimal(value, field)
    if parsed <= 0:
        raise ValueError(f"{field} must be positive")
    return parsed


def _nonnegative_decimal(value: str, field: str) -> Decimal:
    parsed = _decimal(value, field)
    if parsed < 0:
        raise ValueError(f"{field} must be non-negative")
    return parsed


def _decimal(value: str, field: str) -> Decimal:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be a decimal string")
    try:
        parsed = Decimal(value.replace(",", "."))
    except (InvalidOperation, AttributeError) as exc:
        raise ValueError(f"{field} must be a decimal string") from exc
    if not parsed.is_finite():
        raise ValueError(f"{field} must be finite")
    return parsed
