"""Immutable mass-authoritative composition snapshots; no catalogue selectors."""

from dataclasses import dataclass, fields, is_dataclass
from decimal import Context, Decimal, MAX_EMAX, MIN_EMIN, ROUND_HALF_UP, localcontext
from enum import StrEnum
import hashlib
import json
import re
from typing import Any
from uuid import UUID

from app.domain.nutrient_vector import NutrientDefinition, NutrientValue

CALCULATION_VERSION = "FOOD_COMPOSITION_V1"


def calculation_context() -> Context:
    return Context(prec=80, rounding=ROUND_HALF_UP, Emin=MIN_EMIN, Emax=MAX_EMAX)


def decimal_value(value: Decimal, *, positive: bool = True) -> None:
    if not isinstance(value, Decimal):
        raise TypeError("Требуется точное значение Decimal.")
    if not value.is_finite() or value < 0 or (positive and value == 0):
        raise ValueError("Требуется конечное допустимое значение массы или фактора.")


def exact_sum(values: tuple[Decimal, ...]) -> Decimal:
    """No rounding of finite input masses, even beyond the caller's precision."""
    if not values:
        return Decimal(0)
    exponent = min(int(v.as_tuple().exponent) for v in values)
    precision = max(v.adjusted() for v in values) - exponent + len(str(len(values))) + 2
    with localcontext(calculation_context()) as ctx:
        ctx.prec = max(precision, 1)
        return sum(values, Decimal(0))


def exact_product(a: Decimal, b: Decimal) -> Decimal:
    with localcontext(calculation_context()) as ctx:
        ctx.prec = len(a.as_tuple().digits) + len(b.as_tuple().digits) + 1
        return a * b


def identifier(value: UUID) -> None:
    if not isinstance(value, UUID):
        raise TypeError("Требуется идентификатор UUID.")


def code(value: str) -> None:
    if not isinstance(value, str) or not re.fullmatch(r"[A-Z][A-Z0-9_]*", value):
        raise ValueError("Требуется стабильный код проекта.")


def ordered(values: tuple[Any, ...]) -> tuple[Any, ...]:
    result = tuple(sorted(values, key=lambda item: item.position))
    if any(type(v.position) is not int or v.position < 0 for v in result):
        raise ValueError("Позиция должна быть целым неотрицательным числом.")
    if len({v.position for v in result}) != len(result) or len(
        {v.id for v in result}
    ) != len(result):
        raise ValueError("Идентификатор или позиция узла повторяется.")
    return result


class MassState(StrEnum):
    RAW = "RAW"
    INPUT = "INPUT"
    DRAINED = "DRAINED"
    COOKED = "COOKED"
    YIELDED = "YIELDED"
    GROSS_PURCHASE = "GROSS_PURCHASE"
    PREPARED_PRE_COOK = "PREPARED_PRE_COOK"
    DISCARD = "DISCARD"
    SERVING = "SERVING"


class CompositionKind(StrEnum):
    ATOMIC = "ATOMIC"
    COMPOSITE = "COMPOSITE"


class CompositionStatus(StrEnum):
    COMPLETE = "COMPLETE"
    PARTIAL = "PARTIAL"
    INCOMPLETE = "INCOMPLETE"


@dataclass(frozen=True)
class CompositionProvenance:
    source: str
    source_version: str
    evidence_reference: str
    review_reference: str

    def __post_init__(self) -> None:
        if any(
            not isinstance(getattr(self, f.name), str)
            or not getattr(self, f.name).strip()
            for f in fields(self)
        ):
            raise ValueError("Нужны источник, версия, доказательство и проверка.")


@dataclass(frozen=True)
class YieldModel:
    id: UUID
    version: int
    factor: Decimal
    input_state: MassState
    output_state: MassState
    provenance: CompositionProvenance

    def __post_init__(self) -> None:
        versioned(self)
        decimal_value(self.factor)
        states(self)


@dataclass(frozen=True)
class RetentionValue:
    nutrient_code: str
    factor: Decimal
    provenance: CompositionProvenance

    def __post_init__(self) -> None:
        code(self.nutrient_code)
        decimal_value(self.factor, positive=False)
        if not isinstance(self.provenance, CompositionProvenance):
            raise TypeError("Требуется происхождение фактора сохранения.")


@dataclass(frozen=True)
class NutrientRetentionProfile:
    id: UUID
    version: int
    input_state: MassState
    output_state: MassState
    provenance: CompositionProvenance
    values: tuple[RetentionValue, ...]

    def __post_init__(self) -> None:
        versioned(self)
        states(self)
        values = tuple(sorted(self.values, key=lambda v: v.nutrient_code))
        if len({v.nutrient_code for v in values}) != len(values):
            raise ValueError("Фактор нутриента повторяется.")
        object.__setattr__(self, "values", values)


@dataclass(frozen=True)
class FoodTransformation:
    id: UUID
    version: int
    transformation_type: str
    input_state: MassState
    output_state: MassState
    provenance: CompositionProvenance
    yield_model_id: UUID | None = None
    retention_profile_id: UUID | None = None

    def __post_init__(self) -> None:
        versioned(self)
        states(self)
        code(self.transformation_type)
        for value in (self.yield_model_id, self.retention_profile_id):
            if value is not None:
                identifier(value)


