"""Driver-independent readers and versioned review writer contracts."""

from typing import Protocol
from uuid import UUID

from app.domain.nutrition_evidence import (
    MeasureMassEvidence,
    RecipeIngredientNutritionAssessment,
)


class NutritionEvidenceReader(Protocol):
    def get_evidence(self, evidence_id: UUID) -> MeasureMassEvidence | None: ...
    def get_current_assessment(
        self, recipe_ingredient_id: UUID
    ) -> RecipeIngredientNutritionAssessment | None: ...


class NutritionEvidenceRepository(NutritionEvidenceReader, Protocol):
    def get_by_key(self, evidence_key: str) -> MeasureMassEvidence | None: ...
    def add_evidence(self, evidence: MeasureMassEvidence) -> None: ...
    def add_assessment(
        self, assessment: RecipeIngredientNutritionAssessment
    ) -> None: ...


class NutritionEvidenceConflictError(RuntimeError):
    """Immutable fact, reference or assessment version conflicts."""
