"""SQLAlchemy Core repository for Step 6A member selections."""

from collections.abc import Mapping
from typing import Any
from uuid import UUID

from sqlalchemy import insert, select
from sqlalchemy.engine import Connection
from sqlalchemy.exc import DBAPIError, IntegrityError

from app.domain.reference_methodology import MemberReferenceMethodologySelection
from app.persistence.sqlalchemy_core.household_tables import household_members_table
from app.persistence.sqlalchemy_core.reference_methodology_tables import (
    member_reference_methodology_selections_table,
)
from app.services.reference_methodology_contracts import (
    ReferenceMethodologyPersistenceConflictError,
    ReferenceMethodologyPersistenceError,
)


class SqlAlchemyMemberReferenceMethodologySelectionRepository:
    def __init__(self, connection: Connection) -> None:
        self._connection = connection

    def add(self, selection: MemberReferenceMethodologySelection) -> None:
        owner = self._connection.scalar(
            select(household_members_table.c.household_id).where(
                household_members_table.c.id == selection.member_id
            )
        )
        if owner != selection.household_id:
            raise ReferenceMethodologyPersistenceConflictError(
                "Reference-methodology member must belong to the selection Household."
            )
        if selection.version_number == 1:
            if selection.supersedes_selection_id is not None:
                raise ReferenceMethodologyPersistenceConflictError(
                    "Selection version 1 must not supersede another selection."
                )
        elif selection.supersedes_selection_id is None:
            raise ReferenceMethodologyPersistenceConflictError(
                "Selection revisions after version 1 require the previous selection."
            )
        if selection.supersedes_selection_id is not None:
            previous = (
                self._connection.execute(
                    select(member_reference_methodology_selections_table).where(
                        member_reference_methodology_selections_table.c.id
                        == selection.supersedes_selection_id
                    )
                )
                .mappings()
                .one_or_none()
            )
            if (
                previous is None
                or previous["household_id"] != selection.household_id
                or previous["member_id"] != selection.member_id
                or previous["version_number"] != selection.version_number - 1
            ):
                raise ReferenceMethodologyPersistenceConflictError(
                    "supersedes_selection_id must reference the immediately previous selection."
                )
        try:
            self._connection.execute(
                insert(member_reference_methodology_selections_table).values(
                    **_values(selection)
                )
            )
        except IntegrityError as exc:
            raise ReferenceMethodologyPersistenceConflictError(
                "Reference-methodology identity, request, version, or link conflicts."
            ) from exc
        except DBAPIError as exc:
            raise ReferenceMethodologyPersistenceError(
                "Reference-methodology persistence failed."
            ) from exc

    def get(
        self, household_id: UUID, selection_id: UUID
    ) -> MemberReferenceMethodologySelection | None:
        row = (
            self._connection.execute(
                select(member_reference_methodology_selections_table).where(
                    member_reference_methodology_selections_table.c.household_id
                    == household_id,
                    member_reference_methodology_selections_table.c.id
                    == selection_id,
                )
            )
            .mappings()
            .one_or_none()
        )
        return None if row is None else _from_row(row)

    def get_by_request_id(
        self,
        household_id: UUID,
        member_id: UUID,
        acceptance_request_id: UUID,
    ) -> MemberReferenceMethodologySelection | None:
        row = (
            self._connection.execute(
                select(member_reference_methodology_selections_table).where(
                    member_reference_methodology_selections_table.c.household_id
                    == household_id,
                    member_reference_methodology_selections_table.c.member_id
                    == member_id,
                    member_reference_methodology_selections_table.c.acceptance_request_id
                    == acceptance_request_id,
                )
            )
            .mappings()
            .one_or_none()
        )
        return None if row is None else _from_row(row)

    def get_current(
        self, household_id: UUID, member_id: UUID
    ) -> MemberReferenceMethodologySelection | None:
        row = (
            self._connection.execute(
                select(member_reference_methodology_selections_table)
                .where(
                    member_reference_methodology_selections_table.c.household_id
                    == household_id,
                    member_reference_methodology_selections_table.c.member_id
                    == member_id,
                )
                .order_by(
                    member_reference_methodology_selections_table.c.version_number.desc()
                )
                .limit(1)
            )
            .mappings()
            .one_or_none()
        )
        return None if row is None else _from_row(row)

    def list_history(
        self, household_id: UUID, member_id: UUID
    ) -> list[MemberReferenceMethodologySelection]:
        rows = self._connection.execute(
            select(member_reference_methodology_selections_table)
            .where(
                member_reference_methodology_selections_table.c.household_id
                == household_id,
                member_reference_methodology_selections_table.c.member_id
                == member_id,
            )
            .order_by(
                member_reference_methodology_selections_table.c.version_number
            )
        ).mappings()
        return [_from_row(row) for row in rows]


def _values(value: MemberReferenceMethodologySelection) -> dict[str, object]:
    return {
        "id": value.id,
        "household_id": value.household_id,
        "member_id": value.member_id,
        "version_number": value.version_number,
        "nutrition_config_version": value.nutrition_config_version,
        "group_reference_methodology_version": value.group_reference_methodology_version,
        "accepted_local_date": value.accepted_local_date,
        "household_timezone_at_acceptance": value.household_timezone_at_acceptance,
        "member_updated_at_at_acceptance": value.member_updated_at_at_acceptance,
        "household_updated_at_at_acceptance": value.household_updated_at_at_acceptance,
        "acceptance_request_id": value.acceptance_request_id,
        "accepted_at": value.accepted_at,
        "supersedes_selection_id": value.supersedes_selection_id,
        "created_at": value.created_at,
    }


def _from_row(row: Mapping[str, Any]) -> MemberReferenceMethodologySelection:
    return MemberReferenceMethodologySelection(
        id=row["id"],
        household_id=row["household_id"],
        member_id=row["member_id"],
        version_number=row["version_number"],
        nutrition_config_version=row["nutrition_config_version"],
        group_reference_methodology_version=row[
            "group_reference_methodology_version"
        ],
        accepted_local_date=row["accepted_local_date"],
        household_timezone_at_acceptance=row["household_timezone_at_acceptance"],
        member_updated_at_at_acceptance=row["member_updated_at_at_acceptance"],
        household_updated_at_at_acceptance=row[
            "household_updated_at_at_acceptance"
        ],
        acceptance_request_id=row["acceptance_request_id"],
        accepted_at=row["accepted_at"],
        supersedes_selection_id=row["supersedes_selection_id"],
        created_at=row["created_at"],
    )
