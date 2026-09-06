"""Review import transaction; all repositories share the project write scope."""

from app.persistence.sqlalchemy_core.food_ingredient_repositories import (
    SqlAlchemyFoodIngredientRepository,
    SqlAlchemyFoodNutritionProfileRepository,
)
from app.persistence.sqlalchemy_core.food_recipe_repositories import (
    SqlAlchemyRecipeRepository,
    SqlAlchemyRecipeVersionRepository,
)
from app.persistence.sqlalchemy_core.nutrition_evidence_repositories import (
    SqlAlchemyNutritionEvidenceRepository,
)
from app.persistence.sqlalchemy_core.uow import SqlAlchemyUnitOfWork


class SqlAlchemyNutritionEvidenceUnitOfWork(SqlAlchemyUnitOfWork):
    @property
    def evidence(self):
        return SqlAlchemyNutritionEvidenceRepository(self.adapter_connection)

    @property
    def ingredients(self):
        return SqlAlchemyFoodIngredientRepository(self.adapter_connection)

    @property
    def nutrition_profiles(self):
        return SqlAlchemyFoodNutritionProfileRepository(self.adapter_connection)

    @property
    def recipes(self):
        return SqlAlchemyRecipeRepository(self.adapter_connection)

    @property
    def versions(self):
        return SqlAlchemyRecipeVersionRepository(self.adapter_connection)
