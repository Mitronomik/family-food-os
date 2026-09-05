import sqlite3
from pathlib import Path

from app.db.config import DatabaseConfig
from app.db.migrations import (
    MIGRATION_MODULES,
    apply_migrations,
    expected_migration_ids,
)


def migrate_through_0021(database_path):
    original = list(MIGRATION_MODULES)
    cutoff = next(
        index
        for index, module_name in enumerate(original)
        if module_name.endswith("0021_family_food_identity")
    )
    try:
        MIGRATION_MODULES[:] = original[: cutoff + 1]
        apply_migrations(DatabaseConfig(path=database_path))
    finally:
        MIGRATION_MODULES[:] = original


def table_names(database_path):
    with sqlite3.connect(database_path) as connection:
        return {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }


def test_household_foundation_remains_immediately_before_food_catalogue():
    assert expected_migration_ids()[-3:-1] == [
        "0022_household_foundation",
        "0023_food_ingredient_catalogue",
    ]


def test_fresh_database_migrates_through_0022_and_preserves_legacy_tables(tmp_path):
    database_path = tmp_path / "fresh.sqlite"

    applied = apply_migrations(DatabaseConfig(path=database_path))
    tables = table_names(database_path)

    assert applied == expected_migration_ids()
    assert {"households", "household_members"} <= tables
    assert {"clients", "orders", "production_batches"} <= tables
    assert "schema_migrations" in tables


def test_database_at_0021_upgrades_only_to_household_foundation(tmp_path):
    database_path = tmp_path / "upgrade.sqlite"
    migrate_through_0021(database_path)
    before = table_names(database_path)

    applied = apply_migrations(DatabaseConfig(path=database_path))

    assert applied == [
        "0022_household_foundation",
        "0023_food_ingredient_catalogue",
        "0024_food_recipe_catalogue",
    ]
    assert before <= table_names(database_path)
    with sqlite3.connect(database_path) as connection:
        history = [
            row[0]
            for row in connection.execute(
                "SELECT migration_id FROM schema_migrations ORDER BY rowid"
            )
        ]
        foreign_keys = connection.execute(
            "PRAGMA foreign_key_list(household_members)"
        ).fetchall()
    assert history == expected_migration_ids()
    assert any(
        row[2] == "households" and row[3] == "household_id" for row in foreign_keys
    )


def test_household_migration_does_not_rename_or_transform_clients(tmp_path):
    database_path = tmp_path / "coexist.sqlite"
    migrate_through_0021(database_path)
    with sqlite3.connect(database_path) as connection:
        client_columns_before = connection.execute(
            "PRAGMA table_info(clients)"
        ).fetchall()

    apply_migrations(DatabaseConfig(path=database_path))

    with sqlite3.connect(database_path) as connection:
        client_columns_after = connection.execute(
            "PRAGMA table_info(clients)"
        ).fetchall()
        migration_tables = connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name LIKE '%migration%'"
        ).fetchall()
    assert client_columns_after == client_columns_before
    assert migration_tables == [("schema_migrations",)]


def test_household_runtime_introduces_no_create_all_or_alembic_schema_path():
    app_root = Path(__file__).parents[1]
    household_runtime = [
        app_root / "domain" / "households.py",
        app_root / "services" / "household_contracts.py",
        app_root / "services" / "households.py",
        app_root / "persistence" / "sqlalchemy_core" / "household_tables.py",
        app_root / "persistence" / "sqlalchemy_core" / "household_repositories.py",
        app_root / "persistence" / "sqlalchemy_core" / "household_uow.py",
    ]

    source = "\n".join(path.read_text(encoding="utf-8") for path in household_runtime)

    assert ".create_all(" not in source
    assert "alembic" not in source.lower()
