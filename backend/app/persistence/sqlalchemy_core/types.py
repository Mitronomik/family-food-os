"""Portable SQLAlchemy Core type conventions for new persistence adapters."""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import DateTime, String, Uuid
from sqlalchemy.types import TypeDecorator


def entity_uuid_type() -> Uuid:
    """Return the backend-agnostic representation for entity UUID values."""

    return Uuid(as_uuid=True)


class UTCDateTime(TypeDecorator[datetime]):
    """Persist aware instants as naive UTC and restore them as aware UTC."""

    impl = DateTime
    cache_ok = True

    def process_bind_param(
        self, value: datetime | None, dialect: Any
    ) -> datetime | None:
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


class DecimalText(TypeDecorator[Decimal]):
    """Persist authoritative decimals as canonical text on SQLite.

    SQLite's numeric affinity may pass values through binary floating point.
    Text storage preserves the exact application-validated decimal and remains
    explicit until the PostgreSQL cutover chooses its native numeric shape.
    """

    impl = String
    cache_ok = True

    def process_bind_param(self, value: Decimal | None, dialect: Any) -> str | None:
        del dialect
        if value is None:
            return None
        if not isinstance(value, Decimal):
            raise TypeError("DecimalText requires a Decimal value.")
        return format(value, "f")

    def process_result_value(self, value: str | None, dialect: Any) -> Decimal | None:
        del dialect
        if value is None:
            return None
        return Decimal(value)
