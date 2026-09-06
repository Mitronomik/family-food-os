"""Infrastructure composition for the read-only Nutrition engine."""

from sqlalchemy.engine import Engine

from app.persistence.sqlalchemy_core.nutrition_read_scope import (
    SqlAlchemyNutritionReadScope,
)
from app.services.nutrition import NutritionService


def create_nutrition_service(engine: Engine) -> NutritionService:
    return NutritionService(lambda: SqlAlchemyNutritionReadScope(engine))
