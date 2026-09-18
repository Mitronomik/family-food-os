from pathlib import Path

from app.domain.food_recipes import MealTypeCode
from app.domain.meal_patterns import MealRole

ROOT = Path(__file__).resolve().parents[2]


def test_meal_role_remains_distinct_from_recipe_classification():
    assert {item.value for item in MealRole}.isdisjoint(
        {item.value for item in MealTypeCode}
    )
    assert "DINNER" not in {item.value for item in MealTypeCode}
    assert "main" not in {item.value for item in MealRole}


def test_meal_plan_domain_and_services_do_not_import_sqlalchemy():
    for path in (
        ROOT / "app" / "domain" / "meal_plans.py",
        ROOT / "app" / "services" / "meal_plans.py",
        ROOT / "app" / "services" / "meal_plan_contracts.py",
    ):
        text = path.read_text(encoding="utf-8")
        assert "sqlalchemy" not in text.lower()
        assert "sqlite3" not in text.lower()


def test_pr7_does_not_reuse_legacy_order_as_meal_plan():
    text = (ROOT / "app" / "domain" / "meal_plans.py").read_text(encoding="utf-8")
    assert "from app.domain.orders" not in text
    assert "Order" not in text
