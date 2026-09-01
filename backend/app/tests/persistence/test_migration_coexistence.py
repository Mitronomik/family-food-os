import ast
from pathlib import Path

from sqlalchemy import text

from app.db.config import DatabaseConfig
from app.db.migrations import (
    apply_migrations,
    current_migrations,
    expected_migration_ids,
)
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine


def test_custom_migrations_remain_authoritative_with_sqlalchemy_runtime(tmp_path):
    config = DatabaseConfig(path=tmp_path / "coexistence.sqlite")
    expected = expected_migration_ids()

    assert apply_migrations(config) == expected
    migration_truth_before = current_migrations(config)

    engine = create_sqlite_engine(config)
    try:
        with engine.connect() as connection:
            migration_truth_via_sqlalchemy = set(
                connection.execute(
                    text("SELECT migration_id FROM schema_migrations")
                ).scalars()
            )
            product_name = connection.scalar(
                text("SELECT value FROM app_settings WHERE key = 'product.name'")
            )
    finally:
        engine.dispose()

    assert migration_truth_via_sqlalchemy == set(expected)
    assert product_name == "FamilyFoodOS"
    assert current_migrations(config) == migration_truth_before
    assert apply_migrations(config) == []


def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            modules.add(node.module)
    return modules


def test_application_unit_of_work_contract_is_driver_independent():
    contract = Path(__file__).parents[2] / "services" / "unit_of_work.py"

    modules = imported_modules(contract)

    assert not any(module == "sqlite3" or module.startswith("sqlalchemy") for module in modules)


def test_business_neutral_foundation_modules_import_no_food_domain_models():
    app = Path(__file__).parents[2]
    foundation_modules = [
        app / "services" / "unit_of_work.py",
        app / "persistence" / "sqlalchemy_core" / "engine.py",
        app / "persistence" / "sqlalchemy_core" / "types.py",
        app / "persistence" / "sqlalchemy_core" / "uow.py",
    ]
    imported = set()
    for path in foundation_modules:
        imported.update(imported_modules(path))

    forbidden_contexts = {
        "household",
        "meal_plan",
        "mealplan",
        "nutrition",
        "planner",
        "shopping",
        "pantry",
        "prep",
        "retail",
    }
    assert not any(
        segment in forbidden_contexts
        for module in imported
        for segment in module.split(".")
    )
