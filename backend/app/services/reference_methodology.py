"""Step 6A application service for persisted member reference methodology."""

from collections.abc import Callable
from datetime import date, datetime, timezone
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

from app.domain.households import HouseholdMember
from app.domain.nutrition_config import CONFIG
from app.domain.reference_methodology import MemberReferenceMethodologySelection
from app.domain.russian_reference_targets import (
    ReferenceSelectionStatus,
    ReviewedRussianReferenceTable,
    select_russian_reference_targets,
)
from app.services.reference_methodology_contracts import (
    ReferenceMethodologyPersistenceConflictError,
    ReferenceMethodologyReadScope,
    ReferenceMethodologyUnitOfWork,
)


BASELINE_NUTRITION_CONFIG_VERSION = CONFIG.version
RUSSIAN_GROUP_REFERENCE_VERSION = (
    "RU_MR_2_3_1_0253_21_ADULT_MICRONUTRIENT_V1"
)

WriteScopeFactory = Callable[[], ReferenceMethodologyUnitOfWork]
ReadScopeFactory = Callable[[], ReferenceMethodologyReadScope]
TableProvider = Callable[[str], ReviewedRussianReferenceTable]
IdFactory = Callable[[], UUID]
Clock = Callable[[], datetime]


class ReferenceMethodologyNotFoundError(LookupError):
    pass


class ReferenceMethodologyConflictError(ValueError):
    pass


class ReferenceMethodologyUnsupportedError(ValueError):
    pass


def _uuid4(value: object, *, field: str) -> UUID:
    if not isinstance(value, UUID) or value.version != 4:
        raise ValueError(f"{field} must be UUIDv4.")
    return value


def _age_years(member: HouseholdMember, *, local_date: date) -> int | None:
    born = member.birth_date
    if born is None or born > local_date:
        return None
    return (
        local_date.year
        - born.year
        - ((local_date.month, local_date.day) < (born.month, born.day))
    )


