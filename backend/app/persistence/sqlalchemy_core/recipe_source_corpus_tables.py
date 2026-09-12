"""SQLAlchemy Core metadata for the pre-publication recipe source corpus."""

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    UniqueConstraint,
)

from app.persistence.sqlalchemy_core.types import DecimalText, UTCDateTime, entity_uuid_type

recipe_source_corpus_metadata = MetaData()

recipe_source_documents_table = Table(
    "recipe_source_documents",
    recipe_source_corpus_metadata,
    Column("id", entity_uuid_type(), primary_key=True, nullable=False),
    Column("source_code", String, nullable=False),
    Column("title_ru", String, nullable=False),
    Column("authority_ru", String, nullable=False),
    Column("source_url", String, nullable=False),
    Column("source_version", String, nullable=False),
    Column("retrieved_at", UTCDateTime(), nullable=False),
    Column("raw_format", String, nullable=False),
    Column("raw_bytes_sha256", String(64), nullable=False),
    Column("raw_text_sha256", String(64), nullable=False),
    Column("publication_policy", String, nullable=False),
    Column("created_at", UTCDateTime(), nullable=False),
    UniqueConstraint(
        "source_code",
        "source_version",
        "raw_bytes_sha256",
        name="uq_recipe_source_document_revision",
    ),
    CheckConstraint(
        "length(raw_bytes_sha256)=64 AND length(raw_text_sha256)=64",
        name="ck_recipe_source_document_hashes",
    ),
)

recipe_source_cards_table = Table(
    "recipe_source_cards",
    recipe_source_corpus_metadata,
    Column("id", entity_uuid_type(), primary_key=True, nullable=False),
    Column(
        "document_id",
        entity_uuid_type(),
        ForeignKey("recipe_source_documents.id", ondelete="RESTRICT"),
        nullable=False,
    ),
    Column("source_section_code", String, nullable=False, server_default=""),
    Column("source_card_code", String, nullable=False),
    Column("name_ru", String, nullable=False),
    Column("category_ru", String),
    Column("source_recipe_basis", Text),
    Column("technology_text_ru", Text),
    Column("raw_card_text", Text, nullable=False),
    Column("raw_card_sha256", String(64), nullable=False),
    Column("capture_status", String, nullable=False),
    Column("created_at", UTCDateTime(), nullable=False),
    UniqueConstraint(
        "document_id",
        "source_section_code",
        "source_card_code",
        "raw_card_sha256",
        name="uq_recipe_source_card_revision",
    ),
    CheckConstraint("length(raw_card_sha256)=64", name="ck_recipe_source_card_hash"),
)

recipe_source_card_variants_table = Table(
    "recipe_source_card_variants",
    recipe_source_corpus_metadata,
    Column("id", entity_uuid_type(), primary_key=True, nullable=False),
    Column(
        "card_id",
        entity_uuid_type(),
        ForeignKey("recipe_source_cards.id", ondelete="RESTRICT"),
        nullable=False,
    ),
    Column("position", Integer, nullable=False),
    Column("variant_code", String, nullable=False),
    Column("label_ru", String, nullable=False),
    Column("output_g", DecimalText()),
    Column("output_text", String),
    Column("created_at", UTCDateTime(), nullable=False),
    UniqueConstraint("card_id", "position", name="uq_recipe_source_variant_position"),
    UniqueConstraint("card_id", "variant_code", name="uq_recipe_source_variant_code"),
    CheckConstraint("position > 0", name="ck_recipe_source_variant_position"),
)

recipe_source_card_ingredients_table = Table(
    "recipe_source_card_ingredients",
    recipe_source_corpus_metadata,
    Column("id", entity_uuid_type(), primary_key=True, nullable=False),
    Column(
        "variant_id",
        entity_uuid_type(),
        ForeignKey("recipe_source_card_variants.id", ondelete="RESTRICT"),
        nullable=False,
    ),
    Column("position", Integer, nullable=False),
    Column("name_ru", String, nullable=False),
    Column("gross_g", DecimalText()),
    Column("net_g", DecimalText()),
    Column("quantity_text", String),
    Column("source_form_note", String),
    Column("optional", Boolean, nullable=False),
    Column("created_at", UTCDateTime(), nullable=False),
    UniqueConstraint(
        "variant_id", "position", name="uq_recipe_source_ingredient_position"
    ),
    CheckConstraint("position > 0", name="ck_recipe_source_ingredient_position"),
)

recipe_source_declared_nutrients_table = Table(
    "recipe_source_declared_nutrients",
    recipe_source_corpus_metadata,
    Column("id", entity_uuid_type(), primary_key=True, nullable=False),
    Column(
        "variant_id",
        entity_uuid_type(),
        ForeignKey("recipe_source_card_variants.id", ondelete="RESTRICT"),
        nullable=False,
    ),
    Column("nutrient_code", String, nullable=False),
    Column("value", DecimalText(), nullable=False),
    Column("unit", String, nullable=False),
    Column("source_label", String, nullable=False),
    Column("created_at", UTCDateTime(), nullable=False),
    UniqueConstraint(
        "variant_id", "nutrient_code", name="uq_recipe_source_nutrient_code"
    ),
)

Index(
    "idx_recipe_source_cards_document",
    recipe_source_cards_table.c.document_id,
    recipe_source_cards_table.c.source_section_code,
    recipe_source_cards_table.c.source_card_code,
)
Index(
    "idx_recipe_source_variants_card",
    recipe_source_card_variants_table.c.card_id,
    recipe_source_card_variants_table.c.position,
)
Index(
    "idx_recipe_source_ingredients_variant",
    recipe_source_card_ingredients_table.c.variant_id,
    recipe_source_card_ingredients_table.c.position,
)
Index(
    "idx_recipe_source_nutrients_variant",
    recipe_source_declared_nutrients_table.c.variant_id,
    recipe_source_declared_nutrients_table.c.nutrient_code,
)
