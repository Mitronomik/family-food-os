"""Run the existing API against a fresh, loopback-only browser test database."""

import os
import signal
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import UUID, uuid4

import uvicorn

from app.db.config import DATABASE_PATH_ENV, DatabaseConfig
from app.db.migrations import apply_migrations
from app.domain.units import UnitCode
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
from app.persistence.sqlalchemy_core.food_ingredient_composition import (
    create_food_catalogue_service,
)
from app.persistence.sqlalchemy_core.household_uow import (
    SqlAlchemyHouseholdReadScope,
    SqlAlchemyHouseholdUnitOfWork,
)
from app.services.food_ingredients import TrustedFoodIngredientIdentitySeed
from app.services.households import HouseholdService

HOUSEHOLD_ID = UUID("11111111-1111-4111-8111-111111111111")


def seed(config: DatabaseConfig) -> None:
    apply_migrations(config)
    engine = create_sqlite_engine(config)
    try:
        catalogue = create_food_catalogue_service(engine)
        catalogue.reconcile_identity_seed(
            TrustedFoodIngredientIdentitySeed(code, name, category, UnitCode.GRAM)
            for code, name, category in (
                ("TEST_CARROT", "Морковь", "vegetables"),
                ("TEST_BEEF", "Говядина", "meat"),
                ("TEST_BEET", "Свёкла", "vegetables"),
            )
        )
        carrot = catalogue.get_by_code("TEST_CARROT")
        beef = catalogue.get_by_code("TEST_BEEF")
        catalogue.add_alias(beef.id, alias="тестовый мясной продукт")

        synthetic_ids = iter((HOUSEHOLD_ID, uuid4(), uuid4()))
        households = HouseholdService(
            write_scope_factory=lambda: SqlAlchemyHouseholdUnitOfWork(engine),
            read_scope_factory=lambda: SqlAlchemyHouseholdReadScope(engine),
            id_factory=lambda: next(synthetic_ids),
        )
        households.create_household(name="Тестовая семья", timezone_name="Europe/Moscow")
        anna = households.add_household_member(
            HOUSEHOLD_ID, name="Анна", activity_level="moderate", goal="maintain"
        )
        households.add_household_member(
            HOUSEHOLD_ID, name="Борис", activity_level="moderate", goal="maintain"
        )
        households.replace_member_excluded_food_ids(
            HOUSEHOLD_ID, anna.id, expected=frozenset(), selected=frozenset({carrot.id})
        )
        catalogue.deactivate(carrot.id)
    finally:
        engine.dispose()


def main() -> None:
    # Uvicorn re-raises captured signals after shutdown. Let the context manager
    # finish removing the database when Playwright stops the server.
    signal.signal(signal.SIGTERM, lambda *_: None)
    with TemporaryDirectory(prefix="family-food-browser-") as directory:
        config = DatabaseConfig(path=Path(directory) / "synthetic.sqlite")
        os.environ[DATABASE_PATH_ENV] = str(config.path)
        os.environ["AI_ENABLED"] = "false"
        os.environ.pop("FAMILY_FOOD_BACKEND_LIVENESS_LOCK", None)
        seed(config)
        uvicorn.run("app.main:app", host="127.0.0.1", port=8000, access_log=False)


if __name__ == "__main__":
    main()
