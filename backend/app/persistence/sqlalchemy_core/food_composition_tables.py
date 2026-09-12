"""Core metadata; migration 0029 owns constraints/triggers and SQLite schema."""

from sqlalchemy import Column, ForeignKey, Integer, String, Table, UniqueConstraint
from app.persistence.sqlalchemy_core.food_ingredient_tables import (
    food_catalogue_metadata,
)
from app.persistence.sqlalchemy_core.types import DecimalText, entity_uuid_type


def _common():
    return [
        Column("id", entity_uuid_type(), primary_key=True),
        Column("version", Integer, nullable=False),
        Column("input_state", String, nullable=False),
        Column("provenance_json", String, nullable=False),
        Column("snapshot_sha256", String, nullable=False),
    ]


def _reference(name, target, *, nullable=False, deferred=False, primary_key=False):
    return Column(
        name,
        entity_uuid_type(),
        ForeignKey(
            target,
            ondelete="RESTRICT",
            deferrable=True if deferred else None,
            initially="DEFERRED" if deferred else None,
        ),
        nullable=nullable,
        primary_key=primary_key,
    )


yield_models = Table(
    "food_yield_models",
    food_catalogue_metadata,
    *_common(),
    Column("output_state", String, nullable=False),
    Column("factor", DecimalText(), nullable=False),
)
retention_profiles = Table(
    "food_retention_profiles",
    food_catalogue_metadata,
    *_common(),
    Column("output_state", String, nullable=False),
    Column("value_count", Integer, nullable=False),
)
retention_values = Table(
    "food_retention_values",
    food_catalogue_metadata,
    _reference(
        "profile_id", "food_retention_profiles.id", deferred=True, primary_key=True
    ),
    Column(
        "nutrient_code",
        String,
        ForeignKey("nutrient_definitions.code", ondelete="RESTRICT"),
        primary_key=True,
    ),
    Column("factor", DecimalText(), nullable=False),
    Column("provenance_json", String, nullable=False),
)
transformations = Table(
    "food_transformations",
    food_catalogue_metadata,
    *_common(),
    Column("output_state", String, nullable=False),
    Column("transformation_type", String, nullable=False),
    _reference("yield_model_id", "food_yield_models.id", nullable=True),
    _reference("retention_profile_id", "food_retention_profiles.id", nullable=True),
)
versions = Table(
    "food_composition_versions",
    food_catalogue_metadata,
    *_common(),
    _reference("food_ingredient_id", "food_ingredients.id"),
    Column("kind", String, nullable=False),
    _reference("profile_id", "nutrition_vector_seals.profile_id", nullable=True),
    Column("node_count", Integer, nullable=False),
    Column("step_count", Integer, nullable=False),
    UniqueConstraint("food_ingredient_id", "version"),
)
nodes = Table(
    "food_composition_nodes",
    food_catalogue_metadata,
    Column("id", entity_uuid_type(), primary_key=True),
    _reference("composition_id", "food_composition_versions.id", deferred=True),
    Column("position", Integer, nullable=False),
    _reference("child_version_id", "food_composition_versions.id", deferred=True),
    Column("input_mass_g", DecimalText(), nullable=False),
    Column("mass_state", String, nullable=False),
    UniqueConstraint("composition_id", "position"),
)
steps = Table(
    "food_composition_steps",
    food_catalogue_metadata,
    Column("id", entity_uuid_type(), primary_key=True),
    _reference("composition_id", "food_composition_versions.id", deferred=True),
    Column("position", Integer, nullable=False),
    _reference("transformation_id", "food_transformations.id"),
    UniqueConstraint("composition_id", "position"),
)
