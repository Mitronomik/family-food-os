"""Application operations for the verified Recipe Catalogue."""

import hashlib
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from decimal import Decimal
from enum import StrEnum
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
    activate_recipe,
    deactivate_recipe,
    scale_recipe,
)
from app.domain.units import UnitCode
from app.services.food_recipe_contracts import (
    RecipeCatalogueReadScope,
    RecipeCatalogueUnitOfWork,
)
from app.services.pr10_ff_typed_ids import FixtureIdentityError, FixtureTypedIdProvider

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
    source_retrieved_at: datetime | None
    source_document_sha256: str
    source_original_servings: Decimal
    rights_review_status: RightsReviewStatus | str
    rights_basis: str | None
    change_note: str
    ingredients: tuple[TrustedRecipeIngredientSeed, ...]
    steps: tuple[str, ...]
    equipment_codes: tuple[str, ...] = ()
    source_output_g: Decimal | None = None
    source_output_text: str | None = None


@dataclass(frozen=True)
class TrustedRecipeSeed:
    canonical_code: str
    canonical_name: str
    version: TrustedRecipeVersionSeed
    initial_is_active: bool = True


class TrustedRecipeSeedDisposition(StrEnum):
    FRESH = "FRESH"
    EXACT_REPLAY = "EXACT_REPLAY"


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


def _fixture_ingredient_key(
    version_key: Mapping[str, object],
    seed: TrustedRecipeIngredientSeed,
    position: int,
) -> dict[str, object]:
    def digest(value: str | None) -> str | None:
        return (
            None if value is None else hashlib.sha256(value.encode("utf-8")).hexdigest()
        )

    return {
        "recipe_version_key": version_key,
        "position": position,
        "food_ingredient_code": seed.food_ingredient_code,
        "quantity": "0"
        if seed.quantity.is_zero()
        else format(seed.quantity.normalize(), "f"),
        "unit": UnitCode(seed.unit).value,
        "source_amount_text_sha256": digest(seed.source_amount_text),
        "normalization_note_sha256": digest(seed.normalization_note),
        "prep_note_sha256": digest(seed.prep_note),
        "optional": seed.optional,
    }


def _fixture_step_key(
    version_key: Mapping[str, object], instruction: str, position: int
) -> dict[str, object]:
    return {
        "recipe_version_key": version_key,
        "position": position,
        "instruction_sha256": hashlib.sha256(instruction.encode("utf-8")).hexdigest(),
        "stage_code": None,
    }


def _fixture_persisted_seed(
    scope: RecipeCatalogueUnitOfWork | RecipeCatalogueReadScope,
    detail: RecipeVersionDetail,
) -> TrustedRecipeVersionSeed:
    """Reconstruct *every* trusted field from actual stored rows, without UUID keys."""
    version = detail.version
    ingredients = []
    for row in detail.ingredients:
        resolved = scope.food_ingredients.get(row.food_ingredient_id)
        if resolved is None:
            raise FixtureIdentityError("persisted predecessor ingredient missing")
        ingredients.append(
            TrustedRecipeIngredientSeed(
                food_ingredient_code=resolved.canonical_code,
                quantity=row.quantity,
                unit=row.unit,
                source_amount_text=row.source_amount_text,
                normalization_note=row.normalization_note,
                prep_note=row.prep_note,
                optional=row.optional,
            )
        )
    return TrustedRecipeVersionSeed(
        base_servings=version.base_servings,
        meal_type_code=version.meal_type_code,
        prep_time_minutes=version.prep_time_minutes,
        cook_time_minutes=version.cook_time_minutes,
        total_time_minutes=version.total_time_minutes,
        difficulty_code=version.difficulty_code,
        batch_friendly=version.batch_friendly,
        freezable=version.freezable,
        storage_days_fridge=version.storage_days_fridge,
        storage_days_freezer=version.storage_days_freezer,
        verification_status=version.verification_status,
        verified_at=version.verified_at,
        source_name=version.source_name,
        source_recipe_id=version.source_recipe_id,
        source_url=version.source_url,
        source_version=version.source_version,
        source_retrieved_at=version.source_retrieved_at,
        source_document_sha256=version.source_document_sha256,
        source_original_servings=version.source_original_servings,
        rights_review_status=version.rights_review_status,
        rights_basis=version.rights_basis,
        change_note=version.change_note,
        ingredients=tuple(ingredients),
        steps=tuple(row.instruction for row in detail.steps),
        equipment_codes=tuple(row.equipment_code for row in detail.equipment),
        source_output_g=version.source_output_g,
        source_output_text=version.source_output_text,
    )


