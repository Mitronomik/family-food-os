import sqlite3

import pytest
from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
    event,
    func,
    select,
)
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.exc import IntegrityError, ResourceClosedError

from app.db.config import DatabaseConfig
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
from app.persistence.sqlalchemy_core.uow import (
    SqlAlchemyReadOnlyScope,
    SqlAlchemyUnitOfWork,
)


metadata = MetaData()
probe_table = Table(
    "pr2b_transaction_probe",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("source", String, nullable=False),
)
deferred_parent_table = Table(
    "pr2b_deferred_parent_probe",
    metadata,
    Column("id", Integer, primary_key=True),
)
deferred_child_table = Table(
    "pr2b_deferred_child_probe",
    metadata,
    Column("id", Integer, primary_key=True),
    Column(
        "parent_id",
        Integer,
        ForeignKey(
            deferred_parent_table.c.id,
            deferrable=True,
            initially="DEFERRED",
        ),
        nullable=False,
    ),
)


class ProbeRepository:
    def __init__(self, connection: Connection) -> None:
        self.connection = connection

    def add(self, source: str) -> None:
        self.connection.execute(probe_table.insert().values(source=source))

    def sources(self) -> list[str]:
        return list(
            self.connection.execute(
                select(probe_table.c.source).order_by(probe_table.c.id)
            ).scalars()
        )


@pytest.fixture
def engine(tmp_path):
    value = create_sqlite_engine(DatabaseConfig(path=tmp_path / "uow.sqlite"))
    with value.begin() as connection:
        probe_table.create(connection)
        deferred_parent_table.create(connection)
        deferred_child_table.create(connection)
    try:
        yield value
    finally:
        value.dispose()


def independently_persisted_sources(engine: Engine) -> list[str]:
    with sqlite3.connect(engine.url.database) as connection:
        return [
            row[0]
            for row in connection.execute(
                "SELECT source FROM pr2b_transaction_probe ORDER BY id"
            ).fetchall()
        ]


def independent_count(engine: Engine, table_name: str) -> int:
    with sqlite3.connect(engine.url.database) as connection:
        return connection.execute(f"SELECT count(*) FROM {table_name}").fetchone()[0]


def test_multiple_repositories_share_one_connection_and_commit_atomically(engine):
    with SqlAlchemyUnitOfWork(engine) as uow:
        first = ProbeRepository(uow.adapter_connection)
        second = ProbeRepository(uow.adapter_connection)

        assert first.connection is second.connection
        first.add("first")
        second.add("second")
        uow.commit()

    assert independently_persisted_sources(engine) == ["first", "second"]


def test_participating_read_sees_uncommitted_state_on_same_transaction(engine):
    with SqlAlchemyUnitOfWork(engine) as uow:
        writer = ProbeRepository(uow.adapter_connection)
        reader = ProbeRepository(uow.adapter_connection)

        writer.add("visible-inside-command")

        assert reader.sources() == ["visible-inside-command"]
        uow.commit()


def test_exception_rolls_back_every_participating_repository(engine):
    retained_connection = None
    with pytest.raises(RuntimeError, match="simulated command failure"):
        with SqlAlchemyUnitOfWork(engine) as uow:
            retained_connection = uow.adapter_connection
            ProbeRepository(uow.adapter_connection).add("first")
            ProbeRepository(uow.adapter_connection).add("second")
            raise RuntimeError("simulated command failure")

    assert retained_connection is not None
    assert retained_connection.closed
    assert independently_persisted_sources(engine) == []


def test_normal_exit_without_commit_rolls_back(engine):
    with SqlAlchemyUnitOfWork(engine) as uow:
        retained_connection = uow.adapter_connection
        ProbeRepository(uow.adapter_connection).add("not-committed")

    assert retained_connection.closed
    assert independently_persisted_sources(engine) == []


def test_explicit_rollback_discards_writes_and_revokes_retained_connection(engine):
    with SqlAlchemyUnitOfWork(engine) as uow:
        retained_connection = uow.adapter_connection
        ProbeRepository(retained_connection).add("rolled-back")
        uow.rollback()
        assert retained_connection.closed
        with pytest.raises(ResourceClosedError):
            retained_connection.execute(
                probe_table.insert().values(source="post-rollback")
            )

    assert independently_persisted_sources(engine) == []


