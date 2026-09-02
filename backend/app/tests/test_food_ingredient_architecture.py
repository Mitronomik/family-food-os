import ast
from pathlib import Path

APP_ROOT = Path(__file__).parents[1]


def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            modules.add(node.module)
    return modules


def test_food_catalogue_domain_and_application_are_driver_independent():
    paths = [
        APP_ROOT / "domain" / "food_ingredients.py",
        APP_ROOT / "services" / "food_ingredient_contracts.py",
        APP_ROOT / "services" / "food_ingredients.py",
    ]
    imports = set().union(*(imported_modules(path) for path in paths))
    source = "\n".join(path.read_text(encoding="utf-8") for path in paths)

    assert not any(
        module == "sqlite3" or module.startswith("sqlalchemy") for module in imports
    )
    assert "adapter_connection" not in source


def test_food_catalogue_has_no_legacy_household_retail_or_future_context_dependency():
    paths = [
        APP_ROOT / "domain" / "food_ingredients.py",
        APP_ROOT / "services" / "food_ingredient_contracts.py",
        APP_ROOT / "services" / "food_ingredients.py",
        APP_ROOT / "persistence" / "sqlalchemy_core" / "food_ingredient_tables.py",
        APP_ROOT
        / "persistence"
        / "sqlalchemy_core"
        / "food_ingredient_repositories.py",
        APP_ROOT / "migrations" / "versions" / "0023_food_ingredient_catalogue.py",
    ]
    source = "\n".join(path.read_text(encoding="utf-8") for path in paths)
    lowered = source.lower()

    forbidden = [
        "app.repositories.ingredients",
        "app.models.ingredient",
        "ingredientcategory",
        "catalog_categories",
        "ingredient_catalog_tags",
        "owner_id",
        "household_id",
        "retailsku",
        "retail_sku",
        "foodproducttype",
        "food_product_type",
        "alembic",
        ".create_all(",
    ]
    assert all(token.lower() not in lowered for token in forbidden)


def test_food_catalogue_repositories_never_open_or_complete_transactions():
    source = (
        APP_ROOT / "persistence" / "sqlalchemy_core" / "food_ingredient_repositories.py"
    ).read_text(encoding="utf-8")

    assert ".connect(" not in source
    assert ".begin(" not in source
    assert ".commit(" not in source
    assert ".rollback(" not in source


def test_no_public_catalogue_mutation_api_was_added():
    assert not (APP_ROOT / "api" / "food_ingredients.py").exists()
    assert not (APP_ROOT / "schemas" / "food_ingredients.py").exists()
