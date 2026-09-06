"""Deterministic, on-demand FoodIngredient and RecipeVersion nutrition."""

from collections.abc import Mapping
from dataclasses import dataclass, replace
from decimal import Decimal, localcontext
from enum import StrEnum
from uuid import UUID

from app.domain.food_ingredients import FoodIngredient, FoodNutritionProfile
from app.domain.food_recipes import RecipeIngredient, RecipeVersion, RecipeVersionDetail
from app.domain.nutrition_evidence import (
    AssessmentStatus,
    MeasureMassEvidence,
    NutritionAssessmentIssue,
    RecipeIngredientNutritionAssessment,
)
from app.domain.nutrition_config import (
    CONFIG,
    MAX_INPUT,
    MIN_INPUT,
    NUTRIENTS,
    RESULT_QUANTUM,
    NutritionConfig,
    calculation_context,
)
from app.domain.units import UnitCode


class NutritionStatus(StrEnum):
    COMPLETE = "COMPLETE"
    COMPLETE_WITH_WARNINGS = "COMPLETE_WITH_WARNINGS"
    CONDITIONAL = "CONDITIONAL"
    INCOMPLETE = "INCOMPLETE"


class NutritionWarningCode(StrEnum):
    MISSING_NUTRITION_ASSESSMENT = "MISSING_NUTRITION_ASSESSMENT"
    NUTRITION_ASSESSMENT_BLOCKED = "NUTRITION_ASSESSMENT_BLOCKED"
    CONVERSION_ESTIMATE_NOT_ACCEPTED = "CONVERSION_ESTIMATE_NOT_ACCEPTED"
    NUTRITION_ASSESSMENT_PROFILE_STALE = "NUTRITION_ASSESSMENT_PROFILE_STALE"
    MISSING_MEASURE_EVIDENCE = "MISSING_MEASURE_EVIDENCE"
    MISSING_FOOD_INGREDIENT = "MISSING_FOOD_INGREDIENT"
    MISSING_NUTRITION_PROFILE = "MISSING_NUTRITION_PROFILE"
    MISSING_DENSITY = "MISSING_DENSITY"
    UNSUPPORTED_PIECE_MASS = "UNSUPPORTED_PIECE_MASS"
    UNKNOWN_FIBER = "UNKNOWN_FIBER"
    ESTIMATED_SOURCE = "ESTIMATED_SOURCE"
    ESTIMATION_STATUS_UNKNOWN = "ESTIMATION_STATUS_UNKNOWN"
    OPTIONAL_INGREDIENT = "OPTIONAL_INGREDIENT"
    MISSING_BIRTH_DATE = "MISSING_BIRTH_DATE"
    FUTURE_BIRTH_DATE = "FUTURE_BIRTH_DATE"
    UNSUPPORTED_AGE = "UNSUPPORTED_AGE"
    UNSUPPORTED_SEX = "UNSUPPORTED_SEX"
    UNSUPPORTED_ACTIVITY = "UNSUPPORTED_ACTIVITY"
    INVALID_HEIGHT = "INVALID_HEIGHT"
    INVALID_WEIGHT = "INVALID_WEIGHT"
    INVALID_REFERENCE_ENERGY = "INVALID_REFERENCE_ENERGY"
    GOAL_ADJUSTMENT_NOT_APPLIED = "GOAL_ADJUSTMENT_NOT_APPLIED"
    REFERENCE_ESTIMATE = "REFERENCE_ESTIMATE"


@dataclass(frozen=True)
class NutritionWarning:
    code: NutritionWarningCode
    # Recipe row context distinguishes repeated/optional occurrences.
    recipe_ingredient_id: UUID | None = None
    food_ingredient_id: UUID | None = None


@dataclass(frozen=True)
class NutritionValues:
    kcal: Decimal | None = None
    protein_g: Decimal | None = None
    fat_g: Decimal | None = None
    carbohydrates_g: Decimal | None = None
    fiber_g: Decimal | None = None


@dataclass(frozen=True)
class IngredientNutrition:
    ingredient: FoodIngredient | None
    profile: FoodNutritionProfile | None
    quantity: Decimal
    unit: UnitCode
    mass_g: Decimal | None
    values: NutritionValues
    status: NutritionStatus
    warnings: tuple[NutritionWarning, ...]
    config: NutritionConfig = CONFIG


@dataclass(frozen=True)
class RecipeIngredientNutrition:
    row: RecipeIngredient
    nutrition: IngredientNutrition
    assessment: RecipeIngredientNutritionAssessment | None = None
    measure_evidence: MeasureMassEvidence | None = None
    assessment_profile: FoodNutritionProfile | None = None


@dataclass(frozen=True)
class RecipeVersionNutrition:
    version: RecipeVersion
    required_total: NutritionValues
    per_base_serving: NutritionValues
    required_contributions: tuple[RecipeIngredientNutrition, ...]
    optional_contributions: tuple[RecipeIngredientNutrition, ...]
    status: NutritionStatus
    warnings: tuple[NutritionWarning, ...]
    config: NutritionConfig = CONFIG


