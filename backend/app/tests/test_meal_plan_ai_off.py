from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_pr7_core_has_no_ai_dependency():
    for relative in (
        "app/domain/meal_plans.py",
        "app/services/meal_plans.py",
        "app/services/meal_plan_contracts.py",
        "app/persistence/sqlalchemy_core/meal_plan_repositories.py",
        "app/persistence/sqlalchemy_core/meal_plan_uow.py",
    ):
        text = (ROOT / relative).read_text(encoding="utf-8").lower()
        assert "openai" not in text
        assert "llm" not in text
        assert "ai_enabled" not in text
