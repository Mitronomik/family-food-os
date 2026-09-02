"""Infrastructure composition for platform Food Catalogue operations."""

from sqlalchemy.engine import Engine

from app.persistence.sqlalchemy_core.food_ingredient_uow import (
    SqlAlchemyFoodCatalogueReadScope,
    SqlAlchemyFoodCatalogueUnitOfWork,
)
from app.services.food_ingredients import FoodCatalogueService


def create_food_catalogue_service(engine: Engine) -> FoodCatalogueService:
    return FoodCatalogueService(
        write_scope_factory=lambda: SqlAlchemyFoodCatalogueUnitOfWork(engine),
        read_scope_factory=lambda: SqlAlchemyFoodCatalogueReadScope(engine),
    )
