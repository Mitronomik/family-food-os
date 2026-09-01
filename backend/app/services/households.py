"""Application operations for the Household bounded context."""

from collections.abc import Callable, Mapping
from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from app.domain.households import (
    Household,
    HouseholdMember,
    HouseholdState,
    update_household,
    update_household_member,
)
from app.services.household_contracts import HouseholdReadScope, HouseholdUnitOfWork

WriteScopeFactory = Callable[[], HouseholdUnitOfWork]
ReadScopeFactory = Callable[[], HouseholdReadScope]
IdFactory = Callable[[], UUID]
Clock = Callable[[], datetime]


class HouseholdNotFoundError(LookupError):
    pass


class HouseholdMemberNotFoundError(LookupError):
    pass


class HouseholdUpdateRequiredError(ValueError):
    pass


class HouseholdService:
    """Coordinates Household repositories without seeing adapter connections."""

    def __init__(
        self,
        write_scope_factory: WriteScopeFactory,
        read_scope_factory: ReadScopeFactory,
        *,
        id_factory: IdFactory = uuid4,
        clock: Clock | None = None,
    ) -> None:
        self._write_scope_factory = write_scope_factory
        self._read_scope_factory = read_scope_factory
        self._id_factory = id_factory
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def create_household(
        self,
        *,
        name: str,
        timezone_name: str,
        city: str | None = None,
        default_weekly_budget: Decimal | int | str | None = None,
        default_cooking_profile: str | None = None,
    ) -> Household:
        now = self._clock()
        household = Household(
            id=self._id_factory(),
            name=name,
            timezone=timezone_name,
            city=city,
            default_weekly_budget=default_weekly_budget,  # type: ignore[arg-type]
            default_cooking_profile=default_cooking_profile,
            created_at=now,
            updated_at=now,
        )
        with self._write_scope_factory() as scope:
            scope.households.add_household(household)
            scope.commit()
        return household

    def get_household(self, household_id: UUID) -> HouseholdState:
        with self._read_scope_factory() as scope:
            household = scope.households.get_household(household_id)
            if household is None:
                raise HouseholdNotFoundError(household_id)
            members = scope.members.list_members(household_id)
            return HouseholdState(household=household, members=tuple(members))

    def update_household(
        self, household_id: UUID, changes: Mapping[str, object]
    ) -> Household:
        if not changes:
            raise HouseholdUpdateRequiredError(
                "At least one supported Household field must be supplied."
            )
        with self._write_scope_factory() as scope:
            household = scope.households.get_household(household_id)
            if household is None:
                raise HouseholdNotFoundError(household_id)
            updated = update_household(
                household,
                changes,
                updated_at=self._clock(),
            )
            scope.households.update_household(updated)
            scope.commit()
        return updated

    def add_household_member(
        self,
        household_id: UUID,
        *,
        name: str,
        activity_level: str,
        goal: str,
        active: bool = True,
        birth_date: date | None = None,
        sex: str | None = None,
        height_cm: Decimal | int | str | None = None,
        weight_kg: Decimal | int | str | None = None,
    ) -> HouseholdMember:
        now = self._clock()
        member = HouseholdMember(
            id=self._id_factory(),
            household_id=household_id,
            name=name,
            active=active,
            birth_date=birth_date,
            sex=sex,
            height_cm=height_cm,  # type: ignore[arg-type]
            weight_kg=weight_kg,  # type: ignore[arg-type]
            activity_level=activity_level,
            goal=goal,
            created_at=now,
            updated_at=now,
        )
        with self._write_scope_factory() as scope:
            if scope.households.get_household(household_id) is None:
                raise HouseholdNotFoundError(household_id)
            scope.members.add_member(member)
            scope.commit()
        return member

    def list_household_members(self, household_id: UUID) -> list[HouseholdMember]:
        with self._read_scope_factory() as scope:
            if scope.households.get_household(household_id) is None:
                raise HouseholdNotFoundError(household_id)
            return scope.members.list_members(household_id)

    def update_household_member(
        self,
        household_id: UUID,
        member_id: UUID,
        changes: Mapping[str, object],
    ) -> HouseholdMember:
        if not changes:
            raise HouseholdUpdateRequiredError(
                "At least one supported HouseholdMember field must be supplied."
            )
        with self._write_scope_factory() as scope:
            if scope.households.get_household(household_id) is None:
                raise HouseholdNotFoundError(household_id)
            member = scope.members.get_member(household_id, member_id)
            if member is None:
                raise HouseholdMemberNotFoundError(member_id)
            updated = update_household_member(
                member,
                changes,
                updated_at=self._clock(),
            )
            scope.members.update_member(updated)
            scope.commit()
        return updated
