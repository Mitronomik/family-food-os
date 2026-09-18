"""Generate the Gate1-A current-recipe readiness matrix from a fresh database."""

import argparse
from decimal import Decimal
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.db.config import DatabaseConfig  # noqa: E402
from app.persistence.sqlalchemy_core.b2b2 import B2B2UnitOfWork  # noqa: E402
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine  # noqa: E402
from app.persistence.sqlalchemy_core.food_recipe_composition import (  # noqa: E402
    create_food_recipe_catalogue_service,
)
from app.persistence.sqlalchemy_core.nutrition_composition import (  # noqa: E402
    create_nutrition_service,
)
from app.seed.b2b2 import upgrade_b2b2  # noqa: E402
from app.seed.food_recipes import seed_food_recipes  # noqa: E402
from app.seed.nutrition_measure_evidence import (  # noqa: E402
    seed_nutrition_measure_evidence,
)
from app.seed.recipe_corrections import (  # noqa: E402
    seed_correction_assessments,
    seed_recipe_corrections,
)
from app.seed.ru_food_data import seed_ru_food_data  # noqa: E402


def _plain(value):
    if isinstance(value, Decimal):
        return str(value)
    if hasattr(value, "value"):
        return value.value
    return str(value)


def seed_current(config: DatabaseConfig) -> None:
    seed_food_recipes(config)
    seed_nutrition_measure_evidence(config)
    seed_recipe_corrections(config)
    seed_correction_assessments(config)
    seed_ru_food_data(config)
    upgrade_b2b2(config)


def audit(config: DatabaseConfig) -> dict[str, object]:
    seed_current(config)
    engine = create_sqlite_engine(config)
    try:
        recipes = create_food_recipe_catalogue_service(engine)
        nutrition = create_nutrition_service(engine)
        rows = []
        with B2B2UnitOfWork(engine) as scope:
            for recipe in sorted(
                recipes.list_active(limit=100), key=lambda item: item.canonical_code
            ):
                detail = recipes.get_current_verified(recipe.id)
                result = nutrition.recipe_version(detail.version.id)
                blockers = []
                for contribution in result.required_contributions:
                    if contribution.nutrition.mass_g is not None:
                        continue
                    assessment = contribution.assessment
                    evidence = contribution.measure_evidence
                    food = scope.ingredients.get(contribution.row.food_ingredient_id)
                    blockers.append(
                        {
                            "position": contribution.row.position,
                            "food_code": food.canonical_code,
                            "quantity": str(contribution.row.quantity),
                            "unit": contribution.row.unit.value,
                            "assessment_status": None
                            if assessment is None
                            else assessment.status_code.value,
                            "assessment_issues": []
                            if assessment is None
                            else [item.value for item in assessment.issues],
                            "evidence_key": None
                            if evidence is None
                            else evidence.evidence_key,
                            "required_authority": (
                                "exact input grams for the stated food form, backed by "
                                "an authoritative profile and, for non-gram units, an "
                                "exact same-form measure"
                            ),
                            "accepted_repository_evidence_resolves": False,
                            "new_external_primary_evidence_required": True,
                            "repair_class": "EVIDENCE_OR_IMMUTABLE_RECIPE_REVISION",
                        }
                    )
                rows.append(
                    {
                        "recipe_code": recipe.canonical_code,
                        "recipe_version_id": str(detail.version.id),
                        "version_number": detail.version.version_number,
                        "meal_type_code": detail.version.meal_type_code,
                        "nutrition_status": result.status.value,
                        "kcal_per_base_serving": _plain(result.per_base_serving.kcal)
                        if result.per_base_serving.kcal is not None
                        else None,
                        "blocking_ingredient_positions": blockers,
                        "technical_gate1_suitable": result.status.value != "INCOMPLETE",
                        "consumer_publication_ready": False,
                    }
                )
        return {
            "schema_version": 1,
            "accepted_starting_sha": "ce5cf6e2faaf9159e74d8c235f334d47743ab2a0",
            "seed_chain": [
                "seed_food_recipes",
                "seed_nutrition_measure_evidence",
                "seed_recipe_corrections",
                "seed_correction_assessments",
                "seed_ru_food_data",
                "upgrade_b2b2",
            ],
            "recipe_count": len(rows),
            "recipes": rows,
        }
    finally:
        engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("database", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.database.exists():
        raise SystemExit("Audit database must not already exist.")
    result = audit(DatabaseConfig(path=args.database))
    rendered = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
