"""Infrastructure composition for Household application operations."""

from sqlalchemy.engine import Engine

from app.persistence.sqlalchemy_core.household_uow import (
    SqlAlchemyHouseholdReadScope,
    SqlAlchemyHouseholdUnitOfWork,
)
from app.services.households import HouseholdService


def create_household_service(engine: Engine) -> HouseholdService:
    return HouseholdService(
        write_scope_factory=lambda: SqlAlchemyHouseholdUnitOfWork(engine),
        read_scope_factory=lambda: SqlAlchemyHouseholdReadScope(engine),
    )
