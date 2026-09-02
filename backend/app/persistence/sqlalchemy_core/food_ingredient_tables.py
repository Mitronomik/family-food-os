"""SQLAlchemy Core runtime metadata for the platform Food Catalogue."""

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    ForeignKey,
    Index,
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

food_catalogue_metadata = MetaData()

food_ingredients_table = Table(
    "food_ingredients",
    food_catalogue_metadata,
    Column("id", entity_uuid_type(), primary_key=True, nullable=False),
    Column("canonical_code", String, nullable=False),
    Column("canonical_name", String, nullable=False),
    Column("canonical_name_key", String, nullable=False),
    Column("category_code", String, nullable=False),
    Column("default_unit", String, nullable=False),
    Column("density_g_per_ml", DecimalText(), nullable=True),
    Column("edible_fraction", DecimalText(), nullable=True),
    Column("allergens_reviewed", Boolean, nullable=False),
    Column("storage_profile_code", String, nullable=True),
    Column("is_active", Boolean, nullable=False),
    Column("created_at", UTCDateTime(), nullable=False),
    Column("updated_at", UTCDateTime(), nullable=False),
    UniqueConstraint("canonical_code", name="uq_food_ingredients_canonical_code"),
    UniqueConstraint(
        "canonical_name_key", name="uq_food_ingredients_canonical_name_key"
    ),
    CheckConstraint(
        "length(trim(canonical_code)) > 0",
        name="ck_food_ingredients_canonical_code_nonempty",
    ),
    CheckConstraint(
        "length(trim(canonical_name)) > 0",
        name="ck_food_ingredients_canonical_name_nonempty",
    ),
    CheckConstraint(
        "length(trim(canonical_name_key)) > 0",
        name="ck_food_ingredients_name_key_nonempty",
    ),
    CheckConstraint(
        "length(trim(category_code)) > 0",
        name="ck_food_ingredients_category_code_nonempty",
    ),
    CheckConstraint(
        "default_unit IN ('g', 'ml', 'pcs')",
        name="ck_food_ingredients_default_unit",
    ),
    CheckConstraint(
        "density_g_per_ml IS NULL OR CAST(density_g_per_ml AS NUMERIC) > 0",
        name="ck_food_ingredients_density_positive",
    ),
    CheckConstraint(
        "edible_fraction IS NULL OR (CAST(edible_fraction AS NUMERIC) > 0 "
        "AND CAST(edible_fraction AS NUMERIC) <= 1)",
        name="ck_food_ingredients_edible_fraction",
    ),
)

food_ingredient_aliases_table = Table(
    "food_ingredient_aliases",
    food_catalogue_metadata,
    Column("id", entity_uuid_type(), primary_key=True, nullable=False),
    Column(
        "food_ingredient_id",
        entity_uuid_type(),
        ForeignKey("food_ingredients.id", ondelete="RESTRICT"),
        nullable=False,
    ),
    Column("alias", String, nullable=False),
    Column("alias_key", String, nullable=False),
    Column("language_code", String, nullable=True),
    Column("created_at", UTCDateTime(), nullable=False),
    UniqueConstraint("alias_key", name="uq_food_ingredient_aliases_alias_key"),
    CheckConstraint(
        "length(trim(alias)) > 0", name="ck_food_ingredient_aliases_alias_nonempty"
    ),
    CheckConstraint(
        "length(trim(alias_key)) > 0",
        name="ck_food_ingredient_aliases_key_nonempty",
    ),
)

food_nutrition_profiles_table = Table(
    "food_nutrition_profiles",
    food_catalogue_metadata,
    Column("id", entity_uuid_type(), primary_key=True, nullable=False),
    Column(
        "food_ingredient_id",
        entity_uuid_type(),
        ForeignKey("food_ingredients.id", ondelete="RESTRICT"),
        nullable=False,
    ),
    Column("basis_grams", DecimalText(), nullable=False),
    Column("kcal", DecimalText(), nullable=False),
    Column("protein_g", DecimalText(), nullable=False),
    Column("fat_g", DecimalText(), nullable=False),
    Column("carbohydrates_g", DecimalText(), nullable=False),
    Column("fiber_g", DecimalText(), nullable=True),
    Column("source_name", String, nullable=False),
    Column("source_id", String, nullable=False),
    Column("source_version", String, nullable=False),
    Column("source_data_type", String, nullable=True),
    Column("verified_at", UTCDateTime(), nullable=False),
    Column("estimated", Boolean, nullable=True),
    Column("is_current", Boolean, nullable=False),
    Column("created_at", UTCDateTime(), nullable=False),
    UniqueConstraint(
        "food_ingredient_id",
        "source_name",
        "source_id",
        "source_version",
        name="uq_food_nutrition_profiles_provenance",
    ),
    CheckConstraint(
        "CAST(basis_grams AS NUMERIC) = 100",
        name="ck_food_nutrition_profiles_basis",
    ),
    CheckConstraint(
        "CAST(kcal AS NUMERIC) >= 0 AND CAST(kcal AS NUMERIC) <= 1000",
        name="ck_food_nutrition_profiles_kcal",
    ),
    CheckConstraint(
        "CAST(protein_g AS NUMERIC) >= 0 AND CAST(protein_g AS NUMERIC) <= 100",
        name="ck_food_nutrition_profiles_protein",
    ),
    CheckConstraint(
        "CAST(fat_g AS NUMERIC) >= 0 AND CAST(fat_g AS NUMERIC) <= 100",
        name="ck_food_nutrition_profiles_fat",
    ),
    CheckConstraint(
        "CAST(carbohydrates_g AS NUMERIC) >= 0 "
        "AND CAST(carbohydrates_g AS NUMERIC) <= 100",
        name="ck_food_nutrition_profiles_carbohydrates",
    ),
    CheckConstraint(
        "fiber_g IS NULL OR (CAST(fiber_g AS NUMERIC) >= 0 "
        "AND CAST(fiber_g AS NUMERIC) <= 100)",
        name="ck_food_nutrition_profiles_fiber",
    ),
)

food_ingredient_allergens_table = Table(
    "food_ingredient_allergens",
    food_catalogue_metadata,
    Column(
        "food_ingredient_id",
        entity_uuid_type(),
        ForeignKey("food_ingredients.id", ondelete="RESTRICT"),
        primary_key=True,
        nullable=False,
    ),
    Column("allergen_code", String, primary_key=True, nullable=False),
    Column("created_at", UTCDateTime(), nullable=False),
    CheckConstraint(
        "length(trim(allergen_code)) > 0",
        name="ck_food_ingredient_allergens_code_nonempty",
    ),
)

Index(
    "idx_food_ingredients_active_name",
    food_ingredients_table.c.is_active,
    food_ingredients_table.c.canonical_name_key,
    food_ingredients_table.c.id,
)
Index(
    "idx_food_ingredient_aliases_ingredient",
    food_ingredient_aliases_table.c.food_ingredient_id,
    food_ingredient_aliases_table.c.alias_key,
)
Index(
    "idx_food_nutrition_profiles_ingredient_current",
    food_nutrition_profiles_table.c.food_ingredient_id,
    food_nutrition_profiles_table.c.is_current,
)
Index(
    "uq_food_nutrition_profiles_one_current",
    food_nutrition_profiles_table.c.food_ingredient_id,
    unique=True,
    sqlite_where=food_nutrition_profiles_table.c.is_current.is_(True),
)
