"""Versioned interpretation of reviewed source observations, without publication.

This policy cannot establish rights, food-form equivalence or retention. Callers
must resolve those independently. Energy observations are never reconstructed
from macros, and total carbohydrate is never converted into available carbohydrate.
"""

from dataclasses import dataclass
from decimal import Context, Decimal, ROUND_HALF_UP, localcontext
from enum import Enum
import re


class NutrientKind(str, Enum):
    PROTEIN = "protein"
    FAT = "fat"
    FIBRE = "fibre"
    AVAILABLE_CARBOHYDRATE = "available_carbohydrate"
    TOTAL_CARBOHYDRATE = "total_carbohydrate_including_fibre"
    PUBLISHED_ENERGY = "published_energy"
    COMPUTED_ENERGY = "computed_energy"


class ObservationMethod(str, Enum):
    ANALYTICAL = "analytical"
    PUBLISHED = "published_method_unspecified"
    AVAILABLE_SUMMATION = "available_summation"
    AVAILABLE_BY_DIFFERENCE = "available_by_difference_excluding_fibre"
    AVAILABLE_PUBLISHED_ROW_UNSPECIFIED = "available_published_row_method_unspecified"
    TOTAL_BY_DIFFERENCE = "total_by_difference_including_fibre"
    COMPUTED = "computed_with_separate_method_reference"
    UNSUPPORTED = "unsupported"


class ObservationState(str, Enum):
    VALUE = "value"
    MISSING = "missing"
    HELD = "held_source_observation"
    BELOW_DETECTION = "below_detection"


class RussianNutritionPolicy(str, Enum):
    STRICT_V1 = "RU_SOURCE_NATIVE_STRICT_V1"
    PUBLISHED_ZERO_ESTIMATE_V1 = "RU_SOURCE_NATIVE_PUBLISHED_ZERO_ESTIMATE_V1"


def _decimal(value: Decimal, *, positive: bool = False) -> None:
    if not isinstance(value, Decimal):
        raise TypeError("Значение должно иметь тип Decimal.")
    if not value.is_finite() or value < 0 or value > Decimal("1e24"):
        raise ValueError("Значение должно быть конечным, неотрицательным и допустимым.")
    if positive and value < Decimal("1e-18"):
        raise ValueError("Масса должна быть положительной и допустимой.")
    if len(value.as_tuple().digits) > 40 or value.as_tuple().exponent < -40:
        raise ValueError("Точность исходного значения превышает допустимую.")


@dataclass(frozen=True)
class ObservationSource:
    source_id: str
    release: str
    locator: str
    observation_id: str
    food_form_id: str
    method_reference: str

    def __post_init__(self) -> None:
        for value in vars(self).values():
            if not isinstance(value, str) or not value.strip():
                raise ValueError(
                    "Нужны источник, версия, место, форма и основание метода."
                )


@dataclass(frozen=True)
class SourceObservation:
    nutrient: NutrientKind
    method: ObservationMethod
    state: ObservationState
    amount: Decimal | None
    unit: str
    basis_g: Decimal
    source: ObservationSource
    # Exact source token retained for audit, including a printed analytical zero.
    source_literal: str | None = None
    basis_part: str = "edible"
    source_estimated: bool | None = None

    def __post_init__(self) -> None:
        for value, enum in (
            (self.nutrient, NutrientKind),
            (self.method, ObservationMethod),
            (self.state, ObservationState),
        ):
            if not isinstance(value, enum):
                raise TypeError("Нужно типизированное определение наблюдения.")
        if not isinstance(self.source, ObservationSource):
            raise TypeError("Нужно проверяемое происхождение наблюдения.")
        if self.source_estimated is not None and not isinstance(
            self.source_estimated, bool
        ):
            raise TypeError("Признак оценки должен быть bool или None.")
        _decimal(self.basis_g, positive=True)
        energy = self.nutrient in (
            NutrientKind.PUBLISHED_ENERGY,
            NutrientKind.COMPUTED_ENERGY,
        )
        if self.unit != ("kcal" if energy else "g") or self.basis_part != "edible":
            raise ValueError("Нужны каноническая единица и масса съедобной части.")
        if self.state == ObservationState.VALUE:
            if self.amount is None:
                raise ValueError("Для числового наблюдения нужно значение.")
            _decimal(self.amount)
        elif self.amount is not None:
            raise ValueError("Неизвестное значение нельзя подменять числом.")
        if self.source_literal is not None and not isinstance(self.source_literal, str):
            raise TypeError("Исходное обозначение должно быть текстом.")


@dataclass(frozen=True)
class InterpretedObservation:
    observation: SourceObservation
    policy: RussianNutritionPolicy
    amount: Decimal | None
    estimated: bool
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class ObservationContribution:
    observation: SourceObservation
    edible_input_mass_g: Decimal
    food_form_id: str

    def __post_init__(self) -> None:
        _decimal(self.edible_input_mass_g, positive=True)
        if self.food_form_id != self.observation.source.food_form_id:
            raise ValueError("Форма взвешенного продукта не соответствует профилю.")


