"""Household aggregate and deterministic foundation validation."""

from dataclasses import dataclass, replace
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Mapping
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.domain.decimal_utils import quantize_decimal, quantize_money
from app.domain.errors import DomainIssue, DomainIssueCode, DomainValidationError

HEIGHT_CM_QUANT = Decimal("0.1")
WEIGHT_KG_QUANT = Decimal("0.001")
MAX_HEIGHT_CM = Decimal("300.0")
MAX_WEIGHT_KG = Decimal("1000.000")


def _issue(
    code: DomainIssueCode,
    message: str,
    *,
    field: str,
    value: object,
    next_action: str,
) -> DomainValidationError:
    return DomainValidationError(
        DomainIssue(
            code=code,
            message=message,
            field=field,
            value=str(value),
            next_action=next_action,
        )
    )


def _required_text(value: object, *, field: str, label: str) -> str:
    normalized = " ".join(str(value).strip().split()) if value is not None else ""
    if not normalized:
        raise _issue(
            DomainIssueCode.REQUIRED_FIELD,
            f"{label} must not be empty.",
            field=field,
            value=value,
            next_action=f"Provide a non-empty {field}.",
        )
    if len(normalized) > 200:
        raise _issue(
            DomainIssueCode.REQUIRED_FIELD,
            f"{label} must be 200 characters or fewer.",
            field=field,
            value=value,
            next_action=f"Shorten {field} to 200 characters or fewer.",
        )
    return normalized


def _optional_text(value: object, *, field: str, label: str) -> str | None:
    if value is None:
        return None
    normalized = " ".join(str(value).strip().split())
    if not normalized:
        return None
    if len(normalized) > 200:
        raise _issue(
            DomainIssueCode.REQUIRED_FIELD,
            f"{label} must be 200 characters or fewer.",
            field=field,
            value=value,
            next_action=f"Shorten {field} to 200 characters or fewer.",
        )
    return normalized


def normalize_timezone(value: object) -> str:
    timezone_name = _required_text(value, field="timezone", label="Timezone")
    try:
        ZoneInfo(timezone_name)
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise _issue(
            DomainIssueCode.INVALID_TIMEZONE,
            "Timezone must be a valid IANA timezone identifier.",
            field="timezone",
            value=value,
            next_action="Use an identifier such as Europe/Moscow or UTC.",
        ) from exc
    return timezone_name


def normalize_budget(value: object) -> Decimal | None:
    if value is None:
        return None
    budget = quantize_money(value, field="default_weekly_budget")  # type: ignore[arg-type]
    if budget < 0:
        raise _issue(
            DomainIssueCode.NEGATIVE_MONEY,
            "Default weekly budget must not be negative.",
            field="default_weekly_budget",
            value=budget,
            next_action="Provide zero, a positive decimal amount, or null.",
        )
    return budget


def _normalize_measurement(
    value: object,
    *,
    field: str,
    quantum: Decimal,
    maximum: Decimal,
) -> Decimal | None:
    if value is None:
        return None
    measurement = quantize_decimal(value, quantum, field=field)  # type: ignore[arg-type]
    if measurement <= 0:
        raise _issue(
            DomainIssueCode.NON_POSITIVE_MEASUREMENT,
            f"{field} must be greater than zero when supplied.",
            field=field,
            value=measurement,
            next_action=f"Provide a positive {field} or null.",
        )
    if measurement > maximum:
        raise _issue(
            DomainIssueCode.MEASUREMENT_OUT_OF_RANGE,
            f"{field} is outside the supported human measurement range.",
            field=field,
            value=measurement,
            next_action=f"Provide {field} no greater than {maximum} or null.",
        )
    return measurement


def normalize_height_cm(value: object) -> Decimal | None:
    return _normalize_measurement(
        value,
        field="height_cm",
        quantum=HEIGHT_CM_QUANT,
        maximum=MAX_HEIGHT_CM,
    )


def normalize_weight_kg(value: object) -> Decimal | None:
    return _normalize_measurement(
        value,
        field="weight_kg",
        quantum=WEIGHT_KG_QUANT,
        maximum=MAX_WEIGHT_KG,
    )


def normalize_birth_date(value: date | None) -> date | None:
    if value is None:
        return None
    if not isinstance(value, date) or isinstance(value, datetime):
        raise _issue(
            DomainIssueCode.INVALID_DATE,
            "Birth date must be a calendar date.",
            field="birth_date",
            value=value,
            next_action="Provide an ISO date such as 1990-05-20 or null.",
        )
    if value > date.today():
        raise _issue(
            DomainIssueCode.INVALID_DATE,
            "Birth date must not be in the future.",
            field="birth_date",
            value=value,
            next_action="Provide a past or current calendar date.",
        )
    return value


def normalize_active(value: object) -> bool:
    if type(value) is not bool:
        raise _issue(
            DomainIssueCode.INVALID_BOOLEAN,
            "Active must be a boolean value.",
            field="active",
            value=value,
            next_action="Provide true or false.",
        )
    return value


