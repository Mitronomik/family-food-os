"""Canonical platform FoodIngredient catalogue domain types and validation."""

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from decimal import Decimal
import re
import unicodedata
from uuid import UUID

from app.domain.decimal_utils import parse_decimal, quantize_decimal, quantize_density
from app.domain.errors import DomainIssue, DomainIssueCode, DomainValidationError
from app.domain.units import UnitCode

_CANONICAL_CODE_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")
_CATEGORY_CODE_RE = re.compile(r"^[a-z][a-z0-9_]*$")
_ALLERGEN_CODE_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")
_LANGUAGE_CODE_RE = re.compile(r"^[a-z]{2,3}(?:-[A-Z]{2})?$")

EDIBLE_FRACTION_QUANT = Decimal("0.000001")
NUTRIENT_QUANT = Decimal("0.000001")
BASIS_QUANT = Decimal("0.001")
NUTRITION_BASIS_GRAMS = Decimal("100.000")
MAX_KCAL = Decimal("1000.000000")
MAX_MACRO_GRAMS = Decimal("100.000000")


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


def _required_text(value: object, *, field: str, maximum: int = 240) -> str:
    normalized = (
        " ".join(unicodedata.normalize("NFKC", value).strip().split())
        if isinstance(value, str)
        else ""
    )
    if not normalized:
        raise _issue(
            DomainIssueCode.REQUIRED_FIELD,
            f"{field} must not be empty.",
            field=field,
            value=value,
            next_action=f"Provide a non-empty {field}.",
        )
    if len(normalized) > maximum:
        raise _issue(
            DomainIssueCode.VALUE_OUT_OF_RANGE,
            f"{field} must be {maximum} characters or fewer.",
            field=field,
            value=value,
            next_action=f"Shorten {field}.",
        )
    return normalized


def _optional_code(value: object, *, field: str) -> str | None:
    if value is None:
        return None
    normalized = _required_text(value, field=field, maximum=80)
    if not _CATEGORY_CODE_RE.fullmatch(normalized):
        raise _issue(
            DomainIssueCode.INVALID_CODE,
            f"{field} must be a normalized lowercase code.",
            field=field,
            value=value,
            next_action="Use lowercase ASCII letters, digits and underscores.",
        )
    return normalized


def normalize_unicode_search_key(value: object, *, field: str = "name") -> str:
    """Build a persisted Cyrillic-safe key without relying on SQLite NOCASE."""

    normalized = _required_text(value, field=field)
    return " ".join(normalized.casefold().replace("ё", "е").split())


def normalize_canonical_code(value: object) -> str:
    normalized = _required_text(value, field="canonical_code", maximum=80)
    if not _CANONICAL_CODE_RE.fullmatch(normalized):
        raise _issue(
            DomainIssueCode.INVALID_CODE,
            "canonical_code must be a stable uppercase platform code.",
            field="canonical_code",
            value=value,
            next_action="Use uppercase ASCII letters, digits and underscores.",
        )
    return normalized


def normalize_category_code(value: object) -> str:
    normalized = _optional_code(value, field="category_code")
    assert normalized is not None
    return normalized


def normalize_food_unit(value: object) -> UnitCode:
    try:
        unit = value if isinstance(value, UnitCode) else UnitCode(value)
    except (TypeError, ValueError) as exc:
        raise _issue(
            DomainIssueCode.INVALID_UNIT,
            "FoodIngredient default_unit is invalid.",
            field="default_unit",
            value=value,
            next_action="Use g, ml or pcs.",
        ) from exc
    if unit not in {UnitCode.GRAM, UnitCode.MILLILITER, UnitCode.PIECE}:
        raise _issue(
            DomainIssueCode.INVALID_UNIT,
            "Percent is not a FoodIngredient default unit.",
            field="default_unit",
            value=value,
            next_action="Use g, ml or pcs.",
        )
    return unit


