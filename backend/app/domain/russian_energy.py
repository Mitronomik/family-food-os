"""MR 2.3.1.0253-21 appendix 3 factors; separate from published energy.

This is a component accounting calculation, not an individual requirement or a
food-label compliance calculation. Unknown components never become zero.
"""

from dataclasses import dataclass
from decimal import Context, Decimal, ROUND_HALF_UP, localcontext
from enum import StrEnum
from types import MappingProxyType

VERSION = "RU_MR_2_3_1_0253_21_ENERGY_V1"
SOURCE = "МР 2.3.1.0253-21, приложение 3, печатная/PDF страница 58"


class EnergyComponent(StrEnum):
    PROTEIN = "protein"
    FAT = "fat"
    AVAILABLE_CARBOHYDRATE = "available_carbohydrate"
    EXPERIMENTAL_SUGARS = "experimental_mono_disaccharides"
    EXPERIMENTAL_STARCH = "experimental_starch"
    FIBRE = "fibre"
    POLYOLS_EXCLUDING_ERYTHRITOL = "polyols_excluding_erythritol_and_glycerol"
    ERYTHRITOL = "erythritol"
    ETHANOL = "ethanol"
    GLYCEROL = "glycerol"
    OTHER_ORGANIC_ACIDS = "other_organic_acids_excluding_named_acids"
    ACETIC_ACID = "acetic_acid"
    MALIC_ACID = "malic_acid"
    LACTIC_ACID = "lactic_acid"
    CITRIC_ACID = "citric_acid"


FACTORS = MappingProxyType(
    {
        k: Decimal(v)
        for k, v in (
            (EnergyComponent.PROTEIN, "4"),
            (EnergyComponent.FAT, "9"),
            (EnergyComponent.AVAILABLE_CARBOHYDRATE, "4"),
            (EnergyComponent.EXPERIMENTAL_SUGARS, "3.8"),
            (EnergyComponent.EXPERIMENTAL_STARCH, "4.1"),
            (EnergyComponent.FIBRE, "2"),
            (EnergyComponent.POLYOLS_EXCLUDING_ERYTHRITOL, "2.4"),
            (EnergyComponent.ERYTHRITOL, "0"),
            (EnergyComponent.ETHANOL, "7"),
            (EnergyComponent.GLYCEROL, "2.4"),
            (EnergyComponent.OTHER_ORGANIC_ACIDS, "3"),
            (EnergyComponent.ACETIC_ACID, "3.5"),
            (EnergyComponent.MALIC_ACID, "2.4"),
            (EnergyComponent.LACTIC_ACID, "3.6"),
            (EnergyComponent.CITRIC_ACID, "2.5"),
        )
    }
)
GENERIC_PARTITION = frozenset(FACTORS) - {
    EnergyComponent.EXPERIMENTAL_SUGARS,
    EnergyComponent.EXPERIMENTAL_STARCH,
}


@dataclass(frozen=True)
class EnergyTerm:
    component: EnergyComponent
    amount_g: Decimal | None
    source_observation_id: str
    # Source IDs resolve to a reviewed record, including method and value state.
    method_reference: str
    basis_g: Decimal
    food_form_id: str

    def __post_init__(self):
        if not isinstance(self.component, EnergyComponent):
            raise TypeError("Нужно точное определение энергетического компонента.")
        if any(
            not isinstance(t, str) or not t.strip()
            for t in (
                self.source_observation_id,
                self.method_reference,
                self.food_form_id,
            )
        ):
            raise ValueError("Нужны происхождение количества и метод его определения.")
        if (
            not isinstance(self.basis_g, Decimal)
            or not self.basis_g.is_finite()
            or not Decimal("1e-18") <= self.basis_g <= Decimal("1e24")
        ):
            raise ValueError("Недопустимая база компонента.")
        if self.amount_g is not None:
            if not isinstance(self.amount_g, Decimal):
                raise TypeError("Масса компонента должна иметь тип Decimal.")
            if not self.amount_g.is_finite() or not 0 <= self.amount_g <= Decimal(
                "1e24"
            ):
                raise ValueError("Недопустимая масса компонента.")
            if (
                len(self.amount_g.as_tuple().digits) > 40
                or self.amount_g.as_tuple().exponent < -40
            ):
                raise ValueError("Недопустимая точность массы.")


