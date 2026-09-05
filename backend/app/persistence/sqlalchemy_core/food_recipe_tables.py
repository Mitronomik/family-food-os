"""SQLAlchemy Core runtime metadata for the verified Recipe Catalogue."""

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
    UniqueConstraint,
)

from app.persistence.sqlalchemy_core.types import (
    DecimalText,
    UTCDateTime,
    entity_uuid_type,
)

food_recipe_metadata = MetaData()

food_recipes_table = Table(
    "food_recipes",
    food_recipe_metadata,
    Column("id", entity_uuid_type(), primary_key=True, nullable=False),
    Column("canonical_code", String, nullable=False),
    Column("canonical_name", String, nullable=False),
    Column("canonical_name_key", String, nullable=False),
    Column("is_active", Boolean, nullable=False),
    Column("created_at", UTCDateTime(), nullable=False),
    Column("updated_at", UTCDateTime(), nullable=False),
    UniqueConstraint("canonical_code", name="uq_food_recipes_canonical_code"),
    UniqueConstraint("canonical_name_key", name="uq_food_recipes_canonical_name_key"),
)

food_recipe_versions_table = Table(
    "food_recipe_versions",
    food_recipe_metadata,
    Column("id", entity_uuid_type(), primary_key=True, nullable=False),
    Column(
        "recipe_id",
        entity_uuid_type(),
        ForeignKey("food_recipes.id", ondelete="RESTRICT"),
        nullable=False,
    ),
    Column("version_number", Integer, nullable=False),
    Column("base_servings", DecimalText(), nullable=False),
    Column("meal_type_code", String, nullable=False),
    Column("prep_time_minutes", Integer),
    Column("cook_time_minutes", Integer),
    Column("total_time_minutes", Integer),
    Column("difficulty_code", String),
    Column("batch_friendly", Boolean),
    Column("freezable", Boolean),
    Column("storage_days_fridge", Integer),
    Column("storage_days_freezer", Integer),
    Column("verification_status", String, nullable=False),
    Column("verified_at", UTCDateTime()),
    Column("source_name", String, nullable=False),
    Column("source_recipe_id", String, nullable=False),
    Column("source_url", String, nullable=False),
    Column("source_version", String, nullable=False),
    Column("source_retrieved_at", UTCDateTime(), nullable=False),
    Column("source_document_sha256", String, nullable=False),
    Column("source_original_servings", DecimalText(), nullable=False),
    Column("rights_review_status", String, nullable=False),
    Column("rights_basis", String),
    Column(
        "created_from_version_id",
        entity_uuid_type(),
        ForeignKey("food_recipe_versions.id", ondelete="RESTRICT"),
    ),
    Column("change_note", String, nullable=False),
    Column("created_at", UTCDateTime(), nullable=False),
    UniqueConstraint(
        "recipe_id", "version_number", name="uq_food_recipe_versions_number"
    ),
    UniqueConstraint(
        "recipe_id",
        "source_name",
        "source_recipe_id",
        "source_version",
        name="uq_food_recipe_versions_provenance",
    ),
    CheckConstraint(
        "version_number > 0", name="ck_food_recipe_versions_number_positive"
    ),
    CheckConstraint(
        "CAST(base_servings AS NUMERIC) > 0",
        name="ck_food_recipe_versions_servings_positive",
    ),
)

food_recipe_ingredients_table = Table(
    "food_recipe_ingredients",
    food_recipe_metadata,
    Column("id", entity_uuid_type(), primary_key=True, nullable=False),
    Column(
        "recipe_version_id",
        entity_uuid_type(),
        ForeignKey("food_recipe_versions.id", ondelete="RESTRICT"),
        nullable=False,
    ),
    Column(
        "food_ingredient_id",
        entity_uuid_type(),
        ForeignKey("food_ingredients.id", ondelete="RESTRICT"),
        nullable=False,
    ),
    Column("position", Integer, nullable=False),
    Column("quantity", DecimalText(), nullable=False),
    Column("unit", String, nullable=False),
    Column("source_amount_text", String, nullable=False),
    Column("normalization_note", String),
    Column("prep_note", String),
    Column("optional", Boolean, nullable=False),
    Column("created_at", UTCDateTime(), nullable=False),
    UniqueConstraint(
        "recipe_version_id", "position", name="uq_food_recipe_ingredients_position"
    ),
    CheckConstraint(
        "position > 0", name="ck_food_recipe_ingredients_position_positive"
    ),
    CheckConstraint(
        "CAST(quantity AS NUMERIC) > 0",
        name="ck_food_recipe_ingredients_quantity_positive",
    ),
    CheckConstraint(
        "unit IN ('g', 'ml', 'pcs')", name="ck_food_recipe_ingredients_unit"
    ),
)

food_recipe_steps_table = Table(
    "food_recipe_steps",
    food_recipe_metadata,
    Column("id", entity_uuid_type(), primary_key=True, nullable=False),
    Column(
        "recipe_version_id",
        entity_uuid_type(),
        ForeignKey("food_recipe_versions.id", ondelete="RESTRICT"),
        nullable=False,
    ),
    Column("position", Integer, nullable=False),
    Column("instruction", String, nullable=False),
    Column("stage_code", String),
    Column("created_at", UTCDateTime(), nullable=False),
    UniqueConstraint(
        "recipe_version_id", "position", name="uq_food_recipe_steps_position"
    ),
    CheckConstraint("position > 0", name="ck_food_recipe_steps_position_positive"),
)

food_recipe_equipment_table = Table(
    "food_recipe_equipment",
    food_recipe_metadata,
    Column(
        "recipe_version_id",
        entity_uuid_type(),
        ForeignKey("food_recipe_versions.id", ondelete="RESTRICT"),
        primary_key=True,
        nullable=False,
    ),
    Column("position", Integer, primary_key=True, nullable=False),
    Column("equipment_code", String, nullable=False),
    UniqueConstraint(
        "recipe_version_id", "equipment_code", name="uq_food_recipe_equipment_code"
    ),
    CheckConstraint("position > 0", name="ck_food_recipe_equipment_position_positive"),
)

Index(
    "idx_food_recipes_active_name",
    food_recipes_table.c.is_active,
    food_recipes_table.c.canonical_name_key,
    food_recipes_table.c.id,
)
Index(
    "idx_food_recipe_versions_recipe_number",
    food_recipe_versions_table.c.recipe_id,
    food_recipe_versions_table.c.version_number,
)
Index(
    "idx_food_recipe_versions_current_verified",
    food_recipe_versions_table.c.recipe_id,
    food_recipe_versions_table.c.verification_status,
    food_recipe_versions_table.c.version_number,
)
Index(
    "idx_food_recipe_ingredients_version_position",
    food_recipe_ingredients_table.c.recipe_version_id,
    food_recipe_ingredients_table.c.position,
)
Index(
    "idx_food_recipe_steps_version_position",
    food_recipe_steps_table.c.recipe_version_id,
    food_recipe_steps_table.c.position,
)
