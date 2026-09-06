"""Evidence and assessment storage on the caller's active UoW connection."""

from dataclasses import asdict
from uuid import UUID

from sqlalchemy import insert, select, update
from sqlalchemy.engine import Connection
from sqlalchemy.exc import IntegrityError

from app.domain.nutrition_evidence import (
    MeasureMassEvidence,
    RecipeIngredientNutritionAssessment,
)
from app.persistence.sqlalchemy_core.nutrition_evidence_tables import (
    nutrition_measure_evidence_table as evidence_table,
    recipe_ingredient_nutrition_assessments_table as assessment_table,
    recipe_ingredient_nutrition_assessment_issues_table as issue_table,
)
from app.services.nutrition_evidence_contracts import NutritionEvidenceConflictError


class SqlAlchemyNutritionEvidenceRepository:
    def __init__(self, connection: Connection) -> None:
        self._connection = connection

    def get_evidence(self, evidence_id: UUID) -> MeasureMassEvidence | None:
        return self._evidence(evidence_table.c.id == evidence_id)

    def get_by_key(self, evidence_key: str) -> MeasureMassEvidence | None:
        return self._evidence(evidence_table.c.evidence_key == evidence_key)

    def _evidence(self, predicate) -> MeasureMassEvidence | None:
        row = (
            self._connection.execute(select(evidence_table).where(predicate))
            .mappings()
            .one_or_none()
        )
        return None if row is None else MeasureMassEvidence(**row)

    def add_evidence(self, evidence: MeasureMassEvidence) -> None:
        try:
            self._connection.execute(insert(evidence_table).values(**asdict(evidence)))
        except IntegrityError as exc:
            raise NutritionEvidenceConflictError(
                "Evidence identity or value conflicts."
            ) from exc

    def get_current_assessment(
        self, recipe_ingredient_id: UUID
    ) -> RecipeIngredientNutritionAssessment | None:
        row = (
            self._connection.execute(
                select(assessment_table).where(
                    assessment_table.c.recipe_ingredient_id == recipe_ingredient_id,
                    assessment_table.c.is_current.is_(True),
                )
            )
            .mappings()
            .one_or_none()
        )
        if row is None:
            return None
        issues = tuple(
            self._connection.execute(
                select(issue_table.c.issue_code)
                .where(issue_table.c.assessment_id == row["id"])
                .order_by(issue_table.c.position)
            ).scalars()
        )
        return RecipeIngredientNutritionAssessment(**row, issues=issues)

    def add_assessment(self, assessment: RecipeIngredientNutritionAssessment) -> None:
        """Append reviewed version and retire the previous current marker atomically."""
        if not assessment.is_current:
            raise NutritionEvidenceConflictError("New assessment must be current.")
        current = self.get_current_assessment(assessment.recipe_ingredient_id)
        expected = 1 if current is None else current.assessment_version + 1
        if assessment.assessment_version != expected:
            raise NutritionEvidenceConflictError(
                "Assessment must append the next version."
            )
        values = asdict(assessment)
        values.pop("issues")
        try:
            # A failed append must not retire the previous review even if caught by caller.
            with self._connection.begin_nested():
                if current is not None:
                    self._connection.execute(
                        update(assessment_table)
                        .where(
                            assessment_table.c.id == current.id,
                            assessment_table.c.is_current.is_(True),
                        )
                        .values(is_current=False)
                    )
                # The deferred child FK lets issues precede their parent. Inserting
                # the parent seals the set: later INSERTs (even before commit) fail.
                if assessment.issues:
                    self._connection.execute(
                        insert(issue_table),
                        [
                            {
                                "assessment_id": assessment.id,
                                "position": position,
                                "issue_code": code,
                            }
                            for position, code in enumerate(assessment.issues, 1)
                        ],
                    )
                self._connection.execute(insert(assessment_table).values(**values))
        except IntegrityError as exc:
            raise NutritionEvidenceConflictError(
                "Assessment reference/version/current state conflicts."
            ) from exc
