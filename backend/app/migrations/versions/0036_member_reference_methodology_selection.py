"""Persist immutable Household-member reference methodology selections."""

MIGRATION_ID = "0036_member_reference_methodology_selection"


def upgrade(connection):
    # Python sqlite3 legacy transaction control does not start a transaction for
    # DDL. Start one only when the runner/session has none so table/index/trigger
    # creation and the runner-owned migration marker share one rollback boundary.
    # The migration still never commits, rolls back, or writes its own marker.
    if not connection.in_transaction:
        connection.execute("BEGIN")

    connection.execute(
        """CREATE TABLE member_reference_methodology_selections (
            id CHAR(32) PRIMARY KEY NOT NULL,
            household_id CHAR(32) NOT NULL,
            member_id CHAR(32) NOT NULL,
            version_number INTEGER NOT NULL,
            nutrition_config_version TEXT NOT NULL,
            group_reference_methodology_version TEXT,
            accepted_local_date DATE NOT NULL,
            household_timezone_at_acceptance TEXT NOT NULL,
            member_updated_at_at_acceptance DATETIME NOT NULL,
            household_updated_at_at_acceptance DATETIME NOT NULL,
            acceptance_request_id CHAR(32) NOT NULL UNIQUE,
            accepted_at DATETIME NOT NULL,
            supersedes_selection_id CHAR(32),
            created_at DATETIME NOT NULL,
            CONSTRAINT uq_member_reference_methodology_version
                UNIQUE (household_id, member_id, version_number),
            FOREIGN KEY (household_id) REFERENCES households(id) ON DELETE RESTRICT,
            FOREIGN KEY (member_id) REFERENCES household_members(id) ON DELETE RESTRICT,
            FOREIGN KEY (supersedes_selection_id)
                REFERENCES member_reference_methodology_selections(id)
                ON DELETE RESTRICT,
            CHECK (length(id) = 32),
            CHECK (length(household_id) = 32),
            CHECK (length(member_id) = 32),
            CHECK (length(acceptance_request_id) = 32),
            CHECK (
                supersedes_selection_id IS NULL
                OR length(supersedes_selection_id) = 32
            ),
            CHECK (version_number > 0),
            CHECK (length(trim(nutrition_config_version)) > 0),
            CHECK (
                group_reference_methodology_version IS NULL
                OR length(trim(group_reference_methodology_version)) > 0
            ),
            CHECK (length(trim(household_timezone_at_acceptance)) > 0)
        )"""
    )
    connection.execute(
        """CREATE INDEX idx_member_reference_methodology_current
        ON member_reference_methodology_selections(
            household_id, member_id, version_number DESC
        )"""
    )
    connection.execute(
        """CREATE TRIGGER trg_member_reference_methodology_no_update
        BEFORE UPDATE ON member_reference_methodology_selections
        BEGIN
            SELECT RAISE(
                ABORT,
                'member reference methodology selections are immutable'
            );
        END"""
    )
    connection.execute(
        """CREATE TRIGGER trg_member_reference_methodology_no_delete
        BEFORE DELETE ON member_reference_methodology_selections
        BEGIN
            SELECT RAISE(
                ABORT,
                'member reference methodology selections are immutable'
            );
        END"""
    )
