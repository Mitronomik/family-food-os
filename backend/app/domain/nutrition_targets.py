"""Versioned reference targets, without goal adjustments or clinical policy."""

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, localcontext
from uuid import UUID

from app.domain.households import MAX_HEIGHT_CM, MAX_WEIGHT_KG, HouseholdMember
from app.domain.nutrition import (
    NutritionStatus,
    NutritionWarning,
    NutritionWarningCode,
    rounded,
)
from app.domain.nutrition_config import (
    AMDR_BANDS,
    ATWATER_FACTORS,
    CONFIG,
    EER_COEFFICIENTS,
    FIBER_BANDS,
    GROWTH_BANDS,
    PAL_CATEGORIES,
    REFERENCE_SOURCES,
    NutritionConfig,
    ReferenceSource,
    calculation_context,
)


@dataclass(frozen=True)
class MemberTargetInputs:
    household_id: UUID
    member_id: UUID
    birth_date: date | None
    sex: str | None
    height_cm: Decimal | None
    weight_kg: Decimal | None
    activity_level: str
    goal: str
    member_updated_at: datetime


@dataclass(frozen=True)
class ReferenceGramRange:
    min_g: Decimal
    max_g: Decimal
    min_energy_fraction: Decimal
    max_energy_fraction: Decimal
    kcal_per_g: Decimal


@dataclass(frozen=True)
class MemberReferenceNutritionTarget:
    inputs: MemberTargetInputs
    as_of_date: date
    age_years: int | None
    reference_energy_kcal: Decimal | None
    carbohydrate: ReferenceGramRange | None
    protein: ReferenceGramRange | None
    fat: ReferenceGramRange | None
    fiber_ai_g: Decimal | None
    equation_table: str | None
    growth_allowance_kcal: Decimal | None
    sources: tuple[ReferenceSource, ...]
    warnings: tuple[NutritionWarning, ...]
    status: NutritionStatus
    config: NutritionConfig = CONFIG


def calculate_member_reference_target(
    member: HouseholdMember, *, as_of_date: date
) -> MemberReferenceNutritionTarget:
    if type(as_of_date) is not date:
        raise TypeError("as_of_date must be an explicit date, not an instant.")
    with localcontext(calculation_context()):
        warnings: list[NutritionWarning] = []

        def warn(code: NutritionWarningCode) -> None:
            warnings.append(NutritionWarning(code))

        age = None
        if member.birth_date is None:
            warn(NutritionWarningCode.MISSING_BIRTH_DATE)
        elif member.birth_date > as_of_date:
            warn(NutritionWarningCode.FUTURE_BIRTH_DATE)
        else:
            born = member.birth_date
            age = (
                as_of_date.year
                - born.year
                - ((as_of_date.month, as_of_date.day) < (born.month, born.day))
            )
            if age < 3:
                warn(NutritionWarningCode.UNSUPPORTED_AGE)
        if member.sex not in ("male", "female"):
            warn(NutritionWarningCode.UNSUPPORTED_SEX)
        if member.activity_level not in PAL_CATEGORIES:
            warn(NutritionWarningCode.UNSUPPORTED_ACTIVITY)
        for value, maximum, code in (
            (member.height_cm, MAX_HEIGHT_CM, NutritionWarningCode.INVALID_HEIGHT),
            (member.weight_kg, MAX_WEIGHT_KG, NutritionWarningCode.INVALID_WEIGHT),
        ):
            if (
                not isinstance(value, Decimal)
                or not value.is_finite()
                or not 0 < value <= maximum
            ):
                warn(code)

        energy = None
        growth = None
        table = None
        ranges: list[ReferenceGramRange | None] = [None, None, None]
        if not warnings:
            assert (
                age is not None
                and member.height_cm is not None
                and member.weight_kg is not None
            )
            group = "child" if age < 19 else "adult"
            table = "5-15" if age < 19 else "5-16"
            coeff = EER_COEFFICIENTS[group, member.sex][
                PAL_CATEGORIES.index(member.activity_level)
            ]
            growth = Decimal(0)
            if age < 19:
                band = next(row for row in GROWTH_BANDS if age <= row[0])
                growth = band[1 if member.sex == "male" else 2]
            energy = (
                coeff[0]
                + coeff[1] * Decimal(age)
                + coeff[2] * member.height_cm
                + coeff[3] * member.weight_kg
                + growth
            )
            if energy <= 0:
                energy = None
                warn(NutritionWarningCode.INVALID_REFERENCE_ENERGY)
            else:
                warn(NutritionWarningCode.REFERENCE_ESTIMATE)
                amdr = next(
                    bounds
                    for upper, bounds in AMDR_BANDS
                    if upper is None or age <= upper
                )
                ranges = [
                    ReferenceGramRange(
                        rounded(energy * low / factor),
                        rounded(energy * high / factor),
                        low,
                        high,
                        factor,
                    )
                    for (low, high), factor in zip(amdr, ATWATER_FACTORS, strict=True)
                ]

        # Fiber AI can remain available when energy inputs are missing.
        fiber = None
        if age is not None and age >= 3:
            band = next(row for row in FIBER_BANDS if row[0] is None or age <= row[0])
            if member.sex in ("male", "female"):
                fiber = band[1 if member.sex == "male" else 2]
            elif age <= 8:  # The published childhood band is not sex-specific.
                fiber = band[1]
        if member.goal != "maintain":
            warn(NutritionWarningCode.GOAL_ADJUSTMENT_NOT_APPLIED)
        inputs = MemberTargetInputs(
            member.household_id,
            member.id,
            member.birth_date,
            member.sex,
            member.height_cm,
            member.weight_kg,
            member.activity_level,
            member.goal,
            member.updated_at,
        )
        return MemberReferenceNutritionTarget(
            inputs,
            as_of_date,
            age,
            rounded(energy),
            *ranges,
            rounded(fiber),
            table,
            growth,
            REFERENCE_SOURCES,
            tuple(warnings),
            NutritionStatus.INCOMPLETE
            if energy is None
            else NutritionStatus.COMPLETE_WITH_WARNINGS,
        )