def normalize_utc_instant(value: object, *, field: str) -> datetime:
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
            next_action="Provide an aware datetime; authoritative instants use UTC.",
        )
    return value.astimezone(timezone.utc)


def _uuid4(value: object, *, field: str) -> UUID:
    if not isinstance(value, UUID) or value.version != 4:
        raise _issue(
            DomainIssueCode.INVALID_IDENTIFIER,
            f"{field} must be a UUIDv4 value.",
            field=field,
            value=value,
            next_action="Generate the identifier application-side with UUIDv4.",
        )
    return value


def _optional_density(value: object) -> Decimal | None:
    if value is None:
        return None
    parsed = parse_decimal(value, field="density_g_per_ml")  # type: ignore[arg-type]
    if parsed <= 0:
        raise _issue(
            DomainIssueCode.ZERO_OR_NEGATIVE_DENSITY,
            "density_g_per_ml must be greater than zero when supplied.",
            field="density_g_per_ml",
            value=value,
            next_action="Provide a positive density or null when unknown.",
        )
    density = quantize_density(parsed, field="density_g_per_ml")
    if density <= 0:
        raise _issue(
            DomainIssueCode.ZERO_OR_NEGATIVE_DENSITY,
            "density_g_per_ml is below the supported positive precision.",
            field="density_g_per_ml",
            value=value,
            next_action="Provide a positive density of at least 0.0001 or null.",
        )
    return density


def _optional_edible_fraction(value: object) -> Decimal | None:
    if value is None:
        return None
    parsed = parse_decimal(value, field="edible_fraction")  # type: ignore[arg-type]
    if parsed <= 0 or parsed > 1:
        raise _issue(
            DomainIssueCode.VALUE_OUT_OF_RANGE,
            "edible_fraction must be greater than zero and no greater than one.",
            field="edible_fraction",
            value=value,
            next_action="Provide a fraction such as 0.8, 1, or null when unknown.",
        )
    fraction = quantize_decimal(parsed, EDIBLE_FRACTION_QUANT, field="edible_fraction")
    if fraction <= 0:
        raise _issue(
            DomainIssueCode.VALUE_OUT_OF_RANGE,
            "edible_fraction is below the supported positive precision.",
            field="edible_fraction",
            value=value,
            next_action="Provide a fraction of at least 0.000001 or null.",
        )
    return fraction


def normalize_allergen_code(value: object) -> str:
    normalized = _required_text(value, field="allergen_code", maximum=80)
    if not _ALLERGEN_CODE_RE.fullmatch(normalized):
        raise _issue(
            DomainIssueCode.INVALID_CODE,
            "allergen_code must be a normalized uppercase code.",
            field="allergen_code",
            value=value,
            next_action="Use uppercase ASCII letters, digits and underscores.",
        )
    return normalized


def _bounded_nutrient(value: object, *, field: str, maximum: Decimal) -> Decimal:
    parsed = parse_decimal(value, field=field)  # type: ignore[arg-type]
    if parsed < 0 or parsed > maximum:
        raise _issue(
            DomainIssueCode.VALUE_OUT_OF_RANGE,
            f"{field} is outside the supported nutrition sanity bound.",
            field=field,
            value=value,
            next_action=f"Provide a value from 0 through {maximum}.",
        )
    return quantize_decimal(parsed, NUTRIENT_QUANT, field=field)


