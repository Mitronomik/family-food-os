"""SQLAlchemy Core metadata for Household-owned MealPlan / Serving state."""

from sqlalchemy import (
    Boolean,
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

from app.persistence.sqlalchemy_core.types import (
    DecimalText,
    UTCDateTime,
    entity_uuid_type,
)

meal_plan_metadata = MetaData()

member_meal_pattern_selections_table = Table(
    "member_meal_pattern_selections",
    meal_plan_metadata,
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
    Column("source_kind", String, nullable=False),
    Column(
        "program_version_id",
        entity_uuid_type(),
        ForeignKey("meal_pattern_program_versions.id", ondelete="RESTRICT"),
    ),
    Column("recommender_version", String),
    Column("has_user_overrides", Boolean, nullable=False),
    Column("accepted_at", UTCDateTime(), nullable=False),
    Column(
        "supersedes_selection_id",
        entity_uuid_type(),
        ForeignKey("member_meal_pattern_selections.id", ondelete="RESTRICT"),
    ),
    Column("created_at", UTCDateTime(), nullable=False),
    UniqueConstraint(
        "household_id",
        "member_id",
        "version_number",
        name="uq_member_meal_pattern_selection_version",
    ),
    CheckConstraint("version_number > 0", name="ck_member_meal_pattern_version_positive"),
    CheckConstraint(
        "source_kind IN ('PROGRAM','CUSTOM')",
        name="ck_member_meal_pattern_source_kind",
    ),
    CheckConstraint(
        "(source_kind = 'PROGRAM' AND program_version_id IS NOT NULL) OR "
        "(source_kind = 'CUSTOM' AND program_version_id IS NULL)",
        name="ck_member_meal_pattern_program_reference",
    ),
)

member_meal_pattern_opportunities_table = Table(
    "member_meal_pattern_opportunities",
    meal_plan_metadata,
    Column(
        "selection_id",
        entity_uuid_type(),
        ForeignKey("member_meal_pattern_selections.id", ondelete="RESTRICT"),
        primary_key=True,
        nullable=False,
    ),
    Column("weekday", Integer, primary_key=True, nullable=False),
    Column("position", Integer, primary_key=True, nullable=False),
    Column("role_code", String, nullable=False),
    CheckConstraint("weekday BETWEEN 1 AND 7", name="ck_member_meal_pattern_weekday"),
    CheckConstraint("position > 0", name="ck_member_meal_pattern_position"),
    CheckConstraint(
        "role_code IN ('BREAKFAST','LUNCH','DINNER','SNACK','PRE_WORKOUT','POST_WORKOUT','OTHER')",
        name="ck_member_meal_pattern_role",
    ),
)

meal_plans_table = Table(
    "meal_plans",
    meal_plan_metadata,
    Column("id", entity_uuid_type(), primary_key=True, nullable=False),
    Column(
        "household_id",
        entity_uuid_type(),
        ForeignKey("households.id", ondelete="RESTRICT"),
        nullable=False,
    ),
    Column("week_start", Date, nullable=False),
    Column("revision_number", Integer, nullable=False),
    Column("status", String, nullable=False),
    Column("config_version", String, nullable=False),
    Column(
        "supersedes_plan_id",
        entity_uuid_type(),
        ForeignKey("meal_plans.id", ondelete="RESTRICT"),
    ),
    Column("created_at", UTCDateTime(), nullable=False),
    UniqueConstraint(
        "household_id",
        "week_start",
        "revision_number",
        name="uq_meal_plan_household_week_revision",
    ),
    CheckConstraint("revision_number > 0", name="ck_meal_plan_revision_positive"),
    CheckConstraint("status IN ('DRAFT','CONFIRMED')", name="ck_meal_plan_status"),
    CheckConstraint("length(trim(config_version)) > 0", name="ck_meal_plan_config"),
)

meal_plan_member_selections_table = Table(
    "meal_plan_member_selections",
    meal_plan_metadata,
    Column(
        "plan_id",
        entity_uuid_type(),
        ForeignKey("meal_plans.id", ondelete="RESTRICT"),
        primary_key=True,
        nullable=False,
    ),
    Column(
        "member_id",
        entity_uuid_type(),
        ForeignKey("household_members.id", ondelete="RESTRICT"),
        primary_key=True,
        nullable=False,
    ),
    Column(
        "selection_id",
        entity_uuid_type(),
        ForeignKey("member_meal_pattern_selections.id", ondelete="RESTRICT"),
        nullable=False,
    ),
)

meal_plan_events_table = Table(
    "meal_plan_events",
    meal_plan_metadata,
    Column("id", entity_uuid_type(), primary_key=True, nullable=False),
    Column(
        "plan_id",
        entity_uuid_type(),
        ForeignKey("meal_plans.id", ondelete="RESTRICT"),
        nullable=False,
    ),
    Column("local_date", Date, nullable=False),
    Column("position", Integer, nullable=False),
    Column("role_code", String, nullable=False),
    Column("source_kind", String, nullable=False),
    Column(
        "recipe_version_id",
        entity_uuid_type(),
        ForeignKey("food_recipe_versions.id", ondelete="RESTRICT"),
    ),
    Column("source_reference", String),
    Column("created_at", UTCDateTime(), nullable=False),
    UniqueConstraint("plan_id", "local_date", "position", name="uq_meal_plan_event_position"),
    CheckConstraint("position > 0", name="ck_meal_plan_event_position"),
    CheckConstraint(
        "role_code IN ('BREAKFAST','LUNCH','DINNER','SNACK','PRE_WORKOUT','POST_WORKOUT','OTHER')",
        name="ck_meal_plan_event_role",
    ),
    CheckConstraint(
        "source_kind IN ('COOK_RECIPE','ASSEMBLY','LEFTOVER','PREPARED','READY_MEAL','ORDER_OUT','EAT_OUT')",
        name="ck_meal_plan_event_source_kind",
    ),
    CheckConstraint(
        "(source_kind = 'COOK_RECIPE' AND recipe_version_id IS NOT NULL) OR "
        "(source_kind <> 'COOK_RECIPE' AND recipe_version_id IS NULL)",
        name="ck_meal_plan_event_recipe_reference",
    ),
)

servings_table = Table(
    "servings",
    meal_plan_metadata,
    Column("id", entity_uuid_type(), primary_key=True, nullable=False),
    Column(
        "event_id",
        entity_uuid_type(),
        ForeignKey("meal_plan_events.id", ondelete="RESTRICT"),
        nullable=False,
    ),
    Column(
        "member_id",
        entity_uuid_type(),
        ForeignKey("household_members.id", ondelete="RESTRICT"),
        nullable=False,
    ),
    Column("portion_servings", DecimalText(), nullable=False),
    Column("created_at", UTCDateTime(), nullable=False),
    UniqueConstraint("event_id", "member_id", name="uq_serving_event_member"),
    CheckConstraint(
        "CAST(portion_servings AS NUMERIC) > 0",
        name="ck_serving_portion_positive",
    ),
)

Index(
    "idx_member_meal_pattern_current",
    member_meal_pattern_selections_table.c.household_id,
    member_meal_pattern_selections_table.c.member_id,
    member_meal_pattern_selections_table.c.version_number.desc(),
)
Index(
    "idx_member_meal_pattern_schedule",
    member_meal_pattern_opportunities_table.c.selection_id,
    member_meal_pattern_opportunities_table.c.weekday,
    member_meal_pattern_opportunities_table.c.position,
)
Index(
    "idx_meal_plans_current",
    meal_plans_table.c.household_id,
    meal_plans_table.c.week_start,
    meal_plans_table.c.revision_number.desc(),
)
Index(
    "idx_meal_plan_events_order",
    meal_plan_events_table.c.plan_id,
    meal_plan_events_table.c.local_date,
    meal_plan_events_table.c.position,
)
Index("idx_servings_event", servings_table.c.event_id, servings_table.c.member_id)
