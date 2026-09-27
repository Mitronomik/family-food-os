"""Add immutable source-output truth to RecipeVersion.

This migration is intentionally additive. Historical RecipeVersions retain NULL
output fields; no source output is guessed or backfilled.
"""

MIGRATION_ID = "0040_recipe_version_source_output"


def upgrade(connection):
    connection.execute(
        """
        ALTER TABLE food_recipe_versions
        ADD COLUMN source_output_g TEXT
            CHECK (
                source_output_g IS NULL
                OR CAST(source_output_g AS NUMERIC) > 0
            )
        """
    )
    connection.execute(
        """
        ALTER TABLE food_recipe_versions
        ADD COLUMN source_output_text TEXT
            CHECK (
                source_output_text IS NULL
                OR length(trim(source_output_text)) > 0
            )
        """
    )
