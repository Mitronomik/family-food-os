"""Platform-owned Meal Pattern Catalogue domain."""

import re
from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum
from uuid import UUID

from app.domain.errors import DomainIssue, DomainIssueCode, DomainValidationError
from app.domain.food_ingredients import normalize_utc_instant

_UPPER_CODE = re.compile(r"^[A-Z][A-Z0-9_]*$")
_CYRILLIC = re.compile(r"[А-Яа-яЁё]")


class MealPatternLifecycle(StrEnum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    INACTIVE = "INACTIVE"


class MealPatternReviewStatus(StrEnum):
    UNREVIEWED = "UNREVIEWED"
    REVIEWED = "REVIEWED"


class MealPatternScope(StrEnum):
    WELLNESS_SCHEDULE = "WELLNESS_SCHEDULE"


class MealRole(StrEnum):
    BREAKFAST = "BREAKFAST"
    LUNCH = "LUNCH"
    DINNER = "DINNER"
    SNACK = "SNACK"
    PRE_WORKOUT = "PRE_WORKOUT"
    POST_WORKOUT = "POST_WORKOUT"
    OTHER = "OTHER"


class MealPatternTagKind(StrEnum):
    GOAL = "GOAL"
    CONTEXT = "CONTEXT"
    EXCLUSION = "EXCLUSION"


def _issue(
    code: DomainIssueCode, message: str, *, field: str, value: object
) -> DomainValidationError:
    return DomainValidationError(
        DomainIssue(
            code=code,
            message=message,
            field=field,
            value=str(value),
            next_action=f"Provide a valid {field}.",
        )
    )


def _text(value: object, *, field: str, maximum: int = 2000) -> str:
    normalized = " ".join(value.strip().split()) if isinstance(value, str) else ""
    if not normalized:
        raise _issue(
            DomainIssueCode.REQUIRED_FIELD,
            f"{field} must not be empty.",
            field=field,
            value=value,
        )
    if len(normalized) > maximum:
        raise _issue(
            DomainIssueCode.VALUE_OUT_OF_RANGE,
            f"{field} must be {maximum} characters or fewer.",
            field=field,
            value=value,
        )
    return normalized


def _code(value: object, *, field: str) -> str:
    normalized = _text(value, field=field, maximum=100)
    if not _UPPER_CODE.fullmatch(normalized):
        raise _issue(
            DomainIssueCode.INVALID_CODE,
            f"{field} must be an uppercase machine code.",
            field=field,
            value=value,
        )
    return normalized


def _uuid4(value: object, *, field: str) -> UUID:
    if not isinstance(value, UUID) or value.version != 4:
        raise _issue(
            DomainIssueCode.INVALID_IDENTIFIER,
            f"{field} must be UUIDv4.",
            field=field,
            value=value,
        )
    return value


def _positive_int(value: object, *, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise _issue(
            DomainIssueCode.VALUE_OUT_OF_RANGE,
            f"{field} must be a positive integer.",
            field=field,
            value=value,
        )
    return value


def _nonnegative_int(value: object, *, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise _issue(
            DomainIssueCode.VALUE_OUT_OF_RANGE,
            f"{field} must be a non-negative integer.",
            field=field,
            value=value,
        )
    return value


@dataclass(frozen=True)
class MealPatternProgram:
    id: UUID
    code: str
    created_at: datetime

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _uuid4(self.id, field="id"))
        object.__setattr__(self, "code", _code(self.code, field="code"))
        object.__setattr__(
            self,
            "created_at",
            normalize_utc_instant(self.created_at, field="created_at"),
        )


@dataclass(frozen=True)
class MealPatternProgramVersion:
    id: UUID
    program_id: UUID
    version_number: int
    lifecycle: MealPatternLifecycle
    scope: MealPatternScope
    display_name_ru: str
    explanation_ru: str
    min_age_years: int
    max_age_years: int | None
    review_status: MealPatternReviewStatus
    reviewed_at: datetime | None
    published_at: datetime | None
    created_from_version_id: UUID | None
    change_note: str
    created_at: datetime

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _uuid4(self.id, field="id"))
        object.__setattr__(
            self, "program_id", _uuid4(self.program_id, field="program_id")
        )
        if self.created_from_version_id is not None:
            object.__setattr__(
                self,
                "created_from_version_id",
                _uuid4(
                    self.created_from_version_id, field="created_from_version_id"
                ),
            )
        object.__setattr__(
            self,
            "version_number",
            _positive_int(self.version_number, field="version_number"),
        )
        for field, enum_type in (
            ("lifecycle", MealPatternLifecycle),
            ("scope", MealPatternScope),
            ("review_status", MealPatternReviewStatus),
        ):
            try:
                object.__setattr__(self, field, enum_type(getattr(self, field)))
            except (TypeError, ValueError) as exc:
                raise _issue(
                    DomainIssueCode.INVALID_CODE,
                    f"{field} has an invalid controlled value.",
                    field=field,
                    value=getattr(self, field),
                ) from exc
        object.__setattr__(
            self,
            "display_name_ru",
            _text(self.display_name_ru, field="display_name_ru", maximum=160),
        )
        object.__setattr__(
            self,
            "explanation_ru",
            _text(self.explanation_ru, field="explanation_ru", maximum=1000),
        )
        object.__setattr__(
            self,
            "min_age_years",
            _nonnegative_int(self.min_age_years, field="min_age_years"),
        )
        if self.max_age_years is not None:
            object.__setattr__(
                self,
                "max_age_years",
                _nonnegative_int(self.max_age_years, field="max_age_years"),
            )
            if self.max_age_years < self.min_age_years:
                raise _issue(
                    DomainIssueCode.VALUE_OUT_OF_RANGE,
                    "max_age_years must not be below min_age_years.",
                    field="max_age_years",
                    value=self.max_age_years,
                )
        for field in ("reviewed_at", "published_at"):
            value = getattr(self, field)
            if value is not None:
                object.__setattr__(
                    self, field, normalize_utc_instant(value, field=field)
                )
        object.__setattr__(
            self,
            "change_note",
            _text(self.change_note, field="change_note", maximum=1000),
        )
        object.__setattr__(
            self,
            "created_at",
            normalize_utc_instant(self.created_at, field="created_at"),
        )


@dataclass(frozen=True)
class MealPatternOpportunity:
    version_id: UUID
    position: int
    role: MealRole

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "version_id", _uuid4(self.version_id, field="version_id")
        )
        object.__setattr__(
            self, "position", _positive_int(self.position, field="position")
        )
        try:
            object.__setattr__(self, "role", MealRole(self.role))
        except (TypeError, ValueError) as exc:
            raise _issue(
                DomainIssueCode.INVALID_CODE,
                "role has an invalid controlled value.",
                field="role",
                value=self.role,
            ) from exc


