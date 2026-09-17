"""Platform-owned immutable/versioned Meal Pattern Catalogue."""

MIGRATION_ID = "0031_meal_pattern_catalogue"


def upgrade(connection):
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS meal_pattern_programs (
            id CHAR(32) PRIMARY KEY NOT NULL,
            program_code TEXT NOT NULL,
            created_at DATETIME NOT NULL,
            CONSTRAINT uq_meal_pattern_programs_code UNIQUE (program_code),
            CHECK (length(id) = 32),
            CHECK (length(trim(program_code)) > 0)
        );

        CREATE TABLE IF NOT EXISTS meal_pattern_program_versions (
            id CHAR(32) PRIMARY KEY NOT NULL,
            program_id CHAR(32) NOT NULL,
            version_number INTEGER NOT NULL,
            lifecycle TEXT NOT NULL,
            scope_code TEXT NOT NULL,
            display_name_ru TEXT NOT NULL,
            explanation_ru TEXT NOT NULL,
            min_age_years INTEGER NOT NULL,
            max_age_years INTEGER,
            review_status TEXT NOT NULL,
            reviewed_at DATETIME,
            published_at DATETIME,
            created_from_version_id CHAR(32),
            change_note TEXT NOT NULL,
            created_at DATETIME NOT NULL,
            CONSTRAINT uq_meal_pattern_versions_number
                UNIQUE (program_id, version_number),
            FOREIGN KEY (program_id)
                REFERENCES meal_pattern_programs(id) ON DELETE RESTRICT,
            FOREIGN KEY (created_from_version_id)
                REFERENCES meal_pattern_program_versions(id) ON DELETE RESTRICT,
            CHECK (length(id) = 32),
            CHECK (length(program_id) = 32),
            CHECK (
                created_from_version_id IS NULL
                OR length(created_from_version_id) = 32
            ),
            CHECK (version_number > 0),
            CHECK (lifecycle IN ('DRAFT', 'PUBLISHED', 'INACTIVE')),
            CHECK (scope_code = 'WELLNESS_SCHEDULE'),
            CHECK (length(trim(display_name_ru)) > 0),
            CHECK (length(trim(explanation_ru)) > 0),
            CHECK (min_age_years >= 0),
            CHECK (max_age_years IS NULL OR max_age_years >= min_age_years),
            CHECK (review_status IN ('UNREVIEWED', 'REVIEWED')),
            CHECK (
                lifecycle != 'PUBLISHED'
                OR (
                    review_status = 'REVIEWED'
                    AND reviewed_at IS NOT NULL
                    AND published_at IS NOT NULL
                )
            )
        );

        CREATE TABLE IF NOT EXISTS meal_pattern_opportunities (
            version_id CHAR(32) NOT NULL,
            position INTEGER NOT NULL,
            role_code TEXT NOT NULL,
            PRIMARY KEY (version_id, position),
            FOREIGN KEY (version_id)
                REFERENCES meal_pattern_program_versions(id) ON DELETE RESTRICT,
            CHECK (length(version_id) = 32),
            CHECK (position > 0),
            CHECK (
                role_code IN (
                    'BREAKFAST', 'LUNCH', 'DINNER', 'SNACK',
                    'PRE_WORKOUT', 'POST_WORKOUT', 'OTHER'
                )
            )
        );

        CREATE TABLE IF NOT EXISTS meal_pattern_tags (
            version_id CHAR(32) NOT NULL,
            kind TEXT NOT NULL,
            code TEXT NOT NULL,
            PRIMARY KEY (version_id, kind, code),
            FOREIGN KEY (version_id)
                REFERENCES meal_pattern_program_versions(id) ON DELETE RESTRICT,
            CHECK (length(version_id) = 32),
            CHECK (kind IN ('GOAL', 'CONTEXT', 'EXCLUSION')),
            CHECK (length(trim(code)) > 0)
        );

        CREATE TABLE IF NOT EXISTS meal_pattern_evidence (
            version_id CHAR(32) NOT NULL,
            position INTEGER NOT NULL,
            source_name TEXT NOT NULL,
            source_title TEXT NOT NULL,
            source_url TEXT NOT NULL,
            source_version TEXT NOT NULL,
            retrieved_on DATE NOT NULL,
            evidence_scope TEXT NOT NULL,
            review_note_ru TEXT NOT NULL,
            PRIMARY KEY (version_id, position),
            FOREIGN KEY (version_id)
                REFERENCES meal_pattern_program_versions(id) ON DELETE RESTRICT,
            CHECK (length(version_id) = 32),
            CHECK (position > 0),
            CHECK (length(trim(source_name)) > 0),
            CHECK (length(trim(source_title)) > 0),
            CHECK (length(trim(source_url)) > 0),
            CHECK (length(trim(source_version)) > 0),
            CHECK (length(trim(evidence_scope)) > 0),
            CHECK (length(trim(review_note_ru)) > 0)
        );

        CREATE INDEX IF NOT EXISTS idx_meal_pattern_versions_program_number
            ON meal_pattern_program_versions(program_id, version_number);
        CREATE INDEX IF NOT EXISTS idx_meal_pattern_versions_current
            ON meal_pattern_program_versions(program_id, version_number DESC);
        CREATE INDEX IF NOT EXISTS idx_meal_pattern_opportunities_version
            ON meal_pattern_opportunities(version_id, position);
        CREATE INDEX IF NOT EXISTS idx_meal_pattern_evidence_version
            ON meal_pattern_evidence(version_id, position);

        CREATE TRIGGER IF NOT EXISTS trg_meal_pattern_programs_no_update
        BEFORE UPDATE ON meal_pattern_programs
        BEGIN
            SELECT RAISE(ABORT, 'meal_pattern_programs are immutable');
        END;
        CREATE TRIGGER IF NOT EXISTS trg_meal_pattern_programs_no_delete
        BEFORE DELETE ON meal_pattern_programs
        BEGIN
            SELECT RAISE(ABORT, 'meal_pattern_programs are immutable');
        END;

        CREATE TRIGGER IF NOT EXISTS trg_meal_pattern_versions_no_update
        BEFORE UPDATE ON meal_pattern_program_versions
        BEGIN
            SELECT RAISE(ABORT, 'meal_pattern_program_versions are immutable');
        END;
        CREATE TRIGGER IF NOT EXISTS trg_meal_pattern_versions_no_delete
        BEFORE DELETE ON meal_pattern_program_versions
        BEGIN
            SELECT RAISE(ABORT, 'meal_pattern_program_versions are immutable');
        END;

        CREATE TRIGGER IF NOT EXISTS trg_meal_pattern_opportunities_no_update
        BEFORE UPDATE ON meal_pattern_opportunities
        BEGIN
            SELECT RAISE(ABORT, 'meal_pattern_opportunities are immutable');
        END;
        CREATE TRIGGER IF NOT EXISTS trg_meal_pattern_opportunities_no_delete
        BEFORE DELETE ON meal_pattern_opportunities
        BEGIN
            SELECT RAISE(ABORT, 'meal_pattern_opportunities are immutable');
        END;

        CREATE TRIGGER IF NOT EXISTS trg_meal_pattern_tags_no_update
        BEFORE UPDATE ON meal_pattern_tags
        BEGIN
            SELECT RAISE(ABORT, 'meal_pattern_tags are immutable');
        END;
        CREATE TRIGGER IF NOT EXISTS trg_meal_pattern_tags_no_delete
        BEFORE DELETE ON meal_pattern_tags
        BEGIN
            SELECT RAISE(ABORT, 'meal_pattern_tags are immutable');
        END;

        CREATE TRIGGER IF NOT EXISTS trg_meal_pattern_evidence_no_update
        BEFORE UPDATE ON meal_pattern_evidence
        BEGIN
            SELECT RAISE(ABORT, 'meal_pattern_evidence is immutable');
        END;
        CREATE TRIGGER IF NOT EXISTS trg_meal_pattern_evidence_no_delete
        BEFORE DELETE ON meal_pattern_evidence
        BEGIN
            SELECT RAISE(ABORT, 'meal_pattern_evidence is immutable');
        END;
        """
    )
