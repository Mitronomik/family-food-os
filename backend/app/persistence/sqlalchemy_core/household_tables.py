"""SQLAlchemy Core runtime table descriptions for Household persistence."""

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    ForeignKey,
    Index,
    MetaData,
    String,
    Table,
)

from app.persistence.sqlalchemy_core.types import (
    DecimalText,
    UTCDateTime,
    entity_uuid_type,
)

household_metadata = MetaData()

households_table = Table(
    "households",
    household_metadata,
    Column("id", entity_uuid_type(), primary_key=True, nullable=False),
    Column("name", String, nullable=False),
    Column("timezone", String, nullable=False),
    Column("city", String, nullable=True),
    Column("default_weekly_budget", DecimalText(), nullable=True),
    Column("default_cooking_profile", String, nullable=True),
    Column("created_at", UTCDateTime(), nullable=False),
    Column("updated_at", UTCDateTime(), nullable=False),
    CheckConstraint("length(trim(name)) > 0", name="ck_households_name_nonempty"),
    CheckConstraint(
        "length(trim(timezone)) > 0", name="ck_households_timezone_nonempty"
    ),
)

household_members_table = Table(
    "household_members",
    household_metadata,
    Column("id", entity_uuid_type(), primary_key=True, nullable=False),
    Column(
        "household_id",
        entity_uuid_type(),
        ForeignKey("households.id", ondelete="RESTRICT"),
        nullable=False,
    ),
    Column("name", String, nullable=False),
    Column("active", Boolean, nullable=False),
    Column("birth_date", Date, nullable=True),
    Column("sex", String, nullable=True),
    Column("height_cm", DecimalText(), nullable=True),
    Column("weight_kg", DecimalText(), nullable=True),
    Column("activity_level", String, nullable=False),
    Column("goal", String, nullable=False),
    Column("created_at", UTCDateTime(), nullable=False),
    Column("updated_at", UTCDateTime(), nullable=False),
    CheckConstraint(
        "length(trim(name)) > 0", name="ck_household_members_name_nonempty"
    ),
    CheckConstraint(
        "length(trim(activity_level)) > 0",
        name="ck_household_members_activity_level_nonempty",
    ),
    CheckConstraint(
        "length(trim(goal)) > 0", name="ck_household_members_goal_nonempty"
    ),
)

Index(
    "idx_household_members_household",
    household_members_table.c.household_id,
    household_members_table.c.created_at,
    household_members_table.c.id,
)
