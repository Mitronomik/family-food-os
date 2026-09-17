from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_pr7_persistence_schema_does_not_encode_six_as_permanent_maximum():
    migration = (
        ROOT / "app" / "migrations" / "versions" / "0032_meal_plan_serving.py"
    ).read_text(encoding="utf-8")
    tables = (
        ROOT / "app" / "persistence" / "sqlalchemy_core" / "meal_plan_tables.py"
    ).read_text(encoding="utf-8")
    for text in (migration, tables):
        assert "position <= 6" not in text
        assert "position < 7" not in text
        assert "COUNT(*) <= 6" not in text
