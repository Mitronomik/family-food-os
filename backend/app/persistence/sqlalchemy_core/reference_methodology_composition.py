"""Infrastructure composition for Step 6A application operations."""

from sqlalchemy.engine import Engine

from app.persistence.sqlalchemy_core.reference_methodology_uow import (
    SqlAlchemyReferenceMethodologyReadScope,
    SqlAlchemyReferenceMethodologyUnitOfWork,
)
from app.seed.russian_reference_table_step5 import russian_reference_table_provider
from app.services.reference_methodology import ReferenceMethodologyService


def create_reference_methodology_service(engine: Engine) -> ReferenceMethodologyService:
    return ReferenceMethodologyService(
        write_scope_factory=lambda: SqlAlchemyReferenceMethodologyUnitOfWork(engine),
        read_scope_factory=lambda: SqlAlchemyReferenceMethodologyReadScope(engine),
        russian_reference_tables=russian_reference_table_provider,
    )
