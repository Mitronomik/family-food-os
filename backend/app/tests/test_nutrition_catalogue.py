"""Production audit v2 pins actual allowed results without a desired complete count."""

import importlib.util
import json
from pathlib import Path

from app.db.config import DatabaseConfig
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
from app.seed.food_recipes import seed_food_recipes
from app.seed.nutrition_measure_evidence import seed_nutrition_measure_evidence

ROOT = Path(__file__).resolve().parents[3]
SPEC = importlib.util.spec_from_file_location(
    "audit_pr6_data_b1", ROOT / "scripts/audit_pr6_data_b1.py"
)
audit_module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit_module)
audit_catalogue = audit_module.audit_catalogue


def test_production_30_recipe_nutrition_coverage(tmp_path, monkeypatch):
    monkeypatch.setenv("AI_ENABLED", "false")
    config = DatabaseConfig(path=tmp_path / "accepted-catalogue.sqlite")
    seed_food_recipes(config)
    seed_nutrition_measure_evidence(config)
    engine = create_sqlite_engine(config)
    try:
        report = audit_catalogue(engine)
        assert report == json.loads(audit_module.REPORT.read_text())
        assert report["recipes"] == 30 and report["recipe_ingredient_rows"] == 189
        assert report["assessment_status_counts"]["APPROVED_EXACT"] == 66
        assert report["warning_occurrences"]["MISSING_NUTRITION_ASSESSMENT"] == 0
        assert report["warning_occurrences"]["MISSING_DENSITY"] == 0
        assert report["warning_occurrences"]["UNSUPPORTED_PIECE_MASS"] == 0
        print(
            "PR6_DATA_B1_AUDIT="
            + json.dumps(
                {k: v for k, v in report.items() if k != "records"}, sort_keys=True
            )
        )
    finally:
        engine.dispose()
