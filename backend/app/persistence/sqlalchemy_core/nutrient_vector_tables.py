"""Core read/write metadata; migration 0028 remains the SQLite schema authority."""

from sqlalchemy import Column, ForeignKey, Integer, String, Table

from app.persistence.sqlalchemy_core.food_ingredient_tables import (
    food_catalogue_metadata,
)
from app.persistence.sqlalchemy_core.types import DecimalText, entity_uuid_type

registry_snapshots = Table(
    "nutrient_registry_snapshots",
    food_catalogue_metadata,
    Column("version", String, primary_key=True),
    Column("bundle_json", String, nullable=False),
    Column("bundle_sha256", String, nullable=False),
)
nutrient_definitions = Table(
    "nutrient_definitions",
    food_catalogue_metadata,
    Column("code", String, primary_key=True),
    Column("display_name_ru", String, nullable=False),
    Column("unit", String, nullable=False),
    Column(
        "registry_version",
        String,
        ForeignKey("nutrient_registry_snapshots.version", ondelete="RESTRICT"),
        nullable=False,
    ),
    Column("definition_json", String, nullable=False),
)
nutrient_values = Table(
    "nutrient_values",
    food_catalogue_metadata,
    Column(
        "profile_id",
        entity_uuid_type(),
        ForeignKey(
            "nutrition_vector_seals.profile_id",
            ondelete="RESTRICT",
            deferrable=True,
            initially="DEFERRED",
        ),
        primary_key=True,
    ),
    Column(
        "nutrient_code",
        String,
        ForeignKey("nutrient_definitions.code", ondelete="RESTRICT"),
        primary_key=True,
    ),
    Column("amount", DecimalText(), nullable=False),
    Column("provenance_json", String, nullable=False),
)
vector_seals = Table(
    "nutrition_vector_seals",
    food_catalogue_metadata,
    Column(
        "profile_id",
        entity_uuid_type(),
        ForeignKey("food_nutrition_profiles.id", ondelete="RESTRICT"),
        primary_key=True,
    ),
    Column(
        "registry_version",
        String,
        ForeignKey("nutrient_registry_snapshots.version", ondelete="RESTRICT"),
        nullable=False,
    ),
    Column("value_count", Integer, nullable=False),
    Column("value_sha256", String, nullable=False),
    Column("observations_json", String, nullable=False),
)
