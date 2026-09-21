"""Immutable sparse values owned by the existing nutrition profile snapshot."""

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import json
import re
from uuid import UUID

from app.domain.food_ingredients import FoodNutritionProfile
from app.domain.nutrition_methodology import ObservationMethod

V2_VALUE_EVIDENCE_SCHEMA = "FFO_NUTRIENT_VALUE_EVIDENCE_V2"
V2_REGISTRY_VERSION = "RU_NUTRIENT_REGISTRY_V2"


class NutrientVectorUnavailableError(ValueError):
    """No complete audited vector is available; this is not an empty vector."""


class NutrientValueEvidenceError(ValueError):
    """Persisted source evidence is malformed or contradicts its vector row."""


@dataclass(frozen=True)
class NutrientDefinition:
    code: str
    display_name_ru: str
    unit: str
    registry_version: str
    definition_text_ru: str | None = None
    definition_kind: str | None = None

    def __post_init__(self) -> None:
        if not re.fullmatch(r"[A-Z][A-Z0-9_]*", self.code):
            raise ValueError("Нужен стабильный код нутриента проекта.")
        if not re.search(r"[А-Яа-яЁё]", self.display_name_ru):
            raise ValueError("Нужно русское название нутриента.")
        if self.unit not in {"kcal", "g", "mg", "µg"} or not self.registry_version:
            raise ValueError("Нужны каноническая единица и версия реестра.")
        if self.definition_text_ru is not None and (
            not isinstance(self.definition_text_ru, str)
            or not self.definition_text_ru.strip()
        ):
            raise ValueError("Определение нутриента должно быть непустым текстом.")
        if self.definition_kind is not None and (
            not isinstance(self.definition_kind, str)
            or not self.definition_kind.strip()
        ):
            raise ValueError("Тип определения нутриента должен быть непустым.")

    @property
    def semantic_identity(self) -> tuple[str, str]:
        return (self.registry_version, self.code)


@dataclass(frozen=True)
class NutrientProvenance:
    registry_version: str
    audit_identity: str
    source_name: str
    source_food_id: str
    source_release: str
    source_data_type: str | None
    source_nutrient_id: str
    source_nutrient_name: str
    source_nutrient_nbr: str | None
    source_unit: str
    source_amount: Decimal
    source_observation_id: str
    source_derivation_id: str | None
    mapping_status: str
    estimated: bool | None
    evidence_json: str
    origin: str = "SOURCE_COMPONENT_CONFIRMED"


@dataclass(frozen=True)
class DecodedV2ValueEvidence:
    provenance: NutrientProvenance
    method: ObservationMethod
    canonical_code: str
    definition_reference: str
    source_locator: str


def _strict_json_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise NutrientValueEvidenceError(
                f"Повторное поле в доказательстве нутриента V2: {key}."
            )
        result[key] = value
    return result


def _exact_keys(value: object, expected: set[str], *, label: str) -> dict:
    if not isinstance(value, dict) or set(value) != expected:
        raise NutrientValueEvidenceError(
            f"Доказательство нутриента V2 имеет неверный контракт {label}."
        )
    return value


