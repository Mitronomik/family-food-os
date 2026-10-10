"""Compose the accepted Shopping application service against the shared engine."""

from sqlalchemy.engine import Engine

from app.persistence.sqlalchemy_core.shopping_uow import (
    SqlAlchemyShoppingReadScope,
    SqlAlchemyShoppingUnitOfWork,
)
from app.services.shopping import ShoppingService


def create_shopping_service(engine: Engine) -> ShoppingService:
    return ShoppingService(
        write_scope_factory=lambda: SqlAlchemyShoppingUnitOfWork(engine),
        read_scope_factory=lambda: SqlAlchemyShoppingReadScope(engine),
    )
