"""SQLite engine construction for new SQLAlchemy Core persistence adapters."""

from typing import Any

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine, URL

from app.db.config import DatabaseConfig, get_database_config


def create_sqlite_engine(config: DatabaseConfig | None = None) -> Engine:
    """Create an engine without creating or migrating application schema."""

    database_config = config or get_database_config()
    database_config.path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(
        URL.create("sqlite+pysqlite", database=str(database_config.path)),
        connect_args={"autocommit": False},
    )
    event.listen(engine, "connect", _enable_sqlite_foreign_keys)
    return engine


def _enable_sqlite_foreign_keys(
    dbapi_connection: Any, connection_record: Any
) -> None:
    """Enable foreign keys outside the DBAPI transaction opened on connect."""

    del connection_record
    previous_autocommit = dbapi_connection.autocommit
    dbapi_connection.autocommit = True
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("PRAGMA foreign_keys = ON")
    finally:
        cursor.close()
        dbapi_connection.autocommit = previous_autocommit
