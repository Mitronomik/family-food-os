"""Portable SQLAlchemy Core type conventions for new persistence adapters."""

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, Uuid
from sqlalchemy.types import TypeDecorator


def entity_uuid_type() -> Uuid:
    """Return the backend-agnostic representation for entity UUID values."""

    return Uuid(as_uuid=True)


class UTCDateTime(TypeDecorator[datetime]):
    """Persist aware instants as naive UTC and restore them as aware UTC."""

    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect: Any) -> datetime | None:
        del dialect
        if value is None:
            return None
        if not isinstance(value, datetime):
            raise TypeError("UTCDateTime requires a datetime value.")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("UTCDateTime requires a timezone-aware datetime.")
        return value.astimezone(timezone.utc).replace(tzinfo=None)

    def process_result_value(
        self, value: datetime | None, dialect: Any
    ) -> datetime | None:
        del dialect
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
