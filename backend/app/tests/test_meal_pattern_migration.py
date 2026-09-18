import sqlite3
from uuid import uuid4

import pytest

from app.db.config import DatabaseConfig
from app.db.migrations import MIGRATION_MODULES, apply_migrations, expected_migration_ids
from app.seed.food_recipes import seed_food_recipes

PATTERN_TABLES = {
    "meal_pattern_programs",
    "meal_pattern_program_versions",
    "meal_pattern_opportunities",
    "meal_pattern_tags",
    "meal_pattern_evidence",
}
PLAN_TABLES = {
    "member_meal_pattern_selections",
    "member_meal_pattern_opportunities",
    "meal_plans",
    "meal_plan_member_selections",
    "meal_plan_events",
    "servings",
}


def _run_with_chain_through(config, suffix, operation):
    original = list(MIGRATION_MODULES)
    cutoff = next(index for index, module in enumerate(original) if module.endswith(suffix))
    try:
        MIGRATION_MODULES[:] = original[: cutoff + 1]
        return operation(config)
    finally:
        MIGRATION_MODULES[:] = original


def test_migration_chain_keeps_0031_between_0030_and_0032():
    assert expected_migration_ids()[-3:] == [
        "0030_recipe_source_corpus",
        "0031_meal_pattern_catalogue",
        "0032_meal_plan_serving",
    ]


def test_populated_0030_database_upgrades_without_rewriting_existing_food_data(tmp_path):
    config = DatabaseConfig(path=tmp_path / "upgrade.sqlite")
    _run_with_chain_through(config, "0030_recipe_source_corpus", seed_food_recipes)
    with sqlite3.connect(config.path) as connection:
        before = {
            "food_recipes": connection.execute("SELECT COUNT(*) FROM food_recipes").fetchone()[0],
            "food_recipe_versions": connection.execute("SELECT COUNT(*) FROM food_recipe_versions").fetchone()[0],
            "food_ingredients": connection.execute("SELECT COUNT(*) FROM food_ingredients").fetchone()[0],
        }

    assert apply_migrations(config) == [
        "0031_meal_pattern_catalogue",
        "0032_meal_plan_serving",
    ]
    assert apply_migrations(config) == []
    with sqlite3.connect(config.path) as connection:
        after = {
            key: connection.execute(f"SELECT COUNT(*) FROM {key}").fetchone()[0]
            for key in before
        }
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
    assert after == before
    assert PATTERN_TABLES <= tables
    assert PLAN_TABLES <= tables


@pytest.mark.parametrize(
    "table",
    [
        "meal_pattern_programs",
        "meal_pattern_program_versions",
        "meal_pattern_opportunities",
        "meal_pattern_tags",
        "meal_pattern_evidence",
    ],
)
def test_catalogue_tables_have_immutable_update_and_delete_guards(tmp_path, table):
    config = DatabaseConfig(path=tmp_path / "immutable.sqlite")
    apply_migrations(config)
    with sqlite3.connect(config.path) as connection:
        names = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='trigger' AND tbl_name=?",
                (table,),
            )
        }
    assert any(name.endswith("no_update") for name in names)
    assert any(name.endswith("no_delete") for name in names)


def test_sqlite_schema_allows_repeated_role_codes_at_distinct_positions(tmp_path):
    config = DatabaseConfig(path=tmp_path / "roles.sqlite")
    apply_migrations(config)
    program_id = uuid4().hex
    version_id = uuid4().hex
    with sqlite3.connect(config.path) as connection:
        connection.execute(
            "INSERT INTO meal_pattern_programs (id, program_code, created_at) VALUES (?, ?, ?)",
            (program_id, "REPEATED_ROLE", "2026-09-17T04:19:00+00:00"),
        )
        connection.execute(
            """INSERT INTO meal_pattern_program_versions (
                id, program_id, version_number, lifecycle, scope_code,
                display_name_ru, explanation_ru, min_age_years, max_age_years,
                review_status, reviewed_at, published_at, created_from_version_id,
                change_note, created_at
            ) VALUES (?, ?, 1, 'PUBLISHED', 'WELLNESS_SCHEDULE', ?, ?, 19, NULL,
                      'REVIEWED', ?, ?, NULL, ?, ?)""",
            (
                version_id,
                program_id,
                "Повторяемая роль",
                "Синтетический тест структуры.",
                "2026-09-17T04:19:00+00:00",
                "2026-09-17T04:19:00+00:00",
                "Synthetic fixture.",
                "2026-09-17T04:19:00+00:00",
            ),
        )
        connection.executemany(
            "INSERT INTO meal_pattern_opportunities (version_id, position, role_code) VALUES (?, ?, ?)",
            [(version_id, 1, "SNACK"), (version_id, 2, "SNACK")],
        )
        assert connection.execute(
            "SELECT COUNT(*) FROM meal_pattern_opportunities WHERE version_id=?",
            (version_id,),
        ).fetchone()[0] == 2
