from importlib import import_module
import sqlite3

from app.db.config import DatabaseConfig
from app.db.connection import session

MIGRATION_MODULES = [
    "app.migrations.versions.0001_infrastructure",
    "app.migrations.versions.0002_ingredients",
    "app.migrations.versions.0003_ingredient_lots",
    "app.migrations.versions.0004_stock_movements",
    "app.migrations.versions.0005_packaging_items",
    "app.migrations.versions.0006_packaging_stock_movements",
    "app.migrations.versions.0007_recipes",
    "app.migrations.versions.0008_clients",
    "app.migrations.versions.0009_client_recipes",
    "app.migrations.versions.0010_catalog",
    "app.migrations.versions.0011_client_wishes_feedback",
    "app.migrations.versions.0012_orders",
    "app.migrations.versions.0013_production_batches",
    "app.migrations.versions.0014_alerts",
    "app.migrations.versions.0015_purchase_suggestions",
    "app.migrations.versions.0016_import_drafts",
    "app.migrations.versions.0017_import_apply_status",
    "app.migrations.versions.0018_demo_data_tracking",
    "app.migrations.versions.0019_production_batch_tax_rate_snapshots",
    "app.migrations.versions.0020_artifact_audit_operations",
    "app.migrations.versions.0021_family_food_identity",
    "app.migrations.versions.0022_household_foundation",
    "app.migrations.versions.0023_food_ingredient_catalogue",
    "app.migrations.versions.0024_food_recipe_catalogue",
    "app.migrations.versions.0025_pantry",
    "app.migrations.versions.0026_nutrition_measure_evidence",
    "app.migrations.versions.0027_recipe_same_source_revisions",
    "app.migrations.versions.0028_normalized_nutrient_vector",
]
MIGRATION_TABLE = "schema_migrations"


class MigrationRunnerError(RuntimeError):
    """The migration connection or capability violates the runner contract."""


class MigrationForeignKeyValidationError(MigrationRunnerError):
    def __init__(self, migration_id, violations):
        self.migration_id = migration_id
        # SQLite columns: child table, child rowid, parent table, FK index.
        self.violations = tuple(tuple(row) for row in violations)
        super().__init__(
            f"Migration {migration_id}: foreign_key_check failed: {self.violations!r}"
        )


def _insert_migration_marker(connection, migration_id):
    connection.execute(
        f"INSERT INTO {MIGRATION_TABLE} (migration_id) VALUES (?)",
        (migration_id,),
    )


def _rebuild_authorizer(action, first, second, database, trigger):
    # Rebuild modules use execute/executemany, never transaction control or
    # executescript (whose implicit COMMIT would break schema/marker atomicity).
    if action in (sqlite3.SQLITE_TRANSACTION, sqlite3.SQLITE_SAVEPOINT):
        return sqlite3.SQLITE_DENY
    if (
        action == sqlite3.SQLITE_PRAGMA
        and first.lower() == "foreign_keys"
        and second is not None
    ):
        return sqlite3.SQLITE_DENY
    if (
        action in (sqlite3.SQLITE_INSERT, sqlite3.SQLITE_UPDATE, sqlite3.SQLITE_DELETE)
        and first == MIGRATION_TABLE
    ):
        return sqlite3.SQLITE_DENY
    return sqlite3.SQLITE_OK


def _apply_foreign_key_rebuild(connection, migration):
    """Own one opt-in rebuild and marker; earlier migrations form a durable prefix."""
    if connection.in_transaction:
        connection.commit()
    committed = False
    try:
        if connection.execute("PRAGMA foreign_keys").fetchone()[0] != 1:
            raise MigrationRunnerError("Rebuild requires initial foreign_keys=ON.")
        connection.execute("PRAGMA foreign_keys=OFF")
        if connection.execute("PRAGMA foreign_keys").fetchone()[0] != 0:
            raise MigrationRunnerError("Could not disable foreign keys before rebuild.")
        connection.execute("BEGIN")
        connection.set_authorizer(_rebuild_authorizer)
        try:
            migration.upgrade(connection)
        finally:
            connection.set_authorizer(None)
        _insert_migration_marker(connection, migration.MIGRATION_ID)
        violations = connection.execute("PRAGMA foreign_key_check").fetchall()
        if violations:
            raise MigrationForeignKeyValidationError(migration.MIGRATION_ID, violations)
        connection.commit()
        committed = True
    except BaseException:
        connection.rollback()
        raise
    finally:
        # session() disposes this dedicated connection even if restoration fails.
        # A restoration failure after commit cannot undo the valid migration.
        try:
            connection.execute("PRAGMA foreign_keys=ON")
            if connection.execute("PRAGMA foreign_keys").fetchone()[0] != 1:
                raise MigrationRunnerError("foreign_keys readback is not ON")
        except Exception as error:
            raise MigrationRunnerError(
                f"Migration {migration.MIGRATION_ID}: FK restoration failed; "
                f"rebuild committed={committed}. Connection must be disposed."
            ) from error


def _ensure_migration_table(connection) -> None:
    connection.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {MIGRATION_TABLE} (
            migration_id TEXT PRIMARY KEY,
            applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )


def applied_migration_ids(connection) -> set[str]:
    _ensure_migration_table(connection)
    rows = connection.execute(f"SELECT migration_id FROM {MIGRATION_TABLE}").fetchall()
    return {row["migration_id"] for row in rows}


def pending_migration_ids(config: DatabaseConfig | None = None) -> list[str]:
    expected = expected_migration_ids()
    if config is not None and not config.path.exists():
        return expected
    if config is None:
        from app.db.config import get_database_config

        resolved_config = get_database_config()
        if not resolved_config.path.exists():
            return expected
        config = resolved_config
    with session(config) as connection:
        table_exists = connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
            (MIGRATION_TABLE,),
        ).fetchone()
        if table_exists is None:
            return expected
        existing = applied_migration_ids(connection)
    return [migration_id for migration_id in expected if migration_id not in existing]


def apply_migrations(config: DatabaseConfig | None = None) -> list[str]:
    applied: list[str] = []
    with session(config) as connection:
        _ensure_migration_table(connection)
        existing = applied_migration_ids(connection)
        for module_name in MIGRATION_MODULES:
            migration = import_module(module_name)
            migration_id = migration.MIGRATION_ID
            mode = getattr(migration, "SQLITE_MIGRATION_MODE", "standard")
            if mode not in ("standard", "foreign_key_rebuild"):
                raise MigrationRunnerError(
                    f"Migration {migration_id}: unknown SQLite migration mode {mode!r}."
                )
            if migration_id in existing:
                continue
            if mode == "foreign_key_rebuild":
                _apply_foreign_key_rebuild(connection, migration)
            else:
                migration.upgrade(connection)
                _insert_migration_marker(connection, migration_id)
            applied.append(migration_id)
    return applied


def current_migrations(config: DatabaseConfig | None = None) -> set[str]:
    with session(config) as connection:
        return applied_migration_ids(connection)


def expected_migration_ids() -> list[str]:
    return [
        import_module(module_name).MIGRATION_ID for module_name in MIGRATION_MODULES
    ]
