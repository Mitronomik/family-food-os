"""Application operations for the verified Recipe Catalogue."""

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from app.domain.food_ingredients import normalize_unicode_search_key
from app.domain.food_recipes import (
    MealTypeCode,
    Recipe,
    RecipeEquipment,
    RecipeIngredient,
    RecipeStep,
    RecipeVersion,
    RecipeVersionDetail,
    RightsReviewStatus,
    VerificationStatus,
    deactivate_recipe,
    scale_recipe,
)
from app.domain.units import UnitCode
from app.services.food_recipe_contracts import (
    RecipeCatalogueReadScope,
    RecipeCatalogueUnitOfWork,
)

WriteFactory = Callable[[], RecipeCatalogueUnitOfWork]
ReadFactory = Callable[[], RecipeCatalogueReadScope]


class RecipeNotFoundError(LookupError):
    pass


class RecipeCatalogueConflictError(ValueError):
    pass


class FoodIngredientResolutionError(ValueError):
    pass


@dataclass(frozen=True)
class TrustedRecipeIngredientSeed:
    food_ingredient_code: str
    quantity: Decimal
    unit: UnitCode | str
    source_amount_text: str
    normalization_note: str | None = None
    prep_note: str | None = None
    optional: bool = False


@dataclass(frozen=True)
class TrustedRecipeVersionSeed:
    base_servings: Decimal
    meal_type_code: MealTypeCode | str
    prep_time_minutes: int | None
    cook_time_minutes: int | None
    total_time_minutes: int | None
    difficulty_code: str | None
    batch_friendly: bool | None
    freezable: bool | None
    storage_days_fridge: int | None
    storage_days_freezer: int | None
    verification_status: VerificationStatus | str
    verified_at: datetime | None
    source_name: str
    source_recipe_id: str
    source_url: str
    source_version: str
    source_retrieved_at: datetime
    source_document_sha256: str
    source_original_servings: Decimal
    rights_review_status: RightsReviewStatus | str
    rights_basis: str | None
    change_note: str
    ingredients: tuple[TrustedRecipeIngredientSeed, ...]
    steps: tuple[str, ...]
    equipment_codes: tuple[str, ...] = ()


@dataclass(frozen=True)
class TrustedRecipeSeed:
    canonical_code: str
    canonical_name: str
    version: TrustedRecipeVersionSeed


@dataclass(frozen=True)
class RecipeSeedSummary:
    recipes_inserted: int = 0
    recipes_existing: int = 0
    versions_inserted: int = 0
    versions_existing: int = 0
    ingredients_inserted: int = 0
    ingredients_existing: int = 0
    steps_inserted: int = 0
    steps_existing: int = 0
    equipment_inserted: int = 0
    equipment_existing: int = 0
    conflicts: int = 0


