from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest
from sqlalchemy import Column, Integer, MetaData, Table, insert, select
from sqlalchemy.dialects import postgresql, sqlite
from sqlalchemy.exc import StatementError
from sqlalchemy.schema import CreateTable

from app.db.config import DatabaseConfig
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
from app.persistence.sqlalchemy_core.types import UTCDateTime, entity_uuid_type


metadata = MetaData()
portable_values = Table(
    "pr2b_portable_values",
    metadata,
    Column("row_id", Integer, primary_key=True),
    Column("entity_id", entity_uuid_type(), nullable=True),
    Column("occurred_at", UTCDateTime(), nullable=True),
)


@pytest.fixture
def engine(tmp_path):
    value = create_sqlite_engine(DatabaseConfig(path=tmp_path / "types.sqlite"))
    with value.begin() as connection:
        portable_values.create(connection)
    try:
        yield value
    finally:
        value.dispose()


def insert_and_read(engine, *, entity_id=None, occurred_at=None):
    with engine.begin() as connection:
        result = connection.execute(
            insert(portable_values).values(
                entity_id=entity_id,
                occurred_at=occurred_at,
            )
        )
        row_id = result.inserted_primary_key[0]
    with engine.connect() as connection:
        return connection.execute(
            select(portable_values).where(portable_values.c.row_id == row_id)
        ).one()


def test_uuid_roundtrips_as_python_uuid(engine):
    expected = uuid4()

    row = insert_and_read(engine, entity_id=expected)

    assert isinstance(row.entity_id, UUID)
    assert row.entity_id == expected


def test_generic_uuid_convention_compiles_for_sqlite_and_postgresql():
    sqlite_ddl = str(CreateTable(portable_values).compile(dialect=sqlite.dialect()))
    postgresql_ddl = str(
        CreateTable(portable_values).compile(dialect=postgresql.dialect())
    )

    assert "CHAR(32)" in sqlite_ddl
    assert "UUID" in postgresql_ddl


def test_utc_aware_datetime_roundtrips_as_aware_utc(engine):
    expected = datetime(2026, 9, 1, 12, 30, 45, 123456, tzinfo=timezone.utc)

    row = insert_and_read(engine, occurred_at=expected)

    assert row.occurred_at == expected
    assert row.occurred_at.tzinfo is timezone.utc


def test_non_utc_datetime_is_normalized_to_utc(engine):
    source = datetime(
        2026,
        9,
        1,
        15,
        30,
        tzinfo=timezone(timedelta(hours=3)),
    )

    row = insert_and_read(engine, occurred_at=source)

    assert row.occurred_at == datetime(2026, 9, 1, 12, 30, tzinfo=timezone.utc)
    assert row.occurred_at.tzinfo is timezone.utc


def test_naive_datetime_is_rejected(engine):
    with pytest.raises(StatementError, match="timezone-aware"):
        insert_and_read(engine, occurred_at=datetime(2026, 9, 1, 12, 30))


def test_none_roundtrips_unchanged(engine):
    row = insert_and_read(engine, entity_id=None, occurred_at=None)

    assert row.entity_id is None
    assert row.occurred_at is None
