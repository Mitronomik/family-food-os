MIGRATION_ID = "0025_pantry"


def _uuid(column):
    return (
        f"length({column}) = 32 AND {column} NOT GLOB '*[^0-9a-f]*' "
        f"AND substr({column}, 13, 1) = '4' "
        f"AND substr({column}, 17, 1) IN ('8', '9', 'a', 'b')"
    )


def _quantity(column, *, positive=False):
    # Fixed three-place decimal text: all runtime arithmetic remains exact Decimal.
    condition = (
        f"typeof({column}) = 'text' AND length({column}) BETWEEN 5 AND 16 "
        f"AND substr({column}, -4, 1) = '.' "
        f"AND substr({column}, 1, length({column}) - 4) NOT GLOB '*[^0-9]*' "
        f"AND substr({column}, -3) NOT GLOB '*[^0-9]*' "
        f"AND (length({column}) = 5 OR substr({column}, 1, 1) != '0')"
    )
    return condition + (f" AND {column} != '0.000'" if positive else "")


def _date(column):
    return (
        f"{column} IS NULL OR (length({column}) = 10 "
        f"AND {column} GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]' "
        f"AND substr({column}, 1, 4) BETWEEN '0001' AND '9999' "
        f"AND date({column}, '+0 days') IS NOT NULL "
        f"AND date({column}, '+0 days') = {column})"
    )


def _instant(column):
    # UTCDateTime writes offset-free UTC text; reject offset/local variants.
    return (
        f"length({column}) = 26 "
        f"AND {column} GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9] "
        "[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9][0-9][0-9][0-9]' "
        f"AND substr({column}, 1, 4) BETWEEN '0001' AND '9999' "
        f"AND date(substr({column}, 1, 10), '+0 days') IS NOT NULL "
        f"AND date(substr({column}, 1, 10), '+0 days') = substr({column}, 1, 10) "
        f"AND substr({column}, 12, 2) BETWEEN '00' AND '23' "
        f"AND substr({column}, 15, 2) BETWEEN '00' AND '59' "
        f"AND substr({column}, 18, 2) BETWEEN '00' AND '59'"
    )


def upgrade(connection):
    """Append Household Pantry; preserve all earlier food and legacy schema."""
    connection.executescript(
        f"""
        CREATE TABLE pantry_items (
            id CHAR(32) PRIMARY KEY NOT NULL CHECK ({_uuid('id')}),
            household_id CHAR(32) NOT NULL REFERENCES households(id) ON DELETE RESTRICT,
            food_ingredient_id CHAR(32) NOT NULL REFERENCES food_ingredients(id) ON DELETE RESTRICT,
            quantity TEXT NOT NULL CHECK ({_quantity('quantity')}),
            unit TEXT NOT NULL CHECK (unit IN ('g', 'ml', 'pcs')),
            location TEXT NOT NULL CHECK (location IN ('PANTRY', 'FRIDGE', 'FREEZER')),
            estimated BOOLEAN NOT NULL CHECK (estimated IN (0, 1)),
            purchased_on DATE CHECK ({_date('purchased_on')}),
            opened_on DATE CHECK ({_date('opened_on')}),
            expires_on DATE CHECK ({_date('expires_on')}),
            created_at DATETIME NOT NULL CHECK ({_instant('created_at')}),
            updated_at DATETIME NOT NULL CHECK ({_instant('updated_at')}),
            UNIQUE (id, household_id, unit),
            CHECK (updated_at >= created_at)
        );
        CREATE TABLE pantry_movements (
            id CHAR(32) PRIMARY KEY NOT NULL CHECK ({_uuid('id')}),
            household_id CHAR(32) NOT NULL REFERENCES households(id) ON DELETE RESTRICT,
            pantry_item_id CHAR(32) NOT NULL,
            movement_type TEXT NOT NULL CHECK (movement_type IN (
                'ADD', 'CONSUMPTION', 'WASTE', 'ADJUSTMENT_IN', 'ADJUSTMENT_OUT'
            )),
            quantity TEXT NOT NULL CHECK ({_quantity('quantity', positive=True)}),
            unit TEXT NOT NULL CHECK (unit IN ('g', 'ml', 'pcs')),
            occurred_at DATETIME NOT NULL CHECK ({_instant('occurred_at')}),
            created_at DATETIME NOT NULL CHECK ({_instant('created_at')}),
            FOREIGN KEY (pantry_item_id, household_id, unit)
                REFERENCES pantry_items(id, household_id, unit) ON DELETE RESTRICT
        );
        CREATE INDEX idx_pantry_items_household_ingredient_expiry
            ON pantry_items(household_id, food_ingredient_id, expires_on, purchased_on, created_at, id);
        CREATE INDEX idx_pantry_items_household_expiry
            ON pantry_items(household_id, expires_on, created_at, id);
        CREATE INDEX idx_pantry_movements_item_history
            ON pantry_movements(household_id, pantry_item_id, occurred_at, created_at, id);
        CREATE TRIGGER trg_pantry_items_initial_stock
        BEFORE INSERT ON pantry_items
        BEGIN
            SELECT RAISE(ABORT, 'initial Pantry quantity must be positive') WHERE NEW.quantity = '0.000';
            SELECT RAISE(ABORT, 'Pantry requires active FoodIngredient and matching default unit')
            WHERE NOT EXISTS (
                SELECT 1 FROM food_ingredients
                WHERE id = NEW.food_ingredient_id AND is_active = 1 AND default_unit = NEW.unit
            );
        END;
        CREATE TRIGGER trg_pantry_items_identity_immutable
        BEFORE UPDATE OF id, household_id, food_ingredient_id, unit, created_at ON pantry_items
        WHEN NEW.id != OLD.id OR NEW.household_id != OLD.household_id
            OR NEW.food_ingredient_id != OLD.food_ingredient_id OR NEW.unit != OLD.unit
            OR NEW.created_at != OLD.created_at
        BEGIN
            SELECT RAISE(ABORT, 'Pantry item identity is immutable');
        END;
        CREATE TRIGGER trg_pantry_items_no_delete
        BEFORE DELETE ON pantry_items
        BEGIN
            SELECT RAISE(ABORT, 'Pantry items retain durable history');
        END;
        CREATE TRIGGER trg_pantry_movements_no_update
        BEFORE UPDATE ON pantry_movements
        BEGIN
            SELECT RAISE(ABORT, 'Pantry movements are immutable');
        END;
        CREATE TRIGGER trg_pantry_movements_no_delete
        BEFORE DELETE ON pantry_movements
        BEGIN
            SELECT RAISE(ABORT, 'Pantry movements are immutable');
        END;
        """
    )