class FoodRecipeCatalogueService:
    def __init__(
        self,
        write_scope_factory: WriteFactory,
        read_scope_factory: ReadFactory,
        *,
        id_factory: Callable[[], UUID] = uuid4,
        clock: Callable[[], datetime] | None = None,
        id_provider: FixtureTypedIdProvider | None = None,
    ) -> None:
        if id_provider is not None and id_factory is not uuid4:
            raise FixtureIdentityError(
                "custom id_factory conflicts with test ID provider"
            )
        self._id_provider = id_provider
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

    @staticmethod
    def _validate_list_limit(limit: int) -> None:
        if (
            isinstance(limit, bool)
            or not isinstance(limit, int)
            or not 1 <= limit <= 200
        ):
            raise ValueError("limit must be from 1 through 200")

    def list_all(self) -> list[Recipe]:
        """Exhaustive internal catalogue read for admission/audit operations."""

        with self._read() as scope:
            return scope.recipes.list_all()

    def list_active(self, *, limit: int = 100) -> list[Recipe]:
        self._validate_list_limit(limit)
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

    def get_latest_verified(self, recipe_id: UUID) -> RecipeVersionDetail:
        """Latest SOURCE_VERIFIED version regardless of activation state."""

        with self._read() as scope:
            recipe = scope.recipes.get(recipe_id)
            if recipe is None:
                raise RecipeNotFoundError(recipe_id)
            detail = scope.versions.get_current_verified(recipe_id)
            if detail is None:
                raise RecipeNotFoundError(recipe_id)
            return detail

    def scale_version(
        self, version_id: UUID, target_servings: Decimal
    ) -> RecipeVersionDetail:
        return scale_recipe(self.get_version_detail(version_id), target_servings)

    def _activate_after_policy_check_in_scope(
        self,
        scope: RecipeCatalogueUnitOfWork,
        recipe_id: UUID,
        *,
        now: datetime,
    ) -> Recipe:
        """Stage activation inside a caller-owned transaction without committing."""

        recipe = scope.recipes.get(recipe_id)
        if recipe is None:
            raise RecipeNotFoundError(recipe_id)
        if recipe.is_active:
            return recipe
        changed = activate_recipe(recipe, updated_at=now)
        scope.recipes.set_active(recipe_id, active=True, updated_at=changed.updated_at)
        return changed

    def _activate_after_policy_check(self, recipe_id: UUID) -> Recipe:
        """Internal reversible mutation after an owning activation policy passes."""

        now = self._clock()
        with self._write() as scope:
            recipe = scope.recipes.get(recipe_id)
            if recipe is None:
                raise RecipeNotFoundError(recipe_id)
            if recipe.is_active:
                return recipe
            changed = self._activate_after_policy_check_in_scope(
                scope,
                recipe_id,
                now=now,
            )
            scope.commit()
            return changed

    def _activate_batch_after_policy_check(
        self,
        recipe_ids: Iterable[UUID],
    ) -> tuple[Recipe, ...]:
        """Activate an all-inactive batch in one caller-owned UoW and one commit."""

        ids = tuple(recipe_ids)
        if not ids or len(set(ids)) != len(ids):
            raise RecipeCatalogueConflictError(
                "Batch activation requires unique Recipe ids."
            )

        now = self._clock()
        with self._write() as scope:
            recipes = []
            for recipe_id in ids:
                recipe = scope.recipes.get(recipe_id)
                if recipe is None:
                    raise RecipeNotFoundError(recipe_id)
                recipes.append(recipe)

            if any(recipe.is_active for recipe in recipes):
                raise RecipeCatalogueConflictError(
                    "Batch activation requires every Recipe to be inactive."
                )

            changed = tuple(
                self._activate_after_policy_check_in_scope(
                    scope,
                    recipe.id,
                    now=now,
                )
                for recipe in recipes
            )
            scope.commit()
            return changed

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
        with self._write() as scope:
            detail = self.append_trusted_version_in_scope(scope, recipe_id, seed)
            scope.commit()
            return detail

    def append_trusted_version_in_scope(
        self,
        scope: RecipeCatalogueUnitOfWork,
        recipe_id: UUID,
        seed: TrustedRecipeVersionSeed,
    ) -> RecipeVersionDetail:
        """Append one immutable RecipeVersion inside a caller-owned transaction."""

        self._require_active_seed_dependencies(scope, seed)
        recipe = scope.recipes.get(recipe_id)
        if recipe is None:
            raise RecipeNotFoundError(recipe_id)
        self._assert_fixture_recipe_id(recipe)
        versions = scope.versions.list_for_recipe(recipe_id)
        previous = versions[-1] if versions else None
        number = 1 if previous is None else previous.version_number + 1
        detail = self._new_detail(
            scope,
            recipe,
            seed,
            number,
            None if previous is None else previous.id,
            self._clock(),
        )
        scope.versions.add_detail(detail)
        return detail

    def preflight_trusted_seed(
        self, seed: TrustedRecipeSeed
    ) -> TrustedRecipeSeedDisposition:
        """Classify a trusted seed without writes or silent history extension."""

        with self._read() as scope:
            return self._classify_trusted_seed(scope, seed)

    def _require_active_seed_dependencies(
        self,
        scope: RecipeCatalogueReadScope | RecipeCatalogueUnitOfWork,
        seed: TrustedRecipeVersionSeed,
    ) -> None:
        for ingredient in seed.ingredients:
            if ingredient.optional:
                continue
            resolved = scope.food_ingredients.get_by_code(
                ingredient.food_ingredient_code
            )
            if (
                resolved is None
                or resolved.canonical_code != ingredient.food_ingredient_code
                or not resolved.is_active
            ):
                raise FoodIngredientResolutionError(
                    f"FoodIngredient {ingredient.food_ingredient_code!r} is missing or inactive."
                )

    def _classify_trusted_seed(
        self,
        scope: RecipeCatalogueReadScope | RecipeCatalogueUnitOfWork,
        seed: TrustedRecipeSeed,
    ) -> TrustedRecipeSeedDisposition:
        self._require_active_seed_dependencies(scope, seed.version)
        name_key = normalize_unicode_search_key(
            seed.canonical_name, field="canonical_name"
        )
        by_code = scope.recipes.get_by_code(seed.canonical_code)
        by_name = scope.recipes.get_by_name_key(name_key)
        if by_code is None and by_name is None:
            return TrustedRecipeSeedDisposition.FRESH
        if (
            by_code is None
            or by_name is None
            or by_code.id != by_name.id
            or by_code.canonical_name != seed.canonical_name
            or by_code.canonical_name_key != name_key
        ):
            raise RecipeCatalogueConflictError(
                "Existing Recipe identity conflicts with trusted seed."
            )
        self._assert_fixture_recipe_id(by_code)
        candidates = scope.versions.list_by_provenance(
            by_code.id,
            seed.version.source_name,
            seed.version.source_recipe_id,
            seed.version.source_version,
        )
        if not candidates:
            raise RecipeCatalogueConflictError(
                "Existing Recipe lacks the trusted seed provenance."
            )
        matches = tuple(
            detail
            for detail in candidates
            if _seed_matches(scope, detail, seed.version)
        )
        if len(matches) != 1:
            raise RecipeCatalogueConflictError(
                "Same-provenance trusted seed must resolve exactly one structurally "
                "matching RecipeVersion."
            )
        self._assert_fixture_replay(scope, matches[0], seed)
        return TrustedRecipeSeedDisposition.EXACT_REPLAY

    def reconcile_seed(
        self,
        seeds: Iterable[TrustedRecipeSeed],
        *,
        strict_history: bool = False,
    ) -> RecipeSeedSummary:
        with self._write() as scope:
            summary = self.reconcile_seed_in_scope(
                scope, seeds, strict_history=strict_history
            )
            scope.commit()
            return summary

    def reconcile_seed_in_scope(
        self,
        scope: RecipeCatalogueUnitOfWork,
        seeds: Iterable[TrustedRecipeSeed],
        *,
        strict_history: bool = False,
    ) -> RecipeSeedSummary:
        """Reconcile trusted seeds inside a caller-owned transaction."""

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
        for entry in entries:
            if strict_history:
                self._classify_trusted_seed(scope, entry)
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
                detail = self._new_detail(scope, recipe, entry.version, 1, None, now)
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
            self._assert_fixture_recipe_id(recipe)
            counts["recipes_existing"] += 1
            candidates = scope.versions.list_by_provenance(
                recipe.id,
                entry.version.source_name,
                entry.version.source_recipe_id,
                entry.version.source_version,
            )
            if candidates:
                matches = tuple(
                    detail
                    for detail in candidates
                    if _seed_matches(scope, detail, entry.version)
                )
                if len(matches) != 1:
                    raise RecipeCatalogueConflictError(
                        "Same-provenance trusted historical seed must resolve exactly "
                        "one structurally matching RecipeVersion."
                    )
                self._assert_fixture_replay(scope, matches[0], entry)
                _increment_detail(counts, matches[0], inserted=False)
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
        return RecipeSeedSummary(**counts)

    def _assert_fixture_recipe_id(self, recipe: Recipe) -> None:
        """Never attach a fixture Version to a providerless/random Recipe UUID."""
        if self._id_provider is None:
            return
        expected = self._id_provider.id_for(
            "RECIPE", {"canonical_code": recipe.canonical_code}
        )
        if recipe.id != expected:
            raise FixtureIdentityError(
                "persisted Recipe UUID differs from fixture manifest"
            )

    def _assert_fixture_predecessor(
        self,
        scope: RecipeCatalogueReadScope | RecipeCatalogueUnitOfWork,
        recipe: Recipe,
        successor: TrustedRecipeVersionSeed,
        version_number: int,
        predecessor_id: UUID,
        successor_key: Mapping[str, object],
    ) -> None:
        if self._id_provider is None:
            return
        from app.services.pr10_ff_manifest_loader import project_trusted_version_seed

        previous = scope.versions.get_detail(predecessor_id)
        if (
            previous is None
            or previous.version.recipe_id != recipe.id
            or previous.version.version_number != version_number - 1
        ):
            raise FixtureIdentityError("missing, wrong or stale persisted predecessor")
        pinned = successor_key["predecessor_version_key"]
        if not isinstance(pinned, dict):
            raise FixtureIdentityError("missing frozen semantic predecessor")
        actual_seed = _fixture_persisted_seed(scope, previous)
        predecessor_key = self._id_provider.recipe_version_key_for(
            canonical_code=recipe.canonical_code,
            seed=actual_seed,
            version_number=previous.version.version_number,
            predecessor_id=previous.version.created_from_version_id,
        )
        if (
            predecessor_key != pinned
            or self._id_provider.id_for("RECIPE_VERSION", predecessor_key)
            != predecessor_id
        ):
            raise FixtureIdentityError("persisted predecessor full projection/ID drift")
        if project_trusted_version_seed(
            replace(
                actual_seed, steps=successor.steps, change_note=successor.change_note
            )
        ) != project_trusted_version_seed(successor):
            raise FixtureIdentityError(
                "correction changed non-Step trusted version data"
            )

    def _assert_fixture_replay(
        self,
        scope: RecipeCatalogueReadScope | RecipeCatalogueUnitOfWork,
        detail: RecipeVersionDetail,
        seed: TrustedRecipeSeed,
    ) -> None:
        """EXACT_REPLAY must preserve *actual* IDs, not merely equivalent content."""
        if self._id_provider is None:
            return
        version = detail.version
        key = self._id_provider.recipe_version_key_for(
            canonical_code=seed.canonical_code,
            seed=seed.version,
            version_number=version.version_number,
            predecessor_id=version.created_from_version_id,
        )
        if detail.recipe.id != self._id_provider.id_for(
            "RECIPE", {"canonical_code": seed.canonical_code}
        ) or version.id != self._id_provider.id_for("RECIPE_VERSION", key):
            raise FixtureIdentityError(
                "persisted Recipe/Version UUID differs from manifest"
            )
        if version.created_from_version_id is not None:
            self._assert_fixture_predecessor(
                scope,
                detail.recipe,
                seed.version,
                version.version_number,
                version.created_from_version_id,
                key,
            )
        if len(detail.ingredients) != len(seed.version.ingredients) or len(
            detail.steps
        ) != len(seed.version.steps):
            raise FixtureIdentityError("persisted child count differs from fixture")
        for position, (row, ingredient) in enumerate(
            zip(detail.ingredients, seed.version.ingredients, strict=True), start=1
        ):
            expected = self._id_provider.id_for(
                "RECIPE_INGREDIENT", _fixture_ingredient_key(key, ingredient, position)
            )
            if row.id != expected or row.position != position:
                raise FixtureIdentityError(
                    "persisted RecipeIngredient UUID/position drift"
                )
        for position, (row, instruction) in enumerate(
            zip(detail.steps, seed.version.steps, strict=True), start=1
        ):
            expected = self._id_provider.id_for(
                "RECIPE_STEP", _fixture_step_key(key, instruction, position)
            )
            if row.id != expected or row.position != position:
                raise FixtureIdentityError("persisted RecipeStep UUID/position drift")

    def _new_recipe(self, seed: TrustedRecipeSeed, now: datetime) -> Recipe:
        return Recipe(
            id=(
                self._id()
                if self._id_provider is None
                else self._id_provider.id_for(
                    "RECIPE", {"canonical_code": seed.canonical_code}
                )
            ),
            canonical_code=seed.canonical_code,
            canonical_name=seed.canonical_name,
            canonical_name_key=normalize_unicode_search_key(
                seed.canonical_name, field="canonical_name"
            ),
            is_active=seed.initial_is_active,
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
        self._assert_fixture_recipe_id(recipe)
        version_key = None
        if self._id_provider is not None:
            version_key = self._id_provider.recipe_version_key_for(
                canonical_code=recipe.canonical_code,
                seed=seed,
                version_number=number,
                predecessor_id=previous_id,
            )
            if previous_id is not None:
                self._assert_fixture_predecessor(
                    scope, recipe, seed, number, previous_id, version_key
                )
        version_id = (
            self._id()
            if version_key is None
            else self._id_provider.id_for("RECIPE_VERSION", version_key)
        )
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
            source_output_g=seed.source_output_g,
            source_output_text=seed.source_output_text,
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
                    id=(
                        self._id()
                        if version_key is None
                        else self._id_provider.id_for(
                            "RECIPE_INGREDIENT",
                            _fixture_ingredient_key(
                                version_key, ingredient_seed, position
                            ),
                        )
                    ),
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
                id=(
                    self._id()
                    if version_key is None
                    else self._id_provider.id_for(
                        "RECIPE_STEP",
                        _fixture_step_key(version_key, instruction, position),
                    )
                ),
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
    scope: RecipeCatalogueReadScope | RecipeCatalogueUnitOfWork,
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
        version.source_output_g,
        version.source_output_text,
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
        seed.source_output_g,
        seed.source_output_text,
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


def trusted_recipe_seed_matches(
    scope: RecipeCatalogueReadScope | RecipeCatalogueUnitOfWork,
    detail: RecipeVersionDetail,
    seed: TrustedRecipeSeed,
) -> bool:
    """Whether persisted Recipe identity/history exactly matches one trusted seed."""

    return (
        detail.recipe.canonical_code == seed.canonical_code
        and detail.recipe.canonical_name == seed.canonical_name
        and detail.recipe.canonical_name_key
        == normalize_unicode_search_key(seed.canonical_name, field="canonical_name")
        and _seed_matches(scope, detail, seed.version)
    )
