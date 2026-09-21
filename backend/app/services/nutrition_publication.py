"""Reviewed transactional publication of one V2 nutrition/ATOMIC bundle."""

from collections.abc import Callable, Mapping
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from decimal import Decimal
from enum import StrEnum
import json
from uuid import UUID, uuid4

from app.domain.food_composition import (
    CompositionKind,
    CompositionProvenance,
    FoodCompositionVersion,
    MassState,
)
from app.domain.food_ingredients import (
    FoodIngredient,
    FoodNutritionProfile,
    NutritionObservationState,
    NutritionSourceObservation,
    normalize_unicode_search_key,
    validate_nutrition_profile_observations,
)
from app.domain.nutrient_method_adapters import (
    REGISTRY_V2,
    NutrientMethodAdapterError,
    binding_for_code,
    resolve_method,
)
from app.domain.nutrient_vector import (
    NutrientValueEvidenceError,
    NutrientVectorUnavailableError,
    decode_v2_value_evidence,
)
from app.domain.nutrient_vector_backfill_v1 import value_set_digest
from app.domain.units import UnitCode
from app.services.food_ingredient_contracts import (
    FoodCataloguePersistenceConflictError,
)
from app.services.nutrition_publication_contracts import (
    NutritionPublicationPersistenceConflictError,
    NutritionPublicationUnitOfWork,
)

WriteScopeFactory = Callable[[], NutritionPublicationUnitOfWork]
IdFactory = Callable[[], UUID]
Clock = Callable[[], datetime]


class PublicationIngredientAction(StrEnum):
    REUSE_EXISTING = "REUSE_EXISTING"
    CREATE_REVIEWED = "CREATE_REVIEWED"


class NutritionPublicationContractError(ValueError):
    """The requested reviewed bundle violates the frozen Step 3 contract."""


class NutritionPublicationConflictError(ValueError):
    """Persisted immutable truth conflicts with the requested reviewed bundle."""


@dataclass(frozen=True)
class ReviewedIngredientSpec:
    action: PublicationIngredientAction | str
    canonical_code: str
    canonical_name: str
    category_code: str
    default_unit: UnitCode | str
    density_g_per_ml: Decimal | None = None
    edible_fraction: Decimal | None = None
    allergens_reviewed: bool = False
    allergen_codes: tuple[str, ...] = ()
    storage_profile_code: str | None = None


@dataclass(frozen=True)
class ReviewedSourceObservationSpec:
    source_field: str
    state: NutritionObservationState | str
    source_literal: str | None
    method_reference: str | None
    source_locator: str


@dataclass(frozen=True)
class ReviewedNutritionProfileSpec:
    basis_grams: Decimal
    kcal: Decimal | None
    protein_g: Decimal | None
    fat_g: Decimal | None
    carbohydrates_g: Decimal | None
    fiber_g: Decimal | None
    source_name: str
    source_id: str
    source_version: str
    source_data_type: str | None
    verified_at: datetime
    estimated: bool | None
    observations: tuple[ReviewedSourceObservationSpec, ...] = ()


@dataclass(frozen=True)
class ReviewedNutrientValueSpec:
    nutrient_code: str
    amount: Decimal
    provenance_json: str


@dataclass(frozen=True)
class ReviewedNutrientVectorSpec:
    registry_version: str
    values: tuple[ReviewedNutrientValueSpec, ...]
    observations_json: str
    value_count: int
    value_sha256: str


@dataclass(frozen=True)
class ReviewedAtomicCompositionSpec:
    version: int
    input_state: MassState | str
    provenance: CompositionProvenance


@dataclass(frozen=True)
class ReviewedNutritionPublicationBundle:
    ingredient: ReviewedIngredientSpec
    profile: ReviewedNutritionProfileSpec
    vector: ReviewedNutrientVectorSpec
    atomic_composition: ReviewedAtomicCompositionSpec


@dataclass(frozen=True)
class NutritionPublicationResult:
    ingredient_id: UUID
    profile_id: UUID
    composition_version_id: UUID
    ingredient_created: bool
    bundle_created: bool
    nutrient_value_count: int


