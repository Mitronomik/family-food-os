"""R1-F immutable RecipeVersion prepared-output Nutrition authority."""

MIGRATION_ID = "0042_recipe_prepared_output_nutrition"


def upgrade(connection):
    if not connection.in_transaction:
        connection.execute("BEGIN")

    connection.execute(
        """
        CREATE TABLE recipe_prepared_nutrient_values (
            recipe_version_id CHAR(32) NOT NULL
                REFERENCES food_recipe_versions(id) ON DELETE RESTRICT
                CHECK(length(recipe_version_id) = 32
                      AND recipe_version_id NOT GLOB '*[^0-9a-f]*'),
            registry_version TEXT NOT NULL,
            nutrient_code TEXT NOT NULL,
            amount TEXT NOT NULL
                CHECK(typeof(amount) = 'text'
                      AND length(amount) BETWEEN 1 AND 160
                      AND amount NOT GLOB '*[^0-9.]*'
                      AND amount GLOB '*[0-9]*'
                      AND length(amount) - length(replace(amount, '.', '')) <= 1
                      AND CAST(amount AS NUMERIC) >= 0),
            provenance_json TEXT NOT NULL CHECK(json_valid(provenance_json)),
            PRIMARY KEY(recipe_version_id, nutrient_code),
            FOREIGN KEY(registry_version, nutrient_code)
                REFERENCES nutrient_definitions(registry_version, code)
                ON DELETE RESTRICT,
            CHECK(registry_version = 'RU_NUTRIENT_REGISTRY_V2')
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE recipe_prepared_nutrition_authorities (
            recipe_version_id CHAR(32) NOT NULL PRIMARY KEY
                REFERENCES food_recipe_versions(id) ON DELETE RESTRICT
                CHECK(length(recipe_version_id) = 32
                      AND recipe_version_id NOT GLOB '*[^0-9a-f]*'),
            registry_version TEXT NOT NULL
                REFERENCES nutrient_registry_snapshots(version) ON DELETE RESTRICT
                CHECK(registry_version = 'RU_NUTRIENT_REGISTRY_V2'),
            nutrient_set_version TEXT NOT NULL
                CHECK(nutrient_set_version = 'RECIPE_V2_NUTRIENT_SET_V1'),
            recipe_calculation_version TEXT NOT NULL
                CHECK(recipe_calculation_version = 'RECIPE_PREPARED_OUTPUT_NUTRITION_V1'),
            output_mass_g TEXT NOT NULL
                CHECK(typeof(output_mass_g) = 'text'
                      AND length(output_mass_g) BETWEEN 1 AND 64
                      AND output_mass_g NOT GLOB '*[^0-9.]*'
                      AND output_mass_g GLOB '*[0-9]*'
                      AND length(output_mass_g) - length(replace(output_mass_g, '.', '')) <= 1
                      AND CAST(output_mass_g AS NUMERIC) > 0),
            source_name TEXT NOT NULL CHECK(length(trim(source_name)) > 0),
            source_id TEXT NOT NULL CHECK(length(trim(source_id)) > 0),
            source_version TEXT NOT NULL CHECK(length(trim(source_version)) > 0),
            source_locator TEXT NOT NULL CHECK(length(trim(source_locator)) > 0),
            source_document_sha256 TEXT NOT NULL CHECK(length(source_document_sha256) = 64),
            source_data_type TEXT NOT NULL CHECK(length(trim(source_data_type)) > 0),
            rights_review_status TEXT NOT NULL CHECK(length(trim(rights_review_status)) > 0),
            rights_basis TEXT NOT NULL CHECK(length(trim(rights_basis)) > 0),
            review_reference TEXT NOT NULL CHECK(length(trim(review_reference)) > 0),
            value_count INTEGER NOT NULL CHECK(value_count > 0),
            value_sha256 TEXT NOT NULL CHECK(length(value_sha256) = 64),
            created_at DATETIME NOT NULL
                CHECK(length(created_at) = 26
                      AND datetime(created_at) IS NOT NULL
                      AND substr(created_at, 11, 1) = ' ')
        )
        """
    )
    connection.execute(
        """CREATE TRIGGER recipe_prepared_nutrient_values_no_update
        BEFORE UPDATE ON recipe_prepared_nutrient_values
        BEGIN SELECT RAISE(ABORT, 'Prepared Recipe Nutrition value неизменяем.'); END"""
    )
    connection.execute(
        """CREATE TRIGGER recipe_prepared_nutrient_values_no_delete
        BEFORE DELETE ON recipe_prepared_nutrient_values
        BEGIN SELECT RAISE(ABORT, 'Prepared Recipe Nutrition value неизменяем.'); END"""
    )
    connection.execute(
        """CREATE TRIGGER recipe_prepared_nutrient_values_no_late_insert
        BEFORE INSERT ON recipe_prepared_nutrient_values
        WHEN EXISTS(
            SELECT 1 FROM recipe_prepared_nutrition_authorities
            WHERE recipe_version_id = NEW.recipe_version_id
        )
        BEGIN SELECT RAISE(ABORT, 'Prepared Recipe Nutrition уже запечатан.'); END"""
    )
    connection.execute(
        """CREATE TRIGGER recipe_prepared_nutrition_authorities_complete
        BEFORE INSERT ON recipe_prepared_nutrition_authorities
        WHEN NEW.value_count != (
            SELECT count(*) FROM recipe_prepared_nutrient_values
            WHERE recipe_version_id = NEW.recipe_version_id
        )
        OR EXISTS(
            SELECT 1 FROM recipe_prepared_nutrient_values v
            WHERE v.recipe_version_id = NEW.recipe_version_id
              AND v.registry_version != NEW.registry_version
        )
        BEGIN SELECT RAISE(ABORT, 'Prepared Recipe Nutrition values неполны или несовместимы.'); END"""
    )
    connection.execute(
        """CREATE TRIGGER recipe_prepared_nutrition_authorities_no_update
        BEFORE UPDATE ON recipe_prepared_nutrition_authorities
        BEGIN SELECT RAISE(ABORT, 'Prepared Recipe Nutrition authority неизменяема.'); END"""
    )
    connection.execute(
        """CREATE TRIGGER recipe_prepared_nutrition_authorities_no_delete
        BEFORE DELETE ON recipe_prepared_nutrition_authorities
        BEGIN SELECT RAISE(ABORT, 'Prepared Recipe Nutrition authority неизменяема.'); END"""
    )
    connection.execute(
        """CREATE TRIGGER recipe_prepared_nutrition_authorities_no_replace
        BEFORE INSERT ON recipe_prepared_nutrition_authorities
        WHEN EXISTS(
            SELECT 1 FROM recipe_prepared_nutrition_authorities
            WHERE recipe_version_id = NEW.recipe_version_id
        )
        BEGIN SELECT RAISE(ABORT, 'Prepared Recipe Nutrition authority неизменяема.'); END"""
    )
