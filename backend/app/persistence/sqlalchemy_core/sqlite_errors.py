"""SQLite-specific DBAPI error classification for persistence adapters."""

import sqlite3

from sqlalchemy.exc import OperationalError


def is_sqlite_concurrency_conflict(exc: OperationalError) -> bool:
    """Return whether SQLite reported a busy/locked concurrent-writer conflict."""

    original = exc.orig
    code = getattr(original, "sqlite_errorcode", None)
    if not isinstance(code, int):
        return False
    return (code & 0xFF) in {sqlite3.SQLITE_BUSY, sqlite3.SQLITE_LOCKED}
