"""Persist immutable MealPlan member reference-methodology pins."""

MIGRATION_ID = "0037_meal_plan_reference_methodology_pins"


def upgrade(connection):
    if not connection.in_transaction:
        connection.execute("BEGIN")

    connection.execute(
        """CREATE TABLE meal_plan_member_reference_methodology_pins (
            plan_id CHAR(32) NOT NULL,
            member_id CHAR(32) NOT NULL,
            reference_methodology_selection_id CHAR(32) NOT NULL,
            birth_date DATE,
            sex TEXT,
            height_cm TEXT,
            weight_kg TEXT,
            activity_level TEXT NOT NULL,
            goal TEXT NOT NULL,
            member_updated_at DATETIME NOT NULL,
            PRIMARY KEY (plan_id, member_id),
            FOREIGN KEY (plan_id)
                REFERENCES meal_plans(id) ON DELETE RESTRICT,
            FOREIGN KEY (member_id)
                REFERENCES household_members(id) ON DELETE RESTRICT,
            FOREIGN KEY (reference_methodology_selection_id)
                REFERENCES member_reference_methodology_selections(id)
                ON DELETE RESTRICT,
            CHECK (length(plan_id) = 32),
            CHECK (length(member_id) = 32),
            CHECK (length(reference_methodology_selection_id) = 32),
            CHECK (sex IS NULL OR length(trim(sex)) > 0),
            CHECK (height_cm IS NULL OR CAST(height_cm AS NUMERIC) > 0),
            CHECK (weight_kg IS NULL OR CAST(weight_kg AS NUMERIC) > 0),
            CHECK (length(trim(activity_level)) > 0),
            CHECK (length(trim(goal)) > 0)
        )"""
    )
    connection.execute(
        """CREATE TRIGGER trg_meal_plan_reference_methodology_pins_no_update
        BEFORE UPDATE ON meal_plan_member_reference_methodology_pins
        BEGIN
            SELECT RAISE(
                ABORT,
                'meal plan reference methodology pins are immutable'
            );
        END"""
    )
    connection.execute(
        """CREATE TRIGGER trg_meal_plan_reference_methodology_pins_no_delete
        BEFORE DELETE ON meal_plan_member_reference_methodology_pins
        BEGIN
            SELECT RAISE(
                ABORT,
                'meal plan reference methodology pins are immutable'
            );
        END"""
    )