@dataclass(frozen=True)
class FoodIngredient:
    id: UUID
    canonical_code: str
    canonical_name: str
    canonical_name_key: str
    category_code: str
    default_unit: UnitCode
    density_g_per_ml: Decimal | None
    edible_fraction: Decimal | None
    allergens_reviewed: bool
    allergen_codes: tuple[str, ...]
    storage_profile_code: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _uuid4(self.id, field="id"))
        object.__setattr__(
            self, "canonical_code", normalize_canonical_code(self.canonical_code)
        )
        name = _required_text(self.canonical_name, field="canonical_name")
        object.__setattr__(self, "canonical_name", name)
        expected_key = normalize_unicode_search_key(name, field="canonical_name")
        supplied_key = normalize_unicode_search_key(
            self.canonical_name_key, field="canonical_name_key"
        )
        if supplied_key != expected_key:
            raise _issue(
                DomainIssueCode.INVALID_CODE,
                "canonical_name_key must equal the deterministic canonical name key.",
                field="canonical_name_key",
                value=self.canonical_name_key,
                next_action=f"Use {expected_key!r}.",
            )
        object.__setattr__(self, "canonical_name_key", expected_key)
        object.__setattr__(
            self, "category_code", normalize_category_code(self.category_code)
        )
        object.__setattr__(self, "default_unit", normalize_food_unit(self.default_unit))
        object.__setattr__(
            self, "density_g_per_ml", _optional_density(self.density_g_per_ml)
        )
        object.__setattr__(
            self, "edible_fraction", _optional_edible_fraction(self.edible_fraction)
        )
        if type(self.allergens_reviewed) is not bool:
            raise _issue(
                DomainIssueCode.INVALID_BOOLEAN,
                "allergens_reviewed must be boolean.",
                field="allergens_reviewed",
                value=self.allergens_reviewed,
                next_action="Provide true or false.",
            )
        codes = tuple(
            sorted({normalize_allergen_code(code) for code in self.allergen_codes})
        )
        if codes and not self.allergens_reviewed:
            raise _issue(
                DomainIssueCode.INVALID_BOOLEAN,
                "Allergen codes require allergens_reviewed=true.",
                field="allergens_reviewed",
                value=self.allergens_reviewed,
                next_action="Mark the ingredient reviewed or remove unreviewed codes.",
            )
        object.__setattr__(self, "allergen_codes", codes)
        object.__setattr__(
            self,
            "storage_profile_code",
            _optional_code(self.storage_profile_code, field="storage_profile_code"),
        )
        if type(self.is_active) is not bool:
            raise _issue(
                DomainIssueCode.INVALID_BOOLEAN,
                "is_active must be boolean.",
                field="is_active",
                value=self.is_active,
                next_action="Provide true or false.",
            )
        created_at = normalize_utc_instant(self.created_at, field="created_at")
        updated_at = normalize_utc_instant(self.updated_at, field="updated_at")
        if updated_at < created_at:
            raise _issue(
                DomainIssueCode.INVALID_DATE,
                "updated_at must not precede created_at.",
                field="updated_at",
                value=updated_at,
                next_action="Use an update instant on or after creation.",
            )
        object.__setattr__(self, "created_at", created_at)
        object.__setattr__(self, "updated_at", updated_at)


@dataclass(frozen=True)
class IngredientAlias:
    id: UUID
    food_ingredient_id: UUID
    alias: str
    alias_key: str
    language_code: str | None
    created_at: datetime

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _uuid4(self.id, field="id"))
        object.__setattr__(
            self,
            "food_ingredient_id",
            _uuid4(self.food_ingredient_id, field="food_ingredient_id"),
        )
        alias = _required_text(self.alias, field="alias")
        object.__setattr__(self, "alias", alias)
        expected_key = normalize_unicode_search_key(alias, field="alias")
        supplied_key = normalize_unicode_search_key(self.alias_key, field="alias_key")
        if supplied_key != expected_key:
            raise _issue(
                DomainIssueCode.INVALID_CODE,
                "alias_key must equal the deterministic alias key.",
                field="alias_key",
                value=self.alias_key,
                next_action=f"Use {expected_key!r}.",
            )
        object.__setattr__(self, "alias_key", expected_key)
        if self.language_code is not None:
            language_code = _required_text(
                self.language_code, field="language_code", maximum=12
            )
            if not _LANGUAGE_CODE_RE.fullmatch(language_code):
                raise _issue(
                    DomainIssueCode.INVALID_CODE,
                    "language_code is invalid.",
                    field="language_code",
                    value=self.language_code,
                    next_action="Use a code such as ru or en.",
                )
            object.__setattr__(self, "language_code", language_code)
        object.__setattr__(
            self,
            "created_at",
            normalize_utc_instant(self.created_at, field="created_at"),
        )


