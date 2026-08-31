MIGRATION_ID = "0021_family_food_identity"


def upgrade(connection):
    """Project the current FamilyFoodOS identity into application settings."""
    settings = (
        (
            "product.name",
            "FamilyFoodOS",
            "string",
            "Human-facing product name.",
        ),
        (
            "workspace.source",
            "family-food-os",
            "string",
            "Stable FamilyFoodOS workspace/source identity.",
        ),
    )
    connection.executemany(
        """
        INSERT INTO app_settings (key, value, value_type, description)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(key) DO UPDATE SET
            value = excluded.value,
            value_type = excluded.value_type,
            description = excluded.description,
            updated_at = CURRENT_TIMESTAMP
        WHERE app_settings.value IS NOT excluded.value
           OR app_settings.value_type IS NOT excluded.value_type
           OR app_settings.description IS NOT excluded.description
        """,
        settings,
    )
