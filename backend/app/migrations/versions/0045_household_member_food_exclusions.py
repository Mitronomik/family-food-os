"""0045: per-member non-medical canonical food exclusions.

Purely additive: old Household, MealPlan, Recipe, Shopping and Food rows are untouched.
"""
MIGRATION_ID = "0045_household_member_food_exclusions"


def upgrade(db):
    # Composite FK ensures a member from another Household cannot be linked.
    db.execute("""
        CREATE UNIQUE INDEX uq_household_member_scope
        ON household_members (household_id, id)
    """)
    db.execute("""
        CREATE TABLE household_member_excluded_food_ingredients (
            household_id CHAR(32) NOT NULL,
            member_id CHAR(32) NOT NULL,
            food_ingredient_id CHAR(32) NOT NULL,
            PRIMARY KEY (household_id, member_id, food_ingredient_id),
            FOREIGN KEY (household_id, member_id)
                REFERENCES household_members(household_id, id) ON DELETE RESTRICT,
            FOREIGN KEY (food_ingredient_id)
                REFERENCES food_ingredients(id) ON DELETE RESTRICT,
            CHECK (length(household_id) = 32),
            CHECK (length(member_id) = 32),
            CHECK (length(food_ingredient_id) = 32)
        )
    """)
    db.execute("""
        CREATE INDEX idx_household_excluded_food_member
        ON household_member_excluded_food_ingredients
            (household_id, member_id, food_ingredient_id)
    """)
