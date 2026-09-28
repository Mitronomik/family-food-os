"""Add immutable energy-allocation shares to Meal Pattern opportunities.

Historical programme and Household selection rows remain NULL. Exact shares are
published only through reviewed new program/selection revisions.
"""

MIGRATION_ID = "0041_meal_pattern_energy_allocation"


def upgrade(connection):
    if not connection.in_transaction:
        connection.execute("BEGIN")

    connection.execute(
        """
        ALTER TABLE meal_pattern_opportunities
        ADD COLUMN energy_share TEXT
            CHECK (
                energy_share IS NULL
                OR (
                    typeof(energy_share) = 'text'
                AND length(energy_share) BETWEEN 1 AND 64
                AND energy_share NOT GLOB '*[^0-9.]*'
                AND energy_share GLOB '*[0-9]*'
                AND length(energy_share) - length(replace(energy_share, '.', '')) <= 1
                AND CAST(energy_share AS NUMERIC) > 0
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
                    typeof(energy_share) = 'text'
                AND length(energy_share) BETWEEN 1 AND 64
                AND energy_share NOT GLOB '*[^0-9.]*'
                AND energy_share GLOB '*[0-9]*'
                AND length(energy_share) - length(replace(energy_share, '.', '')) <= 1
                AND CAST(energy_share AS NUMERIC) > 0
                AND CAST(energy_share AS NUMERIC) <= 1
                )
            )
        """
    )