@dataclass(frozen=True)
class MealPatternTag:
    version_id: UUID
    kind: MealPatternTagKind
    code: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "version_id", _uuid4(self.version_id, field="version_id")
        )
        try:
            object.__setattr__(self, "kind", MealPatternTagKind(self.kind))
        except (TypeError, ValueError) as exc:
            raise _issue(
                DomainIssueCode.INVALID_CODE,
                "kind has an invalid controlled value.",
                field="kind",
                value=self.kind,
            ) from exc
        object.__setattr__(self, "code", _code(self.code, field="code"))


@dataclass(frozen=True)
class MealPatternEvidence:
    version_id: UUID
    position: int
    source_name: str
    source_title: str
    source_url: str
    source_version: str
    retrieved_on: date
    evidence_scope: str
    review_note_ru: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "version_id", _uuid4(self.version_id, field="version_id")
        )
        object.__setattr__(
            self, "position", _positive_int(self.position, field="position")
        )
        for field, maximum in (
            ("source_name", 240),
            ("source_title", 500),
            ("source_url", 1000),
            ("source_version", 500),
            ("review_note_ru", 1000),
        ):
            object.__setattr__(
                self, field, _text(getattr(self, field), field=field, maximum=maximum)
            )
        if not self.source_url.startswith(("https://", "http://")):
            raise _issue(
                DomainIssueCode.INVALID_CODE,
                "source_url must be HTTP(S).",
                field="source_url",
                value=self.source_url,
            )
        if not isinstance(self.retrieved_on, date) or isinstance(
            self.retrieved_on, datetime
        ):
            raise _issue(
                DomainIssueCode.INVALID_DATE,
                "retrieved_on must be a calendar date.",
                field="retrieved_on",
                value=self.retrieved_on,
            )
        object.__setattr__(
            self,
            "evidence_scope",
            _code(self.evidence_scope, field="evidence_scope"),
        )


@dataclass(frozen=True)
class MealPatternProgramDetail:
    program: MealPatternProgram
    version: MealPatternProgramVersion
    opportunities: tuple[MealPatternOpportunity, ...]
    tags: tuple[MealPatternTag, ...]
    evidence: tuple[MealPatternEvidence, ...]

    def __post_init__(self) -> None:
        if self.version.program_id != self.program.id:
            raise _issue(
                DomainIssueCode.INVALID_IDENTIFIER,
                "version must belong to program.",
                field="program_id",
                value=self.version.program_id,
            )
        version_id = self.version.id
        if any(value.version_id != version_id for value in self.opportunities):
            raise _issue(
                DomainIssueCode.INVALID_IDENTIFIER,
                "opportunities must belong to the version.",
                field="opportunities",
                value=version_id,
            )
        if any(value.version_id != version_id for value in self.tags):
            raise _issue(
                DomainIssueCode.INVALID_IDENTIFIER,
                "tags must belong to the version.",
                field="tags",
                value=version_id,
            )
        if any(value.version_id != version_id for value in self.evidence):
            raise _issue(
                DomainIssueCode.INVALID_IDENTIFIER,
                "evidence must belong to the version.",
                field="evidence",
                value=version_id,
            )