def require_positive_decimal(value: Decimal) -> None:
    if not isinstance(value, Decimal):
        raise TypeError("Nutrition quantities must be Decimal, never float.")
    if not value.is_finite() or not MIN_INPUT <= value <= MAX_INPUT:
        raise ValueError(
            "Nutrition quantity is outside the positive calculation bounds."
        )


def rounded(value: Decimal | None) -> Decimal | None:
    return None if value is None else value.quantize(RESULT_QUANTUM)


def _round_values(values: NutritionValues) -> NutritionValues:
    return NutritionValues(
        **{name: rounded(getattr(values, name)) for name in NUTRIENTS}
    )


def _ingredient(
    ingredient: FoodIngredient | None,
    profile: FoodNutritionProfile | None,
    quantity: Decimal,
    unit: UnitCode,
    *,
    food_ingredient_id: UUID,
    row_id: UUID | None = None,
    row_authority: tuple[Decimal | None, tuple[NutritionWarningCode, ...]]
    | None = None,
) -> IngredientNutrition:
    require_positive_decimal(quantity)
    if unit not in (UnitCode.GRAM, UnitCode.MILLILITER, UnitCode.PIECE):
        raise ValueError("Unsupported nutrition unit.")
    if ingredient is not None and ingredient.id != food_ingredient_id:
        raise ValueError("FoodIngredient does not match the calculation input.")
    if profile is not None and (
        profile.food_ingredient_id != food_ingredient_id or not profile.is_current
    ):
        raise ValueError("Nutrition requires the matching current profile.")
    warnings: list[NutritionWarning] = []

    def warn(code: NutritionWarningCode) -> None:
        warnings.append(NutritionWarning(code, row_id, food_ingredient_id))

    mass = None
    if ingredient is None:
        warn(NutritionWarningCode.MISSING_FOOD_INGREDIENT)
    if row_authority is not None:
        mass, authority_warnings = row_authority
        for code in authority_warnings:
            warn(code)
        if ingredient is None:
            mass = None
    elif ingredient is None:
        pass
    elif unit == UnitCode.GRAM:
        mass = quantity  # Already normalized; no edible_fraction adjustment.
    elif unit == UnitCode.MILLILITER:
        if ingredient.density_g_per_ml is None:
            warn(NutritionWarningCode.MISSING_DENSITY)
        else:
            mass = quantity * ingredient.density_g_per_ml
    else:
        warn(NutritionWarningCode.UNSUPPORTED_PIECE_MASS)
    if profile is None:
        warn(NutritionWarningCode.MISSING_NUTRITION_PROFILE)
    else:
        if profile.fiber_g is None:
            warn(NutritionWarningCode.UNKNOWN_FIBER)
        if profile.estimated is True:
            warn(NutritionWarningCode.ESTIMATED_SOURCE)
        elif profile.estimated is None:
            warn(NutritionWarningCode.ESTIMATION_STATUS_UNKNOWN)
    values = NutritionValues()
    if mass is not None and profile is not None:
        values = NutritionValues(
            **{
                name: None
                if (value := getattr(profile, name)) is None
                else value * mass / profile.basis_grams
                for name in NUTRIENTS
            }
        )
    status = (
        NutritionStatus.INCOMPLETE
        if values.kcal is None
        else NutritionStatus.COMPLETE_WITH_WARNINGS
        if warnings
        else NutritionStatus.COMPLETE
    )
    return IngredientNutrition(
        ingredient,
        profile,
        quantity,
        UnitCode(unit),
        mass,
        values,
        status,
        tuple(warnings),
    )


def scale_food_nutrition(
    ingredient: FoodIngredient,
    profile: FoodNutritionProfile | None,
    quantity: Decimal,
    unit: UnitCode = UnitCode.GRAM,
) -> IngredientNutrition:
    with localcontext(calculation_context()):
        result = _ingredient(
            ingredient, profile, quantity, unit, food_ingredient_id=ingredient.id
        )
        return replace(result, values=_round_values(result.values))


