"""Infrastructure composition for Pantry operations."""

from sqlalchemy.engine import Engine

from app.persistence.sqlalchemy_core.pantry_uow import (
    SqlAlchemyPantryReadScope,
    SqlAlchemyPantryUnitOfWork,
)
from app.services.pantry import PantryService


def create_pantry_service(engine: Engine) -> PantryService:
    return PantryService(
        write_scope_factory=lambda: SqlAlchemyPantryUnitOfWork(engine),
        read_scope_factory=lambda: SqlAlchemyPantryReadScope(engine),
    )
