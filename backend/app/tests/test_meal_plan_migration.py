import sqlite3
from uuid import uuid4

from app.db.config import DatabaseConfig
from app.db.migrations import MIGRATION_MODULES, apply_migrations, expected_migration_ids

MIGRATION_ID = "0032_meal_plan_serving"
PARTIAL_PROFILE_MIGRATION_ID = "0034_partial_nutrition_profiles"
REGISTRY_V2_MIGRATION_ID = "0035_versioned_nutrient_registry"
REFERENCE_METHODOLOGY_MIGRATION_ID = "0036_member_reference_methodology_selection"
REFERENCE_PINS_MIGRATION_ID = "0037_meal_plan_reference_methodology_pins"
NEW_TABLES = {
    "member_meal_pattern_selections",
    "member_meal_pattern_opportunities",
    "meal_plans",
    "meal_plan_member_selections",
    "meal_plan_events",
    "servings",
}


def _apply_through_0031(config):
    original = list(MIGRATION_MODULES)
    cutoff = next(
        index
        for index, module_name in enumerate(original)
        if module_name.endswith("0031_meal_pattern_catalogue")
    )
    try:
        MIGRATION_MODULES[:] = original[: cutoff + 1]
        applied = apply_migrations(config)
    finally:
        MIGRATION_MODULES[:] = original
    assert applied[-1] == "0031_meal_pattern_catalogue"


def test_0032_is_current_head_and_fresh_migration_is_repeat_safe(tmp_path):
    config = DatabaseConfig(path=tmp_path / "fresh.sqlite")

    applied = apply_migrations(config)

    assert applied[-1] == REFERENCE_METHODOLOGY_MIGRATION_ID
    assert expected_migration_ids()[-5:] == [
        "0031_meal_pattern_catalogue",
        MIGRATION_ID,
        PARTIAL_PROFILE_MIGRATION_ID,
        REGISTRY_V2_MIGRATION_ID,
        REFERENCE_METHODOLOGY_MIGRATION_ID,
        REFERENCE_PINS_MIGRATION_ID,
    ]
    assert apply_migrations(config) == []
    with sqlite3.connect(config.path) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
        assert NEW_TABLES <= tables
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []


def test_populated_0031_upgrade_preserves_existing_rows(tmp_path):
    config = DatabaseConfig(path=tmp_path / "upgrade.sqlite")
    _apply_through_0031(config)
    household_id = uuid4().hex
    member_id = uuid4().hex
    program_id = uuid4().hex
    program_version_id = uuid4().hex
    with sqlite3.connect(config.path) as connection:
        connection.execute(
            "INSERT INTO households "
            "(id, name, timezone, city, default_weekly_budget, default_cooking_profile, created_at, updated_at) "
            "VALUES (?, 'Home', 'Europe/Moscow', NULL, NULL, NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)",
            (household_id,),
        )
        connection.execute(
            "INSERT INTO household_members "
            "(id, household_id, name, active, birth_date, sex, height_cm, weight_kg, activity_level, goal, created_at, updated_at) "
            "VALUES (?, ?, 'Anna', 1, '1990-05-20', NULL, NULL, NULL, 'moderate', 'maintain', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)",
            (member_id, household_id),
        )
        connection.execute(
            "INSERT INTO meal_pattern_programs (id, program_code, created_at) "
            "VALUES (?, 'REGULAR_THREE_MEALS', CURRENT_TIMESTAMP)",
            (program_id,),
        )
        connection.execute(
            "INSERT INTO meal_pattern_program_versions "
            "(id, program_id, version_number, lifecycle, scope_code, display_name_ru, explanation_ru, min_age_years, max_age_years, review_status, reviewed_at, published_at, created_from_version_id, change_note, created_at) "
            "VALUES (?, ?, 1, 'PUBLISHED', 'WELLNESS_SCHEDULE', 'Три приёма пищи', 'Регулярный режим.', 19, NULL, 'REVIEWED', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, NULL, 'initial', CURRENT_TIMESTAMP)",
            (program_version_id, program_id),
        )
        connection.commit()

    assert apply_migrations(config) == [
        MIGRATION_ID,
        PARTIAL_PROFILE_MIGRATION_ID,
        REGISTRY_V2_MIGRATION_ID,
        REFERENCE_METHODOLOGY_MIGRATION_ID,
        REFERENCE_PINS_MIGRATION_ID,
    ]

    with sqlite3.connect(config.path) as connection:
        assert connection.execute(
            "SELECT name FROM households WHERE id = ?", (household_id,)
        ).fetchone() == ("Home",)
        assert connection.execute(
            "SELECT name FROM household_members WHERE id = ?", (member_id,)
        ).fetchone() == ("Anna",)
        assert connection.execute(
            "SELECT lifecycle FROM meal_pattern_program_versions WHERE id = ?",
            (program_version_id,),
        ).fetchone() == ("PUBLISHED",)
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []


def test_database_does_not_encode_six_as_permanent_opportunity_maximum(tmp_path):
    config = DatabaseConfig(path=tmp_path / "extensible.sqlite")
    apply_migrations(config)
    household_id = uuid4().hex
    member_id = uuid4().hex
    selection_id = uuid4().hex
    with sqlite3.connect(config.path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute(
            "INSERT INTO households "
            "(id, name, timezone, city, default_weekly_budget, default_cooking_profile, created_at, updated_at) "
            "VALUES (?, 'Home', 'Europe/Moscow', NULL, NULL, NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)",
            (household_id,),
        )
        connection.execute(
            "INSERT INTO household_members "
            "(id, household_id, name, active, birth_date, sex, height_cm, weight_kg, activity_level, goal, created_at, updated_at) "
            "VALUES (?, ?, 'Anna', 1, NULL, NULL, NULL, NULL, 'moderate', 'maintain', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)",
            (member_id, household_id),
        )
        connection.execute(
            "INSERT INTO member_meal_pattern_selections "
            "(id, household_id, member_id, version_number, source_kind, program_version_id, recommender_version, has_user_overrides, accepted_at, supersedes_selection_id, created_at) "
            "VALUES (?, ?, ?, 1, 'CUSTOM', NULL, NULL, 0, CURRENT_TIMESTAMP, NULL, CURRENT_TIMESTAMP)",
            (selection_id, household_id, member_id),
        )
        for position in range(1, 8):
            connection.execute(
                "INSERT INTO member_meal_pattern_opportunities "
                "(selection_id, weekday, position, role_code) VALUES (?, 1, ?, 'SNACK')",
                (selection_id, position),
            )
        connection.commit()
        assert connection.execute(
            "SELECT COUNT(*) FROM member_meal_pattern_opportunities WHERE selection_id = ? AND weekday = 1",
            (selection_id,),
        ).fetchone() == (7,)


def test_0032_history_tables_are_append_only(tmp_path):
    config = DatabaseConfig(path=tmp_path / "immutable.sqlite")
    apply_migrations(config)
    household_id = uuid4().hex
    member_id = uuid4().hex
    selection_id = uuid4().hex
    with sqlite3.connect(config.path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute(
            "INSERT INTO households "
            "(id, name, timezone, city, default_weekly_budget, default_cooking_profile, created_at, updated_at) "
            "VALUES (?, 'Home', 'Europe/Moscow', NULL, NULL, NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)",
            (household_id,),
        )
        connection.execute(
            "INSERT INTO household_members "
            "(id, household_id, name, active, birth_date, sex, height_cm, weight_kg, activity_level, goal, created_at, updated_at) "
            "VALUES (?, ?, 'Anna', 1, NULL, NULL, NULL, NULL, 'moderate', 'maintain', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)",
            (member_id, household_id),
        )
        connection.execute(
            "INSERT INTO member_meal_pattern_selections "
            "(id, household_id, member_id, version_number, source_kind, program_version_id, recommender_version, has_user_overrides, accepted_at, supersedes_selection_id, created_at) "
            "VALUES (?, ?, ?, 1, 'CUSTOM', NULL, NULL, 0, CURRENT_TIMESTAMP, NULL, CURRENT_TIMESTAMP)",
            (selection_id, household_id, member_id),
        )
        connection.commit()
        try:
            connection.execute(
                "UPDATE member_meal_pattern_selections SET version_number = 2 WHERE id = ?",
                (selection_id,),
            )
        except sqlite3.IntegrityError as exc:
            assert "immutable" in str(exc)
        else:
            raise AssertionError("append-only trigger did not reject update")