def _row_mass(
    row: RecipeIngredient,
    profile: FoodNutritionProfile | None,
    assessment: RecipeIngredientNutritionAssessment | None,
    evidence: MeasureMassEvidence | None,
) -> tuple[Decimal | None, tuple[NutritionWarningCode, ...]]:
    """Explicit row authority only. Candidate presence never grants permission."""
    code = NutritionWarningCode
    if assessment is None:
        return None, (code.MISSING_NUTRITION_ASSESSMENT,)
    if assessment.recipe_ingredient_id != row.id or not assessment.is_current:
        return None, (code.NUTRITION_ASSESSMENT_BLOCKED,)
    warnings = []
    if profile is None or assessment.nutrition_profile_id != profile.id:
        warnings.append(code.NUTRITION_ASSESSMENT_PROFILE_STALE)
    if assessment.status_code == AssessmentStatus.BLOCKED:
        warnings.append(code.NUTRITION_ASSESSMENT_BLOCKED)
    if (
        assessment.status_code == AssessmentStatus.REVIEW_REQUIRED_ESTIMATE
        or NutritionAssessmentIssue.CONVERSION_ESTIMATE_NOT_ACCEPTED
        in assessment.issues
    ):
        warnings.append(code.CONVERSION_ESTIMATE_NOT_ACCEPTED)
    if warnings:
        return None, tuple(warnings)
    if assessment.issues:
        return None, (code.NUTRITION_ASSESSMENT_BLOCKED,)
    if assessment.status_code == AssessmentStatus.APPROVED_NO_CONVERSION:
        return (
            (row.quantity, ())
            if row.unit == UnitCode.GRAM
            else (None, (code.NUTRITION_ASSESSMENT_BLOCKED,))
        )
    if assessment.status_code == AssessmentStatus.APPROVED_EXACT:
        if evidence is None or evidence.id != assessment.measure_evidence_id:
            return None, (code.MISSING_MEASURE_EVIDENCE,)
        if evidence.estimated:
            return None, (code.CONVERSION_ESTIMATE_NOT_ACCEPTED,)
        if (
            row.unit not in (UnitCode.MILLILITER, UnitCode.PIECE)
            or row.unit != evidence.normalized_input_unit
        ):
            return None, (code.NUTRITION_ASSESSMENT_BLOCKED,)
        return (
            row.quantity * evidence.gram_weight / evidence.normalized_input_quantity,
            (),
        )
    return None, (code.NUTRITION_ASSESSMENT_BLOCKED,)


def calculate_recipe_nutrition(
    detail: RecipeVersionDetail,
    ingredients: Mapping[UUID, FoodIngredient],
    profiles: Mapping[UUID, FoodNutritionProfile],
    assessments: Mapping[UUID, RecipeIngredientNutritionAssessment] | None = None,
    evidence: Mapping[UUID, MeasureMassEvidence] | None = None,
    assessment_profiles: Mapping[UUID, FoodNutritionProfile] | None = None,
) -> RecipeVersionNutrition:
    """Mappings and detail must come from one coherent read view."""
    assessments = {} if assessments is None else assessments
    evidence = {} if evidence is None else evidence
    assessment_profiles = {} if assessment_profiles is None else assessment_profiles
    with localcontext(calculation_context()):
        required: list[RecipeIngredientNutrition] = []
        optional: list[RecipeIngredientNutrition] = []
        warnings: list[NutritionWarning] = []
        for row in sorted(detail.ingredients, key=lambda item: item.position):
            assessment = assessments.get(row.id)
            measure = (
                None
                if assessment is None
                else evidence.get(assessment.measure_evidence_id)
            )
            profile = profiles.get(row.food_ingredient_id)
            pinned_profile = (
                None
                if assessment is None
                else assessment_profiles.get(assessment.nutrition_profile_id)
            )
            if (
                assessment is not None
                and profile is not None
                and assessment.nutrition_profile_id == profile.id
            ):
                pinned_profile = profile
            result = _ingredient(
                ingredients.get(row.food_ingredient_id),
                profiles.get(row.food_ingredient_id),
                row.quantity,
                row.unit,
                food_ingredient_id=row.food_ingredient_id,
                row_id=row.id,
                row_authority=_row_mass(row, profile, assessment, measure),
            )
            warnings.extend(result.warnings)
            if row.optional:
                warnings.append(
                    NutritionWarning(
                        NutritionWarningCode.OPTIONAL_INGREDIENT,
                        row.id,
                        row.food_ingredient_id,
                    )
                )
            (optional if row.optional else required).append(
                RecipeIngredientNutrition(
                    row, result, assessment, measure, pinned_profile
                )
            )
        # None propagates per nutrient; never expose a diagnostic partial sum as a total.
        total = NutritionValues(
            **{
                name: None
                if any(
                    getattr(item.nutrition.values, name) is None for item in required
                )
                else sum(
                    (getattr(item.nutrition.values, name) for item in required),
                    Decimal(0),
                )
                for name in NUTRIENTS
            }
        )
        require_positive_decimal(detail.version.base_servings)
        per_base = NutritionValues(
            **{
                name: None
                if (value := getattr(total, name)) is None
                else value / detail.version.base_servings
                for name in NUTRIENTS
            }
        )
        status = (
            NutritionStatus.INCOMPLETE
            if total.kcal is None
            else NutritionStatus.CONDITIONAL
            if optional
            else NutritionStatus.COMPLETE_WITH_WARNINGS
            if warnings
            else NutritionStatus.COMPLETE
        )

        def boundary(
            items: list[RecipeIngredientNutrition],
        ) -> tuple[RecipeIngredientNutrition, ...]:
            return tuple(
                replace(
                    item,
                    nutrition=replace(
                        item.nutrition, values=_round_values(item.nutrition.values)
                    ),
                )
                for item in items
            )

        return RecipeVersionNutrition(
            detail.version,
            _round_values(total),
            _round_values(per_base),
            boundary(required),
            boundary(optional),
            status,
            tuple(warnings),
        )
