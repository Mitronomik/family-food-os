"""Infrastructure composition for Recipe Catalogue operations."""

from sqlalchemy.engine import Engine

from app.persistence.sqlalchemy_core.food_recipe_uow import (
    SqlAlchemyRecipeCatalogueReadScope,
    SqlAlchemyRecipeCatalogueUnitOfWork,
)
from app.services.food_recipes import FoodRecipeCatalogueService
from app.services.pr10_ff_typed_ids import FixtureTypedIdProvider


def create_food_recipe_catalogue_service(
    engine: Engine, *, id_provider: FixtureTypedIdProvider | None = None
) -> FoodRecipeCatalogueService:
    return FoodRecipeCatalogueService(
        write_scope_factory=lambda: SqlAlchemyRecipeCatalogueUnitOfWork(engine),
        read_scope_factory=lambda: SqlAlchemyRecipeCatalogueReadScope(engine),
        id_provider=id_provider,
    )
