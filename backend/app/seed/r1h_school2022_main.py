"""R1-H School2022 MAIN prepared-output publication and activation batch."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
from typing import Any
from uuid import UUID

from app.db.config import DatabaseConfig, REPOSITORY_ROOT
from app.db.migrations import apply_migrations
from app.domain.recipe_nutrition_v2 import NUTRIENT_CODES
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
from app.persistence.sqlalchemy_core.food_ingredient_composition import (
    create_food_catalogue_service,
)
from app.persistence.sqlalchemy_core.food_recipe_composition import (
    create_food_recipe_catalogue_service,
)
from app.persistence.sqlalchemy_core.recipe_nutrition_v2 import (
    SqlAlchemyRecipeNutritionV2ReadScope,
    SqlAlchemyRecipeNutritionV2UnitOfWork,
    create_recipe_nutrition_v2_service,
)
from app.seed.food_ingredients import seed_food_ingredients
from app.seed.r1f_prepared_output import seed_r1f_prepared_output
from app.seed.ru_nut_db_r1a import seed_ru_nut_db_r1a
from app.seed.ru_nut_db_step4 import seed_ru_nut_db_step4
from app.seed.ru_nut_db_step8_butter import seed_ru_nut_db_step8_butter
from app.services.food_ingredients import TrustedFoodIngredientIdentitySeed
from app.services.food_recipes import (
    TrustedRecipeIngredientSeed,
    TrustedRecipeSeed,
    TrustedRecipeSeedDisposition,
    TrustedRecipeVersionSeed,
)
from app.services.planner import PlannerAdmissionBlocker, PlannerService
from app.services.prepared_recipe_activation import activate_prepared_recipe
from app.services.recipe_nutrition_v2 import (
    PreparedPublicationDisposition,
    RecipeNutritionV2ConflictError,
    ReviewedPreparedRecipeNutritionSpec,
)

PACKAGE = REPOSITORY_ROOT / "data/curation/r1g-catalogue-capacity-expansion"
PUBLICATION_SPECS_PATH = PACKAGE / "prepared-publication-specs.json"
NEXT_RUNTIME_BATCH_PATH = PACKAGE / "next-runtime-batch.json"

PUBLICATION_SPECS_GIT_BLOB_SHA = "394b35d3d02c0498a681584a37d36b1d98faf40d"
NEXT_RUNTIME_BATCH_GIT_BLOB_SHA = "4575303889a663255fa21ca1c3ce79ba8f510e93"
R1G_ACCEPTED_BASE = "879d68087845dea09454089e822f5d8d8238d12d"

MEATBALLS_RECIPE_CODE = "SCHOOL2022_54_29M_BEEF_MEATBALLS"
GOULASH_RECIPE_CODE = "SCHOOL2022_54_2M_BEEF_GOULASH"
RECIPE_CODES = (MEATBALLS_RECIPE_CODE, GOULASH_RECIPE_CODE)

BEEF_FOOD_CODE = "BEEF_CATEGORY_1_RAW"
BREAD_FOOD_CODE = "WHEAT_BREAD_HIGH_GRADE_STALE"
IODIZED_SALT_FOOD_CODE = "SALT_IODIZED"
TOMATO_PUREE_FOOD_CODE = "TOMATO_PUREE_PASTE"
IDENTITY_ONLY_FOOD_CODES = (
    BEEF_FOOD_CODE,
    BREAD_FOOD_CODE,
    IODIZED_SALT_FOOD_CODE,
    TOMATO_PUREE_FOOD_CODE,
)


@dataclass(frozen=True)
class R1HSchool2022MainResult:
    identity_food_inserted: int
    identity_food_existing: int
    recipe_version_ids: tuple[tuple[str, UUID], ...]
    authority_dispositions: tuple[tuple[str, str], ...]
    active_recipe_codes: tuple[str, ...]
    exact_energy_kcal: tuple[tuple[str, Decimal], ...]


def _git_blob_sha(raw: bytes) -> str:
    header = f"blob {len(raw)}\0".encode()
    return hashlib.sha1(header + raw).hexdigest()


def _checked_json(path: Path, expected_git_blob_sha: str) -> dict[str, Any]:
    raw = path.read_bytes()
    if _git_blob_sha(raw) != expected_git_blob_sha:
        raise ValueError(f"R1-G frozen artifact changed: {path.name}.")
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise ValueError(f"R1-G artifact must be a JSON object: {path.name}.")
    return payload


def _decimal(value: object, *, field: str) -> Decimal:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field} must be a canonical Decimal string.")
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field} is not Decimal.") from exc
    if not parsed.is_finite() or parsed < 0 or format(parsed, "f") != value:
        raise ValueError(f"{field} must be a canonical non-negative Decimal.")
    return parsed


def _load_contract(
    package: Path = PACKAGE,
) -> tuple[dict[str, Any], dict[str, Any]]:
    specs = _checked_json(
        package / PUBLICATION_SPECS_PATH.name,
        PUBLICATION_SPECS_GIT_BLOB_SHA,
    )
    batch = _checked_json(
        package / NEXT_RUNTIME_BATCH_PATH.name,
        NEXT_RUNTIME_BATCH_GIT_BLOB_SHA,
    )

    if (
        specs.get("schema_version") != 1
        or specs.get("operation") != "R1G_PREPARED_PUBLICATION_SPECS"
        or specs.get("accepted_base") != R1G_ACCEPTED_BASE
        or specs.get("authority_kind") != "PREPARED_OUTPUT_V1"
        or specs.get("recipe_calculation_version")
        != "RECIPE_PREPARED_OUTPUT_NUTRITION_V1"
    ):
        raise ValueError("R1-G prepared publication contract identity changed.")
    if (
        batch.get("schema_version") != 1
        or batch.get("operation") != "R1G_NEXT_RUNTIME_BATCH"
        or batch.get("accepted_base") != R1G_ACCEPTED_BASE
    ):
        raise ValueError("R1-G runtime batch identity changed.")

    recipes = specs.get("recipes")
    if not isinstance(recipes, dict) or set(recipes) != set(RECIPE_CODES):
        raise ValueError("R1-G prepared Recipe set changed.")
    batch_recipes = batch.get("recipes")
    if not isinstance(batch_recipes, list) or tuple(
        row.get("canonical_code") for row in batch_recipes
    ) != RECIPE_CODES:
        raise ValueError("R1-G runtime Recipe ordering changed.")

    nutrient_partition = specs.get("nutrient_partition")
    expected_unknown = tuple(
        code for code in NUTRIENT_CODES if code != "ENERGY_KCAL"
    )
    if (
        not isinstance(nutrient_partition, dict)
        or nutrient_partition.get("frozen_code_count") != len(NUTRIENT_CODES)
        or nutrient_partition.get("available_codes") != ["ENERGY_KCAL"]
        or tuple(nutrient_partition.get("unknown_codes", ())) != expected_unknown
    ):
        raise ValueError("R1-G frozen nutrient partition changed.")

    identities = batch.get("new_identity_only_foods")
    if not isinstance(identities, list) or tuple(
        row.get("canonical_code") for row in identities
    ) != IDENTITY_ONLY_FOOD_CODES:
        raise ValueError("R1-G identity-only FoodIngredient set changed.")
    if any(row.get("nutrition_profile") is not None for row in identities):
        raise ValueError("R1-G identity-only FoodIngredient gained Nutrition authority.")

    return specs, batch


def _identity_seeds(batch: dict[str, Any]) -> tuple[TrustedFoodIngredientIdentitySeed, ...]:
    return tuple(
        TrustedFoodIngredientIdentitySeed(
            canonical_code=row["canonical_code"],
            canonical_name=row["canonical_name"],
            category_code=row["category_code"],
            default_unit=row["default_unit"],
        )
        for row in batch["new_identity_only_foods"]
    )


def _recipe_seed(payload: dict[str, Any]) -> TrustedRecipeSeed:
    seed = payload["trusted_recipe_seed"]
    version = seed["version"]
    retrieved = version["source_retrieved_at"]
    return TrustedRecipeSeed(
        canonical_code=seed["canonical_code"],
        canonical_name=seed["canonical_name"],
        initial_is_active=seed["initial_is_active"],
        version=TrustedRecipeVersionSeed(
            base_servings=_decimal(version["base_servings"], field="base_servings"),
            meal_type_code=version["meal_type_code"],
            prep_time_minutes=version["prep_time_minutes"],
            cook_time_minutes=version["cook_time_minutes"],
            total_time_minutes=version["total_time_minutes"],
            difficulty_code=version["difficulty_code"],
            batch_friendly=version["batch_friendly"],
            freezable=version["freezable"],
            storage_days_fridge=version["storage_days_fridge"],
            storage_days_freezer=version["storage_days_freezer"],
            verification_status=version["verification_status"],
            verified_at=datetime.fromisoformat(
                version["verified_at"].replace("Z", "+00:00")
            ),
            source_name=version["source_name"],
            source_recipe_id=version["source_recipe_id"],
            source_url=version["source_url"],
            source_version=version["source_version"],
            source_retrieved_at=(
                None
                if retrieved is None
                else datetime.fromisoformat(retrieved.replace("Z", "+00:00"))
            ),
            source_document_sha256=version["source_document_sha256"],
            source_original_servings=_decimal(
                version["source_original_servings"],
                field="source_original_servings",
            ),
            rights_review_status=version["rights_review_status"],
            rights_basis=version["rights_basis"],
            change_note=version["change_note"],
            ingredients=tuple(
                TrustedRecipeIngredientSeed(
                    food_ingredient_code=row["food_ingredient_code"],
                    quantity=_decimal(row["quantity"], field="ingredient.quantity"),
                    unit=row["unit"],
                    source_amount_text=row["source_amount_text"],
                    normalization_note=row["normalization_note"],
                    prep_note=row["prep_note"],
                    optional=row["optional"],
                )
                for row in version["ingredients"]
            ),
            steps=tuple(version["steps"]),
            equipment_codes=tuple(version["equipment_codes"]),
            source_output_g=_decimal(
                version["source_output_g"], field="source_output_g"
            ),
            source_output_text=version["source_output_text"],
        ),
    )


def _prepared_spec(
    payload: dict[str, Any],
    seed: TrustedRecipeSeed,
) -> ReviewedPreparedRecipeNutritionSpec:
    spec = payload["prepared_spec"]
    return ReviewedPreparedRecipeNutritionSpec(
        trusted_recipe_seed=seed,
        recipe_code=spec["recipe_code"],
        source_name=spec["source_name"],
        source_recipe_id=spec["source_recipe_id"],
        source_version=spec["source_version"],
        source_document_sha256=spec["source_document_sha256"],
        output_mass_g=_decimal(spec["output_mass_g"], field="output_mass_g"),
        source_locator=spec["source_locator"],
        source_data_type=spec["source_data_type"],
        rights_review_status=spec["rights_review_status"],
        rights_basis=spec["rights_basis"],
        review_reference=spec["review_reference"],
        expected_available_amounts=tuple(
            (code, _decimal(amount, field=f"nutrient.{code}"))
            for code, amount in spec["expected_available_amounts"]
        ),
        expected_unknown_codes=tuple(spec["expected_unknown_codes"]),
        require_recipe_inactive=spec["require_recipe_inactive"],
    )


def _recipe_seeds_and_specs(
    specs: dict[str, Any],
) -> tuple[
    tuple[TrustedRecipeSeed, ...],
    tuple[ReviewedPreparedRecipeNutritionSpec, ...],
]:
    seeds = tuple(_recipe_seed(specs["recipes"][code]) for code in RECIPE_CODES)
    reviewed = tuple(
        _prepared_spec(specs["recipes"][code], seed)
        for code, seed in zip(RECIPE_CODES, seeds, strict=True)
    )
    return seeds, reviewed


def _assert_replay_not_partial(engine, catalogue, nutrition, seed, spec) -> None:
    disposition = catalogue.preflight_trusted_seed(seed)
    if disposition is TrustedRecipeSeedDisposition.FRESH:
        return
    recipe = catalogue.get_by_code(seed.canonical_code)
    detail = catalogue.get_latest_verified(recipe.id)
    with SqlAlchemyRecipeNutritionV2ReadScope(engine) as scope:
        authority = scope.prepared.get_authority(detail.version.id)
        values = scope.prepared.list_values(detail.version.id)
    if authority is None or not values:
        raise RecipeNutritionV2ConflictError(
            f"Partial persisted R1-H state for {seed.canonical_code}."
        )
    replay = nutrition.publish_prepared(spec)
    if replay.disposition is not PreparedPublicationDisposition.EXACT_REPLAY:
        raise RecipeNutritionV2ConflictError(
            f"Expected exact R1-H prepared replay for {seed.canonical_code}."
        )


def seed_r1h_school2022_main(
    config: DatabaseConfig | None = None,
    *,
    package: Path = PACKAGE,
) -> R1HSchool2022MainResult:
    specs_payload, batch_payload = _load_contract(package)

    apply_migrations(config)
    seed_food_ingredients(config)
    seed_ru_nut_db_step4(config)
    seed_ru_nut_db_r1a(config)
    seed_ru_nut_db_step8_butter(config)
    seed_r1f_prepared_output(config)

    engine = create_sqlite_engine(config)
    try:
        food = create_food_catalogue_service(engine)
        identity_summary = food.reconcile_identity_seed(
            _identity_seeds(batch_payload)
        )
        catalogue = create_food_recipe_catalogue_service(engine)
        nutrition = create_recipe_nutrition_v2_service(engine)
        seeds, specs = _recipe_seeds_and_specs(specs_payload)

        for seed, spec in zip(seeds, specs, strict=True):
            _assert_replay_not_partial(
                engine,
                catalogue,
                nutrition,
                seed,
                spec,
            )

        dispositions: list[tuple[str, str]] = []
        version_ids: list[tuple[str, UUID]] = []
        energies: list[tuple[str, Decimal]] = []
        fresh_codes: set[str] = set()

        for seed, spec in zip(seeds, specs, strict=True):
            if (
                catalogue.preflight_trusted_seed(seed)
                is TrustedRecipeSeedDisposition.FRESH
            ):
                with SqlAlchemyRecipeNutritionV2UnitOfWork(engine) as uow:
                    catalogue.reconcile_seed_in_scope(uow, (seed,))
                    published = nutrition.publish_prepared_in_scope(uow, spec)
                    if (
                        published.disposition
                        is not PreparedPublicationDisposition.FRESH
                    ):
                        raise RecipeNutritionV2ConflictError(
                            "Fresh R1-H Recipe did not publish fresh prepared authority."
                        )
                    projection = nutrition.prepared_consumption_projection_in_scope(
                        uow, published.authority.recipe_version_id
                    )
                    if (
                        not projection.exact_energy_ready
                        or projection.per_base_serving.kcal is None
                    ):
                        raise RecipeNutritionV2ConflictError(
                            f"R1-H in-scope exact energy unavailable: {seed.canonical_code}."
                        )
                    uow.commit()
                    fresh_codes.add(seed.canonical_code)
            else:
                published = nutrition.publish_prepared(spec)

            recipe = catalogue.get_by_code(seed.canonical_code)
            detail = catalogue.get_latest_verified(recipe.id)
            projection = nutrition.neutral_consumption_projection(detail.version.id)
            if (
                not projection.exact_energy_ready
                or projection.per_base_serving.kcal is None
            ):
                raise RecipeNutritionV2ConflictError(
                    f"R1-H exact energy unavailable: {seed.canonical_code}."
                )
            dispositions.append((seed.canonical_code, published.disposition.value))
            version_ids.append((seed.canonical_code, detail.version.id))
            energies.append((seed.canonical_code, projection.per_base_serving.kcal))

        planner = PlannerService(
            None,
            None,
            catalogue,
            None,
            None,
            recipe_nutrition=nutrition,  # type: ignore[arg-type]
        )
        for seed, spec in zip(seeds, specs, strict=True):
            admission = next(
                row
                for row in planner.compose_candidate_admission()
                if row.canonical_code == seed.canonical_code
            )
            if seed.canonical_code in fresh_codes:
                activate_prepared_recipe(
                    catalogue=catalogue,
                    nutrition=nutrition,
                    planner=planner,
                    spec=spec,
                )
                admission = next(
                    row
                    for row in planner.compose_candidate_admission()
                    if row.canonical_code == seed.canonical_code
                )
            if admission.is_active:
                if not admission.eligible or not admission.exact_energy_ready:
                    raise RecipeNutritionV2ConflictError(
                        f"R1-H active admission failed: {seed.canonical_code}."
                    )
            elif admission.blockers != (PlannerAdmissionBlocker.INACTIVE,):
                raise RecipeNutritionV2ConflictError(
                    f"R1-H replay admission has unexpected blockers: {seed.canonical_code}."
                )

        active_codes = tuple(
            row.canonical_code
            for row in planner.compose_candidate_admission()
            if row.canonical_code in set(RECIPE_CODES) and row.is_active
        )
        return R1HSchool2022MainResult(
            identity_food_inserted=identity_summary.ingredients_inserted,
            identity_food_existing=identity_summary.ingredients_existing,
            recipe_version_ids=tuple(version_ids),
            authority_dispositions=tuple(dispositions),
            active_recipe_codes=active_codes,
            exact_energy_kcal=tuple(energies),
        )
    finally:
        engine.dispose()


if __name__ == "__main__":
    result = seed_r1h_school2022_main()
    print(
        json.dumps(
            {
                "identity_food_inserted": result.identity_food_inserted,
                "identity_food_existing": result.identity_food_existing,
                "recipe_version_ids": [
                    [code, str(version_id)]
                    for code, version_id in result.recipe_version_ids
                ],
                "authority_dispositions": list(result.authority_dispositions),
                "active_recipe_codes": list(result.active_recipe_codes),
                "exact_energy_kcal": [
                    [code, format(value, "f")]
                    for code, value in result.exact_energy_kcal
                ],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