def _text(value: object, *, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise NutrientValueEvidenceError(
            f"Доказательство нутриента V2 не содержит {label}."
        )
    return value


def _optional_text(value: object, *, label: str) -> str | None:
    if value is None:
        return None
    return _text(value, label=label)


def _canonical_decimal(value: object) -> Decimal:
    if not isinstance(value, str) or not value or value.startswith("-"):
        raise NutrientValueEvidenceError(
            "Исходное значение V2 должно быть неотрицательной Decimal-строкой."
        )
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise NutrientValueEvidenceError(
            "Исходное значение V2 не является Decimal."
        ) from exc
    if not parsed.is_finite() or parsed < 0 or format(parsed, "f") != value:
        raise NutrientValueEvidenceError(
            "Исходное значение V2 должно быть канонической Decimal-строкой."
        )
    return parsed


def decode_v2_value_evidence(
    evidence_json: str,
    *,
    profile: FoodNutritionProfile,
    expected_registry_version: str,
    expected_nutrient_code: str,
    expected_amount: Decimal,
) -> DecodedV2ValueEvidence:
    """Decode the frozen source-neutral V2 evidence envelope fail-closed."""

    if expected_registry_version != V2_REGISTRY_VERSION:
        raise NutrientValueEvidenceError("Неверная версия реестра для V2 evidence.")
    try:
        payload = json.loads(evidence_json, object_pairs_hook=_strict_json_object)
    except (TypeError, json.JSONDecodeError) as exc:
        raise NutrientValueEvidenceError(
            "Доказательство нутриента V2 не является валидным JSON."
        ) from exc
    top = _exact_keys(
        payload,
        {
            "schema_version",
            "registry_version",
            "method_code",
            "origin",
            "observation",
            "mapping",
        },
        label="верхнего уровня",
    )
    if top["schema_version"] != V2_VALUE_EVIDENCE_SCHEMA:
        raise NutrientValueEvidenceError("Неизвестная схема доказательства нутриента V2.")
    if top["registry_version"] != expected_registry_version:
        raise NutrientValueEvidenceError(
            "Версия evidence не совпадает с версией снимка нутриентов."
        )
    if top["origin"] != "SOURCE_COMPONENT_CONFIRMED":
        raise NutrientValueEvidenceError(
            "Числовое значение V2 требует подтверждённый исходный компонент."
        )
    try:
        method = ObservationMethod(_text(top["method_code"], label="method_code"))
    except ValueError as exc:
        raise NutrientValueEvidenceError("Неизвестный method_code V2.") from exc
    if method is ObservationMethod.UNSUPPORTED:
        raise NutrientValueEvidenceError(
            "Числовое значение V2 не может иметь unsupported method_code."
        )

    observation = _exact_keys(
        top["observation"],
        {
            "audit_identity",
            "profile_source_name",
            "profile_source_id",
            "profile_source_version",
            "profile_source_data_type",
            "source_component_id",
            "source_component_name",
            "source_unit",
            "source_value",
            "source_observation_id",
            "source_derivation_id",
            "source_locator",
            "uncertainty",
        },
        label="observation",
    )
    mapping = _exact_keys(
        top["mapping"],
        {"canonical_code", "mapping_status", "definition_reference"},
        label="mapping",
    )

    if mapping["canonical_code"] != expected_nutrient_code:
        raise NutrientValueEvidenceError(
            "Код нутриента evidence не совпадает с сохраняемым значением."
        )
    if observation["profile_source_name"] != profile.source_name:
        raise NutrientValueEvidenceError("Источник evidence не совпадает с профилем.")
    if observation["profile_source_id"] != profile.source_id:
        raise NutrientValueEvidenceError(
            "Идентификатор источника evidence не совпадает с профилем."
        )
    if observation["profile_source_version"] != profile.source_version:
        raise NutrientValueEvidenceError(
            "Версия источника evidence не совпадает с профилем."
        )
    if observation["profile_source_data_type"] != profile.source_data_type:
        raise NutrientValueEvidenceError(
            "Тип источника evidence не совпадает с профилем."
        )

    source_amount = _canonical_decimal(observation["source_value"])
    if source_amount != expected_amount:
        raise NutrientValueEvidenceError(
            "Исходное значение evidence не совпадает с сохраняемым Decimal."
        )

    audit_identity = _text(observation["audit_identity"], label="audit_identity")
    source_component_id = _text(
        observation["source_component_id"], label="source_component_id"
    )
    source_component_name = _text(
        observation["source_component_name"], label="source_component_name"
    )
    source_unit = _text(observation["source_unit"], label="source_unit")
    source_observation_id = _text(
        observation["source_observation_id"], label="source_observation_id"
    )
    source_derivation_id = _optional_text(
        observation["source_derivation_id"], label="source_derivation_id"
    )
    source_locator = _text(observation["source_locator"], label="source_locator")
    _optional_text(observation["uncertainty"], label="uncertainty")
    mapping_status = _text(mapping["mapping_status"], label="mapping_status")
    definition_reference = _text(
        mapping["definition_reference"], label="definition_reference"
    )

    provenance = NutrientProvenance(
        registry_version=expected_registry_version,
        audit_identity=audit_identity,
        source_name=profile.source_name,
        source_food_id=profile.source_id,
        source_release=profile.source_version,
        source_data_type=profile.source_data_type,
        source_nutrient_id=source_component_id,
        source_nutrient_name=source_component_name,
        source_nutrient_nbr=None,
        source_unit=source_unit,
        source_amount=source_amount,
        source_observation_id=source_observation_id,
        source_derivation_id=source_derivation_id,
        mapping_status=mapping_status,
        estimated=profile.estimated,
        evidence_json=evidence_json,
        origin=top["origin"],
    )
    return DecodedV2ValueEvidence(
        provenance=provenance,
        method=method,
        canonical_code=expected_nutrient_code,
        definition_reference=definition_reference,
        source_locator=source_locator,
    )


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