@dataclass(frozen=True)
class FoodNutritionProfile:
    id: UUID
    food_ingredient_id: UUID
    basis_grams: Decimal
    kcal: Decimal
    protein_g: Decimal
    fat_g: Decimal
    carbohydrates_g: Decimal
    fiber_g: Decimal | None
    source_name: str
    source_id: str
    source_version: str
    source_data_type: str | None
    verified_at: datetime
    estimated: bool | None
    is_current: bool
    created_at: datetime

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _uuid4(self.id, field="id"))
        object.__setattr__(
            self,
            "food_ingredient_id",
            _uuid4(self.food_ingredient_id, field="food_ingredient_id"),
        )
        basis = quantize_decimal(self.basis_grams, BASIS_QUANT, field="basis_grams")
        if basis != NUTRITION_BASIS_GRAMS:
            raise _issue(
                DomainIssueCode.VALUE_OUT_OF_RANGE,
                "PR3 nutrition profiles must use a 100 g edible-portion basis.",
                field="basis_grams",
                value=self.basis_grams,
                next_action="Use basis_grams=100.",
            )
        object.__setattr__(self, "basis_grams", basis)
        object.__setattr__(
            self, "kcal", _bounded_nutrient(self.kcal, field="kcal", maximum=MAX_KCAL)
        )
        for field in ("protein_g", "fat_g", "carbohydrates_g"):
            object.__setattr__(
                self,
                field,
                _bounded_nutrient(
                    getattr(self, field), field=field, maximum=MAX_MACRO_GRAMS
                ),
            )
        if self.fiber_g is not None:
            object.__setattr__(
                self,
                "fiber_g",
                _bounded_nutrient(
                    self.fiber_g, field="fiber_g", maximum=MAX_MACRO_GRAMS
                ),
            )
        for field in ("source_name", "source_id", "source_version"):
            object.__setattr__(
                self, field, _required_text(getattr(self, field), field=field)
            )
        if self.source_data_type is not None:
            object.__setattr__(
                self,
                "source_data_type",
                _required_text(
                    self.source_data_type, field="source_data_type", maximum=80
                ),
            )
        object.__setattr__(
            self,
            "verified_at",
            normalize_utc_instant(self.verified_at, field="verified_at"),
        )
        if self.estimated is not None and type(self.estimated) is not bool:
            raise _issue(
                DomainIssueCode.INVALID_BOOLEAN,
                "estimated must be boolean or null.",
                field="estimated",
                value=self.estimated,
                next_action="Provide true, false or null.",
            )
        if type(self.is_current) is not bool:
            raise _issue(
                DomainIssueCode.INVALID_BOOLEAN,
                "is_current must be boolean.",
                field="is_current",
                value=self.is_current,
                next_action="Provide true or false.",
            )
        object.__setattr__(
            self,
            "created_at",
            normalize_utc_instant(self.created_at, field="created_at"),
        )

    @property
    def provenance_key(self) -> tuple[UUID, str, str, str]:
        return (
            self.food_ingredient_id,
            self.source_name,
            self.source_id,
            self.source_version,
        )

    def snapshot_values(self) -> tuple[object, ...]:
        return (
            self.basis_grams,
            self.kcal,
            self.protein_g,
            self.fat_g,
            self.carbohydrates_g,
            self.fiber_g,
            self.source_data_type,
            self.verified_at,
            self.estimated,
        )


def deactivate_food_ingredient(
    ingredient: FoodIngredient, *, updated_at: datetime
) -> FoodIngredient:
    return replace(ingredient, is_active=False, updated_at=updated_at)
