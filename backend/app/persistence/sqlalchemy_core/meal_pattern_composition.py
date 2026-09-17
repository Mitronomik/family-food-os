"""Infrastructure composition for Meal Pattern Catalogue operations."""

from sqlalchemy.engine import Engine

from app.persistence.sqlalchemy_core.meal_pattern_uow import (
    SqlAlchemyMealPatternCatalogueReadScope,
    SqlAlchemyMealPatternCatalogueUnitOfWork,
)
from app.services.meal_patterns import MealPatternCatalogueService


def create_meal_pattern_catalogue_service(
    engine: Engine,
) -> MealPatternCatalogueService:
    return MealPatternCatalogueService(
        write_scope_factory=lambda: SqlAlchemyMealPatternCatalogueUnitOfWork(engine),
        read_scope_factory=lambda: SqlAlchemyMealPatternCatalogueReadScope(engine),
    )
