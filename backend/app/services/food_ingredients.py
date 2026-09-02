"""Application operations for the canonical platform Food Catalogue."""

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from app.domain.food_ingredients import (
    FoodIngredient,
    FoodNutritionProfile,
    IngredientAlias,
    deactivate_food_ingredient,
    normalize_unicode_search_key,
)
from app.domain.units import UnitCode
from app.services.food_ingredient_contracts import (
    FoodCatalogueReadScope,
    FoodCatalogueUnitOfWork,
)

WriteScopeFactory = Callable[[], FoodCatalogueUnitOfWork]
ReadScopeFactory = Callable[[], FoodCatalogueReadScope]
IdFactory = Callable[[], UUID]
Clock = Callable[[], datetime]

MAX_CATALOGUE_RESULT_LIMIT = 200


class FoodIngredientNotFoundError(LookupError):
    pass


class FoodCatalogueConflictError(ValueError):
    pass


@dataclass(frozen=True)
class TrustedAliasSeed:
    alias: str
    language_code: str | None = "ru"


@dataclass(frozen=True)
class TrustedNutritionSeed:
    basis_grams: Decimal
    kcal: Decimal
    protein_g: Decimal
    fat_g: Decimal
    carbohydrates_g: Decimal
    fiber_g: Decimal | None
    source_name: str
    source_id: str
    source_version: str
    source_data_type: str | None
    verified_at: datetime
    estimated: bool | None = False


@dataclass(frozen=True)
class TrustedFoodIngredientSeed:
    canonical_code: str
    canonical_name: str
    category_code: str
    default_unit: UnitCode | str
    density_g_per_ml: Decimal | None
    edible_fraction: Decimal | None
    allergens_reviewed: bool
    allergen_codes: tuple[str, ...]
    storage_profile_code: str | None
    aliases: tuple[TrustedAliasSeed, ...]
    nutrition: TrustedNutritionSeed


@dataclass(frozen=True)
class FoodCatalogueSeedSummary:
    ingredients_inserted: int = 0
    ingredients_existing: int = 0
    aliases_inserted: int = 0
    aliases_existing: int = 0
    nutrition_profiles_inserted: int = 0
    nutrition_profiles_existing: int = 0
    conflicts: int = 0


