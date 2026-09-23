"""SQLAlchemy Core Step 6A runtime table description."""

from sqlalchemy import (
    CheckConstraint,
    Column,
    Date,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    String,
    Table,
    UniqueConstraint,
)

from app.persistence.sqlalchemy_core.types import UTCDateTime, entity_uuid_type


reference_methodology_metadata = MetaData()

member_reference_methodology_selections_table = Table(
    "member_reference_methodology_selections",
    reference_methodology_metadata,
    Column("id", entity_uuid_type(), primary_key=True, nullable=False),
    Column(
        "household_id",
        entity_uuid_type(),
        ForeignKey("households.id", ondelete="RESTRICT"),
        nullable=False,
    ),
    Column(
        "member_id",
        entity_uuid_type(),
        ForeignKey("household_members.id", ondelete="RESTRICT"),
        nullable=False,
    ),
    Column("version_number", Integer, nullable=False),
    Column("nutrition_config_version", String, nullable=False),
    Column("group_reference_methodology_version", String, nullable=True),
    Column("accepted_local_date", Date, nullable=False),
    Column("household_timezone_at_acceptance", String, nullable=False),
    Column("member_updated_at_at_acceptance", UTCDateTime(), nullable=False),
    Column("household_updated_at_at_acceptance", UTCDateTime(), nullable=False),
    Column(
        "acceptance_request_id",
        entity_uuid_type(),
        nullable=False,
    ),
    Column("accepted_at", UTCDateTime(), nullable=False),
    Column(
        "supersedes_selection_id",
        entity_uuid_type(),
        ForeignKey(
            "member_reference_methodology_selections.id",
            ondelete="RESTRICT",
        ),
        nullable=True,
    ),
    Column("created_at", UTCDateTime(), nullable=False),
    UniqueConstraint(
        "household_id",
        "member_id",
        "version_number",
        name="uq_member_reference_methodology_version",
    ),
    UniqueConstraint(
        "acceptance_request_id",
        name="uq_member_reference_methodology_request",
    ),
    CheckConstraint(
        "version_number > 0",
        name="ck_member_reference_methodology_version_positive",
    ),
    CheckConstraint(
        "length(trim(nutrition_config_version)) > 0",
        name="ck_member_reference_methodology_config_nonempty",
    ),
    CheckConstraint(
        "group_reference_methodology_version IS NULL "
        "OR length(trim(group_reference_methodology_version)) > 0",
        name="ck_member_reference_methodology_group_nonempty",
    ),
    CheckConstraint(
        "length(trim(household_timezone_at_acceptance)) > 0",
        name="ck_member_reference_methodology_timezone_nonempty",
    ),
)

Index(
    "idx_member_reference_methodology_current",
    member_reference_methodology_selections_table.c.household_id,
    member_reference_methodology_selections_table.c.member_id,
    member_reference_methodology_selections_table.c.version_number.desc(),
)
