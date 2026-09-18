from pathlib import Path

from app.domain.food_recipes import MealTypeCode
from app.domain.meal_patterns import MealRole
from app.domain.planner import ROLE_COMPATIBILITY_V1

ROOT = Path(__file__).resolve().parents[2]


def test_planner_compatibility_is_explicit_and_does_not_merge_role_enums() -> None:
    assert set(ROLE_COMPATIBILITY_V1) == set(MealRole)
    assert all(types <= set(MealTypeCode) for types in ROLE_COMPATIBILITY_V1.values())
    assert {role.value for role in MealRole}.isdisjoint(
        {value.value for value in MealTypeCode}
    )


def test_planner_core_has_no_persistence_ai_retail_or_solver_dependency() -> None:
    for relative in ("app/domain/planner.py", "app/services/planner.py"):
        text = (ROOT / relative).read_text(encoding="utf-8").lower()
        for forbidden in (
            "sqlalchemy",
            "sqlite3",
            "openai",
            "llm",
            "ortools",
            "app.domain.retail",
        ):
            assert forbidden not in text
