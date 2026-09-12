"""Bounded data-upgrade scope; all publications share one project transaction."""

from sqlalchemy import select

from app.persistence.sqlalchemy_core.nutrition_evidence_uow import (
    SqlAlchemyNutritionEvidenceUnitOfWork,
)
from app.persistence.sqlalchemy_core.ru_food_data import SqlAlchemyRuFoodUnitOfWork
from app.persistence.sqlalchemy_core.food_recipe_tables import food_recipes_table


class B2B2UnitOfWork(SqlAlchemyNutritionEvidenceUnitOfWork, SqlAlchemyRuFoodUnitOfWork):
    def current_details(self):
        """Include inactive recipes too: profile authority affects every latest use."""
        ids = self.adapter_connection.scalars(select(food_recipes_table.c.id)).all()
        return [
            self.versions.get_detail(history[-1].id)
            for recipe_id in ids
            if (history := self.versions.list_for_recipe(recipe_id))
        ]
