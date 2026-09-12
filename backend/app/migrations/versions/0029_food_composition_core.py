"""Empty, append-only composition infrastructure; no production backfill."""

MIGRATION_ID = "0029_food_composition_core"
TABLES = (
    "food_yield_models",
    "food_retention_profiles",
    "food_retention_values",
    "food_transformations",
    "food_composition_versions",
    "food_composition_nodes",
    "food_composition_steps",
)
_STATES = "'RAW','INPUT','DRAINED','COOKED','YIELDED','GROSS_PURCHASE','PREPARED_PRE_COOK','DISCARD','SERVING'"
_COMMON = f"""
    id CHAR(32) NOT NULL PRIMARY KEY,
    version INTEGER NOT NULL CHECK(typeof(version) = 'integer' AND version > 0),
    input_state TEXT NOT NULL CHECK(input_state IN ({_STATES})),
    provenance_json TEXT NOT NULL CHECK(json_valid(provenance_json)),
    snapshot_sha256 TEXT NOT NULL CHECK(length(snapshot_sha256) = 64)
"""


def _decimal(name, positive=True):
    positive_check = f" AND {name} GLOB '*[1-9]*'" if positive else ""
    return f"""{name} TEXT NOT NULL CHECK(typeof({name}) = 'text'
        AND {name} NOT GLOB '*[^0-9.]*' AND {name} GLOB '*[0-9]*'
        AND length({name}) - length(replace({name}, '.', '')) <= 1 {positive_check})"""


STATEMENTS = (
    f"""CREATE TABLE food_yield_models ({_COMMON},
        output_state TEXT NOT NULL CHECK(output_state IN ({_STATES})),
        {_decimal('factor')})""",
    f"""CREATE TABLE food_retention_profiles ({_COMMON},
        output_state TEXT NOT NULL CHECK(output_state IN ({_STATES})),
        value_count INTEGER NOT NULL CHECK(typeof(value_count) = 'integer' AND value_count >= 0))""",
    f"""CREATE TABLE food_retention_values (
        profile_id CHAR(32) NOT NULL REFERENCES food_retention_profiles(id) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED,
        nutrient_code TEXT NOT NULL REFERENCES nutrient_definitions(code) ON DELETE RESTRICT,
        {_decimal('factor', False)},
        provenance_json TEXT NOT NULL CHECK(json_valid(provenance_json)),
        PRIMARY KEY(profile_id, nutrient_code))""",
    f"""CREATE TABLE food_transformations ({_COMMON},
        output_state TEXT NOT NULL CHECK(output_state IN ({_STATES})),
        transformation_type TEXT NOT NULL CHECK(length(transformation_type) > 0),
        yield_model_id CHAR(32) REFERENCES food_yield_models(id) ON DELETE RESTRICT,
        retention_profile_id CHAR(32) REFERENCES food_retention_profiles(id) ON DELETE RESTRICT)""",
    f"""CREATE TABLE food_composition_versions ({_COMMON},
        food_ingredient_id CHAR(32) NOT NULL REFERENCES food_ingredients(id) ON DELETE RESTRICT,
        kind TEXT NOT NULL CHECK(kind IN ('ATOMIC','COMPOSITE')),
        profile_id CHAR(32) REFERENCES nutrition_vector_seals(profile_id) ON DELETE RESTRICT,
        node_count INTEGER NOT NULL CHECK(typeof(node_count) = 'integer' AND node_count >= 0),
        step_count INTEGER NOT NULL CHECK(typeof(step_count) = 'integer' AND step_count >= 0),
        CHECK((kind = 'ATOMIC' AND profile_id IS NOT NULL AND node_count = 0)
            OR (kind = 'COMPOSITE' AND profile_id IS NULL AND node_count > 0)),
        UNIQUE(food_ingredient_id, version))""",
    f"""CREATE TABLE food_composition_nodes (
        id CHAR(32) NOT NULL PRIMARY KEY,
        composition_id CHAR(32) NOT NULL REFERENCES food_composition_versions(id) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED,
        position INTEGER NOT NULL CHECK(typeof(position) = 'integer' AND position >= 0),
        child_version_id CHAR(32) NOT NULL REFERENCES food_composition_versions(id) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED,
        {_decimal('input_mass_g')},
        mass_state TEXT NOT NULL CHECK(mass_state IN ({_STATES})),
        CHECK(composition_id != child_version_id), UNIQUE(composition_id, position))""",
    """CREATE TABLE food_composition_steps (
        id CHAR(32) NOT NULL PRIMARY KEY,
        composition_id CHAR(32) NOT NULL REFERENCES food_composition_versions(id) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED,
        position INTEGER NOT NULL CHECK(typeof(position) = 'integer' AND position >= 0),
        transformation_id CHAR(32) NOT NULL REFERENCES food_transformations(id) ON DELETE RESTRICT,
        UNIQUE(composition_id, position))""",
    """CREATE TRIGGER food_retention_profiles_complete BEFORE INSERT ON food_retention_profiles
        WHEN NEW.value_count != (SELECT count(*) FROM food_retention_values WHERE profile_id = NEW.id)
        BEGIN SELECT RAISE(ABORT, 'Набор факторов неполон.'); END""",
    """CREATE TRIGGER food_composition_versions_complete BEFORE INSERT ON food_composition_versions
        WHEN NEW.node_count != (SELECT count(*) FROM food_composition_nodes WHERE composition_id = NEW.id)
          OR NEW.step_count != (SELECT count(*) FROM food_composition_steps WHERE composition_id = NEW.id)
          OR (NEW.kind = 'ATOMIC' AND NOT EXISTS(SELECT 1 FROM food_nutrition_profiles
              WHERE id = NEW.profile_id AND food_ingredient_id = NEW.food_ingredient_id))
        BEGIN SELECT RAISE(ABORT, 'Состав неполон или профиль принадлежит другому продукту.'); END""",
    """CREATE TRIGGER food_composition_nodes_acyclic BEFORE INSERT ON food_composition_nodes
        WHEN EXISTS(WITH RECURSIVE reachable(id) AS (
            SELECT NEW.child_version_id UNION
            SELECT n.child_version_id FROM food_composition_nodes n JOIN reachable r ON n.composition_id = r.id
        ) SELECT 1 FROM reachable WHERE id = NEW.composition_id)
        BEGIN SELECT RAISE(ABORT, 'Цикл в графе состава.'); END""",
)


