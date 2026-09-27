"""Add immutable energy-allocation shares to Meal Pattern opportunities.

Historical programme and Household selection rows remain NULL. Exact shares are
published only through reviewed new program/selection revisions.
"""

MIGRATION_ID = "0041_meal_pattern_energy_allocation"


def upgrade(connection):
    connection.execute(
        """
        ALTER TABLE meal_pattern_opportunities
        ADD COLUMN energy_share TEXT
            CHECK (
                energy_share IS NULL
                OR (
                    CAST(energy_share AS NUMERIC) > 0
                    AND CAST(energy_share AS NUMERIC) <= 1
                )
            )
        """
    )
    connection.execute(
        """
        ALTER TABLE member_meal_pattern_opportunities
        ADD COLUMN energy_share TEXT
            CHECK (
                energy_share IS NULL
                OR (
                    CAST(energy_share AS NUMERIC) > 0
                    AND CAST(energy_share AS NUMERIC) <= 1
                )
            )
        """
    )
