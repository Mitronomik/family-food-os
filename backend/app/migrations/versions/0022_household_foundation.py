MIGRATION_ID = "0022_household_foundation"


def upgrade(connection):
    """Add the first production FamilyFoodOS bounded-context tables."""

    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS households (
            id CHAR(32) PRIMARY KEY NOT NULL,
            name TEXT NOT NULL,
            timezone TEXT NOT NULL,
            city TEXT,
            default_weekly_budget TEXT,
            default_cooking_profile TEXT,
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL,
            CHECK (length(id) = 32),
            CHECK (length(trim(name)) > 0),
            CHECK (length(trim(timezone)) > 0),
            CHECK (default_weekly_budget IS NULL OR CAST(default_weekly_budget AS NUMERIC) >= 0)
        );

        CREATE TABLE IF NOT EXISTS household_members (
            id CHAR(32) PRIMARY KEY NOT NULL,
            household_id CHAR(32) NOT NULL,
            name TEXT NOT NULL,
            active BOOLEAN NOT NULL,
            birth_date DATE,
            sex TEXT,
            height_cm TEXT,
            weight_kg TEXT,
            activity_level TEXT NOT NULL,
            goal TEXT NOT NULL,
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL,
            FOREIGN KEY (household_id) REFERENCES households(id) ON DELETE RESTRICT,
            CHECK (length(id) = 32),
            CHECK (length(household_id) = 32),
            CHECK (length(trim(name)) > 0),
            CHECK (active IN (0, 1)),
            CHECK (height_cm IS NULL OR CAST(height_cm AS NUMERIC) > 0),
            CHECK (weight_kg IS NULL OR CAST(weight_kg AS NUMERIC) > 0),
            CHECK (length(trim(activity_level)) > 0),
            CHECK (length(trim(goal)) > 0)
        );

        CREATE INDEX IF NOT EXISTS idx_household_members_household
            ON household_members(household_id, created_at, id);
        """
    )
