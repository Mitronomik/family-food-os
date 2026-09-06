"""Production Nutrition audit v2 on an isolated accepted catalogue, with B1 seed."""

import argparse
from collections import Counter
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.db.config import DatabaseConfig  # noqa: E402
from app.domain.nutrition import NutritionStatus, NutritionWarningCode  # noqa: E402
from app.domain.nutrition_evidence import AssessmentStatus, NutritionAssessmentIssue  # noqa: E402
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine  # noqa: E402
from app.persistence.sqlalchemy_core.food_recipe_composition import (  # noqa: E402
    create_food_recipe_catalogue_service,
)  # noqa: E402
from app.persistence.sqlalchemy_core.nutrition_composition import (  # noqa: E402
    create_nutrition_service,
)  # noqa: E402
from app.seed.food_recipes import seed_food_recipes  # noqa: E402
from app.seed.nutrition_measure_evidence import seed_nutrition_measure_evidence  # noqa: E402

REPORT = ROOT / "data/seed/nutrition_measure_evidence/production-audit-v2.json"


def audit_catalogue(engine):
    recipes = create_food_recipe_catalogue_service(engine)
    nutrition = create_nutrition_service(engine)
    statuses, reasons, assessments, issues = Counter(), Counter(), Counter(), Counter()
    records = []
    for recipe in sorted(recipes.list_active(), key=lambda r: r.canonical_code):
        detail = recipes.get_current_verified(recipe.id)
        result = nutrition.recipe_version(detail.version.id)
        statuses[result.status] += 1
        reasons.update(w.code for w in result.warnings)
        rows = []
        for contribution in sorted(
            result.required_contributions + result.optional_contributions,
            key=lambda r: r.row.position,
        ):
            review, measure = contribution.assessment, contribution.measure_evidence
            if review:
                assessments[review.status_code] += 1
                issues.update(review.issues)
            rows.append(
                dict(
                    position=contribution.row.position,
                    assessment=None if review is None else review.status_code,
                    issues=[] if review is None else list(review.issues),
                    evidence_key=None if measure is None else measure.evidence_key,
                    mass_g=None
                    if contribution.nutrition.mass_g is None
                    else str(contribution.nutrition.mass_g),
                    warnings=[w.code for w in contribution.nutrition.warnings],
                )
            )
        records.append(
            dict(
                recipe=recipe.canonical_code,
                source_version=detail.version.source_version,
                status=result.status,
                rows=rows,
            )
        )
    return dict(
        schema_version=2,
        recipes=len(records),
        recipe_ingredient_rows=sum(len(r["rows"]) for r in records),
        statuses={c: statuses[c] for c in NutritionStatus},
        assessment_status_counts={c: assessments[c] for c in AssessmentStatus},
        warning_occurrences={
            c: reasons[c]
            for c in NutritionWarningCode
            if c.value
            not in (
                "MISSING_BIRTH_DATE",
                "FUTURE_BIRTH_DATE",
                "UNSUPPORTED_AGE",
                "UNSUPPORTED_SEX",
                "UNSUPPORTED_ACTIVITY",
                "INVALID_HEIGHT",
                "INVALID_WEIGHT",
                "INVALID_REFERENCE_ENERGY",
                "GOAL_ADJUSTMENT_NOT_APPLIED",
                "REFERENCE_ESTIMATE",
            )
        },
        assessment_issue_occurrences={c: issues[c] for c in NutritionAssessmentIssue},
        records=records,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    with TemporaryDirectory() as directory:
        config = DatabaseConfig(path=Path(directory) / "audit.sqlite")
        seed_food_recipes(config)
        seed_nutrition_measure_evidence(config)
        engine = create_sqlite_engine(config)
        try:
            report = audit_catalogue(engine)
        finally:
            engine.dispose()
    encoded = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.write:
        REPORT.write_text(encoded)
    elif REPORT.read_text() != encoded:
        raise SystemExit("Production audit differs from pinned report.")
    print(
        json.dumps({k: v for k, v in report.items() if k != "records"}, sort_keys=True)
    )


if __name__ == "__main__":
    main()