class FoodRecipeCatalogueService:
    def __init__(
        self,
        write_scope_factory: WriteFactory,
        read_scope_factory: ReadFactory,
        *,
        id_factory: Callable[[], UUID] = uuid4,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._write = write_scope_factory
        self._read = read_scope_factory
        self._id = id_factory
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def get(self, recipe_id: UUID) -> Recipe:
        with self._read() as scope:
            recipe = scope.recipes.get(recipe_id)
            if recipe is None:
                raise RecipeNotFoundError(recipe_id)
            return recipe

    def get_by_code(self, canonical_code: str) -> Recipe:
        with self._read() as scope:
            recipe = scope.recipes.get_by_code(canonical_code)
            if recipe is None:
                raise RecipeNotFoundError(canonical_code)
            return recipe

    def list_active(self, *, limit: int = 100) -> list[Recipe]:
        if (
            isinstance(limit, bool)
            or not isinstance(limit, int)
            or not 1 <= limit <= 200
        ):
            raise ValueError("limit must be from 1 through 200")
        with self._read() as scope:
            return scope.recipes.list_active(limit=limit)

    def get_version(self, version_id: UUID) -> RecipeVersion:
        with self._read() as scope:
            version = scope.versions.get(version_id)
            if version is None:
                raise RecipeNotFoundError(version_id)
            return version

    def get_version_detail(self, version_id: UUID) -> RecipeVersionDetail:
        with self._read() as scope:
            detail = scope.versions.get_detail(version_id)
            if detail is None:
                raise RecipeNotFoundError(version_id)
            return detail

    def list_versions(self, recipe_id: UUID) -> list[RecipeVersion]:
        with self._read() as scope:
            if scope.recipes.get(recipe_id) is None:
                raise RecipeNotFoundError(recipe_id)
            return scope.versions.list_for_recipe(recipe_id)

    def get_current_verified(self, recipe_id: UUID) -> RecipeVersionDetail:
        with self._read() as scope:
            recipe = scope.recipes.get(recipe_id)
            if recipe is None or not recipe.is_active:
                raise RecipeNotFoundError(recipe_id)
            detail = scope.versions.get_current_verified(recipe_id)
            if detail is None:
                raise RecipeNotFoundError(recipe_id)
            return detail

    def scale_version(
        self, version_id: UUID, target_servings: Decimal
    ) -> RecipeVersionDetail:
        return scale_recipe(self.get_version_detail(version_id), target_servings)

    def deactivate(self, recipe_id: UUID) -> Recipe:
        now = self._clock()
        with self._write() as scope:
            recipe = scope.recipes.get(recipe_id)
            if recipe is None:
                raise RecipeNotFoundError(recipe_id)
            changed = deactivate_recipe(recipe, updated_at=now)
            scope.recipes.set_active(
                recipe_id, active=False, updated_at=changed.updated_at
            )
            scope.commit()
            return changed

    def create_trusted(self, seed: TrustedRecipeSeed) -> RecipeVersionDetail:
        now = self._clock()
        with self._write() as scope:
            if scope.recipes.get_by_code(seed.canonical_code) is not None:
                raise RecipeCatalogueConflictError("Recipe code already exists.")
            name_key = normalize_unicode_search_key(
                seed.canonical_name, field="canonical_name"
            )
            if scope.recipes.get_by_name_key(name_key) is not None:
                raise RecipeCatalogueConflictError("Recipe name already exists.")
            recipe = self._new_recipe(seed, now)
            scope.recipes.add(recipe)
            detail = self._new_detail(scope, recipe, seed.version, 1, None, now)
            scope.versions.add_detail(detail)
            scope.commit()
            return detail

    def append_trusted_version(
        self, recipe_id: UUID, seed: TrustedRecipeVersionSeed
    ) -> RecipeVersionDetail:
        now = self._clock()
        with self._write() as scope:
            recipe = scope.recipes.get(recipe_id)
            if recipe is None:
                raise RecipeNotFoundError(recipe_id)
            versions = scope.versions.list_for_recipe(recipe_id)
            previous = versions[-1] if versions else None
            number = 1 if previous is None else previous.version_number + 1
            detail = self._new_detail(
                scope,
                recipe,
                seed,
                number,
                None if previous is None else previous.id,
                now,
            )
            scope.versions.add_detail(detail)
            scope.commit()
            return detail

    def reconcile_seed(self, seeds: Iterable[TrustedRecipeSeed]) -> RecipeSeedSummary:
        entries = tuple(seeds)
        identities = [
            (
                seed.canonical_code,
                normalize_unicode_search_key(
                    seed.canonical_name, field="canonical_name"
                ),
            )
            for seed in entries
        ]
        if len(set(identities)) != len(identities):
            raise RecipeCatalogueConflictError(
                "Seed contains duplicate Recipe identity."
            )

        counts = {field: 0 for field in RecipeSeedSummary.__dataclass_fields__}
        now = self._clock()
        with self._write() as scope:
            for entry in entries:
                recipe = scope.recipes.get_by_code(entry.canonical_code)
                if recipe is None:
                    name_key = normalize_unicode_search_key(
                        entry.canonical_name, field="canonical_name"
                    )
                    if scope.recipes.get_by_name_key(name_key) is not None:
                        raise RecipeCatalogueConflictError(
                            "Existing Recipe normalized name conflicts with trusted seed."
                        )
                    recipe = self._new_recipe(entry, now)
                    scope.recipes.add(recipe)
                    detail = self._new_detail(
                        scope, recipe, entry.version, 1, None, now
                    )
                    scope.versions.add_detail(detail)
                    _increment_detail(counts, detail, inserted=True)
                    counts["recipes_inserted"] += 1
                    continue

                if (
                    recipe.canonical_name != entry.canonical_name
                    or recipe.canonical_name_key
                    != normalize_unicode_search_key(
                        entry.canonical_name, field="canonical_name"
                    )
                ):
                    raise RecipeCatalogueConflictError(
                        "Existing Recipe differs from trusted seed."
                    )
                counts["recipes_existing"] += 1
                existing = scope.versions.get_by_provenance(
                    recipe.id,
                    entry.version.source_name,
                    entry.version.source_recipe_id,
                    entry.version.source_version,
                )
                if existing is not None:
                    if not _seed_matches(scope, existing, entry.version):
                        raise RecipeCatalogueConflictError(
                            "Same-provenance RecipeVersion differs; append a reviewed source version instead."
                        )
                    _increment_detail(counts, existing, inserted=False)
                    continue

                versions = scope.versions.list_for_recipe(recipe.id)
                previous = versions[-1] if versions else None
                detail = self._new_detail(
                    scope,
                    recipe,
                    entry.version,
                    1 if previous is None else previous.version_number + 1,
                    None if previous is None else previous.id,
                    now,
                )
                scope.versions.add_detail(detail)
                _increment_detail(counts, detail, inserted=True)
            scope.commit()
        return RecipeSeedSummary(**counts)

    def _new_recipe(self, seed: TrustedRecipeSeed, now: datetime) -> Recipe:
        return Recipe(
            id=self._id(),
            canonical_code=seed.canonical_code,
            canonical_name=seed.canonical_name,
            canonical_name_key=normalize_unicode_search_key(
                seed.canonical_name, field="canonical_name"
            ),
            is_active=True,
            created_at=now,
            updated_at=now,
        )

    def _new_detail(
        self,
        scope: RecipeCatalogueUnitOfWork,
        recipe: Recipe,
        seed: TrustedRecipeVersionSeed,
        number: int,
        previous_id: UUID | None,
        now: datetime,
    ) -> RecipeVersionDetail:
        version_id = self._id()
        version = RecipeVersion(
            id=version_id,
            recipe_id=recipe.id,
            version_number=number,
            base_servings=seed.base_servings,
            meal_type_code=seed.meal_type_code,  # type: ignore[arg-type]
            prep_time_minutes=seed.prep_time_minutes,
            cook_time_minutes=seed.cook_time_minutes,
            total_time_minutes=seed.total_time_minutes,
            difficulty_code=seed.difficulty_code,
            batch_friendly=seed.batch_friendly,
            freezable=seed.freezable,
            storage_days_fridge=seed.storage_days_fridge,
            storage_days_freezer=seed.storage_days_freezer,
            verification_status=seed.verification_status,  # type: ignore[arg-type]
            verified_at=seed.verified_at,
            source_name=seed.source_name,
            source_recipe_id=seed.source_recipe_id,
            source_url=seed.source_url,
            source_version=seed.source_version,
            source_retrieved_at=seed.source_retrieved_at,
            source_document_sha256=seed.source_document_sha256,
            source_original_servings=seed.source_original_servings,
            rights_review_status=seed.rights_review_status,  # type: ignore[arg-type]
            rights_basis=seed.rights_basis,
            created_from_version_id=previous_id,
            change_note=seed.change_note,
            created_at=now,
        )
        ingredients: list[RecipeIngredient] = []
        for position, ingredient_seed in enumerate(seed.ingredients, start=1):
            food_ingredient = scope.food_ingredients.get_by_code(
                ingredient_seed.food_ingredient_code
            )
            if food_ingredient is None or not food_ingredient.is_active:
                raise FoodIngredientResolutionError(
                    f"FoodIngredient {ingredient_seed.food_ingredient_code!r} is missing or inactive."
                )
            ingredients.append(
                RecipeIngredient(
                    id=self._id(),
                    recipe_version_id=version_id,
                    food_ingredient_id=food_ingredient.id,
                    position=position,
                    quantity=ingredient_seed.quantity,
                    unit=ingredient_seed.unit,  # type: ignore[arg-type]
                    source_amount_text=ingredient_seed.source_amount_text,
                    normalization_note=ingredient_seed.normalization_note,
                    prep_note=ingredient_seed.prep_note,
                    optional=ingredient_seed.optional,
                    created_at=now,
                )
            )
        steps = tuple(
            RecipeStep(
                id=self._id(),
                recipe_version_id=version_id,
                position=position,
                instruction=instruction,
                stage_code=None,
                created_at=now,
            )
            for position, instruction in enumerate(seed.steps, start=1)
        )
        equipment = tuple(
            RecipeEquipment(
                recipe_version_id=version_id,
                position=position,
                equipment_code=equipment_code,
            )
            for position, equipment_code in enumerate(seed.equipment_codes, start=1)
        )
        return RecipeVersionDetail(
            recipe=recipe,
            version=version,
            ingredients=tuple(ingredients),
            steps=steps,
            equipment=equipment,
        )


def _increment_detail(
    counts: dict[str, int], detail: RecipeVersionDetail, *, inserted: bool
) -> None:
    suffix = "inserted" if inserted else "existing"
    counts[f"versions_{suffix}"] += 1
    counts[f"ingredients_{suffix}"] += len(detail.ingredients)
    counts[f"steps_{suffix}"] += len(detail.steps)
    counts[f"equipment_{suffix}"] += len(detail.equipment)


def _seed_matches(
    scope: RecipeCatalogueUnitOfWork,
    detail: RecipeVersionDetail,
    seed: TrustedRecipeVersionSeed,
) -> bool:
    version = detail.version
    version_values = (
        version.base_servings,
        version.meal_type_code,
        version.prep_time_minutes,
        version.cook_time_minutes,
        version.total_time_minutes,
        version.difficulty_code,
        version.batch_friendly,
        version.freezable,
        version.storage_days_fridge,
        version.storage_days_freezer,
        version.verification_status,
        version.verified_at,
        version.source_name,
        version.source_recipe_id,
        version.source_url,
        version.source_version,
        version.source_retrieved_at,
        version.source_document_sha256,
        version.source_original_servings,
        version.rights_review_status,
        version.rights_basis,
        version.change_note,
    )
    seed_values = (
        seed.base_servings,
        MealTypeCode(seed.meal_type_code),
        seed.prep_time_minutes,
        seed.cook_time_minutes,
        seed.total_time_minutes,
        seed.difficulty_code,
        seed.batch_friendly,
        seed.freezable,
        seed.storage_days_fridge,
        seed.storage_days_freezer,
        VerificationStatus(seed.verification_status),
        seed.verified_at,
        seed.source_name,
        seed.source_recipe_id,
        seed.source_url,
        seed.source_version,
        seed.source_retrieved_at,
        seed.source_document_sha256,
        seed.source_original_servings,
        RightsReviewStatus(seed.rights_review_status),
        seed.rights_basis,
        seed.change_note,
    )
    ingredients = tuple(
        (
            (
                resolved.canonical_code
                if (
                    resolved := scope.food_ingredients.get(
                        ingredient.food_ingredient_id
                    )
                )
                is not None
                else None
            ),
            ingredient.quantity,
            ingredient.unit,
            ingredient.source_amount_text,
            ingredient.normalization_note,
            ingredient.prep_note,
            ingredient.optional,
        )
        for ingredient in detail.ingredients
    )
    seed_ingredients = tuple(
        (
            ingredient.food_ingredient_code,
            ingredient.quantity,
            UnitCode(ingredient.unit),
            ingredient.source_amount_text,
            ingredient.normalization_note,
            ingredient.prep_note,
            ingredient.optional,
        )
        for ingredient in seed.ingredients
    )
    return (
        version_values == seed_values
        and ingredients == seed_ingredients
        and tuple(step.instruction for step in detail.steps) == seed.steps
        and tuple(item.equipment_code for item in detail.equipment)
        == seed.equipment_codes
    )