class ReferenceMethodologyService:
    def __init__(
        self,
        write_scope_factory: WriteScopeFactory,
        read_scope_factory: ReadScopeFactory,
        *,
        russian_reference_tables: TableProvider | None = None,
        id_factory: IdFactory = uuid4,
        clock: Clock | None = None,
    ) -> None:
        self._write = write_scope_factory
        self._read = read_scope_factory
        self._russian_tables = russian_reference_tables
        self._id_factory = id_factory
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def accept_member_selection(
        self,
        *,
        household_id: UUID,
        member_id: UUID,
        acceptance_request_id: UUID,
        expected_current_selection_id: UUID | None,
        nutrition_config_version: str,
        group_reference_methodology_version: str | None,
    ) -> MemberReferenceMethodologySelection:
        household_id = _uuid4(household_id, field="household_id")
        member_id = _uuid4(member_id, field="member_id")
        acceptance_request_id = _uuid4(
            acceptance_request_id, field="acceptance_request_id"
        )
        if expected_current_selection_id is not None:
            expected_current_selection_id = _uuid4(
                expected_current_selection_id,
                field="expected_current_selection_id",
            )
        requested_bundle = self._resolve_bundle(
            nutrition_config_version,
            group_reference_methodology_version,
        )

        with self._write() as scope:
            try:
                replay = scope.selections.get_by_request_id(
                    household_id, member_id, acceptance_request_id
                )
            except ReferenceMethodologyPersistenceConflictError as exc:
                raise ReferenceMethodologyConflictError(str(exc)) from exc
            if replay is not None:
                if replay.reference_bundle != requested_bundle:
                    raise ReferenceMethodologyConflictError(
                        "acceptance_request_id was already used for another "
                        "reference bundle."
                    )
                return replay

            household = scope.households.get_household(household_id)
            member = scope.members.get_member(household_id, member_id)
            if household is None or member is None:
                raise ReferenceMethodologyNotFoundError(
                    "Household member was not found in the requested Household."
                )
            household_token = household.updated_at
            member_token = member.updated_at

            accepted_at = self._clock()
            if (
                not isinstance(accepted_at, datetime)
                or accepted_at.tzinfo is None
                or accepted_at.utcoffset() is None
            ):
                raise TypeError("Step 6A clock must return a timezone-aware datetime.")
            accepted_at = accepted_at.astimezone(timezone.utc)
            if household_token > accepted_at or member_token > accepted_at:
                raise ReferenceMethodologyConflictError(
                    "Authoritative Household state is newer than the "
                    "acceptance instant."
                )
            accepted_local_date = accepted_at.astimezone(
                ZoneInfo(household.timezone)
            ).date()

            if requested_bundle[1] is not None:
                self._validate_russian_applicability(
                    member,
                    accepted_local_date=accepted_local_date,
                    methodology_version=requested_bundle[1],
                )

            current = scope.selections.get_current(household_id, member_id)
            if current is None:
                if expected_current_selection_id is not None:
                    raise ReferenceMethodologyConflictError(
                        "Expected current selection does not exist."
                    )
            elif expected_current_selection_id != current.id:
                raise ReferenceMethodologyConflictError(
                    "Current reference-methodology selection changed."
                )

            try:
                scope.revalidate_authoritative_state(
                    household_id=household_id,
                    household_updated_at=household_token,
                    member_id=member_id,
                    member_updated_at=member_token,
                )
            except ReferenceMethodologyPersistenceConflictError as exc:
                raise ReferenceMethodologyConflictError(str(exc)) from exc

            if current is not None and current.reference_bundle == requested_bundle:
                return current

            selection = MemberReferenceMethodologySelection(
                id=self._id_factory(),
                household_id=household_id,
                member_id=member_id,
                version_number=1 if current is None else current.version_number + 1,
                nutrition_config_version=requested_bundle[0],
                group_reference_methodology_version=requested_bundle[1],
                accepted_local_date=accepted_local_date,
                household_timezone_at_acceptance=household.timezone,
                member_updated_at_at_acceptance=member_token,
                household_updated_at_at_acceptance=household_token,
                acceptance_request_id=acceptance_request_id,
                accepted_at=accepted_at,
                supersedes_selection_id=None if current is None else current.id,
                created_at=accepted_at,
            )
            try:
                scope.selections.add(selection)
                scope.commit()
            except ReferenceMethodologyPersistenceConflictError as exc:
                raise ReferenceMethodologyConflictError(str(exc)) from exc
            return selection

    def get_selection(
        self, household_id: UUID, selection_id: UUID
    ) -> MemberReferenceMethodologySelection:
        with self._read() as scope:
            selection = scope.selections.get(household_id, selection_id)
        if selection is None:
            raise ReferenceMethodologyNotFoundError(selection_id)
        return selection

    def get_current_selection(
        self, household_id: UUID, member_id: UUID
    ) -> MemberReferenceMethodologySelection:
        with self._read() as scope:
            selection = scope.selections.get_current(household_id, member_id)
        if selection is None:
            raise ReferenceMethodologyNotFoundError(member_id)
        return selection

    def get_selection_history(
        self, household_id: UUID, member_id: UUID
    ) -> tuple[MemberReferenceMethodologySelection, ...]:
        with self._read() as scope:
            return tuple(scope.selections.list_history(household_id, member_id))

    @staticmethod
    def _resolve_bundle(
        nutrition_config_version: str,
        group_reference_methodology_version: str | None,
    ) -> tuple[str, str | None]:
        if nutrition_config_version != BASELINE_NUTRITION_CONFIG_VERSION:
            raise ReferenceMethodologyUnsupportedError(
                "Unsupported personal reference nutrition config version."
            )
        if group_reference_methodology_version not in (
            None,
            RUSSIAN_GROUP_REFERENCE_VERSION,
        ):
            raise ReferenceMethodologyUnsupportedError(
                "Unsupported group-reference methodology version."
            )
        return (
            BASELINE_NUTRITION_CONFIG_VERSION,
            group_reference_methodology_version,
        )

    def _validate_russian_applicability(
        self,
        member: HouseholdMember,
        *,
        accepted_local_date: date,
        methodology_version: str,
    ) -> None:
        validate_russian_group_reference_applicability(
            member,
            reference_date=accepted_local_date,
            methodology_version=methodology_version,
            russian_reference_tables=self._russian_tables,
        )


def validate_russian_group_reference_applicability(
    member: HouseholdMember,
    *,
    reference_date: date,
    methodology_version: str,
    russian_reference_tables: TableProvider | None,
) -> None:
    if russian_reference_tables is None:
        raise ReferenceMethodologyUnsupportedError(
            "Reviewed Russian reference table provider is unavailable."
        )
    try:
        table = russian_reference_tables(methodology_version)
    except (LookupError, ValueError) as exc:
        raise ReferenceMethodologyUnsupportedError(
            "Reviewed Russian reference methodology is unavailable."
        ) from exc
    if (
        not isinstance(table, ReviewedRussianReferenceTable)
        or table.methodology_version != methodology_version
    ):
        raise ReferenceMethodologyUnsupportedError(
            "Reviewed Russian reference methodology version mismatch."
        )
    definition_codes = tuple(sorted({row.definition_code for row in table.rows}))
    if len(definition_codes) != 24:
        raise ReferenceMethodologyUnsupportedError(
            "Step 5 Russian reference definition set is not the accepted "
            "24-code table."
        )
    age = _age_years(member, local_date=reference_date)
    result = select_russian_reference_targets(
        table,
        age_years=age,
        sex=member.sex,
        physical_activity_coefficient=None,
        life_stage="adult" if age is not None and age >= 18 else "child",
        definition_codes=definition_codes,
    )
    if (
        result.status is not ReferenceSelectionStatus.COMPLETE
        or len(result.rows) != 24
    ):
        raise ReferenceMethodologyUnsupportedError(
            "Step 5 Russian group reference is not applicable to this member."
        )
