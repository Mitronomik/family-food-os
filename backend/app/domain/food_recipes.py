"""Platform-owned verified Recipe Catalogue domain."""

from dataclasses import dataclass, replace
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
import re
from uuid import UUID

from app.domain.decimal_utils import parse_decimal, quantize_decimal
from app.domain.errors import DomainIssue, DomainIssueCode, DomainValidationError
from app.domain.food_ingredients import (
    normalize_unicode_search_key,
    normalize_utc_instant,
)
from app.domain.units import UnitCode

_UPPER_CODE = re.compile(r"^[A-Z][A-Z0-9_]*$")
_LOWER_CODE = re.compile(r"^[a-z][a-z0-9_]*$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_QUANT = Decimal("0.000001")


class VerificationStatus(StrEnum):
    UNVERIFIED = "UNVERIFIED"
    SOURCE_VERIFIED = "SOURCE_VERIFIED"
    REJECTED = "REJECTED"


class RightsReviewStatus(StrEnum):
    UNREVIEWED = "UNREVIEWED"
    REVIEWED = "REVIEWED"
    BLOCKED = "BLOCKED"


class MealTypeCode(StrEnum):
    BREAKFAST = "breakfast"
    MAIN = "main"
    SIDE = "side"
    SALAD = "salad"
    SANDWICH = "sandwich"
    OTHER = "other"


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


def _text(value: object, *, field: str, maximum: int = 240) -> str:
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


def _optional_text(value: object, *, field: str, maximum: int = 240) -> str | None:
    return None if value is None else _text(value, field=field, maximum=maximum)


def _code(value: object, *, field: str, uppercase: bool) -> str:
    normalized = _text(value, field=field, maximum=80)
    pattern = _UPPER_CODE if uppercase else _LOWER_CODE
    if not pattern.fullmatch(normalized):
        raise _issue(
            DomainIssueCode.INVALID_CODE,
            f"{field} has an invalid format.",
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


def _optional_nonnegative_int(value: object, *, field: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise _issue(
            DomainIssueCode.VALUE_OUT_OF_RANGE,
            f"{field} must be a non-negative integer or null.",
            field=field,
            value=value,
        )
    return value


def _nullable_bool(value: object, *, field: str) -> bool | None:
    if value is not None and type(value) is not bool:
        raise _issue(
            DomainIssueCode.INVALID_BOOLEAN,
            f"{field} must be boolean or null.",
            field=field,
            value=value,
        )
    return value


def _positive_decimal(value: object, *, field: str) -> Decimal:
    parsed = parse_decimal(value, field=field)  # type: ignore[arg-type]
    if parsed <= 0:
        raise _issue(
            DomainIssueCode.VALUE_OUT_OF_RANGE,
            f"{field} must be positive.",
            field=field,
            value=value,
        )
    normalized = quantize_decimal(parsed, _QUANT, field=field)
    if normalized <= 0:
        raise _issue(
            DomainIssueCode.VALUE_OUT_OF_RANGE,
            f"{field} is below supported precision.",
            field=field,
            value=value,
        )
    return normalized


def _food_unit(value: object) -> UnitCode:
    try:
        unit = value if isinstance(value, UnitCode) else UnitCode(value)
    except (TypeError, ValueError) as exc:
        raise _issue(
            DomainIssueCode.INVALID_UNIT,
            "unit must be g, ml, or pcs.",
            field="unit",
            value=value,
        ) from exc
    if unit is UnitCode.PERCENT:
        raise _issue(
            DomainIssueCode.INVALID_UNIT,
            "percent is forbidden for Recipe ingredients.",
            field="unit",
            value=value,
        )
    return unit


@dataclass(frozen=True)
class Recipe:
    id: UUID
    canonical_code: str
    canonical_name: str
    canonical_name_key: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _uuid4(self.id, field="id"))
        object.__setattr__(
            self,
            "canonical_code",
            _code(self.canonical_code, field="canonical_code", uppercase=True),
        )
        name = _text(self.canonical_name, field="canonical_name")
        object.__setattr__(self, "canonical_name", name)
        expected_key = normalize_unicode_search_key(name, field="canonical_name")
        if self.canonical_name_key != expected_key:
            raise _issue(
                DomainIssueCode.INVALID_CODE,
                "canonical_name_key does not match canonical_name.",
                field="canonical_name_key",
                value=self.canonical_name_key,
            )
        if type(self.is_active) is not bool:
            raise _issue(
                DomainIssueCode.INVALID_BOOLEAN,
                "is_active must be boolean.",
                field="is_active",
                value=self.is_active,
            )
        created_at = normalize_utc_instant(self.created_at, field="created_at")
        updated_at = normalize_utc_instant(self.updated_at, field="updated_at")
        if updated_at < created_at:
            raise _issue(
                DomainIssueCode.INVALID_DATE,
                "updated_at must not precede created_at.",
                field="updated_at",
                value=updated_at,
            )
        object.__setattr__(self, "created_at", created_at)
        object.__setattr__(self, "updated_at", updated_at)


@dataclass(frozen=True)
class RecipeVersion:
    id: UUID
    recipe_id: UUID
    version_number: int
    base_servings: Decimal
    meal_type_code: MealTypeCode
    prep_time_minutes: int | None
    cook_time_minutes: int | None
    total_time_minutes: int | None
    difficulty_code: str | None
    batch_friendly: bool | None
    freezable: bool | None
    storage_days_fridge: int | None
    storage_days_freezer: int | None
    verification_status: VerificationStatus
    verified_at: datetime | None
    source_name: str
    source_recipe_id: str
    source_url: str
    source_version: str
    source_retrieved_at: datetime
    source_document_sha256: str
    source_original_servings: Decimal
    rights_review_status: RightsReviewStatus
    rights_basis: str | None
    created_from_version_id: UUID | None
    change_note: str
    created_at: datetime

    def __post_init__(self) -> None:
        for field in ("id", "recipe_id"):
            object.__setattr__(self, field, _uuid4(getattr(self, field), field=field))
        if self.created_from_version_id is not None:
            object.__setattr__(
                self,
                "created_from_version_id",
                _uuid4(self.created_from_version_id, field="created_from_version_id"),
            )
        object.__setattr__(
            self,
            "version_number",
            _positive_int(self.version_number, field="version_number"),
        )
        object.__setattr__(
            self,
            "base_servings",
            _positive_decimal(self.base_servings, field="base_servings"),
        )
        object.__setattr__(
            self,
            "source_original_servings",
            _positive_decimal(
                self.source_original_servings, field="source_original_servings"
            ),
        )
        for field, enum_type in (
            ("meal_type_code", MealTypeCode),
            ("verification_status", VerificationStatus),
            ("rights_review_status", RightsReviewStatus),
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
        if self.difficulty_code is not None:
            object.__setattr__(
                self,
                "difficulty_code",
                _code(self.difficulty_code, field="difficulty_code", uppercase=False),
            )
        for field in (
            "prep_time_minutes",
            "cook_time_minutes",
            "total_time_minutes",
            "storage_days_fridge",
            "storage_days_freezer",
        ):
            object.__setattr__(
                self,
                field,
                _optional_nonnegative_int(getattr(self, field), field=field),
            )
        for field in ("batch_friendly", "freezable"):
            object.__setattr__(
                self, field, _nullable_bool(getattr(self, field), field=field)
            )
        for field, maximum in (
            ("source_name", 240),
            ("source_recipe_id", 240),
            ("source_url", 1000),
            ("source_version", 240),
            ("change_note", 1000),
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
        if not _SHA256.fullmatch(self.source_document_sha256):
            raise _issue(
                DomainIssueCode.INVALID_CODE,
                "source_document_sha256 must be lowercase SHA-256.",
                field="source_document_sha256",
                value=self.source_document_sha256,
            )
        object.__setattr__(
            self,
            "source_retrieved_at",
            normalize_utc_instant(
                self.source_retrieved_at, field="source_retrieved_at"
            ),
        )
        object.__setattr__(
            self,
            "created_at",
            normalize_utc_instant(self.created_at, field="created_at"),
        )
        if self.verified_at is not None:
            object.__setattr__(
                self,
                "verified_at",
                normalize_utc_instant(self.verified_at, field="verified_at"),
            )
        object.__setattr__(
            self,
            "rights_basis",
            _optional_text(self.rights_basis, field="rights_basis", maximum=2000),
        )
        if (
            self.rights_review_status is RightsReviewStatus.REVIEWED
            and self.rights_basis is None
        ):
            raise _issue(
                DomainIssueCode.REQUIRED_FIELD,
                "Reviewed rights require rights_basis.",
                field="rights_basis",
                value=self.rights_basis,
            )
        if self.verification_status is VerificationStatus.SOURCE_VERIFIED and (
            self.verified_at is None
            or self.rights_review_status is not RightsReviewStatus.REVIEWED
            or self.rights_basis is None
        ):
            raise _issue(
                DomainIssueCode.REQUIRED_FIELD,
                "SOURCE_VERIFIED requires verified provenance and reviewed rights.",
                field="verification_status",
                value=self.verification_status,
            )


@dataclass(frozen=True)
class RecipeIngredient:
    id: UUID
    recipe_version_id: UUID
    food_ingredient_id: UUID
    position: int
    quantity: Decimal
    unit: UnitCode
    source_amount_text: str
    normalization_note: str | None
    prep_note: str | None
    optional: bool
    created_at: datetime

    def __post_init__(self) -> None:
        for field in ("id", "recipe_version_id", "food_ingredient_id"):
            object.__setattr__(self, field, _uuid4(getattr(self, field), field=field))
        object.__setattr__(
            self, "position", _positive_int(self.position, field="position")
        )
        object.__setattr__(
            self, "quantity", _positive_decimal(self.quantity, field="quantity")
        )
        object.__setattr__(self, "unit", _food_unit(self.unit))
        object.__setattr__(
            self,
            "source_amount_text",
            _text(self.source_amount_text, field="source_amount_text", maximum=1000),
        )
        for field in ("normalization_note", "prep_note"):
            object.__setattr__(
                self,
                field,
                _optional_text(getattr(self, field), field=field, maximum=1000),
            )
        if type(self.optional) is not bool:
            raise _issue(
                DomainIssueCode.INVALID_BOOLEAN,
                "optional must be boolean.",
                field="optional",
                value=self.optional,
            )
        object.__setattr__(
            self,
            "created_at",
            normalize_utc_instant(self.created_at, field="created_at"),
        )


@dataclass(frozen=True)
class RecipeStep:
    id: UUID
    recipe_version_id: UUID
    position: int
    instruction: str
    stage_code: str | None
    created_at: datetime

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _uuid4(self.id, field="id"))
        object.__setattr__(
            self,
            "recipe_version_id",
            _uuid4(self.recipe_version_id, field="recipe_version_id"),
        )
        object.__setattr__(
            self, "position", _positive_int(self.position, field="position")
        )
        object.__setattr__(
            self,
            "instruction",
            _text(self.instruction, field="instruction", maximum=4000),
        )
        if self.stage_code is not None:
            object.__setattr__(
                self,
                "stage_code",
                _code(self.stage_code, field="stage_code", uppercase=False),
            )
        object.__setattr__(
            self,
            "created_at",
            normalize_utc_instant(self.created_at, field="created_at"),
        )


@dataclass(frozen=True)
class RecipeEquipment:
    recipe_version_id: UUID
    position: int
    equipment_code: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "recipe_version_id",
            _uuid4(self.recipe_version_id, field="recipe_version_id"),
        )
        object.__setattr__(
            self, "position", _positive_int(self.position, field="position")
        )
        object.__setattr__(
            self,
            "equipment_code",
            _code(self.equipment_code, field="equipment_code", uppercase=False),
        )


@dataclass(frozen=True)
class RecipeVersionDetail:
    recipe: Recipe
    version: RecipeVersion
    ingredients: tuple[RecipeIngredient, ...]
    steps: tuple[RecipeStep, ...]
    equipment: tuple[RecipeEquipment, ...]

    def __post_init__(self) -> None:
        if self.version.recipe_id != self.recipe.id:
            raise _issue(
                DomainIssueCode.INVALID_IDENTIFIER,
                "Version does not belong to Recipe.",
                field="recipe_id",
                value=self.version.recipe_id,
            )
        for label, values in (
            ("ingredient", self.ingredients),
            ("step", self.steps),
            ("equipment", self.equipment),
        ):
            positions = [value.position for value in values]
            if positions != list(range(1, len(values) + 1)):
                raise _issue(
                    DomainIssueCode.VALUE_OUT_OF_RANGE,
                    f"Duplicate, missing, or unordered {label} positions.",
                    field="position",
                    value=positions,
                )
            if any(value.recipe_version_id != self.version.id for value in values):
                raise _issue(
                    DomainIssueCode.INVALID_IDENTIFIER,
                    f"{label} belongs to another version.",
                    field="recipe_version_id",
                    value=self.version.id,
                )
        if not self.ingredients or not self.steps:
            raise _issue(
                DomainIssueCode.REQUIRED_FIELD,
                "A RecipeVersion requires ingredients and steps.",
                field="version",
                value=self.version.id,
            )


def deactivate_recipe(recipe: Recipe, *, updated_at: datetime) -> Recipe:
    return replace(recipe, is_active=False, updated_at=updated_at)


def scale_recipe(
    detail: RecipeVersionDetail, target_servings: Decimal
) -> RecipeVersionDetail:
    target = _positive_decimal(target_servings, field="target_servings")
    factor = target / detail.version.base_servings
    return replace(
        detail,
        ingredients=tuple(
            replace(ingredient, quantity=ingredient.quantity * factor)
            for ingredient in detail.ingredients
        ),
    )
