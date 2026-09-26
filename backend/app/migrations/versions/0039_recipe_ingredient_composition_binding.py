"""Step 10-A immutable RecipeIngredient → CompositionVersion authority binding."""

MIGRATION_ID = "0039_recipe_ingredient_composition_binding"

TABLE = "recipe_ingredient_composition_bindings"


def upgrade(connection):
    if not connection.in_transaction:
        connection.execute("BEGIN")
    connection.execute(
        """
        CREATE TABLE recipe_ingredient_composition_bindings (
            recipe_ingredient_id CHAR(32) NOT NULL PRIMARY KEY
                REFERENCES food_recipe_ingredients(id) ON DELETE RESTRICT
                CHECK(length(recipe_ingredient_id) = 32
                      AND recipe_ingredient_id NOT GLOB '*[^0-9a-f]*'),
            composition_version_id CHAR(32) NOT NULL
                REFERENCES food_composition_versions(id) ON DELETE RESTRICT
                CHECK(length(composition_version_id) = 32
                      AND composition_version_id NOT GLOB '*[^0-9a-f]*'),
            registry_version TEXT NOT NULL
                REFERENCES nutrient_registry_snapshots(version) ON DELETE RESTRICT
                CHECK(registry_version = 'RU_NUTRIENT_REGISTRY_V2'),
            nutrient_set_version TEXT NOT NULL
                CHECK(nutrient_set_version = 'RECIPE_V2_NUTRIENT_SET_V1'),
            composition_calculation_version TEXT NOT NULL
                CHECK(composition_calculation_version = 'FOOD_COMPOSITION_APPLICABILITY_V2'),
            recipe_calculation_version TEXT NOT NULL
                CHECK(recipe_calculation_version = 'RECIPE_COMPOSITION_NUTRITION_V1'),
            created_at DATETIME NOT NULL
                CHECK(length(created_at) = 26
                      AND datetime(created_at) IS NOT NULL
                      AND substr(created_at, 11, 1) = ' ')
        )
        """
    )
    connection.execute(
        """
        CREATE TRIGGER recipe_ingredient_composition_bindings_food_match
        BEFORE INSERT ON recipe_ingredient_composition_bindings
        WHEN NOT EXISTS (
            SELECT 1
            FROM food_recipe_ingredients r
            JOIN food_composition_versions c
              ON c.id = NEW.composition_version_id
            WHERE r.id = NEW.recipe_ingredient_id
              AND r.food_ingredient_id = c.food_ingredient_id
        )
        BEGIN
            SELECT RAISE(ABORT, 'RecipeIngredient и Composition принадлежат разным FoodIngredient.');
        END
        """
    )
    connection.execute(
        """
        CREATE TRIGGER recipe_ingredient_composition_bindings_no_update
        BEFORE UPDATE ON recipe_ingredient_composition_bindings
        BEGIN SELECT RAISE(ABORT, 'Recipe Nutrition binding неизменяем.'); END
        """
    )
    connection.execute(
        """
        CREATE TRIGGER recipe_ingredient_composition_bindings_no_delete
        BEFORE DELETE ON recipe_ingredient_composition_bindings
        BEGIN SELECT RAISE(ABORT, 'Recipe Nutrition binding неизменяем.'); END
        """
    )
    connection.execute(
        """
        CREATE TRIGGER recipe_ingredient_composition_bindings_no_replace
        BEFORE INSERT ON recipe_ingredient_composition_bindings
        WHEN EXISTS (
            SELECT 1
            FROM recipe_ingredient_composition_bindings
            WHERE recipe_ingredient_id = NEW.recipe_ingredient_id
        )
        BEGIN SELECT RAISE(ABORT, 'Recipe Nutrition binding неизменяем.'); END
        """
    )
