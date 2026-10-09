"""PR9-B: additive, immutable household Shopping snapshots.

SQLite custom runner is the sole schema authority. No create_all or Alembic.
"""

MIGRATION_ID = "0043_shopping_engine"

_Q = """typeof({c}) = 'text'
    AND length({c}) BETWEEN 5 AND 24
    AND substr({c}, -4, 1) = '.'
    AND length({c}) - length(replace({c}, '.', '')) = 1
    AND {c} NOT GLOB '*[^0-9.]*'
    AND CAST({c} AS NUMERIC) >= 0
    AND CAST({c} AS NUMERIC) <= 999999999999.999"""


def upgrade(connection):
    # The runner owns the marker. Each execute is contained in its transaction.
    connection.execute("""
        CREATE TABLE shopping_lists (
          id CHAR(32) PRIMARY KEY NOT NULL CHECK(length(id)=32),
          household_id CHAR(32) NOT NULL REFERENCES households(id) ON DELETE RESTRICT,
          meal_plan_id CHAR(32) NOT NULL REFERENCES meal_plans(id) ON DELETE RESTRICT,
          source_plan_revision_number INTEGER NOT NULL CHECK(source_plan_revision_number > 0),
          source_pantry_snapshot_hash TEXT NOT NULL CHECK(length(source_pantry_snapshot_hash)=64),
          as_of_date TEXT NOT NULL CHECK(as_of_date GLOB '????-??-??'),
          engine_version TEXT NOT NULL CHECK(length(engine_version) > 0),
          pantry_policy_version TEXT NOT NULL CHECK(length(pantry_policy_version) > 0),
          config_fingerprint TEXT NOT NULL CHECK(length(config_fingerprint)=64),
          source_fingerprint TEXT NOT NULL CHECK(length(source_fingerprint)=64),
          content_fingerprint TEXT NOT NULL CHECK(length(content_fingerprint)=64),
          status TEXT NOT NULL CHECK(status IN ('COMPLETE','INCOMPLETE')),
          price_status TEXT NOT NULL CHECK(price_status = 'UNKNOWN'),
          provenance_json TEXT NOT NULL CHECK(json_valid(provenance_json)),
          supersedes_list_id CHAR(32) REFERENCES shopping_lists(id) ON DELETE RESTRICT,
          created_at DATETIME NOT NULL,
          UNIQUE(id, household_id),
          UNIQUE(household_id, meal_plan_id, source_fingerprint)
        )
    """)
    connection.execute(
        """
        CREATE TABLE shopping_list_items (
          id CHAR(32) PRIMARY KEY NOT NULL CHECK(length(id)=32),
          shopping_list_id CHAR(32) NOT NULL,
          household_id CHAR(32) NOT NULL,
          food_ingredient_id CHAR(32) NOT NULL REFERENCES food_ingredients(id) ON DELETE RESTRICT,
          form_basis TEXT NOT NULL CHECK(length(trim(form_basis)) > 0),
          unit TEXT NOT NULL CHECK(unit IN ('g','ml','pcs')),
          required_quantity TEXT NOT NULL,
          pantry_available_quantity TEXT NOT NULL,
          purchase_quantity TEXT NOT NULL,
          ordinal INTEGER NOT NULL CHECK(ordinal > 0),
          FOREIGN KEY(shopping_list_id, household_id)
            REFERENCES shopping_lists(id, household_id) ON DELETE RESTRICT,
          UNIQUE(shopping_list_id, food_ingredient_id, form_basis, unit),
          UNIQUE(shopping_list_id, ordinal),
          CHECK( ("""
        + _Q.format(c="required_quantity")
        + """) ),
          CHECK( ("""
        + _Q.format(c="pantry_available_quantity")
        + """) ),
          CHECK( ("""
        + _Q.format(c="purchase_quantity")
        + """) ),
          CHECK(CAST(pantry_available_quantity AS NUMERIC) <= CAST(required_quantity AS NUMERIC)),
          CHECK(unit <> 'pcs' OR substr(purchase_quantity,-3)='000')
        )
    """
    )
    connection.execute("""
        CREATE TABLE shopping_unresolved_obligations (
          id CHAR(32) PRIMARY KEY NOT NULL CHECK(length(id)=32),
          shopping_list_id CHAR(32) NOT NULL,
          household_id CHAR(32) NOT NULL,
          meal_event_id CHAR(32) NOT NULL REFERENCES meal_plan_events(id) ON DELETE RESTRICT,
          source_kind TEXT NOT NULL CHECK(source_kind IN ('ASSEMBLY','LEFTOVER','PREPARED','READY_MEAL')),
          reason TEXT NOT NULL CHECK(reason IN ('ASSEMBLY_UNSUPPORTED',
            'LEFTOVER_SUPPLY_UNVERIFIED','PREPARED_SUPPLY_UNVERIFIED','READY_MEAL_UNRESOLVED')),
          ordinal INTEGER NOT NULL CHECK(ordinal > 0),
          FOREIGN KEY(shopping_list_id, household_id)
            REFERENCES shopping_lists(id, household_id) ON DELETE RESTRICT,
          UNIQUE(shopping_list_id, meal_event_id, reason),
          UNIQUE(shopping_list_id, ordinal)
        )
    """)
    connection.execute("""
      CREATE INDEX idx_shopping_lists_household_plan_history
      ON shopping_lists(household_id,meal_plan_id,created_at,id)
    """)
    connection.execute("""
      CREATE INDEX idx_shopping_items_list ON shopping_list_items(shopping_list_id,ordinal)
    """)
    connection.execute("""
      CREATE INDEX idx_shopping_unresolved_list
      ON shopping_unresolved_obligations(shopping_list_id,ordinal)
    """)
    # A historical shopping snapshot is an immutable record, not an editable cart.
    for table in (
        "shopping_lists",
        "shopping_list_items",
        "shopping_unresolved_obligations",
    ):
        for action in ("UPDATE", "DELETE"):
            connection.execute(f"""
                CREATE TRIGGER trg_{table}_{action.lower()}_immutable
                BEFORE {action} ON {table}
                BEGIN SELECT RAISE(ABORT,'immutable shopping snapshot'); END
            """)
    # Ensure the referenced MealPlan really belongs to the list's household.
    connection.execute("""
      CREATE TRIGGER trg_shopping_list_household BEFORE INSERT ON shopping_lists
      WHEN NOT EXISTS (
        SELECT 1 FROM meal_plans p
        WHERE p.id=NEW.meal_plan_id AND p.household_id=NEW.household_id
          AND p.revision_number=NEW.source_plan_revision_number)
      BEGIN SELECT RAISE(ABORT,'shopping plan household/revision mismatch'); END
    """)
    connection.execute("""
      CREATE TRIGGER trg_shopping_list_supersedes BEFORE INSERT ON shopping_lists
      WHEN NEW.supersedes_list_id IS NOT NULL AND NOT EXISTS (
        SELECT 1 FROM shopping_lists p WHERE p.id=NEW.supersedes_list_id
        AND p.household_id=NEW.household_id AND p.meal_plan_id=NEW.meal_plan_id)
      BEGIN SELECT RAISE(ABORT,'shopping successor household/plan mismatch'); END
    """)
    connection.execute("""
      CREATE TRIGGER trg_shopping_obligation_event BEFORE INSERT ON shopping_unresolved_obligations
      WHEN NOT EXISTS (
        SELECT 1 FROM meal_plan_events e JOIN shopping_lists l ON e.plan_id=l.meal_plan_id
        WHERE l.id=NEW.shopping_list_id AND e.id=NEW.meal_event_id
          AND e.source_kind=NEW.source_kind)
      BEGIN SELECT RAISE(ABORT,'shopping obligation event mismatch'); END
    """)