def test_commit_revokes_retained_connection_and_prevents_autobegin(engine):
    with SqlAlchemyUnitOfWork(engine) as uow:
        retained_connection = uow.adapter_connection
        ProbeRepository(retained_connection).add("committed")
        uow.commit()
        assert retained_connection.closed
        with pytest.raises(ResourceClosedError):
            retained_connection.execute(probe_table.insert().values(source="post-commit"))

    assert independently_persisted_sources(engine) == ["committed"]


def test_commit_while_inactive_and_double_commit_fail_clearly(engine):
    inactive = SqlAlchemyUnitOfWork(engine)
    with pytest.raises(RuntimeError, match="no active transaction"):
        inactive.commit()

    with SqlAlchemyUnitOfWork(engine) as uow:
        uow.commit()
        with pytest.raises(RuntimeError, match="no active transaction"):
            uow.commit()
        with pytest.raises(RuntimeError, match="no active transaction"):
            uow.rollback()
        with pytest.raises(RuntimeError, match="no active transaction"):
            _ = uow.adapter_connection

    with SqlAlchemyUnitOfWork(engine) as rolled_back:
        rolled_back.rollback()
        with pytest.raises(RuntimeError, match="no active transaction"):
            rolled_back.commit()


def test_completed_unit_of_work_cannot_be_reused(engine):
    uow = SqlAlchemyUnitOfWork(engine)
    with uow:
        uow.commit()

    with pytest.raises(RuntimeError, match="single-use"):
        with uow:
            pass


def test_read_only_scope_reads_with_one_connection_and_has_no_commit(engine):
    with SqlAlchemyUnitOfWork(engine) as uow:
        ProbeRepository(uow.adapter_connection).add("persisted")
        uow.commit()

    with SqlAlchemyReadOnlyScope(engine) as scope:
        repository = ProbeRepository(scope.adapter_connection)
        assert repository.connection is scope.adapter_connection
        assert repository.sources() == ["persisted"]
        assert not hasattr(scope, "commit")


def test_read_only_scope_rolls_back_accidental_write(engine):
    with SqlAlchemyReadOnlyScope(engine) as scope:
        ProbeRepository(scope.adapter_connection).add("accidental")

    assert independently_persisted_sources(engine) == []


def test_read_only_scope_rolls_back_and_closes_on_exception(engine):
    retained_connection = None

    with pytest.raises(RuntimeError, match="query failure"):
        with SqlAlchemyReadOnlyScope(engine) as scope:
            retained_connection = scope.adapter_connection
            ProbeRepository(retained_connection).add("accidental")
            raise RuntimeError("query failure")

    assert retained_connection is not None
    assert retained_connection.closed
    assert independently_persisted_sources(engine) == []


def test_failed_deferred_commit_cannot_contaminate_a_later_uow(engine):
    with pytest.raises(IntegrityError):
        with SqlAlchemyUnitOfWork(engine) as failed_uow:
            failed_uow.adapter_connection.execute(
                deferred_child_table.insert().values(id=1, parent_id=999)
            )
            failed_uow.commit()

    assert independent_count(engine, deferred_child_table.name) == 0

    with SqlAlchemyUnitOfWork(engine) as later_uow:
        later_uow.adapter_connection.execute(
            deferred_parent_table.insert().values(id=999)
        )
        later_uow.commit()

    assert independent_count(engine, deferred_parent_table.name) == 1
    assert independent_count(engine, deferred_child_table.name) == 0


def test_rollback_failure_discards_connection_and_preserves_failure(engine):
    retained_connection = None

    def fail_rollback(connection):
        del connection
        raise RuntimeError("simulated rollback failure")

    event.listen(engine, "rollback", fail_rollback, once=True)
    with pytest.raises(RuntimeError, match="simulated rollback failure"):
        with SqlAlchemyUnitOfWork(engine) as uow:
            retained_connection = uow.adapter_connection
            ProbeRepository(retained_connection).add("uncertain")
            uow.rollback()

    assert retained_connection is not None
    assert retained_connection.closed
    assert independently_persisted_sources(engine) == []

    with SqlAlchemyUnitOfWork(engine) as later_uow:
        ProbeRepository(later_uow.adapter_connection).add("later")
        later_uow.commit()
    assert independently_persisted_sources(engine) == ["later"]


def test_probe_fixture_is_scoped_to_one_test_database(engine):
    with engine.connect() as connection:
        assert connection.scalar(select(func.count()).select_from(probe_table)) == 0
