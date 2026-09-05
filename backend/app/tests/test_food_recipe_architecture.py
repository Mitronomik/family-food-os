import ast
from pathlib import Path

APP_ROOT = Path(__file__).parents[1]

BOUNDARY_PATHS = [
    APP_ROOT / "domain" / "food_recipes.py",
    APP_ROOT / "services" / "food_recipe_contracts.py",
    APP_ROOT / "services" / "food_recipes.py",
]

PRODUCTION_PATHS = [
    *BOUNDARY_PATHS,
    APP_ROOT / "persistence" / "sqlalchemy_core" / "food_recipe_tables.py",
    APP_ROOT / "persistence" / "sqlalchemy_core" / "food_recipe_repositories.py",
    APP_ROOT / "persistence" / "sqlalchemy_core" / "food_recipe_uow.py",
    APP_ROOT / "persistence" / "sqlalchemy_core" / "food_recipe_composition.py",
    APP_ROOT / "migrations" / "versions" / "0024_food_recipe_catalogue.py",
    APP_ROOT / "seed" / "food_recipes.py",
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


def test_recipe_domain_and_application_are_driver_independent():
    imports = set().union(*(_imports(path) for path in BOUNDARY_PATHS))
    source = "\n".join(path.read_text(encoding="utf-8") for path in BOUNDARY_PATHS)

    assert not any(
        module == "sqlite3" or module.startswith("sqlalchemy") for module in imports
    )
    assert "adapter_connection" not in source


def test_recipe_catalogue_has_no_legacy_or_downstream_context_dependency():
    source = "\n".join(path.read_text(encoding="utf-8") for path in PRODUCTION_PATHS)
    lowered = source.lower()
    forbidden = (
        "app.repositories.recipes",
        "app.models.recipe",
        "app.domain.recipes",
        "household_id",
        "owner_id",
        "retailsku",
        "retail_sku",
        "pantry",
        "mealplan",
        "meal_plan",
        "app.domain.servings",
        "serving_id",
        "food_servings",
        "planner",
        "recipe_nutrition",
        "openai",
        "alembic",
        ".create_all(",
    )
    assert all(token not in lowered for token in forbidden)


def test_recipe_repositories_never_open_or_complete_transactions():
    source = (
        APP_ROOT / "persistence" / "sqlalchemy_core" / "food_recipe_repositories.py"
    ).read_text(encoding="utf-8")

    assert ".connect(" not in source
    assert ".begin(" not in source
    assert ".commit(" not in source
    assert ".rollback(" not in source


def test_no_public_recipe_catalogue_mutation_api_or_schema_was_added():
    assert not (APP_ROOT / "api" / "food_recipes.py").exists()
    assert not (APP_ROOT / "schemas" / "food_recipes.py").exists()
