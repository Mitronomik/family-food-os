"""Production audit v3: current versions plus all six reviewed quantity outcomes."""

import argparse
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "scripts"))
from audit_pr6_data_b1 import audit_catalogue as audit_nutrition  # noqa: E402
from app.db.config import DatabaseConfig  # noqa: E402
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine  # noqa: E402
from app.persistence.sqlalchemy_core.food_recipe_composition import (  # noqa: E402
    create_food_recipe_catalogue_service,
)
from app.seed.food_recipes import seed_food_recipes  # noqa: E402
from app.seed.nutrition_measure_evidence import seed_nutrition_measure_evidence  # noqa: E402
from app.seed.recipe_corrections import (  # noqa: E402
    CURATION,
    DIRECTORY,
    read_json,
    seed_correction_assessments,
    seed_recipe_corrections,
)

REPORT = DIRECTORY / "production-audit-v3.json"


def audit_catalogue(engine):
    report = audit_nutrition(engine)
    report["schema_version"] = 3
    service = create_food_recipe_catalogue_service(engine)
    current = {}
    for record in report["records"]:
        recipe = service.get_by_code(record["recipe"])
        detail = service.get_current_verified(recipe.id)
        current[recipe.canonical_code] = detail
        record["current_version_number"] = detail.version.version_number
        record["historical_version_count"] = len(service.list_versions(recipe.id)) - 1
    matrix = []
    for finding in read_json(ROOT / CURATION)["records"]:
        detail = current[finding["recipe_canonical_code"]]
        row = detail.ingredients[finding["ingredient_position"] - 1]
        resolved = finding["resolution_status"] in (
            "CORRECTED",
            "CONFIRMED_CURRENT",
        ) and (
            str(row.quantity) == finding["corrected_quantity"]
            and row.unit == finding["corrected_unit"]
        )
        matrix.append(
            dict(
                recipe_canonical_code=detail.recipe.canonical_code,
                ingredient_position=row.position,
                current_version_number=detail.version.version_number,
                current_quantity=str(row.quantity),
                current_unit=row.unit,
                outcome="RESOLVED" if resolved else "UNRESOLVED",
                source_audit_key=finding["source_audit_key"],
                review_result=finding["review_result"],
            )
        )
    report["source_quantity_findings"] = matrix
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    with TemporaryDirectory() as directory:
        config = DatabaseConfig(path=Path(directory) / "audit.sqlite")
        seed_food_recipes(config)
        seed_nutrition_measure_evidence(config)
        seed_recipe_corrections(config)
        seed_correction_assessments(config)
        engine = create_sqlite_engine(config)
        try:
            report = audit_catalogue(engine)
        finally:
            engine.dispose()
    encoded = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.write:
        REPORT.write_text(encoded)
    elif REPORT.read_text() != encoded:
        raise SystemExit("Production audit v3 differs from pinned report.")
    print(
        json.dumps(
            {
                k: v
                for k, v in report.items()
                if k not in ("records", "source_quantity_findings")
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
