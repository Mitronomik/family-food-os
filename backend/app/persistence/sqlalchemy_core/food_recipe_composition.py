"""Infrastructure composition for Recipe Catalogue operations."""

from sqlalchemy.engine import Engine

from app.persistence.sqlalchemy_core.food_recipe_uow import (
    SqlAlchemyRecipeCatalogueReadScope,
    SqlAlchemyRecipeCatalogueUnitOfWork,
)
from app.services.food_recipes import FoodRecipeCatalogueService


def create_food_recipe_catalogue_service(engine: Engine) -> FoodRecipeCatalogueService:
    return FoodRecipeCatalogueService(
        write_scope_factory=lambda: SqlAlchemyRecipeCatalogueUnitOfWork(engine),
        read_scope_factory=lambda: SqlAlchemyRecipeCatalogueReadScope(engine),
    )
