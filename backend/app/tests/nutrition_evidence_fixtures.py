"""Explicit synthetic review authority for Nutrition tests (never production seed)."""

from datetime import datetime, timezone
from decimal import Decimal

from app.domain.nutrition_evidence import (
    MeasureMassEvidence,
    RecipeIngredientNutritionAssessment,
)

NOW = datetime(2026, 9, 7, tzinfo=timezone.utc)


def assessment(
    row,
    profile,
    *,
    status="APPROVED_NO_CONVERSION",
    evidence=None,
    issues=(),
    semantic="MATCH",
):
    return RecipeIngredientNutritionAssessment(
        id=row.id,
        recipe_ingredient_id=row.id,
        nutrition_profile_id=profile.id,
        assessment_version=1,
        is_current=True,
        status_code=status,
        semantic_compatibility_code=semantic,
        conversion_decision_code=None,
        measure_evidence_id=None if evidence is None else evidence.id,
        source_audit_operation="SYNTHETIC_TEST",
        source_audit_key=f"test:{row.position}",
        review_note="Explicit synthetic row review.",
        reviewed_at=NOW,
        created_at=NOW,
        issues=tuple(sorted(issues)),
    )


def measure(row, *, unit="ml", denominator="3", grams="7", estimated=False):
    return MeasureMassEvidence(
        id=row.id,
        evidence_key="synthetic-measure",
        source_name="Synthetic",
        source_type="TEST",
        source_id="source-food",
        source_version="test-v1",
        source_url=None,
        food_description="Synthetic source food",
        form_modifier="reviewed form",
        edible_basis="edible",
        source_measure_amount=Decimal(1),
        source_measure_text="test portion",
        normalized_input_quantity=Decimal(denominator),
        normalized_input_unit=unit,
        gram_weight=Decimal(grams),
        evidence_quality="SYNTHETIC_TEST",
        estimated=estimated,
        retrieved_at=NOW,
        created_at=NOW,
    )


def gram_assessments(detail, profiles):
    return {
        r.id: assessment(r, profiles[r.food_ingredient_id])
        for r in detail.ingredients
        if r.unit == "g" and r.food_ingredient_id in profiles
    }
