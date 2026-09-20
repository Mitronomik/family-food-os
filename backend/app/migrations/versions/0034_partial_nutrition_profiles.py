"""Allow immutable partial nutrition profiles without rewriting legacy history."""

MIGRATION_ID = "0034_partial_nutrition_profiles"
SQLITE_MIGRATION_MODE = "foreign_key_rebuild"


def upgrade(connection):
    """Rebuild profile storage and add immutable source-observation rows.

    The runner owns BEGIN/COMMIT, the migration marker and foreign-key toggling.
    Existing profile IDs and all dependent NutrientVector/Composition references
    remain unchanged.
    """

    connection.execute(
        """
        CREATE TABLE food_nutrition_profiles_new (
            id CHAR(32) PRIMARY KEY NOT NULL,
            food_ingredient_id CHAR(32) NOT NULL,
            basis_grams TEXT NOT NULL,
            kcal TEXT,
            protein_g TEXT,
            fat_g TEXT,
            carbohydrates_g TEXT,
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
            CHECK (
                kcal IS NULL OR (
                    CAST(kcal AS NUMERIC) >= 0
                    AND CAST(kcal AS NUMERIC) <= 1000
                )
            ),
            CHECK (
                protein_g IS NULL OR (
                    CAST(protein_g AS NUMERIC) >= 0
                    AND CAST(protein_g AS NUMERIC) <= 100
                )
            ),
            CHECK (
                fat_g IS NULL OR (
                    CAST(fat_g AS NUMERIC) >= 0
                    AND CAST(fat_g AS NUMERIC) <= 100
                )
            ),
            CHECK (
                carbohydrates_g IS NULL OR (
                    CAST(carbohydrates_g AS NUMERIC) >= 0
                    AND CAST(carbohydrates_g AS NUMERIC) <= 100
                )
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
        )
        """
    )
    connection.execute(
        """
        INSERT INTO food_nutrition_profiles_new (
            id,
            food_ingredient_id,
            basis_grams,
            kcal,
            protein_g,
            fat_g,
            carbohydrates_g,
            fiber_g,
            source_name,
            source_id,
            source_version,
            source_data_type,
            verified_at,
            estimated,
            is_current,
            created_at
        )
        SELECT
            id,
            food_ingredient_id,
            basis_grams,
            kcal,
            protein_g,
            fat_g,
            carbohydrates_g,
            fiber_g,
            source_name,
            source_id,
            source_version,
            source_data_type,
            verified_at,
            estimated,
            is_current,
            created_at
        FROM food_nutrition_profiles
        """
    )
    connection.execute("DROP TABLE food_nutrition_profiles")
    connection.execute(
        "ALTER TABLE food_nutrition_profiles_new RENAME TO food_nutrition_profiles"
    )

    connection.execute(
        """
        CREATE INDEX idx_food_nutrition_profiles_ingredient_current
            ON food_nutrition_profiles(food_ingredient_id, is_current)
        """
    )
    connection.execute(
        """
        CREATE UNIQUE INDEX uq_food_nutrition_profiles_one_current
            ON food_nutrition_profiles(food_ingredient_id)
            WHERE is_current = 1
        """
    )

    connection.execute(
        """
        CREATE TABLE food_nutrition_profile_observations (
            id CHAR(32) PRIMARY KEY NOT NULL,
            profile_id CHAR(32) NOT NULL,
            source_field TEXT NOT NULL,
            state TEXT NOT NULL,
            source_literal TEXT,
            method_reference TEXT,
            source_locator TEXT NOT NULL,
            created_at DATETIME NOT NULL,
            CONSTRAINT uq_food_nutrition_profile_observation_field
                UNIQUE (profile_id, source_field),
            FOREIGN KEY (profile_id)
                REFERENCES food_nutrition_profiles(id) ON DELETE RESTRICT,
            CHECK (length(id) = 32),
            CHECK (length(profile_id) = 32),
            CHECK (
                source_field IN (
                    'kcal',
                    'protein_g',
                    'fat_g',
                    'carbohydrates_g',
                    'fiber_g'
                )
            ),
            CHECK (
                state IN (
                    'value',
                    'missing',
                    'below_detection',
                    'method_incompatible'
                )
            ),
            CHECK (
                (state = 'missing' AND source_literal IS NULL)
                OR (
                    state != 'missing'
                    AND source_literal IS NOT NULL
                    AND length(source_literal) > 0
                )
            ),
            CHECK (
                state != 'method_incompatible'
                OR (
                    method_reference IS NOT NULL
                    AND length(trim(method_reference)) > 0
                )
            ),
            CHECK (length(trim(source_locator)) > 0)
        )
        """
    )
    connection.execute(
        """
        CREATE INDEX idx_food_nutrition_profile_observations_profile
            ON food_nutrition_profile_observations(profile_id, source_field)
        """
    )

    connection.execute(
        """
        CREATE TRIGGER food_nutrition_profile_observations_no_update
        BEFORE UPDATE ON food_nutrition_profile_observations
        BEGIN
            SELECT RAISE(ABORT, 'Наблюдение пищевого профиля неизменяемо.');
        END
        """
    )
    connection.execute(
        """
        CREATE TRIGGER food_nutrition_profile_observations_no_delete
        BEFORE DELETE ON food_nutrition_profile_observations
        BEGIN
            SELECT RAISE(ABORT, 'Наблюдение пищевого профиля неизменяемо.');
        END
        """
    )
    connection.execute(
        """
        CREATE TRIGGER food_nutrition_profile_observations_no_replace
        BEFORE INSERT ON food_nutrition_profile_observations
        WHEN EXISTS(
            SELECT 1
            FROM food_nutrition_profile_observations
            WHERE id = NEW.id
               OR (
                    profile_id = NEW.profile_id
                    AND source_field = NEW.source_field
               )
        )
        BEGIN
            SELECT RAISE(ABORT, 'Наблюдение пищевого профиля неизменяемо.');
        END
        """
    )