def versioned(value: Any) -> None:
    identifier(value.id)
    if type(value.version) is not int or value.version < 1:
        raise ValueError("Версия должна быть положительным целым числом.")
    if not isinstance(value.provenance, CompositionProvenance):
        raise TypeError("Требуется проверяемое происхождение версии.")


def states(value: Any) -> None:
    for name in ("input_state", "output_state"):
        object.__setattr__(value, name, MassState(getattr(value, name)))


@dataclass(frozen=True)
class CompositionNode:
    id: UUID
    position: int
    child_version_id: UUID
    input_mass_g: Decimal
    mass_state: MassState

    def __post_init__(self) -> None:
        identifier(self.id)
        identifier(self.child_version_id)
        decimal_value(self.input_mass_g)
        object.__setattr__(self, "mass_state", MassState(self.mass_state))
        ordered((self,))


@dataclass(frozen=True)
class CompositionStep:
    id: UUID
    position: int
    transformation_id: UUID

    def __post_init__(self) -> None:
        identifier(self.id)
        identifier(self.transformation_id)
        ordered((self,))


@dataclass(frozen=True)
class FoodCompositionVersion:
    id: UUID
    food_ingredient_id: UUID
    version: int
    kind: CompositionKind
    input_state: MassState
    provenance: CompositionProvenance
    profile_id: UUID | None = None
    nodes: tuple[CompositionNode, ...] = ()
    steps: tuple[CompositionStep, ...] = ()

    def __post_init__(self) -> None:
        versioned(self)
        identifier(self.food_ingredient_id)
        object.__setattr__(self, "kind", CompositionKind(self.kind))
        object.__setattr__(self, "input_state", MassState(self.input_state))
        object.__setattr__(self, "nodes", ordered(tuple(self.nodes)))
        object.__setattr__(self, "steps", ordered(tuple(self.steps)))
        if self.kind == CompositionKind.ATOMIC:
            if self.profile_id is None or self.nodes:
                raise ValueError(
                    "Атомарный состав требует один профиль без дочерних узлов."
                )
            identifier(self.profile_id)
        elif self.profile_id is not None or not self.nodes:
            raise ValueError("Точный состав требует компоненты без прямого профиля.")


def snapshot_json(value: Any) -> str:
    """Canonical serialization, also used to verify complete persisted sets."""

    def encode(item: Any) -> Any:
        if is_dataclass(item) and not isinstance(item, type):
            return {f.name: encode(getattr(item, f.name)) for f in fields(item)}
        if isinstance(item, UUID):
            return str(item)
        if isinstance(item, Decimal):
            return format(item, "f")
        if isinstance(item, (list, tuple)):
            return [encode(v) for v in item]
        return item

    return json.dumps(
        encode(value), ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )


def snapshot_digest(value: Any) -> str:
    return hashlib.sha256(snapshot_json(value).encode()).hexdigest()


class CompositionUnavailableError(ValueError):
    def __init__(self, issue_code: str) -> None:
        self.issue_code = issue_code
        super().__init__(
            "Расчёт состава недоступен: нарушена целостность или отсутствует обязательная зависимость."
        )


@dataclass(frozen=True)
class CompositionIssue:
    code: str
    composition_id: UUID
    nutrient_code: str | None = None
    transformation_id: UUID | None = None


@dataclass(frozen=True)
class CalculatedNutrient:
    definition: NutrientDefinition
    amount: Decimal | None
    per_100_g: Decimal | None

    @property
    def availability(self) -> str:
        return (
            "AVAILABLE"
            if self.amount is not None and self.per_100_g is not None
            else "UNKNOWN"
        )


@dataclass(frozen=True)
class AtomicEvidence:
    composition_id: UUID
    profile_id: UUID
    food_ingredient_id: UUID
    basis_grams: Decimal
    registry_version: str
    values: tuple[NutrientValue, ...]
    observations_json: str


@dataclass(frozen=True)
class StageEvidence:
    composition_id: UUID
    transformation_id: UUID | None
    mass_g: Decimal | None
    mass_state: MassState
    amounts: tuple[tuple[str, Decimal | None], ...]


@dataclass(frozen=True)
class CompositionResult:
    root_version_id: UUID
    calculation_version: str
    requested_nutrient_codes: tuple[str, ...]
    input_mass_g: Decimal
    output_mass_g: Decimal | None
    output_mass_state: MassState
    concentration_basis_g: Decimal
    nutrients: tuple[CalculatedNutrient, ...]
    status: CompositionStatus
    issues: tuple[CompositionIssue, ...]
    compositions: tuple[FoodCompositionVersion, ...]
    atomic_evidence: tuple[AtomicEvidence, ...]
    transformations: tuple[FoodTransformation, ...]
    yield_models: tuple[YieldModel, ...]
    retention_profiles: tuple[NutrientRetentionProfile, ...]
    stages: tuple[StageEvidence, ...]
