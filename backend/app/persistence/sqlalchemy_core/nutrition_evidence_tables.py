"""Core mappings only; migration 0026 owns schema creation."""

from sqlalchemy import Boolean, Column, Integer, MetaData, String, Table
from app.persistence.sqlalchemy_core.types import (
    DecimalText,
    UTCDateTime,
    entity_uuid_type,
)

metadata = MetaData()
nutrition_measure_evidence_table = Table(
    "nutrition_measure_evidence",
    metadata,
    Column("id", entity_uuid_type(), nullable=False, primary_key=True),
    Column("evidence_key", String, nullable=False, primary_key=False),
    Column("source_name", String, nullable=False, primary_key=False),
    Column("source_type", String, nullable=False, primary_key=False),
    Column("source_id", String, nullable=True, primary_key=False),
    Column("source_version", String, nullable=False, primary_key=False),
    Column("source_url", String, nullable=True, primary_key=False),
    Column("food_description", String, nullable=True, primary_key=False),
    Column("form_modifier", String, nullable=True, primary_key=False),
    Column("edible_basis", String, nullable=True, primary_key=False),
    Column("source_measure_amount", DecimalText(), nullable=True, primary_key=False),
    Column("source_measure_text", String, nullable=True, primary_key=False),
    Column(
        "normalized_input_quantity", DecimalText(), nullable=False, primary_key=False
    ),
    Column("normalized_input_unit", String, nullable=False, primary_key=False),
    Column("gram_weight", DecimalText(), nullable=False, primary_key=False),
    Column("evidence_quality", String, nullable=False, primary_key=False),
    Column("estimated", Boolean, nullable=False, primary_key=False),
    Column("retrieved_at", UTCDateTime(), nullable=True, primary_key=False),
    Column("created_at", UTCDateTime(), nullable=False, primary_key=False),
)
recipe_ingredient_nutrition_assessments_table = Table(
    "recipe_ingredient_nutrition_assessments",
    metadata,
    Column("id", entity_uuid_type(), nullable=False, primary_key=True),
    Column(
        "recipe_ingredient_id", entity_uuid_type(), nullable=False, primary_key=False
    ),
    Column(
        "nutrition_profile_id", entity_uuid_type(), nullable=False, primary_key=False
    ),
    Column("assessment_version", Integer, nullable=False, primary_key=False),
    Column("is_current", Boolean, nullable=False, primary_key=False),
    Column("status_code", String, nullable=False, primary_key=False),
    Column("semantic_compatibility_code", String, nullable=False, primary_key=False),
    Column("conversion_decision_code", String, nullable=True, primary_key=False),
    Column("measure_evidence_id", entity_uuid_type(), nullable=True, primary_key=False),
    Column("source_audit_operation", String, nullable=False, primary_key=False),
    Column("source_audit_key", String, nullable=False, primary_key=False),
    Column("review_note", String, nullable=False, primary_key=False),
    Column("reviewed_at", UTCDateTime(), nullable=False, primary_key=False),
    Column("created_at", UTCDateTime(), nullable=False, primary_key=False),
)
recipe_ingredient_nutrition_assessment_issues_table = Table(
    "recipe_ingredient_nutrition_assessment_issues",
    metadata,
    Column("assessment_id", entity_uuid_type(), nullable=False, primary_key=True),
    Column("position", Integer, nullable=False, primary_key=True),
    Column("issue_code", String, nullable=False, primary_key=False),
)