class ReviewedNutritionPublicationService:
    def __init__(
        self,
        write_scope_factory: WriteScopeFactory,
        *,
        id_factory: IdFactory = uuid4,
        clock: Clock | None = None,
    ) -> None:
        self._write_scope_factory = write_scope_factory
        self._id_factory = id_factory
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def publish(
        self, bundle: ReviewedNutritionPublicationBundle
    ) -> NutritionPublicationResult:
        if not isinstance(bundle, ReviewedNutritionPublicationBundle):
            raise TypeError("Нужен проверенный пакет публикации питания.")
        now = self._clock()
        if now.tzinfo is None or now.utcoffset() is None:
            raise NutritionPublicationContractError(
                "Часы публикации должны возвращать timezone-aware instant."
            )
        now = now.astimezone(timezone.utc)

        with self._write_scope_factory() as uow:
            ingredient, ingredient_created = self._resolve_ingredient(
                uow, bundle.ingredient, now=now
            )
            existing_profile = uow.nutrition_profiles.get_by_provenance(
                ingredient.id,
                bundle.profile.source_name,
                bundle.profile.source_id,
                bundle.profile.source_version,
            )
            if existing_profile is not None:
                existing_observations = uow.nutrition_profiles.list_observations(
                    existing_profile.id
                )
                expected_profile, expected_observations = self._build_profile(
                    bundle.profile,
                    ingredient.id,
                    profile_id=existing_profile.id,
                    created_at=existing_profile.created_at,
                    existing_observations=existing_observations,
                    now=now,
                )
                if existing_profile != expected_profile:
                    raise NutritionPublicationConflictError(
                        "Закреплённый профиль отличается от проверенного пакета."
                    )
                if existing_observations != expected_observations:
                    raise NutritionPublicationConflictError(
                        "Наблюдения профиля отличаются от проверенного пакета."
                    )
                rows = self._validate_vector(
                    uow, expected_profile, bundle.vector
                )
                return self._assert_existing_bundle(
                    uow,
                    bundle,
                    ingredient,
                    expected_profile,
                    expected_observations,
                    rows,
                )

            profile, observations = self._build_profile(
                bundle.profile,
                ingredient.id,
                profile_id=self._id_factory(),
                created_at=now,
                existing_observations=(),
                now=now,
            )
            rows = self._validate_vector(uow, profile, bundle.vector)
            existing_composition = uow.compositions.find_version(
                ingredient.id, bundle.atomic_composition.version
            )
            if existing_composition is not None:
                raise NutritionPublicationConflictError(
                    "Запрошенная версия ATOMIC уже занята другим снимком."
                )
            composition = self._build_composition(
                bundle.atomic_composition,
                ingredient.id,
                profile.id,
                composition_id=self._id_factory(),
            )

            try:
                if ingredient_created:
                    uow.ingredients.add(ingredient)
                uow.nutrition_profiles.add_unsealed(profile, observations)
                uow.publish_vector(
                    profile.id,
                    registry_version=bundle.vector.registry_version,
                    values=rows,
                    value_sha256=bundle.vector.value_sha256,
                    observations_json=bundle.vector.observations_json,
                )
                uow.compositions.add_versions((composition,))
                verified = self._assert_existing_bundle(
                    uow,
                    bundle,
                    ingredient,
                    profile,
                    observations,
                    rows,
                    expected_composition=composition,
                )
                uow.commit()
            except (
                FoodCataloguePersistenceConflictError,
                NutritionPublicationPersistenceConflictError,
            ) as exc:
                raise NutritionPublicationConflictError(
                    "Публикация конфликтует с уже сохранённой истиной."
                ) from exc

            return replace(
                verified,
                ingredient_created=ingredient_created,
                bundle_created=True,
            )

    def _resolve_ingredient(
        self,
        uow: NutritionPublicationUnitOfWork,
        spec: ReviewedIngredientSpec,
        *,
        now: datetime,
    ) -> tuple[FoodIngredient, bool]:
        try:
            action = PublicationIngredientAction(spec.action)
        except (TypeError, ValueError) as exc:
            raise NutritionPublicationContractError(
                "Неизвестное действие с FoodIngredient."
            ) from exc

        candidate = FoodIngredient(
            id=self._id_factory(),
            canonical_code=spec.canonical_code,
            canonical_name=spec.canonical_name,
            canonical_name_key=normalize_unicode_search_key(spec.canonical_name),
            category_code=spec.category_code,
            default_unit=spec.default_unit,  # type: ignore[arg-type]
            density_g_per_ml=spec.density_g_per_ml,
            edible_fraction=spec.edible_fraction,
            allergens_reviewed=spec.allergens_reviewed,
            allergen_codes=spec.allergen_codes,
            storage_profile_code=spec.storage_profile_code,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        existing = uow.ingredients.get_by_code(candidate.canonical_code)
        if existing is None:
            if action is PublicationIngredientAction.REUSE_EXISTING:
                raise NutritionPublicationConflictError(
                    "Проверенный FoodIngredient отсутствует."
                )
            name_owner = uow.ingredients.get_by_name_key(candidate.canonical_name_key)
            alias_owner = uow.aliases.get_by_key(candidate.canonical_name_key)
            if name_owner is not None or alias_owner is not None:
                raise NutritionPublicationConflictError(
                    "Каноническое имя нового FoodIngredient уже занято."
                )
            return candidate, True

        expected = replace(
            candidate,
            id=existing.id,
            created_at=existing.created_at,
            updated_at=existing.updated_at,
        )
        if not existing.is_active or existing != expected:
            raise NutritionPublicationConflictError(
                "Существующий FoodIngredient отличается от проверенной идентичности."
            )
        return existing, False

    def _build_profile(
        self,
        spec: ReviewedNutritionProfileSpec,
        ingredient_id: UUID,
        *,
        profile_id: UUID,
        created_at: datetime,
        existing_observations: tuple[NutritionSourceObservation, ...],
        now: datetime,
    ) -> tuple[FoodNutritionProfile, tuple[NutritionSourceObservation, ...]]:
        profile = FoodNutritionProfile(
            id=profile_id,
            food_ingredient_id=ingredient_id,
            basis_grams=spec.basis_grams,
            kcal=spec.kcal,
            protein_g=spec.protein_g,
            fat_g=spec.fat_g,
            carbohydrates_g=spec.carbohydrates_g,
            fiber_g=spec.fiber_g,
            source_name=spec.source_name,
            source_id=spec.source_id,
            source_version=spec.source_version,
            source_data_type=spec.source_data_type,
            verified_at=spec.verified_at,
            estimated=spec.estimated,
            is_current=False,
            created_at=created_at,
        )
        by_field = {value.source_field: value for value in existing_observations}
        observations = []
        for observation_spec in spec.observations:
            existing = by_field.get(observation_spec.source_field)
            observations.append(
                NutritionSourceObservation(
                    id=existing.id if existing is not None else self._id_factory(),
                    profile_id=profile.id,
                    source_field=observation_spec.source_field,
                    state=observation_spec.state,  # type: ignore[arg-type]
                    source_literal=observation_spec.source_literal,
                    method_reference=observation_spec.method_reference,
                    source_locator=observation_spec.source_locator,
                    created_at=existing.created_at if existing is not None else now,
                )
            )
        return profile, validate_nutrition_profile_observations(
            profile, tuple(observations)
        )

    def _validate_vector(
        self,
        uow: NutritionPublicationUnitOfWork,
        profile: FoodNutritionProfile,
        spec: ReviewedNutrientVectorSpec,
    ) -> tuple[Mapping[str, object], ...]:
        if spec.registry_version != REGISTRY_V2:
            raise NutritionPublicationContractError(
                "Step 3 публикует только RU_NUTRIENT_REGISTRY_V2."
            )
        try:
            observations = json.loads(spec.observations_json)
        except (TypeError, json.JSONDecodeError) as exc:
            raise NutritionPublicationContractError(
                "История наблюдений вектора должна быть валидным JSON."
            ) from exc
        if not isinstance(observations, list):
            raise NutritionPublicationContractError(
                "История наблюдений вектора должна быть JSON-массивом."
            )

        codes = [value.nutrient_code for value in spec.values]
        if len(codes) != len(set(codes)):
            raise NutritionPublicationContractError(
                "Нутриент повторяется в публикуемом V2 векторе."
            )
        rows: list[Mapping[str, object]] = []
        for value in sorted(spec.values, key=lambda item: item.nutrient_code):
            if not isinstance(value.amount, Decimal):
                raise TypeError("Количество нутриента публикации должно быть Decimal.")
            if not value.amount.is_finite() or value.amount < 0:
                raise NutritionPublicationContractError(
                    "Количество нутриента должно быть конечным и неотрицательным."
                )
            try:
                definition = uow.nutrient_registry.get(
                    spec.registry_version, value.nutrient_code
                )
            except NutrientVectorUnavailableError as exc:
                raise NutritionPublicationContractError(
                    "Нутриент отсутствует в утверждённом V2 реестре."
                ) from exc
            try:
                decoded = decode_v2_value_evidence(
                    value.provenance_json,
                    profile=profile,
                    expected_registry_version=spec.registry_version,
                    expected_nutrient_code=value.nutrient_code,
                    expected_amount=value.amount,
                )
            except NutrientValueEvidenceError as exc:
                raise NutritionPublicationContractError(str(exc)) from exc
            if decoded.provenance.source_unit != definition.unit:
                raise NutritionPublicationContractError(
                    "Step 3 не авторизует неявное преобразование единиц нутриента."
                )
            binding = binding_for_code(spec.registry_version, value.nutrient_code)
            if binding is not None:
                try:
                    resolved = resolve_method(
                        spec.registry_version,
                        binding.nutrient_kind,
                        evidence_json=value.provenance_json,
                    )
                except NutrientMethodAdapterError as exc:
                    raise NutritionPublicationContractError(
                        "Метод источника несовместим с определением нутриента V2."
                    ) from exc
                if resolved is not decoded.method:
                    raise NutritionPublicationContractError(
                        "Декодированный и разрешённый методы нутриента расходятся."
                    )
            rows.append(
                {
                    "nutrient_code": value.nutrient_code,
                    "amount": value.amount,
                    "provenance_json": value.provenance_json,
                }
            )

        actual_digest = value_set_digest(rows)
        if spec.value_count != len(rows) or spec.value_sha256 != actual_digest:
            raise NutritionPublicationContractError(
                "Ссылка на V2 вектор не совпадает с проверенным набором значений."
            )
        return tuple(rows)

    def _build_composition(
        self,
        spec: ReviewedAtomicCompositionSpec,
        ingredient_id: UUID,
        profile_id: UUID,
        *,
        composition_id: UUID,
    ) -> FoodCompositionVersion:
        return FoodCompositionVersion(
            id=composition_id,
            food_ingredient_id=ingredient_id,
            version=spec.version,
            kind=CompositionKind.ATOMIC,
            input_state=MassState(spec.input_state),
            provenance=spec.provenance,
            profile_id=profile_id,
        )

    def _assert_existing_bundle(
        self,
        uow: NutritionPublicationUnitOfWork,
        bundle: ReviewedNutritionPublicationBundle,
        ingredient: FoodIngredient,
        expected_profile: FoodNutritionProfile,
        expected_observations: tuple[NutritionSourceObservation, ...],
        expected_rows: tuple[Mapping[str, object], ...],
        *,
        expected_composition: FoodCompositionVersion | None = None,
    ) -> NutritionPublicationResult:
        persisted_profile = uow.nutrition_profiles.get_by_provenance(
            ingredient.id,
            expected_profile.source_name,
            expected_profile.source_id,
            expected_profile.source_version,
        )
        if persisted_profile != expected_profile:
            raise NutritionPublicationConflictError(
                "Профиль публикации отсутствует или отличается после записи."
            )
        if (
            uow.nutrition_profiles.list_observations(expected_profile.id)
            != expected_observations
        ):
            raise NutritionPublicationConflictError(
                "Наблюдения публикации отсутствуют или отличаются после записи."
            )
        try:
            vector = uow.nutrient_vectors.get(expected_profile.id)
        except NutrientVectorUnavailableError as exc:
            raise NutritionPublicationConflictError(
                "Закреплённый V2 вектор отсутствует или повреждён."
            ) from exc
        actual_rows = tuple(
            {
                "nutrient_code": value.definition.code,
                "amount": value.amount,
                "provenance_json": value.provenance.evidence_json,
            }
            for value in sorted(vector.values, key=lambda item: item.definition.code)
        )
        if (
            vector.registry_version != bundle.vector.registry_version
            or vector.observations_json != bundle.vector.observations_json
            or actual_rows != expected_rows
            or len(actual_rows) != bundle.vector.value_count
            or value_set_digest(actual_rows) != bundle.vector.value_sha256
        ):
            raise NutritionPublicationConflictError(
                "Закреплённый V2 вектор отличается от проверенного пакета."
            )

        persisted_composition = uow.compositions.find_version(
            ingredient.id, bundle.atomic_composition.version
        )
        if persisted_composition is None:
            raise NutritionPublicationConflictError(
                "ATOMIC версия проверенного пакета отсутствует."
            )
        expected = expected_composition or self._build_composition(
            bundle.atomic_composition,
            ingredient.id,
            expected_profile.id,
            composition_id=persisted_composition.id,
        )
        if persisted_composition != expected:
            raise NutritionPublicationConflictError(
                "ATOMIC версия отличается от проверенного пакета."
            )
        return NutritionPublicationResult(
            ingredient_id=ingredient.id,
            profile_id=expected_profile.id,
            composition_version_id=persisted_composition.id,
            ingredient_created=False,
            bundle_created=False,
            nutrient_value_count=len(actual_rows),
        )
