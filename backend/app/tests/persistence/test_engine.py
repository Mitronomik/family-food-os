import sqlite3

import pytest
from sqlalchemy import text

from app.db.config import DatabaseConfig
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine


def test_engine_uses_explicit_path_and_creates_parent_directory(tmp_path):
    database_path = tmp_path / "nested" / "probe.sqlite"

    engine = create_sqlite_engine(DatabaseConfig(path=database_path))
    try:
        assert database_path.parent.is_dir()
        assert engine.url.database == str(database_path)
        with engine.connect() as connection:
            assert connection.scalar(text("SELECT 1")) == 1
        assert database_path.is_file()
    finally:
        engine.dispose()


def test_every_connection_enables_foreign_keys_and_modern_transaction_control(
    tmp_path,
):
    engine = create_sqlite_engine(
        DatabaseConfig(path=tmp_path / "connection-settings.sqlite")
    )
    try:
        with engine.connect() as connection:
            assert connection.scalar(text("PRAGMA foreign_keys")) == 1
            driver_connection = connection.connection.driver_connection
            assert driver_connection.autocommit is False
            assert driver_connection.autocommit != sqlite3.LEGACY_TRANSACTION_CONTROL
    finally:
        engine.dispose()


def test_engine_construction_does_not_create_database_or_application_tables(tmp_path):
    database_path = tmp_path / "empty.sqlite"

    engine = create_sqlite_engine(DatabaseConfig(path=database_path))
    try:
        assert not database_path.exists()
        with engine.connect() as connection:
            table_names = connection.execute(
                text("SELECT name FROM sqlite_master WHERE type = 'table'")
            ).scalars()
            assert list(table_names) == []
    finally:
        engine.dispose()

    assert database_path.exists()


@pytest.mark.parametrize(
    "filename",
    [
        "question?mark.sqlite",
        "hash#mark.sqlite",
        "percent%mark.sqlite",
        "space mark.sqlite",
    ],
)
def test_engine_uses_exact_path_with_url_significant_characters(tmp_path, filename):
    database_path = tmp_path / filename

    engine = create_sqlite_engine(DatabaseConfig(path=database_path))
    try:
        assert engine.url.database == str(database_path)
        with engine.connect() as connection:
            assert connection.scalar(text("SELECT 1")) == 1
    finally:
        engine.dispose()

    assert database_path.is_file()
