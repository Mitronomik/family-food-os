"""Explicit SQLAlchemy Core transaction scopes for persistence adapters."""

from types import TracebackType

from sqlalchemy.engine import Connection, Engine, Transaction


class SqlAlchemyUnitOfWork:
    """Single-use write scope owning exactly one connection and transaction.

    ``adapter_connection`` is intentionally an infrastructure-only escape hatch
    for concrete persistence repositories. It is not part of the application
    ``UnitOfWork`` protocol.
    """

    def __init__(self, engine: Engine) -> None:
        self._engine = engine
        self._connection: Connection | None = None
        self._transaction: Transaction | None = None
        self._used = False

    def __enter__(self) -> "SqlAlchemyUnitOfWork":
        if self._used:
            raise RuntimeError("SqlAlchemyUnitOfWork instances are single-use.")
        self._used = True
        connection = self._engine.connect()
        try:
            transaction = connection.begin()
        except BaseException:
            connection.close()
            raise
        self._connection = connection
        self._transaction = transaction
        return self

    @property
    def adapter_connection(self) -> Connection:
        """Return the active connection to persistence adapter code only."""

        if self._connection is None or self._transaction is None:
            raise RuntimeError("The Unit of Work has no active transaction.")
        return self._connection

    def commit(self) -> None:
        transaction = self._require_active_transaction()
        connection = self._require_active_connection()
        try:
            transaction.commit()
        except BaseException:
            self._discard_uncertain_connection(connection, transaction)
            raise
        self._complete_and_close(connection)

    def rollback(self) -> None:
        transaction = self._require_active_transaction()
        connection = self._require_active_connection()
        try:
            transaction.rollback()
        except BaseException:
            self._discard_uncertain_connection(connection)
            raise
        self._complete_and_close(connection)

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None:
        del exc_value, traceback
        if self._transaction is not None:
            try:
                self.rollback()
            except BaseException:
                if exc_type is None:
                    raise
        return None

    def _require_active_transaction(self) -> Transaction:
        if self._connection is None or self._transaction is None:
            raise RuntimeError("The Unit of Work has no active transaction.")
        return self._transaction

    def _require_active_connection(self) -> Connection:
        if self._connection is None or self._transaction is None:
            raise RuntimeError("The Unit of Work has no active transaction.")
        return self._connection

    def _complete_and_close(self, connection: Connection) -> None:
        self._connection = None
        self._transaction = None
        try:
            connection.close()
        except BaseException:
            _best_effort_invalidate_and_close(connection)
            raise

    def _discard_uncertain_connection(
        self, connection: Connection, transaction: Transaction | None = None
    ) -> None:
        self._connection = None
        self._transaction = None
        if transaction is not None:
            try:
                transaction.rollback()
            except BaseException:
                pass
        _best_effort_invalidate_and_close(connection)


class SqlAlchemyReadOnlyScope:
    """Single-use query scope that always rolls back before closing."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine
        self._connection: Connection | None = None
        self._transaction: Transaction | None = None
        self._used = False

    def __enter__(self) -> "SqlAlchemyReadOnlyScope":
        if self._used:
            raise RuntimeError("SqlAlchemyReadOnlyScope instances are single-use.")
        self._used = True
        connection = self._engine.connect()
        try:
            transaction = connection.begin()
        except BaseException:
            connection.close()
            raise
        self._connection = connection
        self._transaction = transaction
        return self

    @property
    def adapter_connection(self) -> Connection:
        """Return the active connection to persistence adapter code only."""

        if self._connection is None or self._transaction is None:
            raise RuntimeError("The read-only scope is not active.")
        return self._connection

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None:
        del exc_value, traceback
        transaction = self._transaction
        connection = self._connection
        self._transaction = None
        self._connection = None
        if transaction is None or connection is None:
            return None
        try:
            transaction.rollback()
        except BaseException:
            _best_effort_invalidate_and_close(connection)
            if exc_type is None:
                raise
        else:
            try:
                connection.close()
            except BaseException:
                _best_effort_invalidate_and_close(connection)
                if exc_type is None:
                    raise
        return None


def _best_effort_invalidate_and_close(connection: Connection) -> None:
    """Discard a connection whose physical transaction state is uncertain."""

    try:
        connection.invalidate()
    except BaseException:
        pass
    try:
        connection.close()
    except BaseException:
        pass
