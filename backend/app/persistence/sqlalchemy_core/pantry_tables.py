"""Runtime Core mappings; migration 0025 remains the schema authority."""

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    ForeignKeyConstraint,
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

pantry_metadata = MetaData()
pantry_items_table = Table(
    "pantry_items",
    pantry_metadata,
    Column("id", entity_uuid_type(), primary_key=True, nullable=False),
    Column("household_id", entity_uuid_type(), nullable=False),
    Column("food_ingredient_id", entity_uuid_type(), nullable=False),
    Column("quantity", DecimalText(), nullable=False),
    Column("unit", String, nullable=False),
    Column("location", String, nullable=False),
    Column("estimated", Boolean, nullable=False),
    Column("purchased_on", Date),
    Column("opened_on", Date),
    Column("expires_on", Date),
    Column("created_at", UTCDateTime(), nullable=False),
    Column("updated_at", UTCDateTime(), nullable=False),
    UniqueConstraint("id", "household_id", "unit"),
)
pantry_movements_table = Table(
    "pantry_movements",
    pantry_metadata,
    Column("id", entity_uuid_type(), primary_key=True, nullable=False),
    Column("household_id", entity_uuid_type(), nullable=False),
    Column("pantry_item_id", entity_uuid_type(), nullable=False),
    Column("movement_type", String, nullable=False),
    Column("quantity", DecimalText(), nullable=False),
    Column("unit", String, nullable=False),
    Column("occurred_at", UTCDateTime(), nullable=False),
    Column("created_at", UTCDateTime(), nullable=False),
    ForeignKeyConstraint(
        ["pantry_item_id", "household_id", "unit"],
        ["pantry_items.id", "pantry_items.household_id", "pantry_items.unit"],
        ondelete="RESTRICT",
    ),
)
Index(
    "idx_pantry_items_household_ingredient_expiry",
    pantry_items_table.c.household_id,
    pantry_items_table.c.food_ingredient_id,
    pantry_items_table.c.expires_on,
    pantry_items_table.c.purchased_on,
    pantry_items_table.c.created_at,
    pantry_items_table.c.id,
)
Index(
    "idx_pantry_items_household_expiry",
    pantry_items_table.c.household_id,
    pantry_items_table.c.expires_on,
    pantry_items_table.c.created_at,
    pantry_items_table.c.id,
)
Index(
    "idx_pantry_movements_item_history",
    pantry_movements_table.c.household_id,
    pantry_movements_table.c.pantry_item_id,
    pantry_movements_table.c.occurred_at,
    pantry_movements_table.c.created_at,
    pantry_movements_table.c.id,
)
