"""Immutable sparse values owned by the existing nutrition profile snapshot."""

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID
import re

from app.domain.food_ingredients import FoodNutritionProfile


class NutrientVectorUnavailableError(ValueError):
    """No complete audited vector is available; this is not an empty vector."""


@dataclass(frozen=True)
class NutrientDefinition:
    code: str
    display_name_ru: str
    unit: str
    registry_version: str

    def __post_init__(self) -> None:
        if not re.fullmatch(r"[A-Z][A-Z0-9_]*", self.code):
            raise ValueError("Нужен стабильный код нутриента проекта.")
        if not re.search(r"[А-Яа-яЁё]", self.display_name_ru):
            raise ValueError("Нужно русское название нутриента.")
        if self.unit not in {"kcal", "g", "mg", "µg"} or not self.registry_version:
            raise ValueError("Нужны каноническая единица и версия реестра.")


@dataclass(frozen=True)
class NutrientProvenance:
    registry_version: str
    audit_identity: str
    source_name: str
    source_food_id: str
    source_release: str
    source_data_type: str
    source_nutrient_id: str
    source_nutrient_name: str
    source_nutrient_nbr: str
    source_unit: str
    source_amount: Decimal
    source_observation_id: str
    source_derivation_id: str | None
    mapping_status: str
    estimated: bool | None
    evidence_json: str
    origin: str = "SOURCE_COMPONENT_CONFIRMED"


@dataclass(frozen=True)
class NutrientValue:
    definition: NutrientDefinition
    amount: Decimal
    provenance: NutrientProvenance

    def __post_init__(self) -> None:
        if not isinstance(self.amount, Decimal):
            raise TypeError("Количество нутриента должно иметь тип Decimal.")
        if not self.amount.is_finite() or self.amount < 0:
            raise ValueError(
                "Количество нутриента должно быть конечным и неотрицательным."
            )
        if self.definition.registry_version != self.provenance.registry_version:
            raise ValueError(
                "Версия определения не совпадает с происхождением значения."
            )


@dataclass(frozen=True)
class NutrientVector:
    profile: FoodNutritionProfile
    registry_version: str
    values: tuple[NutrientValue, ...]
    # Includes held zeros/absent/conflicting observations, never numeric placeholders.
    observations_json: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "values", tuple(self.values))
        codes = [value.definition.code for value in self.values]
        if len(codes) != len(set(codes)):
            raise ValueError("Нутриент повторяется в одном профиле.")
        for value in self.values:
            provenance = value.provenance
            if (
                provenance.registry_version != self.registry_version
                or provenance.source_name != self.profile.source_name
                or provenance.source_food_id != self.profile.source_id
                or provenance.source_release != self.profile.source_version
                or provenance.source_data_type != self.profile.source_data_type
            ):
                raise ValueError("Происхождение нутриента не соответствует профилю.")

    @property
    def profile_id(self) -> UUID:
        return self.profile.id

    def amount(self, nutrient_code: str) -> Decimal | None:
        return next(
            (v.amount for v in self.values if v.definition.code == nutrient_code), None
        )
