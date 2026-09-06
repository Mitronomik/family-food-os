"""Reproducible PR6 audit of the accepted production seed, never local user data."""

import json
from collections import Counter

from app.db.config import DatabaseConfig
from app.domain.nutrition import NutritionStatus, NutritionWarningCode
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
from app.persistence.sqlalchemy_core.food_recipe_composition import (
    create_food_recipe_catalogue_service,
)
from app.persistence.sqlalchemy_core.nutrition_composition import (
    create_nutrition_service,
)
from app.seed.food_recipes import seed_food_recipes


def audit_catalogue(engine):
    recipes = create_food_recipe_catalogue_service(engine)
    nutrition = create_nutrition_service(engine)
    statuses, reasons, affected_recipes = Counter(), Counter(), Counter()
    rows = []
    for recipe in sorted(recipes.list_active(), key=lambda item: item.canonical_code):
        detail = recipes.get_current_verified(recipe.id)
        result = nutrition.recipe_version(detail.version.id)
        statuses[result.status] += 1
        row_reasons = Counter(warning.code for warning in result.warnings)
        reasons.update(row_reasons)
        affected_recipes.update(row_reasons.keys())
        rows.append(
            {
                "recipe": recipe.canonical_code,
                "source_version": detail.version.source_version,
                "status": result.status,
                "reasons": dict(sorted(row_reasons.items())),
            }
        )
    return {
        "recipes": len(rows),
        "statuses": {code: statuses[code] for code in NutritionStatus},
        "reason_occurrences": {
            code: reasons[code]
            for code in NutritionWarningCode
            if code.value
            in (
                "MISSING_FOOD_INGREDIENT",
                "MISSING_NUTRITION_PROFILE",
                "MISSING_DENSITY",
                "UNSUPPORTED_PIECE_MASS",
                "UNKNOWN_FIBER",
                "ESTIMATED_SOURCE",
                "ESTIMATION_STATUS_UNKNOWN",
                "OPTIONAL_INGREDIENT",
            )
        },
        "reason_affected_recipes": dict(sorted(affected_recipes.items())),
        "rows": rows,
    }


def test_production_30_recipe_nutrition_coverage(tmp_path, monkeypatch):
    monkeypatch.setenv("AI_ENABLED", "false")
    config = DatabaseConfig(path=tmp_path / "accepted-catalogue.sqlite")
    seed_food_recipes(config)
    engine = create_sqlite_engine(config)
    try:
        report = audit_catalogue(engine)
        assert report["recipes"] == 30
        assert report["statuses"] == {
            "COMPLETE": 0,
            "COMPLETE_WITH_WARNINGS": 0,
            "CONDITIONAL": 0,
            "INCOMPLETE": 30,
        }
        assert report["reason_occurrences"] == {
            "MISSING_FOOD_INGREDIENT": 0,
            "MISSING_NUTRITION_PROFILE": 0,
            "MISSING_DENSITY": 123,
            "UNSUPPORTED_PIECE_MASS": 35,
            "UNKNOWN_FIBER": 30,
            "ESTIMATED_SOURCE": 0,
            "ESTIMATION_STATUS_UNKNOWN": 189,
            "OPTIONAL_INGREDIENT": 4,
        }
        print(
            "\nPR6_CATALOGUE_AUDIT="
            + json.dumps(report, ensure_ascii=False, sort_keys=True)
        )
    finally:
        engine.dispose()
