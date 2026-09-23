"""Household-owned immutable member reference-methodology selections."""

from dataclasses import dataclass
from datetime import date, datetime
from uuid import UUID

from app.domain.households import normalize_timezone, normalize_utc_instant


def _uuid4(value: object, *, field: str) -> UUID:
    if not isinstance(value, UUID) or value.version != 4:
        raise ValueError(f"{field} must be UUIDv4.")
    return value


def _positive_int(value: object, *, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{field} must be a positive integer.")
    return value


def _required_code(value: object, *, field: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be a non-empty version code.")
    normalized = value.strip()
    if not normalized or len(normalized) > 200:
        raise ValueError(f"{field} must be a non-empty version code.")
    return normalized


def _optional_code(value: object, *, field: str) -> str | None:
    if value is None:
        return None
    return _required_code(value, field=field)


@dataclass(frozen=True)
class MemberReferenceMethodologySelection:
    id: UUID
    household_id: UUID
    member_id: UUID
    version_number: int
    nutrition_config_version: str
    group_reference_methodology_version: str | None
    accepted_local_date: date
    household_timezone_at_acceptance: str
    member_updated_at_at_acceptance: datetime
    household_updated_at_at_acceptance: datetime
    acceptance_request_id: UUID
    accepted_at: datetime
    supersedes_selection_id: UUID | None
    created_at: datetime

    def __post_init__(self) -> None:
        for field in ("id", "household_id", "member_id", "acceptance_request_id"):
            object.__setattr__(self, field, _uuid4(getattr(self, field), field=field))
        if self.supersedes_selection_id is not None:
            object.__setattr__(
                self,
                "supersedes_selection_id",
                _uuid4(self.supersedes_selection_id, field="supersedes_selection_id"),
            )
            if self.supersedes_selection_id == self.id:
                raise ValueError("A selection cannot supersede itself.")

        object.__setattr__(
            self,
            "version_number",
            _positive_int(self.version_number, field="version_number"),
        )
        object.__setattr__(
            self,
            "nutrition_config_version",
            _required_code(
                self.nutrition_config_version,
                field="nutrition_config_version",
            ),
        )
        object.__setattr__(
            self,
            "group_reference_methodology_version",
            _optional_code(
                self.group_reference_methodology_version,
                field="group_reference_methodology_version",
            ),
        )
        if (
            not isinstance(self.accepted_local_date, date)
            or isinstance(self.accepted_local_date, datetime)
        ):
            raise ValueError("accepted_local_date must be a calendar date.")
        object.__setattr__(
            self,
            "household_timezone_at_acceptance",
            normalize_timezone(self.household_timezone_at_acceptance),
        )
        member_updated = normalize_utc_instant(
            self.member_updated_at_at_acceptance,
            field="member_updated_at_at_acceptance",
        )
        household_updated = normalize_utc_instant(
            self.household_updated_at_at_acceptance,
            field="household_updated_at_at_acceptance",
        )
        accepted_at = normalize_utc_instant(self.accepted_at, field="accepted_at")
        created_at = normalize_utc_instant(self.created_at, field="created_at")
        if member_updated > accepted_at or household_updated > accepted_at:
            raise ValueError(
                "Acceptance cannot precede the authoritative state tokens."
            )
        if created_at < accepted_at:
            raise ValueError("created_at must not precede accepted_at.")
        object.__setattr__(
            self, "member_updated_at_at_acceptance", member_updated
        )
        object.__setattr__(
            self, "household_updated_at_at_acceptance", household_updated
        )
        object.__setattr__(self, "accepted_at", accepted_at)
        object.__setattr__(self, "created_at", created_at)

    @property
    def reference_bundle(self) -> tuple[str, str | None]:
        return (
            self.nutrition_config_version,
            self.group_reference_methodology_version,
        )