def normalize_utc_instant(value: datetime, *, field: str) -> datetime:
    if (
        not isinstance(value, datetime)
        or value.tzinfo is None
        or value.utcoffset() is None
    ):
        raise _issue(
            DomainIssueCode.INVALID_DATE,
            f"{field} must be a timezone-aware instant.",
            field=field,
            value=value,
            next_action="Provide a timezone-aware datetime; persisted instants use UTC.",
        )
    return value.astimezone(timezone.utc)


@dataclass(frozen=True)
class Household:
    id: UUID
    name: str
    timezone: str
    city: str | None
    default_weekly_budget: Decimal | None
    default_cooking_profile: str | None
    created_at: datetime
    updated_at: datetime

    def __post_init__(self) -> None:
        if not isinstance(self.id, UUID) or self.id.version != 4:
            raise ValueError("Household id must be a UUIDv4 value.")
        object.__setattr__(
            self,
            "name",
            _required_text(self.name, field="name", label="Household name"),
        )
        object.__setattr__(self, "timezone", normalize_timezone(self.timezone))
        object.__setattr__(
            self, "city", _optional_text(self.city, field="city", label="City")
        )
        object.__setattr__(
            self, "default_weekly_budget", normalize_budget(self.default_weekly_budget)
        )
        object.__setattr__(
            self,
            "default_cooking_profile",
            _optional_text(
                self.default_cooking_profile,
                field="default_cooking_profile",
                label="Default cooking profile",
            ),
        )
        created_at = normalize_utc_instant(self.created_at, field="created_at")
        updated_at = normalize_utc_instant(self.updated_at, field="updated_at")
        if updated_at < created_at:
            raise ValueError("Household updated_at must not precede created_at.")
        object.__setattr__(self, "created_at", created_at)
        object.__setattr__(self, "updated_at", updated_at)


@dataclass(frozen=True)
class HouseholdMember:
    id: UUID
    household_id: UUID
    name: str
    active: bool
    birth_date: date | None
    sex: str | None
    height_cm: Decimal | None
    weight_kg: Decimal | None
    activity_level: str
    goal: str
    created_at: datetime
    updated_at: datetime

    def __post_init__(self) -> None:
        if not isinstance(self.id, UUID) or self.id.version != 4:
            raise ValueError("HouseholdMember id must be a UUIDv4 value.")
        if not isinstance(self.household_id, UUID) or self.household_id.version != 4:
            raise ValueError("HouseholdMember household_id must be a UUIDv4 value.")
        object.__setattr__(
            self, "name", _required_text(self.name, field="name", label="Member name")
        )
        object.__setattr__(self, "active", normalize_active(self.active))
        object.__setattr__(self, "birth_date", normalize_birth_date(self.birth_date))
        object.__setattr__(
            self, "sex", _optional_text(self.sex, field="sex", label="Sex")
        )
        object.__setattr__(self, "height_cm", normalize_height_cm(self.height_cm))
        object.__setattr__(self, "weight_kg", normalize_weight_kg(self.weight_kg))
        object.__setattr__(
            self,
            "activity_level",
            _required_text(
                self.activity_level,
                field="activity_level",
                label="Activity level",
            ),
        )
        object.__setattr__(
            self, "goal", _required_text(self.goal, field="goal", label="Goal")
        )
        created_at = normalize_utc_instant(self.created_at, field="created_at")
        updated_at = normalize_utc_instant(self.updated_at, field="updated_at")
        if updated_at < created_at:
            raise ValueError("HouseholdMember updated_at must not precede created_at.")
        object.__setattr__(self, "created_at", created_at)
        object.__setattr__(self, "updated_at", updated_at)


@dataclass(frozen=True)
class HouseholdState:
    household: Household
    members: tuple[HouseholdMember, ...]


HOUSEHOLD_MUTABLE_FIELDS = frozenset(
    {
        "name",
        "timezone",
        "city",
        "default_weekly_budget",
        "default_cooking_profile",
    }
)
MEMBER_MUTABLE_FIELDS = frozenset(
    {
        "name",
        "active",
        "birth_date",
        "sex",
        "height_cm",
        "weight_kg",
        "activity_level",
        "goal",
    }
)


def update_household(
    household: Household,
    changes: Mapping[str, object],
    *,
    updated_at: datetime,
) -> Household:
    unknown = set(changes) - HOUSEHOLD_MUTABLE_FIELDS
    if unknown:
        raise ValueError(f"Unsupported Household fields: {sorted(unknown)}")
    values: dict[str, object] = dict(changes)
    return replace(household, **values, updated_at=updated_at)


def update_household_member(
    member: HouseholdMember,
    changes: Mapping[str, object],
    *,
    updated_at: datetime,
) -> HouseholdMember:
    unknown = set(changes) - MEMBER_MUTABLE_FIELDS
    if unknown:
        raise ValueError(f"Unsupported HouseholdMember fields: {sorted(unknown)}")
    values: dict[str, object] = dict(changes)
    return replace(member, **values, updated_at=updated_at)
