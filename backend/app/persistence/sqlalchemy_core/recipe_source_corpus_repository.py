"""Append-only persistence for recipe source documents and cards."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import Connection, select

from app.domain.recipe_source_corpus import SourceCardInput, SourceDocumentInput
from app.persistence.sqlalchemy_core.recipe_source_corpus_tables import (
    recipe_source_card_ingredients_table,
    recipe_source_card_variants_table,
    recipe_source_cards_table,
    recipe_source_declared_nutrients_table,
    recipe_source_documents_table,
)


class SqlAlchemyRecipeSourceCorpusRepository:
    def __init__(self, connection: Connection) -> None:
        self._connection = connection

    def import_document(
        self,
        document: SourceDocumentInput,
        cards: tuple[SourceCardInput, ...],
    ) -> tuple[UUID, int]:
        existing = self._connection.execute(
            select(recipe_source_documents_table.c.id).where(
                recipe_source_documents_table.c.source_code == document.source_code,
                recipe_source_documents_table.c.source_version == document.source_version,
                recipe_source_documents_table.c.raw_bytes_sha256
                == document.raw_bytes_sha256,
            )
        ).scalar_one_or_none()
        if existing is not None:
            return existing, 0
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
                source_card_code=card.source_card_code,
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
                        Decimal(variant.output_g)
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
                        gross_g=(
                            Decimal(row.gross_g) if row.gross_g is not None else None
                        ),
                        net_g=Decimal(row.net_g) if row.net_g is not None else None,
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
                        value=Decimal(nutrient.value),
                        unit=nutrient.unit,
                        source_label=nutrient.source_label,
                        created_at=now,
                    )
                )