@dataclass(frozen=True)
class RussianEnergyResult:
    version: str
    source: str
    basis_g: Decimal
    food_form_id: str
    terms: tuple[EnergyTerm, ...]
    computed_kcal: Decimal | None
    known_components_subtotal_kcal: Decimal
    missing_components: tuple[EnergyComponent, ...]
    # Published value is separate and never corrected to fit the formula.
    published_kcal: Decimal | None
    published_observation_id: str | None
    difference_from_published_kcal: Decimal | None
    disjoint_partition_review: str | None


def calculate_russian_energy(
    terms: tuple[EnergyTerm, ...],
    *,
    basis_g: Decimal,
    food_form_id: str,
    published_kcal: Decimal | None = None,
    published_observation_id: str | None = None,
    disjoint_partition_review: str | None = None,
) -> RussianEnergyResult:
    if not isinstance(basis_g, Decimal):
        raise TypeError("База расчёта должна иметь тип Decimal.")
    if (
        not basis_g.is_finite()
        or not Decimal("1e-18") <= basis_g <= Decimal("1e24")
        or not isinstance(food_form_id, str)
        or not food_form_id.strip()
    ):
        raise ValueError("Нужны положительная база и точная форма продукта.")
    terms = tuple(terms)
    if not terms or any(not isinstance(t, EnergyTerm) for t in terms):
        raise ValueError("Нужны типизированные исходные компоненты.")
    if any(t.basis_g != basis_g or t.food_form_id != food_form_id for t in terms):
        raise ValueError("База или форма компонента не совпадает с расчётом.")
    if disjoint_partition_review is not None and (
        not isinstance(disjoint_partition_review, str)
        or not disjoint_partition_review.strip()
    ):
        raise ValueError("Нужно основание непересекающегося состава.")
    keys = {t.component for t in terms}
    if len(keys) != len(terms):
        raise ValueError("Повтор энергетического компонента.")
    experimental = {
        EnergyComponent.EXPERIMENTAL_SUGARS,
        EnergyComponent.EXPERIMENTAL_STARCH,
    }
    if EnergyComponent.AVAILABLE_CARBOHYDRATE in keys and keys & experimental:
        raise ValueError(
            "Углеводы и входящие в них сахара/крахмал нельзя учитывать дважды."
        )
    if published_kcal is not None:
        if not isinstance(published_kcal, Decimal):
            raise TypeError("Опубликованная энергия должна иметь тип Decimal.")
        if (
            not published_kcal.is_finite()
            or not 0 <= published_kcal <= Decimal("1e24")
            or not isinstance(published_observation_id, str)
            or not published_observation_id.strip()
        ):
            raise ValueError(
                "Нужно допустимое значение опубликованной энергии и источник."
            )
        if (
            len(published_kcal.as_tuple().digits) > 40
            or published_kcal.as_tuple().exponent < -40
        ):
            raise ValueError("Недопустимая точность опубликованной энергии.")
    # Experimental components can produce a traced subtotal only: sugar+starch
    # alone do not establish exhaustive available-carbohydrate composition.
    values = {t.component: t.amount_g for t in terms}
    missing = tuple(sorted(k for k in GENERIC_PARTITION if values.get(k) is None))
    with localcontext(Context(prec=80, rounding=ROUND_HALF_UP)):
        subtotal = sum(
            (
                t.amount_g * FACTORS[t.component]
                for t in terms
                if t.amount_g is not None
            ),
            Decimal(0),
        ).quantize(Decimal(".000001"))
        computed = (
            subtotal if not missing and disjoint_partition_review is not None else None
        )
        difference = (
            (computed - published_kcal).quantize(Decimal(".000001"))
            if computed is not None and published_kcal is not None
            else None
        )
    return RussianEnergyResult(
        VERSION,
        SOURCE,
        basis_g,
        food_form_id,
        terms,
        computed,
        subtotal,
        missing,
        published_kcal,
        published_observation_id,
        difference,
        disjoint_partition_review,
    )
