"""Registry-version-aware nutrient/method adapters.

Nutrient identity and observation method are separate concerns. V1 keeps its
historical fixed projection. V2 requires explicit method evidence for present
values so a method can never be inferred from a nutrient code or matching unit.
"""

from dataclasses import dataclass
import json

from app.domain.nutrient_vector_backfill_v1 import REGISTRY_VERSION as REGISTRY_V1
from app.domain.nutrition_methodology import NutrientKind, ObservationMethod

REGISTRY_V2 = "RU_NUTRIENT_REGISTRY_V2"
ADAPTER_VERSION_V2 = "RU_NUTRIENT_METHOD_ADAPTER_V2"


class NutrientMethodAdapterError(ValueError):
    """Registry/method evidence cannot support the requested interpretation."""


@dataclass(frozen=True)
class NutrientMethodBinding:
    nutrient_code: str
    nutrient_kind: NutrientKind
    allowed_methods: tuple[ObservationMethod, ...]
    legacy_default_method: ObservationMethod | None = None


_V1_BINDINGS = (
    NutrientMethodBinding(
        "PROTEIN", NutrientKind.PROTEIN, (ObservationMethod.PUBLISHED,),
        ObservationMethod.PUBLISHED,
    ),
    NutrientMethodBinding(
        "FAT_TOTAL", NutrientKind.FAT, (ObservationMethod.PUBLISHED,),
        ObservationMethod.PUBLISHED,
    ),
    NutrientMethodBinding(
        "FIBER_TOTAL_DIETARY", NutrientKind.FIBRE, (ObservationMethod.PUBLISHED,),
        ObservationMethod.PUBLISHED,
    ),
    NutrientMethodBinding(
        "CARBOHYDRATE_AVAILABLE",
        NutrientKind.AVAILABLE_CARBOHYDRATE,
        (ObservationMethod.AVAILABLE_SUMMATION,),
        ObservationMethod.AVAILABLE_SUMMATION,
    ),
    NutrientMethodBinding(
        "CARBOHYDRATE_BY_DIFFERENCE",
        NutrientKind.TOTAL_CARBOHYDRATE,
        (ObservationMethod.TOTAL_BY_DIFFERENCE,),
        ObservationMethod.TOTAL_BY_DIFFERENCE,
    ),
    NutrientMethodBinding(
        "ENERGY_KCAL",
        NutrientKind.PUBLISHED_ENERGY,
        (ObservationMethod.PUBLISHED,),
        ObservationMethod.PUBLISHED,
    ),
)

_V2_BINDINGS = (
    NutrientMethodBinding(
        "PROTEIN",
        NutrientKind.PROTEIN,
        (ObservationMethod.ANALYTICAL, ObservationMethod.PUBLISHED),
    ),
    NutrientMethodBinding(
        "FAT_TOTAL",
        NutrientKind.FAT,
        (ObservationMethod.ANALYTICAL, ObservationMethod.PUBLISHED),
    ),
    NutrientMethodBinding(
        "FIBER_TOTAL_DIETARY",
        NutrientKind.FIBRE,
        (ObservationMethod.ANALYTICAL, ObservationMethod.PUBLISHED),
    ),
    NutrientMethodBinding(
        "CARBOHYDRATE_AVAILABLE",
        NutrientKind.AVAILABLE_CARBOHYDRATE,
        (
            ObservationMethod.AVAILABLE_SUMMATION,
            ObservationMethod.AVAILABLE_BY_DIFFERENCE,
            ObservationMethod.AVAILABLE_PUBLISHED_ROW_UNSPECIFIED,
        ),
    ),
    NutrientMethodBinding(
        "CARBOHYDRATE_BY_DIFFERENCE",
        NutrientKind.TOTAL_CARBOHYDRATE,
        (ObservationMethod.TOTAL_BY_DIFFERENCE,),
    ),
    NutrientMethodBinding(
        "ENERGY_KCAL",
        NutrientKind.PUBLISHED_ENERGY,
        (ObservationMethod.PUBLISHED,),
    ),
)

_BINDINGS = {
    REGISTRY_V1: {binding.nutrient_kind: binding for binding in _V1_BINDINGS},
    REGISTRY_V2: {binding.nutrient_kind: binding for binding in _V2_BINDINGS},
}


def supported_registry(registry_version: str) -> bool:
    return registry_version in _BINDINGS


def binding_for_kind(
    registry_version: str, nutrient_kind: NutrientKind
) -> NutrientMethodBinding:
    if not isinstance(nutrient_kind, NutrientKind):
        raise TypeError("Нужно типизированное определение нутриента.")
    try:
        return _BINDINGS[registry_version][nutrient_kind]
    except KeyError as exc:
        raise NutrientMethodAdapterError(
            "Для версии реестра нет адаптера этого показателя."
        ) from exc


def resolve_method(
    registry_version: str,
    nutrient_kind: NutrientKind,
    *,
    evidence_json: str | None,
) -> ObservationMethod:
    """Resolve method separately from nutrient identity.

    V1 is intentionally frozen to its accepted historical projection. V2 present
    values require an explicit method_code in provenance. For an unavailable
    observation callers may pass no evidence and keep the value unavailable.
    """

    binding = binding_for_kind(registry_version, nutrient_kind)
    if registry_version == REGISTRY_V1:
        assert binding.legacy_default_method is not None
        return binding.legacy_default_method
    if registry_version != REGISTRY_V2:
        raise NutrientMethodAdapterError("Неизвестная версия реестра нутриентов.")
    if evidence_json is None:
        return ObservationMethod.UNSUPPORTED
    try:
        payload = json.loads(evidence_json)
    except (TypeError, json.JSONDecodeError) as exc:
        raise NutrientMethodAdapterError(
            "Происхождение значения не содержит валидный JSON метода."
        ) from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("method_code"), str):
        raise NutrientMethodAdapterError(
            "V2 требует явный method_code в происхождении значения."
        )
    try:
        method = ObservationMethod(payload["method_code"])
    except ValueError as exc:
        raise NutrientMethodAdapterError("Неизвестный method_code.") from exc
    if method not in binding.allowed_methods:
        raise NutrientMethodAdapterError(
            "Метод несовместим с определением нутриента V2."
        )
    return method


def canonical_code_for_kind(
    registry_version: str, nutrient_kind: NutrientKind
) -> str:
    return binding_for_kind(registry_version, nutrient_kind).nutrient_code


def binding_for_code(
    registry_version: str, nutrient_code: str
) -> NutrientMethodBinding | None:
    """Return the reviewed method binding for a canonical code when one exists."""

    if not isinstance(nutrient_code, str) or not nutrient_code:
        raise TypeError("Нужен стабильный код нутриента.")
    try:
        bindings = _BINDINGS[registry_version].values()
    except KeyError as exc:
        raise NutrientMethodAdapterError(
            "Неизвестная версия реестра нутриентов."
        ) from exc
    return next(
        (binding for binding in bindings if binding.nutrient_code == nutrient_code),
        None,
    )
