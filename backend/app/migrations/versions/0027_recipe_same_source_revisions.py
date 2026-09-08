"""Allow immutable internal revisions to retain identical external provenance.

Only RecipeVersion is rebuilt. Child tables retain their original FK targets;
all IDs and stored values are copied verbatim. The runner owns transaction/FK
lifecycle and validates the whole database before committing the marker.
"""

MIGRATION_ID = "0027_recipe_same_source_revisions"
SQLITE_MIGRATION_MODE = "foreign_key_rebuild"


def upgrade(connection):
    connection.execute(
        """
        CREATE TABLE food_recipe_versions_rebuild (
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
            source_retrieved_at DATETIME,
            source_document_sha256 TEXT NOT NULL,
            source_original_servings TEXT NOT NULL,
            rights_review_status TEXT NOT NULL,
            rights_basis TEXT,
            created_from_version_id CHAR(32),
            change_note TEXT NOT NULL,
            created_at DATETIME NOT NULL,
            CONSTRAINT uq_food_recipe_versions_number
                UNIQUE (recipe_id, version_number),
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
        )
        """
    )
    connection.execute(
        """INSERT INTO food_recipe_versions_rebuild
        (
            id, recipe_id, version_number,
            base_servings, meal_type_code, prep_time_minutes,
            cook_time_minutes, total_time_minutes, difficulty_code,
            batch_friendly, freezable, storage_days_fridge,
            storage_days_freezer, verification_status, verified_at,
            source_name, source_recipe_id, source_url,
            source_version, source_retrieved_at, source_document_sha256,
            source_original_servings, rights_review_status, rights_basis,
            created_from_version_id, change_note, created_at
        )
        SELECT
            id, recipe_id, version_number,
            base_servings, meal_type_code, prep_time_minutes,
            cook_time_minutes, total_time_minutes, difficulty_code,
            batch_friendly, freezable, storage_days_fridge,
            storage_days_freezer, verification_status, verified_at,
            source_name, source_recipe_id, source_url,
            source_version, source_retrieved_at, source_document_sha256,
            source_original_servings, rights_review_status, rights_basis,
            created_from_version_id, change_note, created_at
        FROM food_recipe_versions"""
    )
    connection.execute("DROP TABLE food_recipe_versions")
    connection.execute(
        "ALTER TABLE food_recipe_versions_rebuild RENAME TO food_recipe_versions"
    )
    connection.execute("""CREATE INDEX idx_food_recipe_versions_recipe_number
            ON food_recipe_versions(recipe_id, version_number)""")
    connection.execute("""CREATE INDEX idx_food_recipe_versions_current_verified
            ON food_recipe_versions(recipe_id, verification_status, version_number DESC)""")
    connection.execute(
        """CREATE INDEX idx_food_recipe_versions_provenance ON food_recipe_versions
        (recipe_id, source_name, source_recipe_id, source_version, version_number)"""
    )
    connection.execute("""CREATE TRIGGER trg_food_recipe_versions_no_update
        BEFORE UPDATE ON food_recipe_versions
        BEGIN
            SELECT RAISE(ABORT, 'food_recipe_versions are immutable');
        END""")
    connection.execute("""CREATE TRIGGER trg_food_recipe_versions_no_delete
        BEFORE DELETE ON food_recipe_versions
        BEGIN
            SELECT RAISE(ABORT, 'food_recipe_versions are immutable');
        END""")
