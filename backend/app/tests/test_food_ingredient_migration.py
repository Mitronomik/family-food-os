import sqlite3
from pathlib import Path

from app.db.config import DatabaseConfig
from app.db.migrations import (
    MIGRATION_MODULES,
    apply_migrations,
    expected_migration_ids,
)

CATALOGUE_TABLES = {
    "food_ingredients",
    "food_ingredient_aliases",
    "food_nutrition_profiles",
    "food_ingredient_allergens",
}


def migrate_through_0022(database_path: Path) -> None:
    original = list(MIGRATION_MODULES)
    cutoff = next(
        index
        for index, module_name in enumerate(original)
        if module_name.endswith("0022_household_foundation")
    )
    try:
        MIGRATION_MODULES[:] = original[: cutoff + 1]
        apply_migrations(DatabaseConfig(path=database_path))
    finally:
        MIGRATION_MODULES[:] = original


def table_names(database_path: Path) -> set[str]:
    with sqlite3.connect(database_path) as connection:
        return {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }


def test_migration_chain_ends_with_food_ingredient_catalogue():
    assert expected_migration_ids()[-3:-1] == [
        "0022_household_foundation",
        "0023_food_ingredient_catalogue",
    ]


def test_fresh_database_migrates_through_0023_with_only_authorized_new_tables(
    tmp_path,
):
    database_path = tmp_path / "fresh.sqlite"

    assert (
        apply_migrations(DatabaseConfig(path=database_path)) == expected_migration_ids()
    )
    tables = table_names(database_path)

    assert CATALOGUE_TABLES <= tables
    assert {"ingredients", "households", "household_members"} <= tables
    assert (
        not {
            "recipes",
            "pantry_items",
            "meal_plans",
            "retail_skus",
            "food_product_types",
        }
        & tables
    )


def test_0022_database_upgrades_only_to_0023_and_preserves_existing_schema(tmp_path):
    database_path = tmp_path / "upgrade.sqlite"
    migrate_through_0022(database_path)
    with sqlite3.connect(database_path) as connection:
        legacy_before = connection.execute("PRAGMA table_info(ingredients)").fetchall()
        households_before = connection.execute(
            "PRAGMA table_info(households)"
        ).fetchall()
        members_before = connection.execute(
            "PRAGMA table_info(household_members)"
        ).fetchall()

    original = list(MIGRATION_MODULES)
    try:
        MIGRATION_MODULES[:] = original[
            : original.index("app.migrations.versions.0023_food_ingredient_catalogue")
            + 1
        ]
        applied = apply_migrations(DatabaseConfig(path=database_path))
        expected_through_0023 = expected_migration_ids()
    finally:
        MIGRATION_MODULES[:] = original

    assert applied == ["0023_food_ingredient_catalogue"]
    with sqlite3.connect(database_path) as connection:
        assert (
            connection.execute("PRAGMA table_info(ingredients)").fetchall()
            == legacy_before
        )
        assert (
            connection.execute("PRAGMA table_info(households)").fetchall()
            == households_before
        )
        assert (
            connection.execute("PRAGMA table_info(household_members)").fetchall()
            == members_before
        )
        history = [
            row[0]
            for row in connection.execute(
                "SELECT migration_id FROM schema_migrations ORDER BY rowid"
            )
        ]
    assert history == expected_through_0023


def test_catalogue_foreign_keys_unique_constraints_and_indexes_are_real(tmp_path):
    database_path = tmp_path / "constraints.sqlite"
    apply_migrations(DatabaseConfig(path=database_path))

    with sqlite3.connect(database_path) as connection:
        alias_fks = connection.execute(
            "PRAGMA foreign_key_list(food_ingredient_aliases)"
        ).fetchall()
        nutrition_fks = connection.execute(
            "PRAGMA foreign_key_list(food_nutrition_profiles)"
        ).fetchall()
        allergen_fks = connection.execute(
            "PRAGMA foreign_key_list(food_ingredient_allergens)"
        ).fetchall()
        ingredient_indexes = connection.execute(
            "PRAGMA index_list(food_ingredients)"
        ).fetchall()
        alias_indexes = connection.execute(
            "PRAGMA index_list(food_ingredient_aliases)"
        ).fetchall()
        alias_unique_columns = {
            tuple(
                column[2]
                for column in connection.execute(
                    f"PRAGMA index_info('{index[1]}')"
                ).fetchall()
            )
            for index in alias_indexes
            if index[2] == 1
        }
        nutrition_indexes = connection.execute(
            "PRAGMA index_list(food_nutrition_profiles)"
        ).fetchall()

    assert any(row[2] == "food_ingredients" for row in alias_fks)
    assert any(row[2] == "food_ingredients" for row in nutrition_fks)
    assert any(row[2] == "food_ingredients" for row in allergen_fks)
    assert any(
        row[1] == "idx_food_ingredients_active_name" for row in ingredient_indexes
    )
    assert ("alias_key",) in alias_unique_columns
    assert any(
        row[1] == "uq_food_nutrition_profiles_one_current" and row[2] == 1
        for row in nutrition_indexes
    )


def test_catalogue_runtime_does_not_add_a_second_schema_authority():
    app_root = Path(__file__).parents[1]
    paths = [
        app_root / "migrations" / "versions" / "0023_food_ingredient_catalogue.py",
        app_root / "persistence" / "sqlalchemy_core" / "food_ingredient_tables.py",
        app_root / "persistence" / "sqlalchemy_core" / "food_ingredient_uow.py",
    ]
    source = "\n".join(path.read_text(encoding="utf-8") for path in paths).lower()
    assert "alembic" not in source
    assert ".create_all(" not in source
