import ast
from pathlib import Path

from app.db.migrations import expected_migration_ids

APP = Path(__file__).parents[1]
BOUNDARY = [
    *(APP / "domain").glob("nutrition*.py"),
    *(APP / "services").glob("nutrition*.py"),
]
ADAPTERS = list((APP / "persistence" / "sqlalchemy_core").glob("nutrition*.py"))


def test_nutrition_has_no_driver_ai_or_future_context_dependency():
    forbidden = (
        "sqlalchemy",
        "sqlite3",
        "app.persistence",
        "app.api",
        "app.schemas",
        "openai",
        "anthropic",
        "app.domain.serving",
        "app.domain.meal",
        "app.services.planner",
        "app.domain.pantry",
        "app.services.pantry",
        "app.models",
    )
    for path in BOUNDARY:
        tree = ast.parse(path.read_text())
        imports = [
            node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)
        ]
        imports += [
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        ]
        assert not any(
            module.startswith(forbidden) for module in imports if module
        ), path
        assert not any(
            isinstance(node, ast.Constant) and isinstance(node.value, float)
            for node in ast.walk(tree)
        ), path
        assert "adapter_connection" not in path.read_text()
    for path in BOUNDARY + ADAPTERS:
        source = path.read_text().lower()
        assert not any(
            token in source
            for token in (
                "mealplan",
                "meal_plan",
                "pantry",
                "planner",
                "openai",
                "serving_id",
                "retail",
            )
        )


def test_nutrition_adds_no_schema_api_or_write_uow():
    assert expected_migration_ids()[-1] == "0025_pantry"
    assert len(expected_migration_ids()) == 25
    assert not list((APP / "migrations" / "versions").glob("0026*"))
    assert not list((APP / "api").glob("*nutrition*"))
    assert not list((APP / "schemas").glob("*nutrition*"))
    for path in ADAPTERS:
        source = path.read_text()
        assert not any(
            token in source
            for token in (
                ".commit(",
                "create_all",
                "Table(",
                "SqlAlchemyUnitOfWork",
                "create_engine",
            )
        )
