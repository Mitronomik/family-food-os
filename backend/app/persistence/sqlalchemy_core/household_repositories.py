"""Focused SQLAlchemy Core repositories for the Household context."""

from collections.abc import Mapping
from typing import Any
from uuid import UUID

from sqlalchemy import insert, select, update
from sqlalchemy.engine import Connection
from sqlalchemy.exc import IntegrityError

from app.domain.households import Household, HouseholdMember
from app.persistence.sqlalchemy_core.household_tables import (
    household_members_table,
    households_table,
)
from app.services.household_contracts import (
    HouseholdPersistenceConflictError,
    HouseholdPersistenceError,
)


class SqlAlchemyHouseholdRepository:
    def __init__(self, connection: Connection) -> None:
        self._connection = connection

    def add_household(self, household: Household) -> None:
        try:
            self._connection.execute(
                insert(households_table).values(**_household_values(household))
            )
        except IntegrityError as exc:
            raise HouseholdPersistenceConflictError(
                "Household could not be created because its persisted identity conflicts."
            ) from exc

    def get_household(self, household_id: UUID) -> Household | None:
        row = (
            self._connection.execute(
                select(households_table).where(households_table.c.id == household_id)
            )
            .mappings()
            .one_or_none()
        )
        return None if row is None else _household_from_row(row)

    def update_household(self, household: Household) -> None:
        try:
            result = self._connection.execute(
                update(households_table)
                .where(households_table.c.id == household.id)
                .values(**_household_values(household, include_id=False))
            )
        except IntegrityError as exc:
            raise HouseholdPersistenceConflictError(
                "Household update conflicted with persisted state."
            ) from exc
        if result.rowcount != 1:
            raise HouseholdPersistenceError(
                "Household update did not affect exactly one persisted row."
            )


class SqlAlchemyHouseholdMemberRepository:
    def __init__(self, connection: Connection) -> None:
        self._connection = connection

    def add_member(self, member: HouseholdMember) -> None:
        try:
            self._connection.execute(
                insert(household_members_table).values(**_member_values(member))
            )
        except IntegrityError as exc:
            raise HouseholdPersistenceConflictError(
                "Household member could not be created because its identity or Household link conflicts."
            ) from exc

    def get_member(self, household_id: UUID, member_id: UUID) -> HouseholdMember | None:
        row = (
            self._connection.execute(
                select(household_members_table).where(
                    household_members_table.c.household_id == household_id,
                    household_members_table.c.id == member_id,
                )
            )
            .mappings()
            .one_or_none()
        )
        return None if row is None else _member_from_row(row)

    def list_members(self, household_id: UUID) -> list[HouseholdMember]:
        rows = self._connection.execute(
            select(household_members_table)
            .where(household_members_table.c.household_id == household_id)
            .order_by(
                household_members_table.c.created_at,
                household_members_table.c.id,
            )
        ).mappings()
        return [_member_from_row(row) for row in rows]

    def update_member(self, member: HouseholdMember) -> None:
        try:
            result = self._connection.execute(
                update(household_members_table)
                .where(
                    household_members_table.c.household_id == member.household_id,
                    household_members_table.c.id == member.id,
                )
                .values(**_member_values(member, include_identity=False))
            )
        except IntegrityError as exc:
            raise HouseholdPersistenceConflictError(
                "Household member update conflicted with persisted state."
            ) from exc
        if result.rowcount != 1:
            raise HouseholdPersistenceError(
                "Household member update did not affect exactly one household-scoped row."
            )


def _household_values(
    household: Household, *, include_id: bool = True
) -> dict[str, object]:
    values: dict[str, object] = {
        "name": household.name,
        "timezone": household.timezone,
        "city": household.city,
        "default_weekly_budget": household.default_weekly_budget,
        "default_cooking_profile": household.default_cooking_profile,
        "created_at": household.created_at,
        "updated_at": household.updated_at,
    }
    if include_id:
        values["id"] = household.id
    return values


def _member_values(
    member: HouseholdMember, *, include_identity: bool = True
) -> dict[str, object]:
    values: dict[str, object] = {
        "name": member.name,
        "active": member.active,
        "birth_date": member.birth_date,
        "sex": member.sex,
        "height_cm": member.height_cm,
        "weight_kg": member.weight_kg,
        "activity_level": member.activity_level,
        "goal": member.goal,
        "created_at": member.created_at,
        "updated_at": member.updated_at,
    }
    if include_identity:
        values["id"] = member.id
        values["household_id"] = member.household_id
    return values


def _household_from_row(row: Mapping[str, Any]) -> Household:
    return Household(
        id=row["id"],
        name=row["name"],
        timezone=row["timezone"],
        city=row["city"],
        default_weekly_budget=row["default_weekly_budget"],
        default_cooking_profile=row["default_cooking_profile"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _member_from_row(row: Mapping[str, Any]) -> HouseholdMember:
    return HouseholdMember(
        id=row["id"],
        household_id=row["household_id"],
        name=row["name"],
        active=row["active"],
        birth_date=row["birth_date"],
        sex=row["sex"],
        height_cm=row["height_cm"],
        weight_kg=row["weight_kg"],
        activity_level=row["activity_level"],
        goal=row["goal"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )
