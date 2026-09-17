import ast
from pathlib import Path

APP_ROOT = Path(__file__).parents[1]

BOUNDARY_PATHS = [
    APP_ROOT / "domain" / "meal_patterns.py",
    APP_ROOT / "services" / "meal_pattern_contracts.py",
    APP_ROOT / "services" / "meal_patterns.py",
]

PRODUCTION_PATHS = [
    *BOUNDARY_PATHS,
    APP_ROOT / "persistence" / "sqlalchemy_core" / "meal_pattern_tables.py",
    APP_ROOT / "persistence" / "sqlalchemy_core" / "meal_pattern_repositories.py",
    APP_ROOT / "persistence" / "sqlalchemy_core" / "meal_pattern_uow.py",
    APP_ROOT / "persistence" / "sqlalchemy_core" / "meal_pattern_composition.py",
    APP_ROOT / "migrations" / "versions" / "0031_meal_pattern_catalogue.py",
    APP_ROOT / "seed" / "meal_patterns.py",
]


def _imports(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            modules.add(node.module)
    return modules


def test_domain_and_application_are_driver_independent():
    imports = set().union(*(_imports(path) for path in BOUNDARY_PATHS))
    assert not any(
        module == "sqlite3" or module.startswith("sqlalchemy") for module in imports
    )


def test_catalogue_does_not_pull_pr7_pr8_recipe_retail_ai_or_tenant_state_forward():
    source = "\n".join(path.read_text(encoding="utf-8") for path in PRODUCTION_PATHS).lower()
    forbidden = (
        "meal_type_code",
        "membermealpatternselection",
        "member_meal_pattern_selection",
        "meal_plan",
        "mealplan",
        "serving_id",
        "planner",
        "retail_sku",
        "retailsku",
        "household_id",
        "openai",
        "alembic",
        ".create_all(",
    )
    assert all(token not in source for token in forbidden)


def test_repositories_do_not_open_or_complete_transactions():
    source = (
        APP_ROOT / "persistence" / "sqlalchemy_core" / "meal_pattern_repositories.py"
    ).read_text(encoding="utf-8")
    assert ".connect(" not in source
    assert ".begin(" not in source
    assert ".commit(" not in source
    assert ".rollback(" not in source


def test_no_public_meal_pattern_api_or_schema_is_added():
    assert not (APP_ROOT / "api" / "meal_patterns.py").exists()
    assert not (APP_ROOT / "schemas" / "meal_patterns.py").exists()