class FoodCatalogueService:
    """Coordinates catalogue repositories without exposing adapter connections."""

    def __init__(
        self,
        write_scope_factory: WriteScopeFactory,
        read_scope_factory: ReadScopeFactory,
        *,
        id_factory: IdFactory = uuid4,
        clock: Clock | None = None,
    ) -> None:
        self._write_scope_factory = write_scope_factory
        self._read_scope_factory = read_scope_factory
        self._id_factory = id_factory
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def get(self, ingredient_id: UUID) -> FoodIngredient:
        with self._read_scope_factory() as scope:
            ingredient = scope.ingredients.get(ingredient_id)
            if ingredient is None:
                raise FoodIngredientNotFoundError(ingredient_id)
            return ingredient

    def get_by_code(self, canonical_code: str) -> FoodIngredient:
        with self._read_scope_factory() as scope:
            ingredient = scope.ingredients.get_by_code(canonical_code)
            if ingredient is None:
                raise FoodIngredientNotFoundError(canonical_code)
            return ingredient

    def list_active(self, *, limit: int = 100) -> list[FoodIngredient]:
        bounded_limit = _bounded_limit(limit)
        with self._read_scope_factory() as scope:
            return scope.ingredients.list_active(limit=bounded_limit)

    def search(self, query: str, *, limit: int = 20) -> list[FoodIngredient]:
        search_key = normalize_unicode_search_key(query, field="query")
        bounded_limit = _bounded_limit(limit)
        with self._read_scope_factory() as scope:
            return scope.ingredients.search_active(search_key, limit=bounded_limit)

    def add_trusted_ingredient(self, seed: TrustedFoodIngredientSeed) -> FoodIngredient:
        now = self._clock()
        with self._write_scope_factory() as scope:
            if scope.ingredients.get_by_code(seed.canonical_code) is not None:
                raise FoodCatalogueConflictError(
                    f"canonical_code {seed.canonical_code!r} already exists."
                )
            ingredient = self._new_ingredient(seed, now=now)
            self._ensure_name_available(scope, ingredient)
            scope.ingredients.add(ingredient)
            for alias_seed in seed.aliases:
                self._add_alias_in_scope(scope, ingredient, alias_seed, now=now)
            self._attach_nutrition_in_scope(
                scope, ingredient.id, seed.nutrition, now=now
            )
            scope.commit()
        return ingredient

    def add_alias(
        self,
        ingredient_id: UUID,
        *,
        alias: str,
        language_code: str | None = "ru",
    ) -> IngredientAlias:
        now = self._clock()
        alias_seed = TrustedAliasSeed(alias=alias, language_code=language_code)
        with self._write_scope_factory() as scope:
            ingredient = scope.ingredients.get(ingredient_id)
            if ingredient is None:
                raise FoodIngredientNotFoundError(ingredient_id)
            value, _ = self._add_alias_in_scope(scope, ingredient, alias_seed, now=now)
            scope.commit()
        return value

    def attach_nutrition_profile(
        self, ingredient_id: UUID, nutrition: TrustedNutritionSeed
    ) -> FoodNutritionProfile:
        now = self._clock()
        with self._write_scope_factory() as scope:
            if scope.ingredients.get(ingredient_id) is None:
                raise FoodIngredientNotFoundError(ingredient_id)
            profile, _ = self._attach_nutrition_in_scope(
                scope, ingredient_id, nutrition, now=now
            )
            scope.commit()
        return profile

    def deactivate(self, ingredient_id: UUID) -> FoodIngredient:
        now = self._clock()
        with self._write_scope_factory() as scope:
            ingredient = scope.ingredients.get(ingredient_id)
            if ingredient is None:
                raise FoodIngredientNotFoundError(ingredient_id)
            deactivated = deactivate_food_ingredient(ingredient, updated_at=now)
            scope.ingredients.set_active(
                ingredient_id, active=False, updated_at=deactivated.updated_at
            )
            scope.commit()
        return deactivated

    def reconcile_seed(
        self, entries: Iterable[TrustedFoodIngredientSeed]
    ) -> FoodCatalogueSeedSummary:
        """Atomically reconcile a fully parsed and validated trusted seed."""

        entries = tuple(entries)
        now = self._clock()
        counters = {
            "ingredients_inserted": 0,
            "ingredients_existing": 0,
            "aliases_inserted": 0,
            "aliases_existing": 0,
            "nutrition_profiles_inserted": 0,
            "nutrition_profiles_existing": 0,
        }
        with self._write_scope_factory() as scope:
            for seed in entries:
                existing = scope.ingredients.get_by_code(seed.canonical_code)
                if existing is None:
                    ingredient = self._new_ingredient(seed, now=now)
                    self._ensure_name_available(scope, ingredient)
                    scope.ingredients.add(ingredient)
                    counters["ingredients_inserted"] += 1
                else:
                    ingredient = existing
                    self._assert_seed_ingredient_matches(ingredient, seed, now=now)
                    counters["ingredients_existing"] += 1

                for alias_seed in seed.aliases:
                    _, inserted = self._add_alias_in_scope(
                        scope, ingredient, alias_seed, now=now
                    )
                    counters[
                        "aliases_inserted" if inserted else "aliases_existing"
                    ] += 1

                _, inserted = self._attach_nutrition_in_scope(
                    scope, ingredient.id, seed.nutrition, now=now
                )
                counters[
                    "nutrition_profiles_inserted"
                    if inserted
                    else "nutrition_profiles_existing"
                ] += 1
            scope.commit()
        return FoodCatalogueSeedSummary(**counters)

    def _new_ingredient(
        self, seed: TrustedFoodIngredientSeed, *, now: datetime
    ) -> FoodIngredient:
        canonical_name_key = normalize_unicode_search_key(
            seed.canonical_name, field="canonical_name"
        )
        return FoodIngredient(
            id=self._id_factory(),
            canonical_code=seed.canonical_code,
            canonical_name=seed.canonical_name,
            canonical_name_key=canonical_name_key,
            category_code=seed.category_code,
            default_unit=seed.default_unit,  # type: ignore[arg-type]
            density_g_per_ml=seed.density_g_per_ml,
            edible_fraction=seed.edible_fraction,
            allergens_reviewed=seed.allergens_reviewed,
            allergen_codes=seed.allergen_codes,
            storage_profile_code=seed.storage_profile_code,
            is_active=True,
            created_at=now,
            updated_at=now,
        )

    @staticmethod
    def _ensure_name_available(
        scope: FoodCatalogueUnitOfWork, ingredient: FoodIngredient
    ) -> None:
        if scope.ingredients.get_by_name_key(ingredient.canonical_name_key) is not None:
            raise FoodCatalogueConflictError(
                f"canonical name key {ingredient.canonical_name_key!r} already exists."
            )
        alias = scope.aliases.get_by_key(ingredient.canonical_name_key)
        if alias is not None:
            raise FoodCatalogueConflictError(
                f"canonical name key {ingredient.canonical_name_key!r} collides with an alias."
            )

    def _add_alias_in_scope(
        self,
        scope: FoodCatalogueUnitOfWork,
        ingredient: FoodIngredient,
        seed: TrustedAliasSeed,
        *,
        now: datetime,
    ) -> tuple[IngredientAlias, bool]:
        alias_key = normalize_unicode_search_key(seed.alias, field="alias")
        canonical = scope.ingredients.get_by_name_key(alias_key)
        if canonical is not None and canonical.id != ingredient.id:
            raise FoodCatalogueConflictError(
                f"alias key {alias_key!r} collides with {canonical.canonical_code}."
            )
        existing = scope.aliases.get_by_key(alias_key)
        if existing is not None:
            if existing.food_ingredient_id != ingredient.id:
                raise FoodCatalogueConflictError(
                    f"alias key {alias_key!r} maps to another FoodIngredient."
                )
            return existing, False
        value = IngredientAlias(
            id=self._id_factory(),
            food_ingredient_id=ingredient.id,
            alias=seed.alias,
            alias_key=alias_key,
            language_code=seed.language_code,
            created_at=now,
        )
        scope.aliases.add(value)
        return value, True

    def _attach_nutrition_in_scope(
        self,
        scope: FoodCatalogueUnitOfWork,
        ingredient_id: UUID,
        seed: TrustedNutritionSeed,
        *,
        now: datetime,
    ) -> tuple[FoodNutritionProfile, bool]:
        candidate = FoodNutritionProfile(
            id=self._id_factory(),
            food_ingredient_id=ingredient_id,
            basis_grams=seed.basis_grams,
            kcal=seed.kcal,
            protein_g=seed.protein_g,
            fat_g=seed.fat_g,
            carbohydrates_g=seed.carbohydrates_g,
            fiber_g=seed.fiber_g,
            source_name=seed.source_name,
            source_id=seed.source_id,
            source_version=seed.source_version,
            source_data_type=seed.source_data_type,
            verified_at=seed.verified_at,
            estimated=seed.estimated,
            is_current=True,
            created_at=now,
        )
        existing = scope.nutrition_profiles.get_by_provenance(
            ingredient_id,
            candidate.source_name,
            candidate.source_id,
            candidate.source_version,
        )
        if existing is not None:
            if existing.snapshot_values() != candidate.snapshot_values():
                raise FoodCatalogueConflictError(
                    "Existing nutrition provenance has different authoritative values."
                )
            return existing, False
        scope.nutrition_profiles.clear_current(ingredient_id)
        scope.nutrition_profiles.add(candidate)
        return candidate, True

    def _assert_seed_ingredient_matches(
        self,
        existing: FoodIngredient,
        seed: TrustedFoodIngredientSeed,
        *,
        now: datetime,
    ) -> None:
        candidate = self._new_ingredient(seed, now=now)
        fields = (
            "canonical_code",
            "canonical_name",
            "canonical_name_key",
            "category_code",
            "default_unit",
            "density_g_per_ml",
            "edible_fraction",
            "allergens_reviewed",
            "allergen_codes",
            "storage_profile_code",
        )
        if any(
            getattr(existing, field) != getattr(candidate, field) for field in fields
        ):
            raise FoodCatalogueConflictError(
                f"Seed definition for {seed.canonical_code} conflicts with persisted catalogue truth."
            )


def _bounded_limit(value: int) -> int:
    if type(value) is not int or value < 1 or value > MAX_CATALOGUE_RESULT_LIMIT:
        raise ValueError(
            f"limit must be an integer from 1 through {MAX_CATALOGUE_RESULT_LIMIT}."
        )
    return value
