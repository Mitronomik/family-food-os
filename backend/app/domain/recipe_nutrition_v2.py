"""Composition-backed canonical RecipeVersion nutrition authority (Step 10-A)."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from app.domain.nutrition import NutritionStatus, NutritionValues

REGISTRY_VERSION = "RU_NUTRIENT_REGISTRY_V2"
NUTRIENT_SET_VERSION = "RECIPE_V2_NUTRIENT_SET_V1"
COMPOSITION_CALCULATION_VERSION = "FOOD_COMPOSITION_APPLICABILITY_V2"
RECIPE_CALCULATION_VERSION = "RECIPE_COMPOSITION_NUTRITION_V1"
PREPARED_RECIPE_CALCULATION_VERSION = "RECIPE_PREPARED_OUTPUT_NUTRITION_V1"
RESULT_QUANTUM = Decimal("0.000001")

NUTRIENT_CODES = (
    "ALPHA_LINOLENIC_ACID",
    "BETA_CAROTENE",
    "BIOTIN",
    "CALCIUM",
    "CARBOHYDRATE_AVAILABLE",
    "CARBOHYDRATE_BY_DIFFERENCE",
    "CHLORIDE",
    "CHOLESTEROL",
    "CHOLINE_TOTAL",
    "CHROMIUM",
    "COPPER",
    "DHA",
    "ENERGY_KCAL",
    "EPA",
    "FAT_TOTAL",
    "FATTY_ACIDS_MONOUNSATURATED_TOTAL",
    "FATTY_ACIDS_POLYUNSATURATED_TOTAL",
    "FATTY_ACIDS_SATURATED_TOTAL",
    "FATTY_ACIDS_TRANS_TOTAL",
    "FIBER_TOTAL_DIETARY",
    "FLUORIDE",
    "FOLATE_DFE",
    "FOLATE_TOTAL",
    "FOLIC_ACID",
    "IODINE",
    "IRON",
    "LINOLEIC_ACID",
    "MAGNESIUM",
    "MANGANESE",
    "MOLYBDENUM",
    "NIACIN",
    "NIACIN_EQUIVALENT",
    "PANTOTHENIC_ACID",
    "PHOSPHORUS",
    "POTASSIUM",
    "PROTEIN",
    "RETINOL",
    "RIBOFLAVIN",
    "SELENIUM",
    "SODIUM",
    "STARCH",
    "SUGARS_TOTAL",
    "THIAMIN",
    "VITAMIN_A_RAE",
    "VITAMIN_A_RE",
    "VITAMIN_B12",
    "VITAMIN_B6",
    "VITAMIN_C",
    "VITAMIN_D_D2_D3",
    "VITAMIN_E_ALPHA_TOCOPHEROL",
    "VITAMIN_E_TOCOPHEROL_EQUIVALENT",
    "VITAMIN_K_PHYLLOQUINONE",
    "WATER",
    "ZINC",
)

if len(NUTRIENT_CODES) != 54 or len(set(NUTRIENT_CODES)) != 54:
    raise RuntimeError("Step 10-A nutrient-set constant is not the frozen 54-code tuple.")


class RecipeNutritionV2Status(StrEnum):
    COMPLETE = "COMPLETE"
    PARTIAL = "PARTIAL"
    INCOMPLETE = "INCOMPLETE"


class RecipeNutritionAuthorityKind(StrEnum):
    LEGACY_V1 = "LEGACY_V1"
    COMPOSITION_V2 = "COMPOSITION_V2"
    PREPARED_OUTPUT_V1 = "PREPARED_OUTPUT_V1"


@dataclass(frozen=True)
class RecipeIngredientCompositionBinding:
    recipe_ingredient_id: UUID
    composition_version_id: UUID
    registry_version: str
    nutrient_set_version: str
    composition_calculation_version: str
    recipe_calculation_version: str
    created_at: datetime

    def __post_init__(self) -> None:
        for value in (self.recipe_ingredient_id, self.composition_version_id):
            if not isinstance(value, UUID):
                raise TypeError("Идентификатор binding должен быть UUID.")
        expected = (
            (self.registry_version, REGISTRY_VERSION),
            (self.nutrient_set_version, NUTRIENT_SET_VERSION),
            (
                self.composition_calculation_version,
                COMPOSITION_CALCULATION_VERSION,
            ),
            (self.recipe_calculation_version, RECIPE_CALCULATION_VERSION),
        )
        if any(actual != frozen for actual, frozen in expected):
            raise ValueError("Binding использует неподдерживаемую версию authority.")
        if (
            not isinstance(self.created_at, datetime)
            or self.created_at.tzinfo is None
            or self.created_at.utcoffset() is None
        ):
            raise ValueError("Binding created_at должен быть timezone-aware instant.")


@dataclass(frozen=True)
class PreparedRecipeNutrientValue:
    recipe_version_id: UUID
    registry_version: str
    nutrient_code: str
    amount: Decimal
    provenance_json: str

    def __post_init__(self) -> None:
        if not isinstance(self.recipe_version_id, UUID):
            raise TypeError("RecipeVersion id должен быть UUID.")
        if self.registry_version != REGISTRY_VERSION:
            raise ValueError("Prepared nutrient использует неверный registry_version.")
        if self.nutrient_code not in NUTRIENT_CODES:
            raise ValueError("Prepared nutrient не входит в frozen nutrient set.")
        if (
            not isinstance(self.amount, Decimal)
            or not self.amount.is_finite()
            or self.amount < 0
        ):
            raise ValueError("Prepared nutrient amount должен быть конечным и неотрицательным.")
        if not isinstance(self.provenance_json, str) or not self.provenance_json.strip():
            raise ValueError("Prepared nutrient provenance_json обязателен.")


@dataclass(frozen=True)
class PreparedRecipeNutritionAuthority:
    recipe_version_id: UUID
    registry_version: str
    nutrient_set_version: str
    recipe_calculation_version: str
    output_mass_g: Decimal
    source_name: str
    source_id: str
    source_version: str
    source_locator: str
    source_document_sha256: str
    source_data_type: str
    rights_review_status: str
    rights_basis: str
    review_reference: str
    value_count: int
    value_sha256: str
    created_at: datetime

    def __post_init__(self) -> None:
        if not isinstance(self.recipe_version_id, UUID):
            raise TypeError("RecipeVersion id должен быть UUID.")
        expected = (
            (self.registry_version, REGISTRY_VERSION),
            (self.nutrient_set_version, NUTRIENT_SET_VERSION),
            (self.recipe_calculation_version, PREPARED_RECIPE_CALCULATION_VERSION),
        )
        if any(actual != frozen for actual, frozen in expected):
            raise ValueError("Prepared Recipe authority использует неверную version identity.")
        if (
            not isinstance(self.output_mass_g, Decimal)
            or not self.output_mass_g.is_finite()
            or self.output_mass_g <= 0
        ):
            raise ValueError("Prepared output_mass_g должен быть положительным Decimal.")
        for value, label in (
            (self.source_name, "source_name"),
            (self.source_id, "source_id"),
            (self.source_version, "source_version"),
            (self.source_locator, "source_locator"),
            (self.source_data_type, "source_data_type"),
            (self.rights_review_status, "rights_review_status"),
            (self.rights_basis, "rights_basis"),
            (self.review_reference, "review_reference"),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"Prepared authority {label} обязателен.")
        if (
            not isinstance(self.source_document_sha256, str)
            or len(self.source_document_sha256) != 64
            or any(ch not in "0123456789abcdef" for ch in self.source_document_sha256)
        ):
            raise ValueError("Prepared authority source_document_sha256 должен быть lowercase SHA-256.")
        if not isinstance(self.value_count, int) or isinstance(self.value_count, bool) or self.value_count <= 0:
            raise ValueError("Prepared authority value_count должен быть положительным integer.")
        if (
            not isinstance(self.value_sha256, str)
            or len(self.value_sha256) != 64
            or any(ch not in "0123456789abcdef" for ch in self.value_sha256)
        ):
            raise ValueError("Prepared authority value_sha256 должен быть lowercase SHA-256.")
        if (
            not isinstance(self.created_at, datetime)
            or self.created_at.tzinfo is None
            or self.created_at.utcoffset() is None
        ):
            raise ValueError("Prepared authority created_at должен быть timezone-aware instant.")


@dataclass(frozen=True)
class CanonicalNutrientAmount:
    code: str
    amount: Decimal | None

    def __post_init__(self) -> None:
        if self.code not in NUTRIENT_CODES:
            raise ValueError("Нутриент не входит в RECIPE_V2_NUTRIENT_SET_V1.")
        if self.amount is not None and (
            not isinstance(self.amount, Decimal)
            or not self.amount.is_finite()
            or self.amount < 0
        ):
            raise ValueError("Количество нутриента должно быть конечным и неотрицательным.")

    @property
    def availability(self) -> str:
        return "AVAILABLE" if self.amount is not None else "UNKNOWN"


@dataclass(frozen=True)
class RecipeNutritionV2Issue:
    code: str
    nutrient_code: str | None = None
    recipe_ingredient_id: UUID | None = None


@dataclass(frozen=True)
class CanonicalRecipeVersionNutrition:
    recipe_version_id: UUID
    registry_version: str
    nutrient_set_version: str
    composition_calculation_version: str
    recipe_calculation_version: str
    bindings: tuple[RecipeIngredientCompositionBinding, ...]
    required_total: tuple[CanonicalNutrientAmount, ...]
    per_base_serving: tuple[CanonicalNutrientAmount, ...]
    status: RecipeNutritionV2Status
    issues: tuple[RecipeNutritionV2Issue, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.recipe_version_id, UUID):
            raise TypeError("RecipeVersion id должен быть UUID.")
        expected_versions = (
            (self.registry_version, REGISTRY_VERSION),
            (self.nutrient_set_version, NUTRIENT_SET_VERSION),
            (
                self.composition_calculation_version,
                COMPOSITION_CALCULATION_VERSION,
            ),
            (self.recipe_calculation_version, RECIPE_CALCULATION_VERSION),
        )
        if any(actual != frozen for actual, frozen in expected_versions):
            raise ValueError("Canonical Recipe Nutrition использует неверную authority version.")
        for values in (self.required_total, self.per_base_serving):
            if tuple(item.code for item in values) != NUTRIENT_CODES:
                raise ValueError("Canonical Recipe Nutrition должен содержать ровно 54 кода.")
        object.__setattr__(self, "status", RecipeNutritionV2Status(self.status))

    def total_amount(self, code: str) -> Decimal | None:
        return next(item.amount for item in self.required_total if item.code == code)

    def per_serving_amount(self, code: str) -> Decimal | None:
        return next(item.amount for item in self.per_base_serving if item.code == code)


@dataclass(frozen=True)
class RecipeNutritionConsumptionProjection:
    recipe_version_id: UUID
    required_total: NutritionValues
    per_base_serving: NutritionValues
    legacy_status: NutritionStatus
    authority_kind: RecipeNutritionAuthorityKind
    canonical_status: RecipeNutritionV2Status | None
    exact_energy_ready: bool
    registry_version: str | None
    nutrient_set_version: str | None
    composition_calculation_version: str | None
    recipe_calculation_version: str | None
