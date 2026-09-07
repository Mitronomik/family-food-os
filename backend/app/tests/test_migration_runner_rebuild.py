"""Real SQLite contract tests; synthetic modules never enter production lineage."""

from importlib import import_module
import sqlite3
from types import SimpleNamespace

import pytest

from app.db import connection as connections
from app.db import migrations
from app.db.config import DatabaseConfig
from app.db.migrations import (
    MigrationForeignKeyValidationError,
    MigrationRunnerError,
    apply_migrations,
    current_migrations,
    expected_migration_ids,
)
from app.seed.food_recipes import seed_food_recipes
from app.seed.nutrition_measure_evidence import seed_nutrition_measure_evidence

HEAD = "0026_nutrition_measure_evidence"
REBUILD = "synthetic_rebuild"


class ObservedConnection(sqlite3.Connection):
    """Observe actual transaction/FK state; inject only the requested SQL fault."""

    fault = None
    events = None
    closed_fk = None

    def execute(self, sql, parameters=()):
        state = super().execute("PRAGMA foreign_keys").fetchone()[0]
        self.events.append((sql, self.in_transaction, state))
        if self.fault == "disable" and sql == "PRAGMA foreign_keys=OFF":
            return super().execute("SELECT 1")
        if self.fault == "restore" and sql == "PRAGMA foreign_keys=ON" and state == 0:
            return super().execute("SELECT 1")
        if self.fault == "check" and sql == "PRAGMA foreign_key_check":
            raise sqlite3.OperationalError("injected FK check failure")
        if self.fault == "marker" and sql.startswith("INSERT INTO schema_migrations"):
            if parameters == (REBUILD,):
                raise sqlite3.IntegrityError("injected marker failure")
        return super().execute(sql, parameters)

    def commit(self):
        self.events.append(("COMMIT", self.in_transaction, None))
        return super().commit()

    def rollback(self):
        self.events.append(("ROLLBACK", self.in_transaction, None))
        return super().rollback()

    def close(self):
        self.closed_fk = super().execute("PRAGMA foreign_keys").fetchone()[0]
        super().close()


@pytest.fixture
def observed(monkeypatch):
    opened = []

    def connect(config):
        db = sqlite3.connect(config.path, factory=ObservedConnection)
        db.events = []
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        opened.append(db)
        return db

    monkeypatch.setattr(connections, "connect", connect)
    return opened


def install(monkeypatch, *modules, prefix=()):
    by_name = {module.MIGRATION_ID: module for module in modules}
    monkeypatch.setattr(migrations, "MIGRATION_MODULES", list(prefix) + list(by_name))
    monkeypatch.setattr(
        migrations,
        "import_module",
        lambda name: by_name[name] if name in by_name else import_module(name),
    )


def module(name, upgrade, mode="foreign_key_rebuild"):
    result = SimpleNamespace(MIGRATION_ID=name, upgrade=upgrade)
    if mode is not None:
        result.SQLITE_MIGRATION_MODE = mode
    return result


def standard(db):
    assert db.execute("PRAGMA foreign_keys").fetchone()[0] == 1
    db.execute("CREATE TABLE parent (id INTEGER PRIMARY KEY, label TEXT UNIQUE)")
    db.execute(
        "CREATE TABLE child (id INTEGER PRIMARY KEY, parent_id INTEGER REFERENCES parent(id) ON DELETE RESTRICT)"
    )
    db.execute("INSERT INTO parent VALUES (7, 'preserved')")
    db.execute("INSERT INTO child VALUES (9, 7)")
    assert db.in_transaction  # Real implicit DBAPI transaction left to the runner.


def rebuild(db):
    assert db.in_transaction
    assert db.execute("PRAGMA foreign_keys").fetchone()[0] == 0
    db.execute("CREATE TABLE replacement (id INTEGER PRIMARY KEY, label TEXT)")
    db.execute("INSERT INTO replacement SELECT * FROM parent")
    db.execute("DROP TABLE parent")
    db.execute("ALTER TABLE replacement RENAME TO parent")
    db.execute("CREATE INDEX parent_label ON parent(label)")


def dump(config, *, omit_marker=None):
    with sqlite3.connect(config.path) as db:
        return tuple(
            line
            for line in db.iterdump()
            if omit_marker is None
            or not (
                line.startswith('INSERT INTO "schema_migrations"')
                and f"'{omit_marker}'" in line
            )
        )