@dataclass(frozen=True)
class MethodologyTotal:
    nutrient: NutrientKind
    unit: str
    policy: RussianNutritionPolicy
    amount: Decimal | None
    estimated: bool
    # Contributions keep source, basis, mass, method and original missing state.
    contributions: tuple[ObservationContribution, ...]
    interpretations: tuple[InterpretedObservation, ...]
    warnings: tuple[str, ...]


def evaluate_observation(
    observation: SourceObservation,
    policy: RussianNutritionPolicy = RussianNutritionPolicy.STRICT_V1,
) -> InterpretedObservation:
    """Interpret without relabelling the source method or overwriting its value."""
    if not isinstance(policy, RussianNutritionPolicy):
        raise TypeError("Нужна поддерживаемая версия политики.")
    if not isinstance(observation, SourceObservation):
        raise TypeError("Нужно типизированное наблюдение.")
    kind, method = observation.nutrient, observation.method
    allowed = {
        NutrientKind.AVAILABLE_CARBOHYDRATE: {
            ObservationMethod.AVAILABLE_SUMMATION,
            ObservationMethod.AVAILABLE_BY_DIFFERENCE,
            ObservationMethod.AVAILABLE_PUBLISHED_ROW_UNSPECIFIED,
        },
        NutrientKind.TOTAL_CARBOHYDRATE: {ObservationMethod.TOTAL_BY_DIFFERENCE},
        NutrientKind.PUBLISHED_ENERGY: {ObservationMethod.PUBLISHED},
        NutrientKind.COMPUTED_ENERGY: {ObservationMethod.COMPUTED},
    }.get(kind, {ObservationMethod.ANALYTICAL, ObservationMethod.PUBLISHED})
    warnings = []
    amount = observation.amount
    estimated = observation.source_estimated is True
    if observation.source_estimated is True:
        warnings.append("SOURCE_ESTIMATED")
    elif observation.source_estimated is None:
        warnings.append("SOURCE_ESTIMATION_STATUS_UNKNOWN")
    if observation.state == ObservationState.HELD:
        warnings.append("HELD_SOURCE_OBSERVATION")
    if method not in allowed:
        amount = None
        warnings.append("UNSUPPORTED_METHOD")
    elif observation.state == ObservationState.MISSING:
        warnings.append("MISSING_OBSERVATION")
    elif observation.state == ObservationState.BELOW_DETECTION:
        warnings.append("BELOW_DETECTION_LIMIT_UNSPECIFIED")
        literal = observation.source_literal
        printed_zero = (
            literal is not None
            and re.fullmatch(r"0(?:[.,]0+)?", literal.strip()) is not None
        )
        if policy == RussianNutritionPolicy.PUBLISHED_ZERO_ESTIMATE_V1 and printed_zero:
            amount, estimated = Decimal("0"), True
            warnings.append("PUBLISHED_ZERO_ESTIMATE")
    if method == ObservationMethod.AVAILABLE_PUBLISHED_ROW_UNSPECIFIED:
        warnings.append("ROW_METHOD_UNSPECIFIED")
    if method == ObservationMethod.AVAILABLE_BY_DIFFERENCE:
        warnings.append("AVAILABLE_BY_DIFFERENCE")
    return InterpretedObservation(
        observation, policy, amount, estimated, tuple(warnings)
    )


def aggregate_observations(
    contributions: tuple[ObservationContribution, ...],
    policy: RussianNutritionPolicy = RussianNutritionPolicy.STRICT_V1,
) -> MethodologyTotal:
    """Scale reviewed matching input forms; do not apply cooking/yield factors.

    An unknown contributing value makes the total unknown. This is an input-mass
    sum, not an assertion about the composition of a cooked dish or its final mass.
    """
    contributions = tuple(contributions)
    if not contributions:
        raise ValueError("Для суммы нужны наблюдения.")
    first = contributions[0].observation
    if any(
        c.observation.nutrient != first.nutrient or c.observation.unit != first.unit
        for c in contributions
    ):
        raise ValueError("Нельзя смешивать разные определения нутриентов.")
    interpretations = tuple(
        evaluate_observation(c.observation, policy) for c in contributions
    )
    amount = None
    if all(i.amount is not None for i in interpretations):
        with localcontext(Context(prec=80, rounding=ROUND_HALF_UP)):
            amount = sum(
                (
                    i.amount * c.edible_input_mass_g / c.observation.basis_g
                    for c, i in zip(contributions, interpretations)
                ),
                Decimal("0"),
            )
            amount = amount.quantize(Decimal("0.000001"))
    warnings = tuple(sorted({w for i in interpretations for w in i.warnings}))
    return MethodologyTotal(
        first.nutrient,
        first.unit,
        policy,
        amount,
        any(i.estimated for i in interpretations),
        contributions,
        interpretations,
        warnings,
    )
