"""Add exact immutable applicability for FoodTransformation versions."""

MIGRATION_ID = "0038_transformation_applicability"
TABLE = "food_transformation_applicability"


def upgrade(connection):
    if not connection.in_transaction:
        connection.execute("BEGIN")

    connection.execute(
        """CREATE TABLE food_transformation_applicability (
            transformation_id CHAR(32) NOT NULL PRIMARY KEY,
            food_ingredient_id CHAR(32) NOT NULL,
            retention_registry_version TEXT,
            season_scope TEXT NOT NULL,
            season_reference TEXT,
            evidence_scope_id TEXT NOT NULL,
            provenance_json TEXT NOT NULL,
            snapshot_sha256 TEXT NOT NULL,
            FOREIGN KEY (transformation_id)
                REFERENCES food_transformations(id) ON DELETE RESTRICT,
            FOREIGN KEY (food_ingredient_id)
                REFERENCES food_ingredients(id) ON DELETE RESTRICT,
            FOREIGN KEY (retention_registry_version)
                REFERENCES nutrient_registry_snapshots(version) ON DELETE RESTRICT,
            CHECK (length(transformation_id) = 32),
            CHECK (length(food_ingredient_id) = 32),
            CHECK (season_scope IN ('ALL_SEASONS', 'EXACT_SOURCE_PERIOD')),
            CHECK (
                (season_scope = 'ALL_SEASONS' AND season_reference IS NULL)
                OR
                (
                    season_scope = 'EXACT_SOURCE_PERIOD'
                    AND season_reference IS NOT NULL
                    AND length(trim(season_reference)) > 0
                )
            ),
            CHECK (length(trim(evidence_scope_id)) > 0),
            CHECK (json_valid(provenance_json)),
            CHECK (length(snapshot_sha256) = 64)
        )"""
    )
    connection.execute(
        """CREATE TRIGGER food_transformation_applicability_no_update
        BEFORE UPDATE ON food_transformation_applicability
        BEGIN
            SELECT RAISE(ABORT, 'Применимость трансформации неизменяема.');
        END"""
    )
    connection.execute(
        """CREATE TRIGGER food_transformation_applicability_no_delete
        BEFORE DELETE ON food_transformation_applicability
        BEGIN
            SELECT RAISE(ABORT, 'Применимость трансформации неизменяема.');
        END"""
    )
    connection.execute(
        """CREATE TRIGGER food_transformation_applicability_no_replace
        BEFORE INSERT ON food_transformation_applicability
        WHEN EXISTS(
            SELECT 1 FROM food_transformation_applicability
            WHERE transformation_id = NEW.transformation_id
        )
        BEGIN
            SELECT RAISE(ABORT, 'Применимость трансформации уже зафиксирована.');
        END"""
    )
    connection.execute(
        """CREATE TRIGGER food_transformation_applicability_no_late_insert
        BEFORE INSERT ON food_transformation_applicability
        WHEN EXISTS(
            SELECT 1 FROM food_composition_steps
            WHERE transformation_id = NEW.transformation_id
        )
        BEGIN
            SELECT RAISE(ABORT, 'Трансформация уже используется историей состава.');
        END"""
    )
    connection.execute(
        """CREATE TRIGGER food_transformation_applicability_retention_binding
        BEFORE INSERT ON food_transformation_applicability
        WHEN
            (
                (
                    SELECT retention_profile_id
                    FROM food_transformations
                    WHERE id = NEW.transformation_id
                ) IS NULL
                AND NEW.retention_registry_version IS NOT NULL
            )
            OR
            (
                (
                    SELECT retention_profile_id
                    FROM food_transformations
                    WHERE id = NEW.transformation_id
                ) IS NOT NULL
                AND NEW.retention_registry_version IS NULL
            )
            OR
            (
                NEW.retention_registry_version IS NOT NULL
                AND EXISTS(
                    SELECT 1
                    FROM food_retention_values
                    WHERE profile_id = (
                        SELECT retention_profile_id
                        FROM food_transformations
                        WHERE id = NEW.transformation_id
                    )
                    AND registry_version != NEW.retention_registry_version
                )
            )
        BEGIN
            SELECT RAISE(ABORT, 'Реестр удержания не соответствует трансформации.');
        END"""
    )
    connection.execute(
        """CREATE TRIGGER food_retention_values_single_registry
        BEFORE INSERT ON food_retention_values
        WHEN EXISTS(
            SELECT 1
            FROM food_retention_values
            WHERE profile_id = NEW.profile_id
              AND registry_version != NEW.registry_version
        )
        BEGIN
            SELECT RAISE(ABORT, 'Профиль удержания не может смешивать реестры.');
        END"""
    )