def assert_valid(config):
    with connections.session(config) as db:
        assert db.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        assert db.execute("PRAGMA foreign_key_check").fetchall() == []


@pytest.mark.parametrize("mode", [None, "standard"])
def test_standard_rebuild_standard_boundary_success(
    tmp_path, monkeypatch, observed, mode
):
    config = DatabaseConfig(path=tmp_path / "boundary.sqlite")

    def following(db):
        assert db.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        db.execute("INSERT INTO parent VALUES (8, 'preserved')")

    install(
        monkeypatch,
        module("prior", standard, mode),
        module(REBUILD, rebuild),
        module("following", following, "standard"),
    )
    assert apply_migrations(config) == ["prior", REBUILD, "following"]
    events = observed[0].events
    toggle = events.index(("PRAGMA foreign_keys=OFF", False, 1))
    assert events[toggle - 2] == ("COMMIT", True, None)
    assert ("BEGIN", False, 0) in events
    marker = next(
        i
        for i, event in enumerate(events[toggle:], toggle)
        if event[0].startswith("INSERT INTO schema_migrations")
    )
    check = events.index(("PRAGMA foreign_key_check", True, 0))
    commit = events.index(("COMMIT", True, None), toggle)
    assert marker < check < commit
    assert ("PRAGMA foreign_keys=ON", False, 0) in events[commit:]
    assert observed[0].closed_fk == 1
    assert apply_migrations(config) == []
    with sqlite3.connect(config.path) as db:
        assert db.execute("SELECT * FROM parent ORDER BY id").fetchall() == [
            (7, "preserved"),
            (8, "preserved"),
        ]
        assert db.execute("SELECT * FROM child").fetchall() == [(9, 7)]
    assert_valid(config)


@pytest.mark.parametrize("failure", ["upgrade", "violation", "check", "marker"])
def test_rebuild_failures_roll_back_schema_data_marker_and_restore_fk(
    tmp_path, monkeypatch, observed, failure
):
    config = DatabaseConfig(path=tmp_path / "rollback.sqlite")
    prior = module("prior", standard, None)
    install(monkeypatch, prior)
    apply_migrations(config)
    before = dump(config)

    def failing(db):
        rebuild(db)
        if failure == "upgrade":
            raise ValueError("injected upgrade failure")
        if failure == "violation":
            db.execute("UPDATE child SET parent_id=404")
        db.fault = failure

    install(monkeypatch, prior, module(REBUILD, failing))
    error = (
        MigrationForeignKeyValidationError
        if failure == "violation"
        else (ValueError if failure == "upgrade" else sqlite3.Error)
    )
    with pytest.raises(error) as raised:
        apply_migrations(config)
    if failure == "violation":
        assert raised.value.violations == (("child", 9, "parent", 0),)
        assert raised.value.migration_id == REBUILD
    assert observed[-1].closed_fk == 1
    assert ("ROLLBACK", True, None) in observed[-1].events
    assert dump(config) == before
    assert current_migrations(config) == {"prior"}
    assert_valid(config)


@pytest.mark.parametrize("fault", ["initial", "disable", "restore"])
def test_fk_setting_failures_are_loud_and_connection_disposed(
    tmp_path, monkeypatch, observed, fault
):
    config = DatabaseConfig(path=tmp_path / "setting.sqlite")
    ran = []

    def setup(db):
        standard(db)
        db.fault = fault
        if fault == "initial":
            db.commit()
            db.execute("PRAGMA foreign_keys=OFF")

    def special(db):
        ran.append(True)
        rebuild(db)

    install(monkeypatch, module("prior", setup, None), module(REBUILD, special))
    with pytest.raises(MigrationRunnerError) as raised:
        apply_migrations(config)
    if fault == "restore":
        assert "committed=True" in str(raised.value)
        assert ran == [True]
        assert observed[0].closed_fk == 0
        assert current_migrations(config) == {"prior", REBUILD}
    else:
        assert ran == []
        assert observed[0].closed_fk == 1
        assert current_migrations(config) == {"prior"}
    with pytest.raises(sqlite3.ProgrammingError):
        observed[0].execute("SELECT 1")
    assert_valid(config)  # A new connection always enables enforcement.