@dataclass(frozen=True)
class MealPatternEligibilityQuery:
    age_years: int
    goal_codes: tuple[str, ...] = ()
    context_codes: tuple[str, ...] = ()
    exclusion_codes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "age_years", _nonnegative_int(self.age_years, field="age_years")
        )
        for field in ("goal_codes", "context_codes", "exclusion_codes"):
            values = tuple(_code(value, field=field) for value in getattr(self, field))
            if len(values) != len(set(values)):
                raise _issue(
                    DomainIssueCode.INVALID_CODE,
                    f"{field} must not contain duplicates.",
                    field=field,
                    value=values,
                )
            object.__setattr__(self, field, values)


def validate_publishable(detail: MealPatternProgramDetail) -> None:
    version = detail.version
    if version.lifecycle is not MealPatternLifecycle.PUBLISHED:
        raise _issue(
            DomainIssueCode.INVALID_CODE,
            "Only PUBLISHED versions can pass publication validation.",
            field="lifecycle",
            value=version.lifecycle,
        )
    if version.scope is not MealPatternScope.WELLNESS_SCHEDULE:
        raise _issue(
            DomainIssueCode.INVALID_CODE,
            "Only wellness schedule programs are supported.",
            field="scope",
            value=version.scope,
        )
    if version.review_status is not MealPatternReviewStatus.REVIEWED:
        raise _issue(
            DomainIssueCode.REQUIRED_FIELD,
            "Published programs require review.",
            field="review_status",
            value=version.review_status,
        )
    if version.reviewed_at is None or version.published_at is None:
        raise _issue(
            DomainIssueCode.REQUIRED_FIELD,
            "Published programs require reviewed_at and published_at.",
            field="published_at",
            value=version.published_at,
        )
    if not _CYRILLIC.search(version.display_name_ru) or not _CYRILLIC.search(
        version.explanation_ru
    ):
        raise _issue(
            DomainIssueCode.REQUIRED_FIELD,
            "Published consumer text must be Russian.",
            field="display_name_ru",
            value=version.display_name_ru,
        )
    if not detail.opportunities:
        raise _issue(
            DomainIssueCode.REQUIRED_FIELD,
            "Published programs require at least one meal opportunity.",
            field="opportunities",
            value=detail.opportunities,
        )
    positions = tuple(value.position for value in detail.opportunities)
    if positions != tuple(range(1, len(positions) + 1)):
        raise _issue(
            DomainIssueCode.INVALID_CODE,
            "Meal opportunities must have contiguous deterministic ordering.",
            field="opportunities",
            value=positions,
        )
    if not detail.evidence:
        raise _issue(
            DomainIssueCode.REQUIRED_FIELD,
            "Published programs require reviewable evidence.",
            field="evidence",
            value=detail.evidence,
        )
    evidence_positions = tuple(value.position for value in detail.evidence)
    if evidence_positions != tuple(range(1, len(evidence_positions) + 1)):
        raise _issue(
            DomainIssueCode.INVALID_CODE,
            "Evidence must have contiguous deterministic ordering.",
            field="evidence",
            value=evidence_positions,
        )
    if any(not _CYRILLIC.search(item.review_note_ru) for item in detail.evidence):
        raise _issue(
            DomainIssueCode.REQUIRED_FIELD,
            "Evidence review notes must be Russian.",
            field="review_note_ru",
            value="non-Russian evidence note",
        )


def detail_is_eligible(
    detail: MealPatternProgramDetail, query: MealPatternEligibilityQuery
) -> bool:
    version = detail.version
    if version.lifecycle is not MealPatternLifecycle.PUBLISHED:
        return False
    if query.age_years < version.min_age_years:
        return False
    if version.max_age_years is not None and query.age_years > version.max_age_years:
        return False
    tags = {(tag.kind, tag.code) for tag in detail.tags}
    required_goals = {
        code for kind, code in tags if kind is MealPatternTagKind.GOAL
    }
    required_contexts = {
        code for kind, code in tags if kind is MealPatternTagKind.CONTEXT
    }
    excluded = {
        code for kind, code in tags if kind is MealPatternTagKind.EXCLUSION
    }
    if query.goal_codes and not set(query.goal_codes).issubset(required_goals):
        return False
    if query.context_codes and not set(query.context_codes).issubset(required_contexts):
        return False
    if excluded.intersection(query.exclusion_codes):
        return False
    return True
