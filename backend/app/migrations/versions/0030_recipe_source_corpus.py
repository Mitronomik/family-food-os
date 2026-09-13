"""Versioned pre-publication corpus for normative/base recipe cards."""

MIGRATION_ID = "0030_recipe_source_corpus"

STATEMENTS = (
    """CREATE TABLE recipe_source_documents (
        id CHAR(32) NOT NULL PRIMARY KEY,
        source_code TEXT NOT NULL,
        title_ru TEXT NOT NULL,
        authority_ru TEXT NOT NULL,
        source_url TEXT NOT NULL,
        source_version TEXT NOT NULL,
        retrieved_at TEXT NOT NULL,
        raw_format TEXT NOT NULL CHECK(raw_format IN ('TEXT','HTML','PDF_TEXT','JSON')),
        raw_bytes_sha256 TEXT NOT NULL CHECK(length(raw_bytes_sha256)=64),
        raw_text_sha256 TEXT NOT NULL CHECK(length(raw_text_sha256)=64),
        publication_policy TEXT NOT NULL CHECK(publication_policy='NORMATIVE_BASE_RECIPE_APPROVED'),
        created_at TEXT NOT NULL,
        UNIQUE(source_code, source_version, raw_bytes_sha256)
    )""",
    """CREATE TABLE recipe_source_cards (
        id CHAR(32) NOT NULL PRIMARY KEY,
        document_id CHAR(32) NOT NULL REFERENCES recipe_source_documents(id) ON DELETE RESTRICT,
        source_section_code TEXT NOT NULL CHECK(length(source_section_code)>0),
        source_card_code TEXT NOT NULL,
        source_page_url TEXT,
        name_ru TEXT NOT NULL,
        category_ru TEXT,
        source_recipe_basis TEXT,
        technology_text_ru TEXT,
        raw_card_text TEXT NOT NULL,
        raw_card_sha256 TEXT NOT NULL CHECK(length(raw_card_sha256)=64),
        capture_status TEXT NOT NULL CHECK(capture_status IN ('RAW_CAPTURED','STRUCTURED','PARTIAL')),
        created_at TEXT NOT NULL,
        UNIQUE(document_id, source_section_code, source_card_code, raw_card_sha256)
    )""",
    """CREATE TABLE recipe_source_card_variants (
        id CHAR(32) NOT NULL PRIMARY KEY,
        card_id CHAR(32) NOT NULL REFERENCES recipe_source_cards(id) ON DELETE RESTRICT,
        position INTEGER NOT NULL CHECK(typeof(position)='integer' AND position>0),
        variant_code TEXT NOT NULL,
        label_ru TEXT NOT NULL,
        output_g TEXT,
        output_text TEXT,
        created_at TEXT NOT NULL,
        UNIQUE(card_id, position), UNIQUE(card_id, variant_code)
    )""",
    """CREATE TABLE recipe_source_card_ingredients (
        id CHAR(32) NOT NULL PRIMARY KEY,
        variant_id CHAR(32) NOT NULL REFERENCES recipe_source_card_variants(id) ON DELETE RESTRICT,
        position INTEGER NOT NULL CHECK(typeof(position)='integer' AND position>0),
        name_ru TEXT NOT NULL,
        gross_g TEXT,
        net_g TEXT,
        quantity_text TEXT,
        source_form_note TEXT,
        optional INTEGER NOT NULL CHECK(optional IN (0,1)),
        created_at TEXT NOT NULL,
        UNIQUE(variant_id, position)
    )""",
    """CREATE TABLE recipe_source_declared_nutrients (
        id CHAR(32) NOT NULL PRIMARY KEY,
        variant_id CHAR(32) NOT NULL REFERENCES recipe_source_card_variants(id) ON DELETE RESTRICT,
        nutrient_code TEXT NOT NULL,
        value TEXT NOT NULL,
        unit TEXT NOT NULL,
        source_label TEXT NOT NULL,
        created_at TEXT NOT NULL,
        UNIQUE(variant_id, nutrient_code)
    )""",
    "CREATE INDEX idx_recipe_source_cards_document ON recipe_source_cards(document_id, source_section_code, source_card_code)",
    "CREATE INDEX idx_recipe_source_variants_card ON recipe_source_card_variants(card_id, position)",
    "CREATE INDEX idx_recipe_source_ingredients_variant ON recipe_source_card_ingredients(variant_id, position)",
    "CREATE INDEX idx_recipe_source_nutrients_variant ON recipe_source_declared_nutrients(variant_id, nutrient_code)",
)


def upgrade(connection):
    if not connection.in_transaction:
        connection.execute("BEGIN")
    for statement in STATEMENTS:
        connection.execute(statement)