def test_fresh_accepted_chain_failure_and_resume(tmp_path, monkeypatch, observed):
    config = DatabaseConfig(path=tmp_path / "fresh-resume.sqlite")
    prefix = list(migrations.MIGRATION_MODULES)
    accepted = expected_migration_ids()
    assert len(accepted) == 26 and accepted[-1] == HEAD

    def fail(db):
        assert db.in_transaction
        db.execute("CREATE TABLE synthetic_added (id INTEGER PRIMARY KEY)")
        raise ValueError("stop after schema change")

    special = module(REBUILD, fail)
    install(monkeypatch, special, prefix=prefix)
    with pytest.raises(ValueError, match="stop after schema change"):
        apply_migrations(config)
    assert observed[0].closed_fk == 1
    assert current_migrations(config) == set(accepted)
    before = dump(config)
    assert not any("synthetic_added" in line for line in before)

    def fixed(db):
        assert db.in_transaction
        assert db.execute("PRAGMA foreign_keys").fetchone()[0] == 0

    special.upgrade = fixed
    assert apply_migrations(config) == [REBUILD]
    assert dump(config, omit_marker=REBUILD) == before
    after = dump(config)
    assert apply_migrations(config) == []
    assert dump(config) == after
    assert_valid(config)


def test_populated_accepted_catalogue_is_preserved(tmp_path, monkeypatch, observed):
    config = DatabaseConfig(path=tmp_path / "populated.sqlite")
    seed_food_recipes(config)
    seed_nutrition_measure_evidence(config)
    with sqlite3.connect(config.path) as db:
        for table, count in {
            "food_recipe_versions": 30,
            "food_recipe_ingredients": 189,
            "nutrition_measure_evidence": 57,
            "recipe_ingredient_nutrition_assessments": 189,
            "recipe_ingredient_nutrition_assessment_issues": 123,
        }.items():
            assert db.execute(f'SELECT count(*) FROM "{table}"').fetchone()[0] == count
        assert db.execute(
            "SELECT DISTINCT version_number FROM food_recipe_versions"
        ).fetchall() == [(1,)]
    before = dump(config)

    def noop(db):
        assert db.in_transaction
        assert db.execute("PRAGMA foreign_keys").fetchone()[0] == 0

    install(monkeypatch, module(REBUILD, noop), prefix=migrations.MIGRATION_MODULES)
    assert apply_migrations(config) == [REBUILD]
    assert observed[-1].closed_fk == 1
    assert dump(config, omit_marker=REBUILD) == before
    assert apply_migrations(config) == []
    assert_valid(config)


@pytest.mark.parametrize("mode", ["unknown", "", 1, None, []])
def test_unknown_mode_fails_before_upgrade(tmp_path, monkeypatch, mode):
    special = module(REBUILD, lambda db: pytest.fail("must not run"))
    special.SQLITE_MIGRATION_MODE = mode
    install(monkeypatch, special)
    config = DatabaseConfig(path=tmp_path / "unknown.sqlite")
    with pytest.raises(MigrationRunnerError, match="unknown SQLite migration mode"):
        apply_migrations(config)
    assert current_migrations(config) == set()


@pytest.mark.parametrize(
    "action",
    [
        lambda db: db.commit(),
        lambda db: db.rollback(),
        lambda db: db.executescript("CREATE TABLE escaped (id INTEGER)"),
        lambda db: db.execute("SAVEPOINT escaped"),
        lambda db: db.execute("PRAGMA foreign_keys=ON"),
        lambda db: db.execute("DELETE FROM schema_migrations"),
    ],
)
def test_rebuild_module_cannot_take_transaction_or_marker_ownership(
    tmp_path, monkeypatch, observed, action
):
    config = DatabaseConfig(path=tmp_path / "ownership.sqlite")
    prior = module("prior", standard, None)
    install(monkeypatch, prior)
    apply_migrations(config)
    before = dump(config)

    def forbidden(db):
        rebuild(db)
        action(db)

    install(monkeypatch, prior, module(REBUILD, forbidden))
    with pytest.raises(sqlite3.DatabaseError, match="not authorized"):
        apply_migrations(config)
    assert observed[-1].closed_fk == 1
    assert dump(config) == before
    assert_valid(config)
