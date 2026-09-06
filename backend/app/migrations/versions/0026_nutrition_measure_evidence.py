"""Add immutable platform measure evidence and versioned row assessments."""

MIGRATION_ID = "0026_nutrition_measure_evidence"

# Literal DDL is intentionally independent of evolving runtime enums/metadata.
STATEMENTS = (
    """
    CREATE TABLE nutrition_measure_evidence (
        id CHAR(32) NOT NULL PRIMARY KEY CHECK (length(id) = 32 AND id NOT GLOB '*[^0-9a-f]*'),
        evidence_key TEXT NOT NULL UNIQUE CHECK (length(trim(evidence_key)) > 0),
        source_name TEXT NOT NULL CHECK (length(trim(source_name)) > 0),
        source_type TEXT NOT NULL CHECK (length(trim(source_type)) > 0),
        source_id TEXT CHECK (source_id IS NULL OR (length(trim(source_id)) > 0)),
        source_version TEXT NOT NULL CHECK (length(trim(source_version)) > 0),
        source_url TEXT CHECK (source_url IS NULL OR (length(trim(source_url)) > 0)),
        food_description TEXT CHECK (food_description IS NULL OR (length(trim(food_description)) > 0)),
        form_modifier TEXT CHECK (form_modifier IS NULL OR (length(trim(form_modifier)) > 0)),
        edible_basis TEXT CHECK (edible_basis IS NULL OR (length(trim(edible_basis)) > 0)),
        source_measure_amount TEXT CHECK (source_measure_amount IS NULL OR (typeof(source_measure_amount) = 'text' AND length(source_measure_amount) BETWEEN 1 AND 62 AND source_measure_amount NOT GLOB '*[^0-9.]*' AND source_measure_amount GLOB '*[0-9]*' AND length(source_measure_amount) - length(replace(source_measure_amount, '.', '')) <= 1 AND CAST(source_measure_amount AS REAL) BETWEEN 1e-18 AND 1e24)),
        source_measure_text TEXT CHECK (source_measure_text IS NULL OR (length(trim(source_measure_text)) > 0)),
        normalized_input_quantity TEXT NOT NULL CHECK (typeof(normalized_input_quantity) = 'text' AND length(normalized_input_quantity) BETWEEN 1 AND 62 AND normalized_input_quantity NOT GLOB '*[^0-9.]*' AND normalized_input_quantity GLOB '*[0-9]*' AND length(normalized_input_quantity) - length(replace(normalized_input_quantity, '.', '')) <= 1 AND CAST(normalized_input_quantity AS REAL) BETWEEN 1e-18 AND 1e24),
        normalized_input_unit TEXT NOT NULL CHECK ((length(trim(normalized_input_unit)) > 0) AND (normalized_input_unit IN ('ml', 'pcs'))),
        gram_weight TEXT NOT NULL CHECK (typeof(gram_weight) = 'text' AND length(gram_weight) BETWEEN 1 AND 62 AND gram_weight NOT GLOB '*[^0-9.]*' AND gram_weight GLOB '*[0-9]*' AND length(gram_weight) - length(replace(gram_weight, '.', '')) <= 1 AND CAST(gram_weight AS REAL) BETWEEN 1e-18 AND 1e24),
        evidence_quality TEXT NOT NULL CHECK (length(trim(evidence_quality)) > 0),
        estimated BOOLEAN NOT NULL CHECK (estimated IN (0, 1)),
        retrieved_at DATETIME CHECK (retrieved_at IS NULL OR (length(retrieved_at) = 26 AND datetime(retrieved_at) IS NOT NULL AND substr(retrieved_at, 11, 1) = ' ')),
        created_at DATETIME NOT NULL CHECK (length(created_at) = 26 AND datetime(created_at) IS NOT NULL AND substr(created_at, 11, 1) = ' ')
    )
    """,
    """
    CREATE TABLE recipe_ingredient_nutrition_assessments (
        id CHAR(32) NOT NULL PRIMARY KEY CHECK (length(id) = 32 AND id NOT GLOB '*[^0-9a-f]*'),
        recipe_ingredient_id CHAR(32) NOT NULL REFERENCES food_recipe_ingredients(id) ON DELETE RESTRICT CHECK (length(recipe_ingredient_id) = 32 AND recipe_ingredient_id NOT GLOB '*[^0-9a-f]*'),
        nutrition_profile_id CHAR(32) NOT NULL REFERENCES food_nutrition_profiles(id) ON DELETE RESTRICT CHECK (length(nutrition_profile_id) = 32 AND nutrition_profile_id NOT GLOB '*[^0-9a-f]*'),
        assessment_version INTEGER NOT NULL CHECK ((typeof(assessment_version) = 'integer') AND (assessment_version > 0)),
        is_current BOOLEAN NOT NULL CHECK (is_current IN (0, 1)),
        status_code TEXT NOT NULL CHECK ((length(trim(status_code)) > 0) AND (status_code IN ('APPROVED_NO_CONVERSION', 'APPROVED_EXACT', 'REVIEW_REQUIRED_ESTIMATE', 'BLOCKED'))),
        semantic_compatibility_code TEXT NOT NULL CHECK ((length(trim(semantic_compatibility_code)) > 0) AND (semantic_compatibility_code IN ('MATCH', 'MATCH_WITH_FORM_QUALIFIER', 'ACCEPTED_SUBSTITUTION', 'FORM_MISMATCH', 'IDENTITY_MISMATCH', 'AMBIGUOUS'))),
        conversion_decision_code TEXT CHECK (conversion_decision_code IS NULL OR ((length(trim(conversion_decision_code)) > 0) AND (conversion_decision_code IN ('DIRECT_RECIPE_MASS', 'FDC_EXACT_PORTION', 'FDC_COMPATIBLE_ESTIMATE', 'INFOODS_EXACT_OR_STRONG_MATCH', 'INFOODS_COMPATIBLE_ESTIMATE', 'OTHER_SOURCE_EXACT', 'OTHER_SOURCE_ESTIMATE', 'FOOD_FORM_MISMATCH', 'CANONICAL_IDENTITY_MISMATCH', 'MEASURE_OR_SIZE_AMBIGUOUS', 'NO_ACCEPTABLE_SOURCE')))),
        measure_evidence_id CHAR(32) REFERENCES nutrition_measure_evidence(id) ON DELETE RESTRICT CHECK (measure_evidence_id IS NULL OR (length(measure_evidence_id) = 32 AND measure_evidence_id NOT GLOB '*[^0-9a-f]*')),
        source_audit_operation TEXT NOT NULL CHECK (length(trim(source_audit_operation)) > 0),
        source_audit_key TEXT NOT NULL CHECK (length(trim(source_audit_key)) > 0),
        review_note TEXT NOT NULL CHECK (length(trim(review_note)) > 0),
        reviewed_at DATETIME NOT NULL CHECK (length(reviewed_at) = 26 AND datetime(reviewed_at) IS NOT NULL AND substr(reviewed_at, 11, 1) = ' '),
        created_at DATETIME NOT NULL CHECK (length(created_at) = 26 AND datetime(created_at) IS NOT NULL AND substr(created_at, 11, 1) = ' '),
        UNIQUE (recipe_ingredient_id, assessment_version),
        CHECK ((status_code != 'APPROVED_NO_CONVERSION' OR measure_evidence_id IS NULL) AND (status_code NOT IN ('APPROVED_EXACT', 'REVIEW_REQUIRED_ESTIMATE') OR measure_evidence_id IS NOT NULL))
    )
    """,
    """
    CREATE TABLE recipe_ingredient_nutrition_assessment_issues (
        assessment_id CHAR(32) NOT NULL REFERENCES recipe_ingredient_nutrition_assessments(id) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED CHECK (length(assessment_id) = 32 AND assessment_id NOT GLOB '*[^0-9a-f]*'),
        position INTEGER NOT NULL CHECK ((typeof(position) = 'integer') AND (position > 0)),
        issue_code TEXT NOT NULL CHECK ((length(trim(issue_code)) > 0) AND (issue_code IN ('CONVERSION_ESTIMATE_NOT_ACCEPTED', 'PROFILE_REPRESENTATIVENESS_REVIEW', 'SOURCE_ALTERNATIVE_WEIGHT_MISAPPLIED', 'SOURCE_QUANTITY_AMBIGUOUS', 'SOURCE_QUANTITY_MISMATCH', 'FOOD_FORM_MISMATCH', 'IDENTITY_MISMATCH', 'MEASURE_OR_SIZE_AMBIGUOUS', 'NO_ACCEPTABLE_SOURCE'))),
        PRIMARY KEY (assessment_id, position),
        UNIQUE (assessment_id, issue_code)
    )
    """,
    """
    CREATE UNIQUE INDEX uq_nutrition_assessment_current ON recipe_ingredient_nutrition_assessments(recipe_ingredient_id) WHERE is_current = 1
    """,
    """
    CREATE TRIGGER nutrition_measure_evidence_no_update BEFORE UPDATE ON nutrition_measure_evidence BEGIN SELECT RAISE(ABORT, 'Nutrition evidence/review history is immutable'); END
    """,
    """
    CREATE TRIGGER nutrition_measure_evidence_no_delete BEFORE DELETE ON nutrition_measure_evidence BEGIN SELECT RAISE(ABORT, 'Nutrition evidence/review history is immutable'); END
    """,
    """
    CREATE TRIGGER recipe_ingredient_nutrition_assessments_no_update BEFORE UPDATE ON recipe_ingredient_nutrition_assessments WHEN NOT (OLD.is_current = 1 AND NEW.is_current = 0 AND NEW.id IS OLD.id AND NEW.recipe_ingredient_id IS OLD.recipe_ingredient_id AND NEW.nutrition_profile_id IS OLD.nutrition_profile_id AND NEW.assessment_version IS OLD.assessment_version AND NEW.status_code IS OLD.status_code AND NEW.semantic_compatibility_code IS OLD.semantic_compatibility_code AND NEW.conversion_decision_code IS OLD.conversion_decision_code AND NEW.measure_evidence_id IS OLD.measure_evidence_id AND NEW.source_audit_operation IS OLD.source_audit_operation AND NEW.source_audit_key IS OLD.source_audit_key AND NEW.review_note IS OLD.review_note AND NEW.reviewed_at IS OLD.reviewed_at AND NEW.created_at IS OLD.created_at) BEGIN SELECT RAISE(ABORT, 'Nutrition evidence/review history is immutable'); END
    """,
    """
    CREATE TRIGGER recipe_ingredient_nutrition_assessments_no_delete BEFORE DELETE ON recipe_ingredient_nutrition_assessments BEGIN SELECT RAISE(ABORT, 'Nutrition evidence/review history is immutable'); END
    """,
    """
    CREATE TRIGGER recipe_ingredient_nutrition_assessment_issues_no_late_insert
    BEFORE INSERT ON recipe_ingredient_nutrition_assessment_issues
    WHEN EXISTS (SELECT 1 FROM recipe_ingredient_nutrition_assessments WHERE id = NEW.assessment_id)
    BEGIN
        SELECT RAISE(ABORT, 'Nutrition assessment issue set is sealed');
    END
    """,
    """
    CREATE TRIGGER recipe_ingredient_nutrition_assessment_issues_no_update BEFORE UPDATE ON recipe_ingredient_nutrition_assessment_issues BEGIN SELECT RAISE(ABORT, 'Nutrition evidence/review history is immutable'); END
    """,
    """
    CREATE TRIGGER recipe_ingredient_nutrition_assessment_issues_no_delete BEFORE DELETE ON recipe_ingredient_nutrition_assessment_issues BEGIN SELECT RAISE(ABORT, 'Nutrition evidence/review history is immutable'); END
    """,
)


def upgrade(connection):
    # Do not use executescript: it commits a pending SQLite transaction.
    # The runner commits the additive DDL together with its migration marker.
    if not connection.in_transaction:
        connection.execute("BEGIN")
    for statement in STATEMENTS:
        connection.execute(statement)
