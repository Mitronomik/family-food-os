"""0044: immutable, diagnostic-only multi-course meal events.

Existing events, Servings, RecipeVersions and Shopping snapshots are not
rewritten. A foreign-key-safe SQLite rebuild only extends the event source enum.
The custom runner owns the transaction, FK revalidation and migration marker.
"""

MIGRATION_ID = "0044_meal_plan_components"
SQLITE_MIGRATION_MODE = "foreign_key_rebuild"


def upgrade(db):
    # Called only by the custom runner with an open physical transaction
    # and foreign_keys=OFF. Do not execute executescript or transaction control.
    # SQLite reparses ALL existing triggers during DROP TABLE. Shopping 0043
    # has an immutable source-obligation trigger that SELECTs meal_plan_events;
    # preserve its exact SQL, temporarily drop it, then restore atomically.
    referencing = db.execute(
        "SELECT type, name, sql FROM sqlite_master "
        "WHERE type IN ('trigger','view') "
        "AND sql LIKE '%meal_plan_events%'"
    ).fetchall()
    names = {item[1] for item in referencing}
    expected = {
        "trg_meal_plan_events_no_update",
        "trg_meal_plan_events_no_delete",
        "trg_shopping_obligation_event",
    }
    if names != expected or any(item[0] != "trigger" for item in referencing):
        raise RuntimeError(
            "Unreviewed schema trigger/view dependency on meal_plan_events."
        )
    shopping_sql = next(
        item[2] for item in referencing if item[1] == "trg_shopping_obligation_event"
    )
    if (
        not shopping_sql
        or "BEFORE INSERT ON shopping_unresolved_obligations" not in shopping_sql
        or "FROM meal_plan_events" not in shopping_sql
    ):
        raise RuntimeError("Unexpected Shopping source-obligation trigger definition.")
    db.execute("DROP TRIGGER trg_shopping_obligation_event")
    db.execute("""
        CREATE TABLE meal_plan_events__0044 (
            id CHAR(32) PRIMARY KEY NOT NULL,
            plan_id CHAR(32) NOT NULL,
            local_date DATE NOT NULL,
            position INTEGER NOT NULL,
            role_code TEXT NOT NULL,
            source_kind TEXT NOT NULL,
            recipe_version_id CHAR(32),
            source_reference TEXT,
            created_at DATETIME NOT NULL,
            CONSTRAINT uq_meal_plan_event_position
                UNIQUE (plan_id, local_date, position),
            FOREIGN KEY (plan_id) REFERENCES meal_plans(id) ON DELETE RESTRICT,
            FOREIGN KEY (recipe_version_id)
                REFERENCES food_recipe_versions(id) ON DELETE RESTRICT,
            CHECK (length(id) = 32),
            CHECK (length(plan_id) = 32),
            CHECK (position > 0),
            CHECK (
                role_code IN (
                    'BREAKFAST', 'LUNCH', 'DINNER', 'SNACK',
                    'PRE_WORKOUT', 'POST_WORKOUT', 'OTHER'
                )
            ),
            CHECK (
                source_kind IN (
                    'COOK_RECIPE', 'COOK_COMPOSITION', 'ASSEMBLY',
                    'LEFTOVER', 'PREPARED', 'READY_MEAL', 'ORDER_OUT', 'EAT_OUT'
                )
            ),
            CHECK (
                (source_kind = 'COOK_RECIPE' AND recipe_version_id IS NOT NULL)
                OR (source_kind <> 'COOK_RECIPE' AND recipe_version_id IS NULL)
            ),
            CHECK (
                source_kind <> 'COOK_COMPOSITION' OR source_reference IS NULL
            )
        )
    """)
    db.execute("""
        INSERT INTO meal_plan_events__0044
        (id, plan_id, local_date, position, role_code, source_kind,
         recipe_version_id, source_reference, created_at)
        SELECT id, plan_id, local_date, position, role_code, source_kind,
               recipe_version_id, source_reference, created_at
        FROM meal_plan_events
    """)
    db.execute("DROP TABLE meal_plan_events")
    db.execute("ALTER TABLE meal_plan_events__0044 RENAME TO meal_plan_events")
    db.execute("""
        CREATE INDEX idx_meal_plan_events_order
        ON meal_plan_events (plan_id, local_date, position)
    """)
    db.execute("""
        CREATE TRIGGER trg_meal_plan_events_no_update
        BEFORE UPDATE ON meal_plan_events
        BEGIN SELECT RAISE(ABORT, 'meal_plan_events are immutable'); END
    """)
    db.execute("""
        CREATE TRIGGER trg_meal_plan_events_no_delete
        BEFORE DELETE ON meal_plan_events
        BEGIN SELECT RAISE(ABORT, 'meal_plan_events are immutable'); END
    """)
    # Restore the exact historical Shopping trigger, without modifying 0043.
    db.execute(shopping_sql)
    db.execute("""
        CREATE TABLE meal_plan_event_compositions (
            event_id CHAR(32) PRIMARY KEY NOT NULL
                REFERENCES meal_plan_events(id) ON DELETE RESTRICT,
            structure_rule_code TEXT NOT NULL CHECK(length(trim(structure_rule_code)) > 0),
            structure_rule_version INTEGER NOT NULL CHECK(structure_rule_version > 0),
            required_coverage TEXT NOT NULL
                CHECK(required_coverage IN ('EVENT','PER_PARTICIPANT')),
            rule_snapshot_schema_version INTEGER NOT NULL
                CHECK(rule_snapshot_schema_version = 1),
            requirements_json TEXT NOT NULL
                CHECK(json_valid(requirements_json) AND json_type(requirements_json)='array'),
            rule_snapshot_sha256 CHAR(64) NOT NULL
                CHECK(length(rule_snapshot_sha256)=64
                    AND rule_snapshot_sha256 NOT GLOB '*[^0-9a-f]*'),
            admission_status TEXT NOT NULL
                CHECK(admission_status='DIAGNOSTIC_ONLY'),
            created_at DATETIME NOT NULL
        )
    """)
    db.execute("""
        CREATE TABLE meal_plan_event_components (
            id CHAR(32) PRIMARY KEY NOT NULL CHECK(length(id)=32),
            event_id CHAR(32) NOT NULL
                REFERENCES meal_plan_event_compositions(event_id) ON DELETE RESTRICT,
            position INTEGER NOT NULL CHECK(position > 0),
            course_kind TEXT NOT NULL
                CHECK(course_kind IN ('FIRST','SECOND','DESSERT','MAIN','SIDE','SNACK','DRINK')),
            recipe_version_id CHAR(32) NOT NULL
                REFERENCES food_recipe_versions(id) ON DELETE RESTRICT,
            created_at DATETIME NOT NULL,
            UNIQUE(event_id, position)
        )
    """)
    db.execute("""
        CREATE TABLE meal_plan_component_servings (
            component_id CHAR(32) NOT NULL
                REFERENCES meal_plan_event_components(id) ON DELETE RESTRICT,
            member_id CHAR(32) NOT NULL
                REFERENCES household_members(id) ON DELETE RESTRICT,
            portion_servings TEXT NOT NULL CHECK(
                typeof(portion_servings)='text'
                AND length(portion_servings) BETWEEN 8 AND 26
                AND portion_servings GLOB '*.*'
                AND portion_servings NOT GLOB '*[^0-9.]*'
                AND length(portion_servings) - length(replace(portion_servings, '.', '')) = 1
                AND length(substr(portion_servings, instr(portion_servings, '.') + 1)) = 6
                AND CAST(portion_servings AS NUMERIC) > 0
                AND CAST(portion_servings AS NUMERIC) <= 999999999999.999999
            ),
            created_at DATETIME NOT NULL,
            PRIMARY KEY(component_id, member_id)
        )
    """)
    db.execute("""
        CREATE INDEX idx_meal_plan_event_components
        ON meal_plan_event_components(event_id, position)
    """)
    db.execute("""
        CREATE INDEX idx_meal_plan_component_servings_member
        ON meal_plan_component_servings(member_id, component_id)
    """)
    for table in (
        "meal_plan_event_compositions",
        "meal_plan_event_components",
        "meal_plan_component_servings",
    ):
        db.execute(f"""
            CREATE TRIGGER trg_{table}_no_update
            BEFORE UPDATE ON {table}
            BEGIN SELECT RAISE(ABORT, '{table} are immutable'); END
        """)
        db.execute(f"""
            CREATE TRIGGER trg_{table}_no_delete
            BEFORE DELETE ON {table}
            BEGIN SELECT RAISE(ABORT, '{table} are immutable'); END
        """)
