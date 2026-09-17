"""SQLAlchemy Core metadata for the Meal Pattern Catalogue."""

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

meal_pattern_metadata = MetaData()

meal_pattern_programs_table = Table(
    "meal_pattern_programs",
    meal_pattern_metadata,
    Column("id", entity_uuid_type(), primary_key=True, nullable=False),
    Column("program_code", String, nullable=False),
    Column("created_at", UTCDateTime(), nullable=False),
    UniqueConstraint("program_code", name="uq_meal_pattern_programs_code"),
)

meal_pattern_program_versions_table = Table(
    "meal_pattern_program_versions",
    meal_pattern_metadata,
    Column("id", entity_uuid_type(), primary_key=True, nullable=False),
    Column(
        "program_id",
        entity_uuid_type(),
        ForeignKey("meal_pattern_programs.id", ondelete="RESTRICT"),
        nullable=False,
    ),
    Column("version_number", Integer, nullable=False),
    Column("lifecycle", String, nullable=False),
    Column("scope_code", String, nullable=False),
    Column("display_name_ru", String, nullable=False),
    Column("explanation_ru", String, nullable=False),
    Column("min_age_years", Integer, nullable=False),
    Column("max_age_years", Integer),
    Column("review_status", String, nullable=False),
    Column("reviewed_at", UTCDateTime()),
    Column("published_at", UTCDateTime()),
    Column(
        "created_from_version_id",
        entity_uuid_type(),
        ForeignKey("meal_pattern_program_versions.id", ondelete="RESTRICT"),
    ),
    Column("change_note", String, nullable=False),
    Column("created_at", UTCDateTime(), nullable=False),
    UniqueConstraint(
        "program_id", "version_number", name="uq_meal_pattern_versions_number"
    ),
    CheckConstraint(
        "version_number > 0", name="ck_meal_pattern_versions_number_positive"
    ),
    CheckConstraint(
        "lifecycle IN ('DRAFT','PUBLISHED','INACTIVE')",
        name="ck_meal_pattern_versions_lifecycle",
    ),
    CheckConstraint(
        "scope_code = 'WELLNESS_SCHEDULE'",
        name="ck_meal_pattern_versions_scope",
    ),
    CheckConstraint(
        "min_age_years >= 0", name="ck_meal_pattern_versions_min_age"
    ),
    CheckConstraint(
        "max_age_years IS NULL OR max_age_years >= min_age_years",
        name="ck_meal_pattern_versions_age_range",
    ),
    CheckConstraint(
        "review_status IN ('UNREVIEWED','REVIEWED')",
        name="ck_meal_pattern_versions_review_status",
    ),
)

meal_pattern_opportunities_table = Table(
    "meal_pattern_opportunities",
    meal_pattern_metadata,
    Column(
        "version_id",
        entity_uuid_type(),
        ForeignKey("meal_pattern_program_versions.id", ondelete="RESTRICT"),
        primary_key=True,
        nullable=False,
    ),
    Column("position", Integer, primary_key=True, nullable=False),
    Column("role_code", String, nullable=False),
    CheckConstraint("position > 0", name="ck_meal_pattern_opportunities_position"),
    CheckConstraint(
        "role_code IN ('BREAKFAST','LUNCH','DINNER','SNACK','PRE_WORKOUT','POST_WORKOUT','OTHER')",
        name="ck_meal_pattern_opportunities_role",
    ),
)

meal_pattern_tags_table = Table(
    "meal_pattern_tags",
    meal_pattern_metadata,
    Column(
        "version_id",
        entity_uuid_type(),
        ForeignKey("meal_pattern_program_versions.id", ondelete="RESTRICT"),
        primary_key=True,
        nullable=False,
    ),
    Column("kind", String, primary_key=True, nullable=False),
    Column("code", String, primary_key=True, nullable=False),
    CheckConstraint(
        "kind IN ('GOAL','CONTEXT','EXCLUSION')",
        name="ck_meal_pattern_tags_kind",
    ),
)

meal_pattern_evidence_table = Table(
    "meal_pattern_evidence",
    meal_pattern_metadata,
    Column(
        "version_id",
        entity_uuid_type(),
        ForeignKey("meal_pattern_program_versions.id", ondelete="RESTRICT"),
        primary_key=True,
        nullable=False,
    ),
    Column("position", Integer, primary_key=True, nullable=False),
    Column("source_name", String, nullable=False),
    Column("source_title", String, nullable=False),
    Column("source_url", String, nullable=False),
    Column("source_version", String, nullable=False),
    Column("retrieved_on", Date, nullable=False),
    Column("evidence_scope", String, nullable=False),
    Column("review_note_ru", String, nullable=False),
    CheckConstraint("position > 0", name="ck_meal_pattern_evidence_position"),
)

Index(
    "idx_meal_pattern_versions_program_number",
    meal_pattern_program_versions_table.c.program_id,
    meal_pattern_program_versions_table.c.version_number,
)
Index(
    "idx_meal_pattern_versions_current",
    meal_pattern_program_versions_table.c.program_id,
    meal_pattern_program_versions_table.c.version_number.desc(),
)
Index(
    "idx_meal_pattern_opportunities_version",
    meal_pattern_opportunities_table.c.version_id,
    meal_pattern_opportunities_table.c.position,
)
Index(
    "idx_meal_pattern_evidence_version",
    meal_pattern_evidence_table.c.version_id,
    meal_pattern_evidence_table.c.position,
)
