import ast
import inspect
from pathlib import Path

from app.persistence.sqlalchemy_core.household_repositories import (
    SqlAlchemyHouseholdMemberRepository,
)
from app.services.household_contracts import HouseholdMemberRepository

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


def test_household_domain_and_application_contracts_are_driver_independent():
    boundary_files = [
        APP_ROOT / "domain" / "households.py",
        APP_ROOT / "services" / "household_contracts.py",
        APP_ROOT / "services" / "households.py",
    ]
    imported = set()
    source = ""
    for path in boundary_files:
        imported.update(imported_modules(path))
        source += path.read_text(encoding="utf-8")

    assert not any(
        module == "sqlite3" or module.startswith("sqlalchemy") for module in imported
    )
    assert "adapter_connection" not in source


def test_api_boundary_contains_no_sql_or_persistence_adapter_imports():
    api_path = APP_ROOT / "api" / "households.py"
    modules = imported_modules(api_path)
    source = api_path.read_text(encoding="utf-8")

    assert not any(
        module.startswith("sqlalchemy")
        or module.startswith("app.persistence")
        or module == "sqlite3"
        for module in modules
    )
    assert ".execute(" not in source
    assert "adapter_connection" not in source


def test_member_repository_lookup_and_update_contracts_are_household_scoped():
    protocol_get = inspect.signature(HouseholdMemberRepository.get_member)
    concrete_get = inspect.signature(SqlAlchemyHouseholdMemberRepository.get_member)

    assert "household_id" in protocol_get.parameters
    assert "member_id" in protocol_get.parameters
    assert "household_id" in concrete_get.parameters
    assert "member_id" in concrete_get.parameters
    concrete_source = inspect.getsource(SqlAlchemyHouseholdMemberRepository)
    assert (
        "household_members_table.c.household_id == member.household_id"
        in concrete_source
    )


def test_household_repositories_never_open_or_complete_transactions():
    path = APP_ROOT / "persistence" / "sqlalchemy_core" / "household_repositories.py"
    source = path.read_text(encoding="utf-8")

    assert ".connect(" not in source
    assert ".begin(" not in source
    assert ".commit(" not in source
    assert ".rollback(" not in source


def test_production_household_slice_contains_no_owner_id():
    paths = [
        APP_ROOT / "domain" / "households.py",
        APP_ROOT / "services" / "household_contracts.py",
        APP_ROOT / "services" / "households.py",
        APP_ROOT / "schemas" / "households.py",
        APP_ROOT / "api" / "households.py",
        APP_ROOT / "persistence" / "sqlalchemy_core" / "household_tables.py",
        APP_ROOT / "persistence" / "sqlalchemy_core" / "household_repositories.py",
        APP_ROOT / "migrations" / "versions" / "0022_household_foundation.py",
    ]

    assert all("owner_id" not in path.read_text(encoding="utf-8") for path in paths)
