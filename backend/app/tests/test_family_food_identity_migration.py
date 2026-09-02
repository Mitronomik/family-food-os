from importlib import import_module
import sqlite3

from app.db.config import DatabaseConfig
from app.db.migrations import MIGRATION_MODULES, apply_migrations


IDENTITY_MIGRATION = import_module("app.migrations.versions.0021_family_food_identity")


def migrate_through_0020(database_path):
    original = list(MIGRATION_MODULES)
    cutoff = next(
        index
        for index, module_name in enumerate(original)
        if module_name.endswith("0020_artifact_audit_operations")
    )
    try:
        MIGRATION_MODULES[:] = original[: cutoff + 1]
        apply_migrations(DatabaseConfig(path=database_path))
    finally:
        MIGRATION_MODULES[:] = original


def read_identity_settings(database_path):
    with sqlite3.connect(database_path) as connection:
        rows = connection.execute(
            """
            SELECT key, value, value_type, description
            FROM app_settings
            WHERE key IN ('product.name', 'workspace.source')
            ORDER BY key
            """
        ).fetchall()
    return {row[0]: row[1:] for row in rows}


def table_names(connection):
    return {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
    }


def test_fresh_database_contains_family_food_identity(tmp_path):
    database_path = tmp_path / "fresh.sqlite"

    apply_migrations(DatabaseConfig(path=database_path))

    assert read_identity_settings(database_path) == {
        "product.name": ("FamilyFoodOS", "string", "Human-facing product name."),
        "workspace.source": (
            "family-food-os",
            "string",
            "Stable FamilyFoodOS workspace/source identity.",
        ),
    }


def test_database_at_0020_is_upgraded_to_family_food_identity(tmp_path):
    database_path = tmp_path / "upgrade.sqlite"
    migrate_through_0020(database_path)

    assert read_identity_settings(database_path) == {
        "product.name": (
            "Мастерская косметолога",
            "string",
            "Human-facing product name.",
        )
    }

    applied = apply_migrations(DatabaseConfig(path=database_path))

    assert applied == [
        "0021_family_food_identity",
        "0022_household_foundation",
        "0023_food_ingredient_catalogue",
    ]
    assert read_identity_settings(database_path)["product.name"][0] == "FamilyFoodOS"
    assert (
        read_identity_settings(database_path)["workspace.source"][0] == "family-food-os"
    )


def test_direct_identity_migration_is_idempotent(tmp_path):
    database_path = tmp_path / "idempotent.sqlite"
    migrate_through_0020(database_path)

    with sqlite3.connect(database_path) as connection:
        IDENTITY_MIGRATION.upgrade(connection)
        after_first = connection.execute(
            """
            SELECT key, value, value_type, description, created_at, updated_at
            FROM app_settings
            WHERE key IN ('product.name', 'workspace.source')
            ORDER BY key
            """
        ).fetchall()

        IDENTITY_MIGRATION.upgrade(connection)
        after_second = connection.execute(
            """
            SELECT key, value, value_type, description, created_at, updated_at
            FROM app_settings
            WHERE key IN ('product.name', 'workspace.source')
            ORDER BY key
            """
        ).fetchall()

    assert after_second == after_first


def test_identity_migration_creates_no_table_and_changes_no_business_data_or_audit(
    tmp_path,
):
    database_path = tmp_path / "bounded.sqlite"
    migrate_through_0020(database_path)

    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            INSERT INTO ingredients (
                name, category, default_unit, density_g_per_ml, is_active,
                notes, inci_name, supplier_hint, allergen_note, usage_note
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "Representative inherited ingredient",
                "oil",
                "g",
                "0.91",
                1,
                "unchanged",
                "legacy-inci",
                "legacy-supplier",
                "legacy-allergen",
                "legacy-usage",
            ),
        )
        business_row_before = connection.execute(
            "SELECT * FROM ingredients WHERE name = ?",
            ("Representative inherited ingredient",),
        ).fetchone()
        tables_before = table_names(connection)
        audit_count_before = connection.execute(
            "SELECT count(*) FROM audit_logs"
        ).fetchone()[0]

        IDENTITY_MIGRATION.upgrade(connection)

        business_row_after = connection.execute(
            "SELECT * FROM ingredients WHERE name = ?",
            ("Representative inherited ingredient",),
        ).fetchone()
        tables_after = table_names(connection)
        audit_count_after = connection.execute(
            "SELECT count(*) FROM audit_logs"
        ).fetchone()[0]

    assert tables_after == tables_before
    assert business_row_after == business_row_before
    assert audit_count_after == audit_count_before
