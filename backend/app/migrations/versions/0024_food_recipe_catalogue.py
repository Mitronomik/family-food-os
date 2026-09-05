MIGRATION_ID = "0024_food_recipe_catalogue"


def upgrade(connection):
    """Add the verified food Recipe Catalogue beside legacy recipe tables."""

    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS food_recipes (
            id CHAR(32) PRIMARY KEY NOT NULL,
            canonical_code TEXT NOT NULL,
            canonical_name TEXT NOT NULL,
            canonical_name_key TEXT NOT NULL,
            is_active BOOLEAN NOT NULL,
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL,
            CONSTRAINT uq_food_recipes_canonical_code UNIQUE (canonical_code),
            CONSTRAINT uq_food_recipes_canonical_name_key UNIQUE (canonical_name_key),
            CHECK (length(id) = 32),
            CHECK (length(trim(canonical_code)) > 0),
            CHECK (length(trim(canonical_name)) > 0),
            CHECK (length(trim(canonical_name_key)) > 0),
            CHECK (is_active IN (0, 1))
        );

        CREATE TABLE IF NOT EXISTS food_recipe_versions (
            id CHAR(32) PRIMARY KEY NOT NULL,
            recipe_id CHAR(32) NOT NULL,
            version_number INTEGER NOT NULL,
            base_servings TEXT NOT NULL,
            meal_type_code TEXT NOT NULL,
            prep_time_minutes INTEGER,
            cook_time_minutes INTEGER,
            total_time_minutes INTEGER,
            difficulty_code TEXT,
            batch_friendly BOOLEAN,
            freezable BOOLEAN,
            storage_days_fridge INTEGER,
            storage_days_freezer INTEGER,
            verification_status TEXT NOT NULL,
            verified_at DATETIME,
            source_name TEXT NOT NULL,
            source_recipe_id TEXT NOT NULL,
            source_url TEXT NOT NULL,
            source_version TEXT NOT NULL,
            source_retrieved_at DATETIME NOT NULL,
            source_document_sha256 TEXT NOT NULL,
            source_original_servings TEXT NOT NULL,
            rights_review_status TEXT NOT NULL,
            rights_basis TEXT,
            created_from_version_id CHAR(32),
            change_note TEXT NOT NULL,
            created_at DATETIME NOT NULL,
            CONSTRAINT uq_food_recipe_versions_number
                UNIQUE (recipe_id, version_number),
            CONSTRAINT uq_food_recipe_versions_provenance UNIQUE (
                recipe_id, source_name, source_recipe_id, source_version
            ),
            FOREIGN KEY (recipe_id) REFERENCES food_recipes(id) ON DELETE RESTRICT,
            FOREIGN KEY (created_from_version_id)
                REFERENCES food_recipe_versions(id) ON DELETE RESTRICT,
            CHECK (length(id) = 32),
            CHECK (length(recipe_id) = 32),
            CHECK (created_from_version_id IS NULL OR length(created_from_version_id) = 32),
            CHECK (version_number > 0),
            CHECK (CAST(base_servings AS NUMERIC) > 0),
            CHECK (meal_type_code IN ('breakfast', 'main', 'side', 'salad', 'sandwich', 'other')),
            CHECK (prep_time_minutes IS NULL OR prep_time_minutes >= 0),
            CHECK (cook_time_minutes IS NULL OR cook_time_minutes >= 0),
            CHECK (total_time_minutes IS NULL OR total_time_minutes >= 0),
            CHECK (batch_friendly IS NULL OR batch_friendly IN (0, 1)),
            CHECK (freezable IS NULL OR freezable IN (0, 1)),
            CHECK (storage_days_fridge IS NULL OR storage_days_fridge >= 0),
            CHECK (storage_days_freezer IS NULL OR storage_days_freezer >= 0),
            CHECK (verification_status IN ('UNVERIFIED', 'SOURCE_VERIFIED', 'REJECTED')),
            CHECK (length(trim(source_name)) > 0),
            CHECK (length(trim(source_recipe_id)) > 0),
            CHECK (length(trim(source_url)) > 0),
            CHECK (length(trim(source_version)) > 0),
            CHECK (length(source_document_sha256) = 64),
            CHECK (CAST(source_original_servings AS NUMERIC) > 0),
            CHECK (rights_review_status IN ('UNREVIEWED', 'REVIEWED', 'BLOCKED')),
            CHECK (
                rights_review_status != 'REVIEWED'
                OR length(trim(rights_basis)) > 0
            ),
            CHECK (
                verification_status != 'SOURCE_VERIFIED'
                OR (
                    verified_at IS NOT NULL
                    AND rights_review_status = 'REVIEWED'
                    AND length(trim(rights_basis)) > 0
                )
            )
        );

        CREATE TABLE IF NOT EXISTS food_recipe_ingredients (
            id CHAR(32) PRIMARY KEY NOT NULL,
            recipe_version_id CHAR(32) NOT NULL,
            food_ingredient_id CHAR(32) NOT NULL,
            position INTEGER NOT NULL,
            quantity TEXT NOT NULL,
            unit TEXT NOT NULL,
            source_amount_text TEXT NOT NULL,
            normalization_note TEXT,
            prep_note TEXT,
            optional BOOLEAN NOT NULL,
            created_at DATETIME NOT NULL,
            CONSTRAINT uq_food_recipe_ingredients_position
                UNIQUE (recipe_version_id, position),
            FOREIGN KEY (recipe_version_id)
                REFERENCES food_recipe_versions(id) ON DELETE RESTRICT,
            FOREIGN KEY (food_ingredient_id)
                REFERENCES food_ingredients(id) ON DELETE RESTRICT,
            CHECK (length(id) = 32),
            CHECK (length(recipe_version_id) = 32),
            CHECK (length(food_ingredient_id) = 32),
            CHECK (position > 0),
            CHECK (CAST(quantity AS NUMERIC) > 0),
            CHECK (unit IN ('g', 'ml', 'pcs')),
            CHECK (length(trim(source_amount_text)) > 0),
            CHECK (optional IN (0, 1))
        );

        CREATE TABLE IF NOT EXISTS food_recipe_steps (
            id CHAR(32) PRIMARY KEY NOT NULL,
            recipe_version_id CHAR(32) NOT NULL,
            position INTEGER NOT NULL,
            instruction TEXT NOT NULL,
            stage_code TEXT,
            created_at DATETIME NOT NULL,
            CONSTRAINT uq_food_recipe_steps_position
                UNIQUE (recipe_version_id, position),
            FOREIGN KEY (recipe_version_id)
                REFERENCES food_recipe_versions(id) ON DELETE RESTRICT,
            CHECK (length(id) = 32),
            CHECK (length(recipe_version_id) = 32),
            CHECK (position > 0),
            CHECK (length(trim(instruction)) > 0)
        );

        CREATE TABLE IF NOT EXISTS food_recipe_equipment (
            recipe_version_id CHAR(32) NOT NULL,
            position INTEGER NOT NULL,
            equipment_code TEXT NOT NULL,
            PRIMARY KEY (recipe_version_id, position),
            CONSTRAINT uq_food_recipe_equipment_code
                UNIQUE (recipe_version_id, equipment_code),
            FOREIGN KEY (recipe_version_id)
                REFERENCES food_recipe_versions(id) ON DELETE RESTRICT,
            CHECK (length(recipe_version_id) = 32),
            CHECK (position > 0),
            CHECK (length(trim(equipment_code)) > 0)
        );

        CREATE INDEX IF NOT EXISTS idx_food_recipes_active_name
            ON food_recipes(is_active, canonical_name_key, id);
        CREATE INDEX IF NOT EXISTS idx_food_recipe_versions_recipe_number
            ON food_recipe_versions(recipe_id, version_number);
        CREATE INDEX IF NOT EXISTS idx_food_recipe_versions_current_verified
            ON food_recipe_versions(recipe_id, verification_status, version_number DESC);
        CREATE INDEX IF NOT EXISTS idx_food_recipe_ingredients_version_position
            ON food_recipe_ingredients(recipe_version_id, position);
        CREATE INDEX IF NOT EXISTS idx_food_recipe_ingredients_food_ingredient
            ON food_recipe_ingredients(food_ingredient_id, recipe_version_id);
        CREATE INDEX IF NOT EXISTS idx_food_recipe_steps_version_position
            ON food_recipe_steps(recipe_version_id, position);

        CREATE TRIGGER IF NOT EXISTS trg_food_recipe_versions_no_update
        BEFORE UPDATE ON food_recipe_versions
        BEGIN
            SELECT RAISE(ABORT, 'food_recipe_versions are immutable');
        END;
        CREATE TRIGGER IF NOT EXISTS trg_food_recipe_versions_no_delete
        BEFORE DELETE ON food_recipe_versions
        BEGIN
            SELECT RAISE(ABORT, 'food_recipe_versions are immutable');
        END;
        CREATE TRIGGER IF NOT EXISTS trg_food_recipe_ingredients_no_update
        BEFORE UPDATE ON food_recipe_ingredients
        BEGIN
            SELECT RAISE(ABORT, 'food_recipe_ingredients are immutable');
        END;
        CREATE TRIGGER IF NOT EXISTS trg_food_recipe_ingredients_no_delete
        BEFORE DELETE ON food_recipe_ingredients
        BEGIN
            SELECT RAISE(ABORT, 'food_recipe_ingredients are immutable');
        END;
        CREATE TRIGGER IF NOT EXISTS trg_food_recipe_steps_no_update
        BEFORE UPDATE ON food_recipe_steps
        BEGIN
            SELECT RAISE(ABORT, 'food_recipe_steps are immutable');
        END;
        CREATE TRIGGER IF NOT EXISTS trg_food_recipe_steps_no_delete
        BEFORE DELETE ON food_recipe_steps
        BEGIN
            SELECT RAISE(ABORT, 'food_recipe_steps are immutable');
        END;
        CREATE TRIGGER IF NOT EXISTS trg_food_recipe_equipment_no_update
        BEFORE UPDATE ON food_recipe_equipment
        BEGIN
            SELECT RAISE(ABORT, 'food_recipe_equipment is immutable');
        END;
        CREATE TRIGGER IF NOT EXISTS trg_food_recipe_equipment_no_delete
        BEFORE DELETE ON food_recipe_equipment
        BEGIN
            SELECT RAISE(ABORT, 'food_recipe_equipment is immutable');
        END;
        """
    )
