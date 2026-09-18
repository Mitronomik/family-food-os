"""Household-owned meal-pattern selection and MealPlan / Serving history."""

MIGRATION_ID = "0032_meal_plan_serving"


def upgrade(connection):
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS member_meal_pattern_selections (
            id CHAR(32) PRIMARY KEY NOT NULL,
            household_id CHAR(32) NOT NULL,
            member_id CHAR(32) NOT NULL,
            version_number INTEGER NOT NULL,
            source_kind TEXT NOT NULL,
            program_version_id CHAR(32),
            recommender_version TEXT,
            has_user_overrides INTEGER NOT NULL,
            accepted_at DATETIME NOT NULL,
            supersedes_selection_id CHAR(32),
            created_at DATETIME NOT NULL,
            CONSTRAINT uq_member_meal_pattern_selection_version
                UNIQUE (household_id, member_id, version_number),
            FOREIGN KEY (household_id) REFERENCES households(id) ON DELETE RESTRICT,
            FOREIGN KEY (member_id) REFERENCES household_members(id) ON DELETE RESTRICT,
            FOREIGN KEY (program_version_id)
                REFERENCES meal_pattern_program_versions(id) ON DELETE RESTRICT,
            FOREIGN KEY (supersedes_selection_id)
                REFERENCES member_meal_pattern_selections(id) ON DELETE RESTRICT,
            CHECK (length(id) = 32),
            CHECK (length(household_id) = 32),
            CHECK (length(member_id) = 32),
            CHECK (version_number > 0),
            CHECK (source_kind IN ('PROGRAM', 'CUSTOM')),
            CHECK (has_user_overrides IN (0, 1)),
            CHECK (
                (source_kind = 'PROGRAM' AND program_version_id IS NOT NULL)
                OR (source_kind = 'CUSTOM' AND program_version_id IS NULL)
            )
        );

        CREATE TABLE IF NOT EXISTS member_meal_pattern_opportunities (
            selection_id CHAR(32) NOT NULL,
            weekday INTEGER NOT NULL,
            position INTEGER NOT NULL,
            role_code TEXT NOT NULL,
            PRIMARY KEY (selection_id, weekday, position),
            FOREIGN KEY (selection_id)
                REFERENCES member_meal_pattern_selections(id) ON DELETE RESTRICT,
            CHECK (length(selection_id) = 32),
            CHECK (weekday BETWEEN 1 AND 7),
            CHECK (position > 0),
            CHECK (
                role_code IN (
                    'BREAKFAST', 'LUNCH', 'DINNER', 'SNACK',
                    'PRE_WORKOUT', 'POST_WORKOUT', 'OTHER'
                )
            )
        );

        CREATE TABLE IF NOT EXISTS meal_plans (
            id CHAR(32) PRIMARY KEY NOT NULL,
            household_id CHAR(32) NOT NULL,
            week_start DATE NOT NULL,
            revision_number INTEGER NOT NULL,
            status TEXT NOT NULL,
            config_version TEXT NOT NULL,
            supersedes_plan_id CHAR(32),
            created_at DATETIME NOT NULL,
            CONSTRAINT uq_meal_plan_household_week_revision
                UNIQUE (household_id, week_start, revision_number),
            FOREIGN KEY (household_id) REFERENCES households(id) ON DELETE RESTRICT,
            FOREIGN KEY (supersedes_plan_id) REFERENCES meal_plans(id) ON DELETE RESTRICT,
            CHECK (length(id) = 32),
            CHECK (length(household_id) = 32),
            CHECK (revision_number > 0),
            CHECK (status IN ('DRAFT', 'CONFIRMED')),
            CHECK (length(trim(config_version)) > 0)
        );

        CREATE TABLE IF NOT EXISTS meal_plan_member_selections (
            plan_id CHAR(32) NOT NULL,
            member_id CHAR(32) NOT NULL,
            selection_id CHAR(32) NOT NULL,
            PRIMARY KEY (plan_id, member_id),
            FOREIGN KEY (plan_id) REFERENCES meal_plans(id) ON DELETE RESTRICT,
            FOREIGN KEY (member_id) REFERENCES household_members(id) ON DELETE RESTRICT,
            FOREIGN KEY (selection_id)
                REFERENCES member_meal_pattern_selections(id) ON DELETE RESTRICT,
            CHECK (length(plan_id) = 32),
            CHECK (length(member_id) = 32),
            CHECK (length(selection_id) = 32)
        );

        CREATE TABLE IF NOT EXISTS meal_plan_events (
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
                    'COOK_RECIPE', 'ASSEMBLY', 'LEFTOVER', 'PREPARED',
                    'READY_MEAL', 'ORDER_OUT', 'EAT_OUT'
                )
            ),
            CHECK (
                (source_kind = 'COOK_RECIPE' AND recipe_version_id IS NOT NULL)
                OR (source_kind <> 'COOK_RECIPE' AND recipe_version_id IS NULL)
            )
        );

        CREATE TABLE IF NOT EXISTS servings (
            id CHAR(32) PRIMARY KEY NOT NULL,
            event_id CHAR(32) NOT NULL,
            member_id CHAR(32) NOT NULL,
            portion_servings TEXT NOT NULL,
            created_at DATETIME NOT NULL,
            CONSTRAINT uq_serving_event_member UNIQUE (event_id, member_id),
            FOREIGN KEY (event_id) REFERENCES meal_plan_events(id) ON DELETE RESTRICT,
            FOREIGN KEY (member_id) REFERENCES household_members(id) ON DELETE RESTRICT,
            CHECK (length(id) = 32),
            CHECK (length(event_id) = 32),
            CHECK (length(member_id) = 32),
            CHECK (CAST(portion_servings AS NUMERIC) > 0)
        );

        CREATE INDEX IF NOT EXISTS idx_member_meal_pattern_current
            ON member_meal_pattern_selections(
                household_id, member_id, version_number DESC
            );
        CREATE INDEX IF NOT EXISTS idx_member_meal_pattern_schedule
            ON member_meal_pattern_opportunities(selection_id, weekday, position);
        CREATE INDEX IF NOT EXISTS idx_meal_plans_current
            ON meal_plans(household_id, week_start, revision_number DESC);
        CREATE INDEX IF NOT EXISTS idx_meal_plan_events_order
            ON meal_plan_events(plan_id, local_date, position);
        CREATE INDEX IF NOT EXISTS idx_servings_event
            ON servings(event_id, member_id);

        CREATE TRIGGER IF NOT EXISTS trg_member_meal_pattern_selections_no_update
        BEFORE UPDATE ON member_meal_pattern_selections
        BEGIN
            SELECT RAISE(ABORT, 'member_meal_pattern_selections are immutable');
        END;
        CREATE TRIGGER IF NOT EXISTS trg_member_meal_pattern_selections_no_delete
        BEFORE DELETE ON member_meal_pattern_selections
        BEGIN
            SELECT RAISE(ABORT, 'member_meal_pattern_selections are immutable');
        END;
        CREATE TRIGGER IF NOT EXISTS trg_member_meal_pattern_opportunities_no_update
        BEFORE UPDATE ON member_meal_pattern_opportunities
        BEGIN
            SELECT RAISE(ABORT, 'member_meal_pattern_opportunities are immutable');
        END;
        CREATE TRIGGER IF NOT EXISTS trg_member_meal_pattern_opportunities_no_delete
        BEFORE DELETE ON member_meal_pattern_opportunities
        BEGIN
            SELECT RAISE(ABORT, 'member_meal_pattern_opportunities are immutable');
        END;
        CREATE TRIGGER IF NOT EXISTS trg_meal_plans_no_update
        BEFORE UPDATE ON meal_plans
        BEGIN
            SELECT RAISE(ABORT, 'meal_plans are immutable revisions');
        END;
        CREATE TRIGGER IF NOT EXISTS trg_meal_plans_no_delete
        BEFORE DELETE ON meal_plans
        BEGIN
            SELECT RAISE(ABORT, 'meal_plans are immutable revisions');
        END;
        CREATE TRIGGER IF NOT EXISTS trg_meal_plan_member_selections_no_update
        BEFORE UPDATE ON meal_plan_member_selections
        BEGIN
            SELECT RAISE(ABORT, 'meal_plan_member_selections are immutable');
        END;
        CREATE TRIGGER IF NOT EXISTS trg_meal_plan_member_selections_no_delete
        BEFORE DELETE ON meal_plan_member_selections
        BEGIN
            SELECT RAISE(ABORT, 'meal_plan_member_selections are immutable');
        END;
        CREATE TRIGGER IF NOT EXISTS trg_meal_plan_events_no_update
        BEFORE UPDATE ON meal_plan_events
        BEGIN
            SELECT RAISE(ABORT, 'meal_plan_events are immutable');
        END;
        CREATE TRIGGER IF NOT EXISTS trg_meal_plan_events_no_delete
        BEFORE DELETE ON meal_plan_events
        BEGIN
            SELECT RAISE(ABORT, 'meal_plan_events are immutable');
        END;
        CREATE TRIGGER IF NOT EXISTS trg_servings_no_update
        BEFORE UPDATE ON servings
        BEGIN
            SELECT RAISE(ABORT, 'servings are immutable');
        END;
        CREATE TRIGGER IF NOT EXISTS trg_servings_no_delete
        BEFORE DELETE ON servings
        BEGIN
            SELECT RAISE(ABORT, 'servings are immutable');
        END;
        """
    )
