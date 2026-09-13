"""Append-only persistence for recipe source documents and cards."""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import Connection, RowMapping, Table, select

from app.domain.recipe_source_corpus import (
    CorpusImportConflictError,
    SourceCardInput,
    SourceDocumentInput,
)
from app.persistence.sqlalchemy_core.recipe_source_corpus_tables import (
    recipe_source_card_ingredients_table,
    recipe_source_card_variants_table,
    recipe_source_cards_table,
    recipe_source_declared_nutrients_table,
    recipe_source_documents_table,
)
from app.persistence.sqlalchemy_core.types import DecimalText, UTCDateTime


class SqlAlchemyRecipeSourceCorpusRepository:
    def __init__(self, connection: Connection) -> None:
        self._connection = connection

    def import_document(
        self,
        document: SourceDocumentInput,
        cards: tuple[SourceCardInput, ...],
    ) -> tuple[UUID, int]:
        existing = (
            self._connection.execute(
                select(recipe_source_documents_table).where(
                    recipe_source_documents_table.c.source_code == document.source_code,
                    recipe_source_documents_table.c.source_version
                    == document.source_version,
                    recipe_source_documents_table.c.raw_bytes_sha256
                    == document.raw_bytes_sha256,
                )
            )
            .mappings()
            .one_or_none()
        )
        if existing is not None:
            self._assert_exact_repeat(existing, document, cards)
            return existing["id"], 0
        now = datetime.now(timezone.utc)
        document_id = uuid4()
        self._connection.execute(
            recipe_source_documents_table.insert().values(
                id=document_id,
                source_code=document.source_code,
                title_ru=document.title_ru,
                authority_ru=document.authority_ru,
                source_url=document.source_url,
                source_version=document.source_version,
                retrieved_at=datetime.fromisoformat(document.retrieved_at),
                raw_format=document.raw_format.value,
                raw_bytes_sha256=document.raw_bytes_sha256,
                raw_text_sha256=document.raw_text_sha256,
                publication_policy=document.publication_policy.value,
                created_at=now,
            )
        )
        for card in cards:
            self._insert_card(document_id, card, now)
        return document_id, len(cards)

    def _assert_exact_repeat(
        self,
        existing: RowMapping,
        document: SourceDocumentInput,
        cards: tuple[SourceCardInput, ...],
    ) -> None:
        # Compare stored facts before any write. IDs/created_at are storage-owned;
        # collection order is defined by persisted identities, not bundle order.
        _assert_row_matches(recipe_source_documents_table, existing, asdict(document))
        for card_row, card in self._matching_children(
            recipe_source_cards_table,
            "document_id",
            existing["id"],
            tuple(asdict(card) for card in cards),
            ("source_section_code", "source_card_code"),
        ):
            for variant_row, variant in self._matching_children(
                recipe_source_card_variants_table,
                "card_id",
                card_row["id"],
                card["variants"],
                ("position",),
            ):
                self._matching_children(
                    recipe_source_card_ingredients_table,
                    "variant_id",
                    variant_row["id"],
                    variant["ingredients"],
                    ("position",),
                )
                self._matching_children(
                    recipe_source_declared_nutrients_table,
                    "variant_id",
                    variant_row["id"],
                    variant["declared_nutrients"],
                    ("nutrient_code",),
                )

    def _matching_children(
        self,
        table: Table,
        parent_key: str,
        parent_id: UUID,
        payloads: tuple[dict[str, Any], ...],
        identity: tuple[str, ...],
    ) -> list[tuple[RowMapping, dict[str, Any]]]:
        rows = (
            self._connection.execute(
                select(table).where(table.c[parent_key] == parent_id)
            )
            .mappings()
            .all()
        )
        if len(rows) != len(payloads):
            raise CorpusImportConflictError(
                "Конфликт повторного импорта: состав записей источника изменён."
            )

        def key(row):
            return tuple(row[field] for field in identity)

        pairs = list(zip(sorted(rows, key=key), sorted(payloads, key=key), strict=True))
        for row, payload in pairs:
            _assert_row_matches(table, row, payload, parent_key)
        return pairs

    def card_count(self, document_id: UUID) -> int:
        return len(
            self._connection.execute(
                select(recipe_source_cards_table.c.id).where(
                    recipe_source_cards_table.c.document_id == document_id
                )
            ).all()
        )

    def _insert_card(
        self,
        document_id: UUID,
        card: SourceCardInput,
        now: datetime,
    ) -> None:
        card_id = uuid4()
        self._connection.execute(
            recipe_source_cards_table.insert().values(
                id=card_id,
                document_id=document_id,
                source_section_code=card.source_section_code,
                source_card_code=card.source_card_code,
                source_page_url=card.source_page_url,
                name_ru=card.name_ru,
                category_ru=card.category_ru,
                source_recipe_basis=card.source_recipe_basis,
                technology_text_ru=card.technology_text_ru,
                raw_card_text=card.raw_card_text,
                raw_card_sha256=card.raw_card_sha256,
                capture_status=card.capture_status.value,
                created_at=now,
            )
        )
        for variant in card.variants:
            variant_id = uuid4()
            self._connection.execute(
                recipe_source_card_variants_table.insert().values(
                    id=variant_id,
                    card_id=card_id,
                    position=variant.position,
                    variant_code=variant.variant_code,
                    label_ru=variant.label_ru,
                    output_g=(
                        _decimal(variant.output_g)
                        if variant.output_g is not None
                        else None
                    ),
                    output_text=variant.output_text,
                    created_at=now,
                )
            )
            for row in variant.ingredients:
                self._connection.execute(
                    recipe_source_card_ingredients_table.insert().values(
                        id=uuid4(),
                        variant_id=variant_id,
                        position=row.position,
                        name_ru=row.name_ru,
                        gross_g=_decimal(row.gross_g)
                        if row.gross_g is not None
                        else None,
                        net_g=_decimal(row.net_g) if row.net_g is not None else None,
                        quantity_text=row.quantity_text,
                        source_form_note=row.source_form_note,
                        optional=row.optional,
                        created_at=now,
                    )
                )
            for nutrient in variant.declared_nutrients:
                self._connection.execute(
                    recipe_source_declared_nutrients_table.insert().values(
                        id=uuid4(),
                        variant_id=variant_id,
                        nutrient_code=nutrient.nutrient_code,
                        value=_decimal(nutrient.value),
                        unit=nutrient.unit,
                        source_label=nutrient.source_label,
                        created_at=now,
                    )
                )


def _assert_row_matches(
    table: Table,
    row: RowMapping,
    payload: dict[str, Any],
    parent_key: str | None = None,
) -> None:
    for column in table.columns:
        if column.name in ("id", "created_at", parent_key):
            continue
        value = payload[column.name]
        # Use the same value semantics as insertion and Core result conversion.
        if value is not None and isinstance(column.type, DecimalText):
            value = _decimal(value)
        elif isinstance(column.type, UTCDateTime):
            value = datetime.fromisoformat(value)
        if row[column.name] != value:
            raise CorpusImportConflictError(
                "Конфликт повторного импорта: сохранённые данные источника отличаются."
            )


def _decimal(value: str) -> Decimal:
    return Decimal(value.replace(",", "."))
