"""Synchronous SQLAlchemy Core adapter primitives."""

from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
from app.persistence.sqlalchemy_core.types import UTCDateTime, entity_uuid_type
from app.persistence.sqlalchemy_core.uow import (
    SqlAlchemyReadOnlyScope,
    SqlAlchemyUnitOfWork,
)

__all__ = [
    "SqlAlchemyReadOnlyScope",
    "SqlAlchemyUnitOfWork",
    "UTCDateTime",
    "create_sqlite_engine",
    "entity_uuid_type",
]
