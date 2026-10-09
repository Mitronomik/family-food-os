"""SQLAlchemy Core mappings; 0043_shopping_engine is schema authority."""

from sqlalchemy import Column, Date, Integer, MetaData, String, Table

from app.persistence.sqlalchemy_core.types import (
    DecimalText,
    UTCDateTime,
    entity_uuid_type,
)

shopping_metadata = MetaData()

shopping_lists_table = Table(
    "shopping_lists",
    shopping_metadata,
    Column("id", entity_uuid_type(), primary_key=True),
    Column("household_id", entity_uuid_type(), nullable=False),
    Column("meal_plan_id", entity_uuid_type(), nullable=False),
    Column("source_plan_revision_number", Integer, nullable=False),
    Column("source_pantry_snapshot_hash", String, nullable=False),
    Column("as_of_date", Date, nullable=False),
    Column("engine_version", String, nullable=False),
    Column("pantry_policy_version", String, nullable=False),
    Column("config_fingerprint", String, nullable=False),
    Column("source_fingerprint", String, nullable=False),
    Column("content_fingerprint", String, nullable=False),
    Column("status", String, nullable=False),
    Column("price_status", String, nullable=False),
    Column("provenance_json", String, nullable=False),
    Column("supersedes_list_id", entity_uuid_type()),
    Column("created_at", UTCDateTime(), nullable=False),
)

shopping_list_items_table = Table(
    "shopping_list_items",
    shopping_metadata,
    Column("id", entity_uuid_type(), primary_key=True),
    Column("shopping_list_id", entity_uuid_type(), nullable=False),
    Column("household_id", entity_uuid_type(), nullable=False),
    Column("food_ingredient_id", entity_uuid_type(), nullable=False),
    Column("form_basis", String, nullable=False),
    Column("unit", String, nullable=False),
    Column("required_quantity", DecimalText(), nullable=False),
    Column("pantry_available_quantity", DecimalText(), nullable=False),
    Column("purchase_quantity", DecimalText(), nullable=False),
    Column("ordinal", Integer, nullable=False),
)

shopping_unresolved_obligations_table = Table(
    "shopping_unresolved_obligations",
    shopping_metadata,
    Column("id", entity_uuid_type(), primary_key=True),
    Column("shopping_list_id", entity_uuid_type(), nullable=False),
    Column("household_id", entity_uuid_type(), nullable=False),
    Column("meal_event_id", entity_uuid_type(), nullable=False),
    Column("source_kind", String, nullable=False),
    Column("reason", String, nullable=False),
    Column("ordinal", Integer, nullable=False),
)
