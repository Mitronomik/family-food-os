MIGRATION_ID = "0023_food_ingredient_catalogue"


def upgrade(connection):
    """Add the canonical platform FoodIngredient catalogue beside legacy tables."""

    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS food_ingredients (
            id CHAR(32) PRIMARY KEY NOT NULL,
            canonical_code TEXT NOT NULL,
            canonical_name TEXT NOT NULL,
            canonical_name_key TEXT NOT NULL,
            category_code TEXT NOT NULL,
            default_unit TEXT NOT NULL,
            density_g_per_ml TEXT,
            edible_fraction TEXT,
            allergens_reviewed BOOLEAN NOT NULL,
            storage_profile_code TEXT,
            is_active BOOLEAN NOT NULL,
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL,
            CONSTRAINT uq_food_ingredients_canonical_code UNIQUE (canonical_code),
            CONSTRAINT uq_food_ingredients_canonical_name_key UNIQUE (canonical_name_key),
            CHECK (length(id) = 32),
            CHECK (length(trim(canonical_code)) > 0),
            CHECK (length(trim(canonical_name)) > 0),
            CHECK (length(trim(canonical_name_key)) > 0),
            CHECK (length(trim(category_code)) > 0),
            CHECK (default_unit IN ('g', 'ml', 'pcs')),
            CHECK (density_g_per_ml IS NULL OR CAST(density_g_per_ml AS NUMERIC) > 0),
            CHECK (
                edible_fraction IS NULL OR (
                    CAST(edible_fraction AS NUMERIC) > 0
                    AND CAST(edible_fraction AS NUMERIC) <= 1
                )
            ),
            CHECK (allergens_reviewed IN (0, 1)),
            CHECK (is_active IN (0, 1))
        );

        CREATE TABLE IF NOT EXISTS food_ingredient_aliases (
            id CHAR(32) PRIMARY KEY NOT NULL,
            food_ingredient_id CHAR(32) NOT NULL,
            alias TEXT NOT NULL,
            alias_key TEXT NOT NULL,
            language_code TEXT,
            created_at DATETIME NOT NULL,
            CONSTRAINT uq_food_ingredient_aliases_alias_key UNIQUE (alias_key),
            FOREIGN KEY (food_ingredient_id)
                REFERENCES food_ingredients(id) ON DELETE RESTRICT,
            CHECK (length(id) = 32),
            CHECK (length(food_ingredient_id) = 32),
            CHECK (length(trim(alias)) > 0),
            CHECK (length(trim(alias_key)) > 0)
        );

        CREATE TABLE IF NOT EXISTS food_nutrition_profiles (
            id CHAR(32) PRIMARY KEY NOT NULL,
            food_ingredient_id CHAR(32) NOT NULL,
            basis_grams TEXT NOT NULL,
            kcal TEXT NOT NULL,
            protein_g TEXT NOT NULL,
            fat_g TEXT NOT NULL,
            carbohydrates_g TEXT NOT NULL,
            fiber_g TEXT,
            source_name TEXT NOT NULL,
            source_id TEXT NOT NULL,
            source_version TEXT NOT NULL,
            source_data_type TEXT,
            verified_at DATETIME NOT NULL,
            estimated BOOLEAN,
            is_current BOOLEAN NOT NULL,
            created_at DATETIME NOT NULL,
            CONSTRAINT uq_food_nutrition_profiles_provenance UNIQUE (
                food_ingredient_id, source_name, source_id, source_version
            ),
            FOREIGN KEY (food_ingredient_id)
                REFERENCES food_ingredients(id) ON DELETE RESTRICT,
            CHECK (length(id) = 32),
            CHECK (length(food_ingredient_id) = 32),
            CHECK (CAST(basis_grams AS NUMERIC) = 100),
            CHECK (CAST(kcal AS NUMERIC) >= 0 AND CAST(kcal AS NUMERIC) <= 1000),
            CHECK (CAST(protein_g AS NUMERIC) >= 0 AND CAST(protein_g AS NUMERIC) <= 100),
            CHECK (CAST(fat_g AS NUMERIC) >= 0 AND CAST(fat_g AS NUMERIC) <= 100),
            CHECK (
                CAST(carbohydrates_g AS NUMERIC) >= 0
                AND CAST(carbohydrates_g AS NUMERIC) <= 100
            ),
            CHECK (
                fiber_g IS NULL OR (
                    CAST(fiber_g AS NUMERIC) >= 0
                    AND CAST(fiber_g AS NUMERIC) <= 100
                )
            ),
            CHECK (length(trim(source_name)) > 0),
            CHECK (length(trim(source_id)) > 0),
            CHECK (length(trim(source_version)) > 0),
            CHECK (estimated IS NULL OR estimated IN (0, 1)),
            CHECK (is_current IN (0, 1))
        );

        CREATE TABLE IF NOT EXISTS food_ingredient_allergens (
            food_ingredient_id CHAR(32) NOT NULL,
            allergen_code TEXT NOT NULL,
            created_at DATETIME NOT NULL,
            PRIMARY KEY (food_ingredient_id, allergen_code),
            FOREIGN KEY (food_ingredient_id)
                REFERENCES food_ingredients(id) ON DELETE RESTRICT,
            CHECK (length(food_ingredient_id) = 32),
            CHECK (length(trim(allergen_code)) > 0)
        );

        CREATE INDEX IF NOT EXISTS idx_food_ingredients_active_name
            ON food_ingredients(is_active, canonical_name_key, id);

        CREATE INDEX IF NOT EXISTS idx_food_ingredient_aliases_ingredient
            ON food_ingredient_aliases(food_ingredient_id, alias_key);

        CREATE INDEX IF NOT EXISTS idx_food_nutrition_profiles_ingredient_current
            ON food_nutrition_profiles(food_ingredient_id, is_current);

        CREATE UNIQUE INDEX IF NOT EXISTS uq_food_nutrition_profiles_one_current
            ON food_nutrition_profiles(food_ingredient_id)
            WHERE is_current = 1;
        """
    )
