"""SQLAlchemy Core mapping for Step 10-A Recipe Nutrition authority."""

from sqlalchemy import (
    Column,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    MetaData,
    String,
    Table,
)

from app.persistence.sqlalchemy_core.types import (
    DecimalText,
    UTCDateTime,
    entity_uuid_type,
)

metadata = MetaData()

recipe_ingredient_composition_bindings_table = Table(
    "recipe_ingredient_composition_bindings",
    metadata,
    Column(
        "recipe_ingredient_id",
        entity_uuid_type(),
        ForeignKey("food_recipe_ingredients.id", ondelete="RESTRICT"),
        primary_key=True,
        nullable=False,
    ),
    Column(
        "composition_version_id",
        entity_uuid_type(),
        ForeignKey("food_composition_versions.id", ondelete="RESTRICT"),
        nullable=False,
    ),
    Column(
        "registry_version",
        String,
        ForeignKey("nutrient_registry_snapshots.version", ondelete="RESTRICT"),
        nullable=False,
    ),
    Column("nutrient_set_version", String, nullable=False),
    Column("composition_calculation_version", String, nullable=False),
    Column("recipe_calculation_version", String, nullable=False),
    Column("created_at", UTCDateTime(), nullable=False),
)


recipe_prepared_nutrition_authorities_table = Table(
    "recipe_prepared_nutrition_authorities",
    metadata,
    Column(
        "recipe_version_id",
        entity_uuid_type(),
        ForeignKey("food_recipe_versions.id", ondelete="RESTRICT"),
        primary_key=True,
        nullable=False,
    ),
    Column("registry_version", String, nullable=False),
    Column("nutrient_set_version", String, nullable=False),
    Column("recipe_calculation_version", String, nullable=False),
    Column("output_mass_g", DecimalText(), nullable=False),
    Column("source_name", String, nullable=False),
    Column("source_id", String, nullable=False),
    Column("source_version", String, nullable=False),
    Column("source_locator", String, nullable=False),
    Column("source_document_sha256", String, nullable=False),
    Column("source_data_type", String, nullable=False),
    Column("rights_review_status", String, nullable=False),
    Column("rights_basis", String, nullable=False),
    Column("review_reference", String, nullable=False),
    Column("value_count", Integer, nullable=False),
    Column("value_sha256", String, nullable=False),
    Column("created_at", UTCDateTime(), nullable=False),
)

recipe_prepared_nutrient_values_table = Table(
    "recipe_prepared_nutrient_values",
    metadata,
    Column(
        "recipe_version_id",
        entity_uuid_type(),
        ForeignKey("food_recipe_versions.id", ondelete="RESTRICT"),
        primary_key=True,
        nullable=False,
    ),
    Column("registry_version", String, primary_key=False, nullable=False),
    Column("nutrient_code", String, primary_key=True, nullable=False),
    Column("amount", DecimalText(), nullable=False),
    Column("provenance_json", String, nullable=False),
    ForeignKeyConstraint(
        ["registry_version", "nutrient_code"],
        ["nutrient_definitions.registry_version", "nutrient_definitions.code"],
        ondelete="RESTRICT",
    ),
)
