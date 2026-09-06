"""Immutable platform source measurements and explicit row review authority."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from app.domain.units import UnitCode


class AssessmentStatus(StrEnum):
    APPROVED_NO_CONVERSION = "APPROVED_NO_CONVERSION"
    APPROVED_EXACT = "APPROVED_EXACT"
    REVIEW_REQUIRED_ESTIMATE = "REVIEW_REQUIRED_ESTIMATE"
    BLOCKED = "BLOCKED"


class SemanticCompatibility(StrEnum):
    MATCH = "MATCH"
    MATCH_WITH_FORM_QUALIFIER = "MATCH_WITH_FORM_QUALIFIER"
    ACCEPTED_SUBSTITUTION = "ACCEPTED_SUBSTITUTION"
    FORM_MISMATCH = "FORM_MISMATCH"
    IDENTITY_MISMATCH = "IDENTITY_MISMATCH"
    AMBIGUOUS = "AMBIGUOUS"


class ConversionDecision(StrEnum):
    DIRECT_RECIPE_MASS = "DIRECT_RECIPE_MASS"
    FDC_EXACT_PORTION = "FDC_EXACT_PORTION"
    FDC_COMPATIBLE_ESTIMATE = "FDC_COMPATIBLE_ESTIMATE"
    INFOODS_EXACT_OR_STRONG_MATCH = "INFOODS_EXACT_OR_STRONG_MATCH"
    INFOODS_COMPATIBLE_ESTIMATE = "INFOODS_COMPATIBLE_ESTIMATE"
    OTHER_SOURCE_EXACT = "OTHER_SOURCE_EXACT"
    OTHER_SOURCE_ESTIMATE = "OTHER_SOURCE_ESTIMATE"
    FOOD_FORM_MISMATCH = "FOOD_FORM_MISMATCH"
    CANONICAL_IDENTITY_MISMATCH = "CANONICAL_IDENTITY_MISMATCH"
    MEASURE_OR_SIZE_AMBIGUOUS = "MEASURE_OR_SIZE_AMBIGUOUS"
    NO_ACCEPTABLE_SOURCE = "NO_ACCEPTABLE_SOURCE"


class NutritionAssessmentIssue(StrEnum):
    CONVERSION_ESTIMATE_NOT_ACCEPTED = "CONVERSION_ESTIMATE_NOT_ACCEPTED"
    PROFILE_REPRESENTATIVENESS_REVIEW = "PROFILE_REPRESENTATIVENESS_REVIEW"
    SOURCE_ALTERNATIVE_WEIGHT_MISAPPLIED = "SOURCE_ALTERNATIVE_WEIGHT_MISAPPLIED"
    SOURCE_QUANTITY_AMBIGUOUS = "SOURCE_QUANTITY_AMBIGUOUS"
    SOURCE_QUANTITY_MISMATCH = "SOURCE_QUANTITY_MISMATCH"
    FOOD_FORM_MISMATCH = "FOOD_FORM_MISMATCH"
    IDENTITY_MISMATCH = "IDENTITY_MISMATCH"
    MEASURE_OR_SIZE_AMBIGUOUS = "MEASURE_OR_SIZE_AMBIGUOUS"
    NO_ACCEPTABLE_SOURCE = "NO_ACCEPTABLE_SOURCE"


def _positive(value: Decimal) -> None:
    if not isinstance(value, Decimal):
        raise TypeError("Source measurements must be Decimal.")
    if not value.is_finite() or not Decimal("1e-18") <= value <= Decimal("1e24"):
        raise ValueError("Source measurement outside positive bounds.")
    if len(value.as_tuple().digits) > 42 or value.as_tuple().exponent < -18:
        raise ValueError("Source measurement exceeds retained precision.")


def _instant(value: datetime) -> None:
    if not isinstance(value, datetime) or value.utcoffset() is None:
        raise ValueError("Review/source instants must be timezone-aware.")


def _text(value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Evidence and review provenance must be nonblank.")


@dataclass(frozen=True)
class MeasureMassEvidence:
    id: UUID
    evidence_key: str
    source_name: str
    source_type: str
    source_id: str | None
    source_version: str
    source_url: str | None
    food_description: str | None
    form_modifier: str | None
    edible_basis: str | None
    source_measure_amount: Decimal | None
    source_measure_text: str | None
    normalized_input_quantity: Decimal
    normalized_input_unit: UnitCode
    gram_weight: Decimal
    evidence_quality: str
    estimated: bool
    retrieved_at: datetime | None
    created_at: datetime

    def __post_init__(self) -> None:
        if not isinstance(self.id, UUID):
            raise TypeError("Evidence id must be UUID.")
        for value in (
            self.evidence_key,
            self.source_name,
            self.source_type,
            self.source_version,
            self.evidence_quality,
        ):
            _text(value)
        for value in (
            self.source_id,
            self.source_url,
            self.food_description,
            self.form_modifier,
            self.edible_basis,
            self.source_measure_text,
        ):
            if value is not None:
                _text(value)
        object.__setattr__(
            self, "normalized_input_unit", UnitCode(self.normalized_input_unit)
        )
        if self.normalized_input_unit not in (UnitCode.MILLILITER, UnitCode.PIECE):
            raise ValueError("Measure evidence supports ml/pcs only.")
        for value in (self.normalized_input_quantity, self.gram_weight):
            _positive(value)
        if self.source_measure_amount is not None:
            _positive(self.source_measure_amount)
        if type(self.estimated) is not bool:
            raise TypeError("Evidence estimated must be explicit boolean.")
        if self.retrieved_at is not None:
            _instant(self.retrieved_at)
        _instant(self.created_at)


@dataclass(frozen=True)
class RecipeIngredientNutritionAssessment:
    id: UUID
    recipe_ingredient_id: UUID
    nutrition_profile_id: UUID
    assessment_version: int
    is_current: bool
    status_code: AssessmentStatus
    semantic_compatibility_code: SemanticCompatibility
    conversion_decision_code: ConversionDecision | None
    measure_evidence_id: UUID | None
    source_audit_operation: str
    source_audit_key: str
    review_note: str
    reviewed_at: datetime
    created_at: datetime
    issues: tuple[NutritionAssessmentIssue, ...] = ()

    def __post_init__(self) -> None:
        for value in (self.id, self.recipe_ingredient_id, self.nutrition_profile_id):
            if not isinstance(value, UUID):
                raise TypeError("Assessment identities must be UUID.")
        if self.measure_evidence_id is not None and not isinstance(
            self.measure_evidence_id, UUID
        ):
            raise TypeError("Evidence reference must be UUID.")
        if type(self.assessment_version) is not int or self.assessment_version <= 0:
            raise ValueError("Assessment version must be positive integer.")
        if type(self.is_current) is not bool:
            raise TypeError("Current marker must be boolean.")
        object.__setattr__(self, "status_code", AssessmentStatus(self.status_code))
        object.__setattr__(
            self,
            "semantic_compatibility_code",
            SemanticCompatibility(self.semantic_compatibility_code),
        )
        if self.conversion_decision_code is not None:
            object.__setattr__(
                self,
                "conversion_decision_code",
                ConversionDecision(self.conversion_decision_code),
            )
        issues = tuple(NutritionAssessmentIssue(code) for code in self.issues)
        if issues != tuple(sorted(set(issues))):
            raise ValueError("Assessment issues must be unique and lexically ordered.")
        object.__setattr__(self, "issues", issues)
        for value in (
            self.source_audit_operation,
            self.source_audit_key,
            self.review_note,
        ):
            _text(value)
        _instant(self.reviewed_at)
        _instant(self.created_at)
        if self.status_code in (
            AssessmentStatus.APPROVED_EXACT,
            AssessmentStatus.APPROVED_NO_CONVERSION,
        ):
            if issues or self.semantic_compatibility_code in (
                SemanticCompatibility.FORM_MISMATCH,
                SemanticCompatibility.IDENTITY_MISMATCH,
                SemanticCompatibility.AMBIGUOUS,
            ):
                raise ValueError(
                    "Approved assessment cannot contain semantic/review blockers."
                )
        if (
            self.status_code == AssessmentStatus.APPROVED_NO_CONVERSION
            and self.measure_evidence_id is not None
        ):
            raise ValueError("Gram approval must not bind conversion evidence.")
        if (
            self.status_code
            in (
                AssessmentStatus.APPROVED_EXACT,
                AssessmentStatus.REVIEW_REQUIRED_ESTIMATE,
            )
            and self.measure_evidence_id is None
        ):
            raise ValueError("Numeric assessment requires evidence reference.")
        if (
            self.status_code == AssessmentStatus.REVIEW_REQUIRED_ESTIMATE
            and NutritionAssessmentIssue.CONVERSION_ESTIMATE_NOT_ACCEPTED not in issues
        ):
            raise ValueError("Estimate review must retain non-acceptance issue.")
        if self.status_code == AssessmentStatus.BLOCKED and not issues:
            raise ValueError("Blocked assessment requires explicit issues.")
