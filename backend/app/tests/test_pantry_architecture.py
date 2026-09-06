"""Keep Pantry ownership and persistence seams independent of future contexts."""

import ast
from pathlib import Path

APP = Path(__file__).parents[1]


def test_domain_and_application_are_driver_and_framework_independent():
    paths = [
        APP / "domain/pantry.py",
        APP / "services/pantry.py",
        APP / "services/pantry_contracts.py",
    ]
    for path in paths:
        tree = ast.parse(path.read_text())
        imports = [
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module
        ]
        imports += [
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        ]
        assert not any(
            name.startswith(
                (
                    "sqlalchemy",
                    "sqlite3",
                    "fastapi",
                    "app.persistence",
                    "app.api",
                    "app.schemas",
                )
            )
            for name in imports
        )
        assert "adapter_connection" not in path.read_text()


def test_pantry_has_no_legacy_or_future_dependencies():
    paths = [
        *APP.glob("domain/pantry.py"),
        *APP.glob("services/pantry*.py"),
        *APP.glob("persistence/sqlalchemy_core/pantry*.py"),
        *APP.glob("api/pantry.py"),
    ]
    source = "\n".join(path.read_text() for path in paths)
    for forbidden in (
        "app.repositories.ingredients",
        "app.models.ingredient",
        "app.services.inventory",
        "food_recipes",
        "PantryLot",
        "RetailSKU",
        "MealPlan",
        "alembic",
        ".create_all(",
        "sqlalchemy.orm",
        "AsyncSession",
    ):
        assert forbidden not in source


def test_pantry_repositories_cannot_complete_transactions():
    source = (APP / "persistence/sqlalchemy_core/pantry_repositories.py").read_text()
    for forbidden in (".connect(", ".begin(", ".commit(", ".rollback("):
        assert forbidden not in source
