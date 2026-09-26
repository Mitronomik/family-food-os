"""Step 10-A composition-backed canonical RecipeVersion Nutrition."""

from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from decimal import Decimal, localcontext
from enum import StrEnum
from uuid import UUID

from app.domain.food_composition import (
    APPLICABILITY_CALCULATION_VERSION,
    CompositionUnavailableError,
    MassState,
    calculation_context,
)
from app.domain.nutrition import (
    NutritionStatus,
    NutritionValues,
    RecipeVersionNutrition,
)
from app.domain.recipe_nutrition_v2 import (
    COMPOSITION_CALCULATION_VERSION,
    NUTRIENT_CODES,
    NUTRIENT_SET_VERSION,
    RECIPE_CALCULATION_VERSION,
    REGISTRY_VERSION,
    RESULT_QUANTUM,
    CanonicalNutrientAmount,
    CanonicalRecipeVersionNutrition,
    RecipeIngredientCompositionBinding,
    RecipeNutritionAuthorityKind,
    RecipeNutritionConsumptionProjection,
    RecipeNutritionV2Issue,
    RecipeNutritionV2Status,
)
from app.domain.units import UnitCode
from app.services.food_composition import ApplicabilityAwareCompositionCalculator
from app.services.food_recipes import (
    TrustedRecipeSeed,
    trusted_recipe_seed_matches,
)
from app.services.recipe_nutrition_v2_contracts import (
    RecipeNutritionV2PersistenceConflictError,
    RecipeNutritionV2ReadScope,
    RecipeNutritionV2UnitOfWork,
)

ReadScopeFactory = Callable[[], RecipeNutritionV2ReadScope]
WriteScopeFactory = Callable[[], RecipeNutritionV2UnitOfWork]
LegacyRecipeNutrition = Callable[[UUID], RecipeVersionNutrition]
Clock = Callable[[], datetime]


class RecipeNutritionV2ContractError(ValueError):
    """Requested Step 10-A authority violates the frozen contract."""


class RecipeNutritionV2ConflictError(ValueError):
    """Persisted authority conflicts with a reviewed binding publication."""


class RecipeNutritionV2UnavailableError(ValueError):
    """Canonical V2 Recipe Nutrition cannot be calculated from pinned authority."""


class BindingDisposition(StrEnum):
    FRESH = "FRESH"
    EXACT_REPLAY = "EXACT_REPLAY"


@dataclass(frozen=True)
class ReviewedRecipeIngredientBindingSpec:
    trusted_recipe_seed: TrustedRecipeSeed
    recipe_code: str
    source_name: str
    source_recipe_id: str
    source_version: str
    recipe_version_number: int
    ingredient_position: int
    food_ingredient_code: str
    quantity: Decimal
    unit: UnitCode | str
    composition_version: int
    expected_available_amounts: tuple[tuple[str, Decimal], ...]
    expected_unknown_codes: tuple[str, ...]
    require_recipe_inactive: bool = True


@dataclass(frozen=True)
class BindingPublicationResult:
    disposition: BindingDisposition
    binding: RecipeIngredientCompositionBinding
    recipe_version_id: UUID


def _round(value: Decimal | None) -> Decimal | None:
    if value is None:
        return None
    return value.quantize(RESULT_QUANTUM)


def _values(items: tuple[CanonicalNutrientAmount, ...]) -> dict[str, Decimal | None]:
    return {item.code: item.amount for item in items}


def project_recipe_nutrition_consumption(
    canonical: CanonicalRecipeVersionNutrition,
) -> RecipeNutritionConsumptionProjection:
    total = _values(canonical.required_total)
    per_serving = _values(canonical.per_base_serving)

    def legacy(source: dict[str, Decimal | None]) -> NutritionValues:
        return NutritionValues(
            kcal=source["ENERGY_KCAL"],
            protein_g=source["PROTEIN"],
            fat_g=source["FAT_TOTAL"],
            carbohydrates_g=source["CARBOHYDRATE_BY_DIFFERENCE"],
            fiber_g=source["FIBER_TOTAL_DIETARY"],
        )

    required = legacy(total)
    serving = legacy(per_serving)
    legacy_fields = (
        required.kcal,
        required.protein_g,
        required.fat_g,
        required.carbohydrates_g,
        required.fiber_g,
    )
    legacy_status = (
        NutritionStatus.INCOMPLETE
        if any(value is None for value in legacy_fields)
        else NutritionStatus.COMPLETE
    )
    energy = serving.kcal
    energy_ready = (
        isinstance(energy, Decimal) and energy.is_finite() and energy > 0
    )
    return RecipeNutritionConsumptionProjection(
        recipe_version_id=canonical.recipe_version_id,
        required_total=required,
        per_base_serving=serving,
        legacy_status=legacy_status,
        authority_kind=RecipeNutritionAuthorityKind.COMPOSITION_V2,
        canonical_status=canonical.status,
        exact_energy_ready=energy_ready,
        registry_version=canonical.registry_version,
        nutrient_set_version=canonical.nutrient_set_version,
        composition_calculation_version=canonical.composition_calculation_version,
        recipe_calculation_version=canonical.recipe_calculation_version,
    )


def project_legacy_recipe_nutrition_consumption(
    legacy: RecipeVersionNutrition,
) -> RecipeNutritionConsumptionProjection:
    energy = legacy.per_base_serving.kcal
    energy_ready = (
        legacy.status is not NutritionStatus.INCOMPLETE
        and isinstance(energy, Decimal)
        and energy.is_finite()
        and energy > 0
    )
    return RecipeNutritionConsumptionProjection(
        recipe_version_id=legacy.version.id,
        required_total=legacy.required_total,
        per_base_serving=legacy.per_base_serving,
        legacy_status=legacy.status,
        authority_kind=RecipeNutritionAuthorityKind.LEGACY_V1,
        canonical_status=None,
        exact_energy_ready=energy_ready,
        registry_version=None,
        nutrient_set_version=None,
        composition_calculation_version=None,
        recipe_calculation_version=None,
    )


class RecipeNutritionV2Service:
    def __init__(
        self,
        read_scope_factory: ReadScopeFactory,
        write_scope_factory: WriteScopeFactory,
        *,
        legacy_recipe_nutrition: LegacyRecipeNutrition | None = None,
        clock: Clock | None = None,
    ) -> None:
        self._read_scope_factory = read_scope_factory
        self._write_scope_factory = write_scope_factory
        self._legacy_recipe_nutrition = legacy_recipe_nutrition
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def publish_binding(
        self, spec: ReviewedRecipeIngredientBindingSpec
    ) -> BindingPublicationResult:
        self._validate_spec(spec)
        with self._write_scope_factory() as uow:
            try:
                detail, row, food, composition = self._resolve_publication_target(
                    uow, spec
                )
                calculation = self._calculate_row(uow, row, composition)
                self._require_reviewed_calculation(spec, row, calculation)
                existing = uow.bindings.get(row.id)
                if existing is not None:
                    expected = RecipeIngredientCompositionBinding(
                        recipe_ingredient_id=row.id,
                        composition_version_id=composition.id,
                        registry_version=REGISTRY_VERSION,
                        nutrient_set_version=NUTRIENT_SET_VERSION,
                        composition_calculation_version=COMPOSITION_CALCULATION_VERSION,
                        recipe_calculation_version=RECIPE_CALCULATION_VERSION,
                        created_at=existing.created_at,
                    )
                    if existing != expected:
                        raise RecipeNutritionV2ConflictError(
                            "Существующий Recipe Nutrition binding отличается от проверенной authority."
                        )
                    return BindingPublicationResult(
                        BindingDisposition.EXACT_REPLAY,
                        existing,
                        detail.version.id,
                    )

                now = self._clock()
                if (
                    not isinstance(now, datetime)
                    or now.tzinfo is None
                    or now.utcoffset() is None
                ):
                    raise RecipeNutritionV2ContractError(
                        "Часы publication должны возвращать timezone-aware instant."
                    )
                binding = RecipeIngredientCompositionBinding(
                    recipe_ingredient_id=row.id,
                    composition_version_id=composition.id,
                    registry_version=REGISTRY_VERSION,
                    nutrient_set_version=NUTRIENT_SET_VERSION,
                    composition_calculation_version=COMPOSITION_CALCULATION_VERSION,
                    recipe_calculation_version=RECIPE_CALCULATION_VERSION,
                    created_at=now.astimezone(timezone.utc),
                )
                uow.bindings.add(binding)
                uow.commit()
                return BindingPublicationResult(
                    BindingDisposition.FRESH,
                    binding,
                    detail.version.id,
                )
            except RecipeNutritionV2PersistenceConflictError as exc:
                raise RecipeNutritionV2ConflictError(
                    "Recipe Nutrition binding конфликтует с сохранённой authority."
                ) from exc

    def calculate(self, recipe_version_id: UUID) -> CanonicalRecipeVersionNutrition:
        with self._read_scope_factory() as scope:
            detail = scope.versions.get_detail(recipe_version_id)
            if detail is None:
                raise RecipeNutritionV2UnavailableError("RecipeVersion не найден.")
            return self._calculate_detail(scope, detail)

    def neutral_consumption_projection(
        self, recipe_version_id: UUID
    ) -> RecipeNutritionConsumptionProjection:
        legacy_path = False
        with self._read_scope_factory() as scope:
            detail = scope.versions.get_detail(recipe_version_id)
            if detail is None:
                raise RecipeNutritionV2UnavailableError("RecipeVersion не найден.")
            required_rows = tuple(row for row in detail.ingredients if not row.optional)
            bindings = tuple(scope.bindings.get(row.id) for row in required_rows)
            bound_count = sum(binding is not None for binding in bindings)
            if bound_count == 0:
                legacy_path = True
            elif bound_count != len(required_rows):
                raise RecipeNutritionV2UnavailableError(
                    "Partial required-row V2 binding запрещён."
                )
            else:
                return project_recipe_nutrition_consumption(
                    self._calculate_detail(scope, detail)
                )

        if legacy_path:
            if self._legacy_recipe_nutrition is None:
                raise RecipeNutritionV2UnavailableError(
                    "Legacy Nutrition authority не подключена."
                )
            return project_legacy_recipe_nutrition_consumption(
                self._legacy_recipe_nutrition(recipe_version_id)
            )
        raise AssertionError("Nutrition authority classification is incomplete.")

    def _calculate_detail(self, scope, detail) -> CanonicalRecipeVersionNutrition:
        if not detail.ingredients:
            raise RecipeNutritionV2UnavailableError(
                "RecipeVersion не содержит обязательные ингредиенты."
            )
        if any(row.optional for row in detail.ingredients):
            raise RecipeNutritionV2UnavailableError(
                "RECIPE_COMPOSITION_NUTRITION_V1 не поддерживает optional rows."
            )
        if detail.version.base_servings <= 0:
            raise RecipeNutritionV2UnavailableError(
                "RecipeVersion base_servings должен быть положительным."
            )

        row_amounts: list[dict[str, Decimal | None]] = []
        bindings = []
        issues = []
        for row in sorted(detail.ingredients, key=lambda item: item.position):
            if row.unit is not UnitCode.GRAM:
                raise RecipeNutritionV2UnavailableError(
                    "RECIPE_COMPOSITION_NUTRITION_V1 поддерживает только точные граммы."
                )
            binding = scope.bindings.get(row.id)
            if binding is None:
                raise RecipeNutritionV2UnavailableError(
                    "Для обязательного RecipeIngredient отсутствует Composition binding."
                )
            self._require_binding_versions(binding)
            food = scope.food_ingredients.get(row.food_ingredient_id)
            if food is None:
                raise RecipeNutritionV2UnavailableError(
                    "Закреплённый FoodIngredient отсутствует."
                )
            try:
                composition = scope.compositions.get(binding.composition_version_id)
            except CompositionUnavailableError as exc:
                raise RecipeNutritionV2UnavailableError(
                    "Закреплённый FoodCompositionVersion недоступен."
                ) from exc
            if composition.food_ingredient_id != row.food_ingredient_id:
                raise RecipeNutritionV2UnavailableError(
                    "RecipeIngredient и Composition принадлежат разным FoodIngredient."
                )
            result = self._calculate_row(scope, row, composition)
            amounts = {item.definition.code: item.amount for item in result.nutrients}
            with localcontext(calculation_context()):
                row_amounts.append(
                    {
                        code: (
                            None
                            if amounts[code] is None
                            else amounts[code]
                            * row.quantity
                            / result.input_mass_g
                        )
                        for code in NUTRIENT_CODES
                    }
                )
            bindings.append(binding)
            for issue in result.issues:
                issues.append(
                    RecipeNutritionV2Issue(
                        issue.code,
                        issue.nutrient_code,
                        row.id,
                    )
                )
            for code in NUTRIENT_CODES:
                if amounts[code] is None:
                    issues.append(
                        RecipeNutritionV2Issue(
                            "REQUIRED_NUTRIENT_UNKNOWN", code, row.id
                        )
                    )

        with localcontext(calculation_context()):
            totals = {}
            per_serving = {}
            for code in NUTRIENT_CODES:
                values = tuple(row[code] for row in row_amounts)
                total = (
                    None
                    if any(value is None for value in values)
                    else sum((value for value in values if value is not None), Decimal(0))
                )
                totals[code] = _round(total)
                per_serving[code] = _round(
                    None if total is None else total / detail.version.base_servings
                )

        available = sum(value is not None for value in totals.values())
        status = (
            RecipeNutritionV2Status.COMPLETE
            if available == len(NUTRIENT_CODES)
            else RecipeNutritionV2Status.INCOMPLETE
            if available == 0
            else RecipeNutritionV2Status.PARTIAL
        )
        return CanonicalRecipeVersionNutrition(
            recipe_version_id=detail.version.id,
            registry_version=REGISTRY_VERSION,
            nutrient_set_version=NUTRIENT_SET_VERSION,
            composition_calculation_version=COMPOSITION_CALCULATION_VERSION,
            recipe_calculation_version=RECIPE_CALCULATION_VERSION,
            bindings=tuple(bindings),
            required_total=tuple(
                CanonicalNutrientAmount(code, totals[code])
                for code in NUTRIENT_CODES
            ),
            per_base_serving=tuple(
                CanonicalNutrientAmount(code, per_serving[code])
                for code in NUTRIENT_CODES
            ),
            status=status,
            issues=tuple(
                sorted(
                    set(issues),
                    key=lambda item: (
                        item.nutrient_code or "",
                        str(item.recipe_ingredient_id or ""),
                        item.code,
                    ),
                )
            ),
        )

    def consumption_projection(
        self, recipe_version_id: UUID
    ) -> RecipeNutritionConsumptionProjection:
        return project_recipe_nutrition_consumption(self.calculate(recipe_version_id))

    @staticmethod
    def _validate_spec(spec: ReviewedRecipeIngredientBindingSpec) -> None:
        seed = spec.trusted_recipe_seed
        if (
            seed.canonical_code != spec.recipe_code
            or seed.version.source_name != spec.source_name
            or seed.version.source_recipe_id != spec.source_recipe_id
            or seed.version.source_version != spec.source_version
            or seed.initial_is_active is not False
        ):
            raise RecipeNutritionV2ContractError(
                "Binding spec не совпадает с trusted Recipe seed."
            )
        if not isinstance(spec.quantity, Decimal) or not spec.quantity.is_finite() or spec.quantity <= 0:
            raise RecipeNutritionV2ContractError("Binding quantity должна быть положительным Decimal.")
        if type(spec.recipe_version_number) is not int or spec.recipe_version_number <= 0:
            raise RecipeNutritionV2ContractError("RecipeVersion number должен быть положительным.")
        if type(spec.ingredient_position) is not int or spec.ingredient_position <= 0:
            raise RecipeNutritionV2ContractError("RecipeIngredient position должен быть положительным.")
        if type(spec.composition_version) is not int or spec.composition_version <= 0:
            raise RecipeNutritionV2ContractError("Composition version должен быть положительным.")
        try:
            unit = UnitCode(spec.unit)
        except (TypeError, ValueError) as exc:
            raise RecipeNutritionV2ContractError("Неподдерживаемая единица RecipeIngredient.") from exc
        if unit is not UnitCode.GRAM:
            raise RecipeNutritionV2ContractError(
                "RECIPE_COMPOSITION_NUTRITION_V1 binding допускает только граммы."
            )
        available_codes = tuple(code for code, _ in spec.expected_available_amounts)
        if len(available_codes) != len(set(available_codes)):
            raise RecipeNutritionV2ContractError(
                "Reviewed available nutrient code повторяется."
            )
        if len(spec.expected_unknown_codes) != len(set(spec.expected_unknown_codes)):
            raise RecipeNutritionV2ContractError(
                "Reviewed unknown nutrient code повторяется."
            )
        if set(available_codes) & set(spec.expected_unknown_codes):
            raise RecipeNutritionV2ContractError(
                "Нутриент не может быть одновременно AVAILABLE и UNKNOWN."
            )
        if set(available_codes) | set(spec.expected_unknown_codes) != set(NUTRIENT_CODES):
            raise RecipeNutritionV2ContractError(
                "Reviewed publication должна покрывать frozen 54-code request set."
            )
        for code, amount in spec.expected_available_amounts:
            if code not in NUTRIENT_CODES:
                raise RecipeNutritionV2ContractError(
                    "Reviewed nutrient отсутствует в frozen request set."
                )
            if (
                not isinstance(amount, Decimal)
                or not amount.is_finite()
                or amount < 0
            ):
                raise RecipeNutritionV2ContractError(
                    "Reviewed nutrient amount должен быть конечным Decimal."
                )
        if not 1 <= spec.ingredient_position <= len(seed.version.ingredients):
            raise RecipeNutritionV2ContractError(
                "Binding position отсутствует в trusted Recipe seed."
            )
        expected_row = seed.version.ingredients[spec.ingredient_position - 1]
        if (
            expected_row.food_ingredient_code != spec.food_ingredient_code
            or expected_row.quantity != spec.quantity
            or UnitCode(expected_row.unit) is not unit
            or expected_row.optional
        ):
            raise RecipeNutritionV2ContractError(
                "Binding row не совпадает с trusted Recipe seed."
            )

    def _resolve_publication_target(
        self,
        scope: RecipeNutritionV2ReadScope,
        spec: ReviewedRecipeIngredientBindingSpec,
    ):
        seed = spec.trusted_recipe_seed
        recipe = scope.recipes.get_by_code(spec.recipe_code)
        if recipe is None:
            raise RecipeNutritionV2ConflictError("Проверенный Recipe отсутствует.")
        if recipe.canonical_name != seed.canonical_name:
            raise RecipeNutritionV2ConflictError(
                "Recipe identity отличается от trusted Step 9 seed."
            )
        if spec.require_recipe_inactive and recipe.is_active:
            raise RecipeNutritionV2ConflictError(
                "Step 10-A production Recipe должен оставаться inactive."
            )
        candidates = scope.versions.list_by_provenance(
            recipe.id,
            spec.source_name,
            spec.source_recipe_id,
            spec.source_version,
        )
        matches = [
            detail
            for detail in candidates
            if detail.version.version_number == spec.recipe_version_number
        ]
        if len(matches) != 1:
            raise RecipeNutritionV2ConflictError(
                "Exact RecipeVersion provenance/version отсутствует или неоднозначен."
            )
        detail = matches[0]
        if not trusted_recipe_seed_matches(scope, detail, seed):
            raise RecipeNutritionV2ConflictError(
                "RecipeVersion structure/provenance отличается от trusted Step 9 seed."
            )
        rows = [
            row
            for row in detail.ingredients
            if row.position == spec.ingredient_position
        ]
        if len(rows) != 1:
            raise RecipeNutritionV2ConflictError(
                "Exact RecipeIngredient position отсутствует или неоднозначен."
            )
        row = rows[0]
        if row.optional or row.quantity != spec.quantity or row.unit != UnitCode(spec.unit):
            raise RecipeNutritionV2ConflictError(
                "RecipeIngredient quantity/unit/optional отличаются от проверенной authority."
            )
        food = scope.food_ingredients.get_by_code(spec.food_ingredient_code)
        if (
            food is None
            or food.id != row.food_ingredient_id
            or not food.is_active
        ):
            raise RecipeNutritionV2ConflictError(
                "Exact FoodIngredient отсутствует, не совпадает или inactive."
            )
        composition = scope.compositions.find_version(
            food.id, spec.composition_version
        )
        if composition is None:
            raise RecipeNutritionV2ConflictError(
                "Exact FoodCompositionVersion отсутствует."
            )
        return detail, row, food, composition

    @staticmethod
    def _require_reviewed_calculation(spec, row, result) -> None:
        amounts = {item.definition.code: item.amount for item in result.nutrients}
        with localcontext(calculation_context()):
            scaled = {
                code: (
                    None
                    if amounts[code] is None
                    else _round(amounts[code] * row.quantity / result.input_mass_g)
                )
                for code in NUTRIENT_CODES
            }
        expected = dict(spec.expected_available_amounts)
        actual_available = {
            code: amount for code, amount in scaled.items() if amount is not None
        }
        actual_unknown = {code for code, amount in scaled.items() if amount is None}
        if actual_available != expected or actual_unknown != set(
            spec.expected_unknown_codes
        ):
            raise RecipeNutritionV2ConflictError(
                "Composition calculation отличается от reviewed Step 10-A nutrient truth."
            )

    @staticmethod
    def _require_binding_versions(
        binding: RecipeIngredientCompositionBinding,
    ) -> None:
        expected = (
            binding.registry_version == REGISTRY_VERSION
            and binding.nutrient_set_version == NUTRIENT_SET_VERSION
            and binding.composition_calculation_version
            == COMPOSITION_CALCULATION_VERSION
            and binding.recipe_calculation_version == RECIPE_CALCULATION_VERSION
        )
        if not expected:
            raise RecipeNutritionV2UnavailableError(
                "Binding authority versions не соответствуют Step 10-A."
            )

    @staticmethod
    def _calculate_row(scope, row, composition):
        if row.unit is not UnitCode.GRAM or row.optional:
            raise RecipeNutritionV2UnavailableError(
                "RECIPE_COMPOSITION_NUTRITION_V1 поддерживает только required gram rows."
            )
        if composition.input_state is not MassState.INPUT or composition.steps:
            raise RecipeNutritionV2UnavailableError(
                "V1 допускает только untransformed INPUT-basis Composition."
            )
        try:
            result = ApplicabilityAwareCompositionCalculator(
                scope.compositions,
                scope.nutrient_vectors,
                scope.nutrient_registry,
            ).calculate(
                composition.id,
                registry_version=REGISTRY_VERSION,
                nutrient_codes=NUTRIENT_CODES,
            )
        except CompositionUnavailableError as exc:
            raise RecipeNutritionV2UnavailableError(
                "Composition calculation недоступен."
            ) from exc
        if APPLICABILITY_CALCULATION_VERSION != COMPOSITION_CALCULATION_VERSION:
            raise RuntimeError("Composition calculation version constant drifted.")
        if (
            result.calculation_version != COMPOSITION_CALCULATION_VERSION
            or result.requested_nutrient_codes != tuple(sorted(NUTRIENT_CODES))
            or result.input_mass_g <= 0
            or result.output_mass_state is not MassState.INPUT
            or result.output_mass_g != result.input_mass_g
        ):
            raise RecipeNutritionV2UnavailableError(
                "Composition calculation не соответствует RECIPE_COMPOSITION_NUTRITION_V1."
            )
        if tuple(item.definition.code for item in result.nutrients) != tuple(
            sorted(NUTRIENT_CODES)
        ):
            raise RecipeNutritionV2UnavailableError(
                "Composition result не содержит frozen 54-code request set."
            )
        return result