def upgrade(connection):
    if not connection.in_transaction:
        connection.execute("BEGIN")
    for statement in STATEMENTS:
        connection.execute(statement)
    for table in TABLES:
        for operation in ("UPDATE", "DELETE"):
            connection.execute(f"""CREATE TRIGGER {table}_no_{operation.lower()}
                BEFORE {operation} ON {table}
                BEGIN SELECT RAISE(ABORT, 'Исторический состав неизменяем.'); END""")
        condition = "id = NEW.id"
        if table == "food_retention_values":
            condition = (
                "profile_id = NEW.profile_id AND nutrient_code = NEW.nutrient_code"
            )
        elif table == "food_composition_versions":
            condition += " OR (food_ingredient_id = NEW.food_ingredient_id AND version = NEW.version)"
        elif table in ("food_composition_nodes", "food_composition_steps"):
            condition += (
                " OR (composition_id = NEW.composition_id AND position = NEW.position)"
            )
        connection.execute(f"""CREATE TRIGGER {table}_no_replace BEFORE INSERT ON {table}
            WHEN EXISTS(SELECT 1 FROM {table} WHERE {condition})
            BEGIN SELECT RAISE(ABORT, 'Исторический состав неизменяем.'); END""")
    for child, parent, fk in (
        ("food_retention_values", "food_retention_profiles", "profile_id"),
        ("food_composition_nodes", "food_composition_versions", "composition_id"),
        ("food_composition_steps", "food_composition_versions", "composition_id"),
    ):
        connection.execute(f"""CREATE TRIGGER {child}_no_late_insert BEFORE INSERT ON {child}
            WHEN EXISTS(SELECT 1 FROM {parent} WHERE id = NEW.{fk})
            BEGIN SELECT RAISE(ABORT, 'Снимок уже зафиксирован.'); END""")
