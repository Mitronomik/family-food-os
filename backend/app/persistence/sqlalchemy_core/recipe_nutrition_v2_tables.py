"""SQLAlchemy Core mapping for Step 10-A Recipe Nutrition authority."""

from sqlalchemy import Column, ForeignKey, MetaData, String, Table

from app.persistence.sqlalchemy_core.types import UTCDateTime, entity_uuid_type

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
