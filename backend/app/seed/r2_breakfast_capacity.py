"""R2 School2022 breakfast-capacity prepared-output publication batch."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any
from uuid import UUID

from app.db.config import REPOSITORY_ROOT, DatabaseConfig
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
from app.seed.r1h_school2022_main import seed_r1h_school2022_main
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

PACKAGE = REPOSITORY_ROOT / "data/curation/r2-breakfast-capacity"
SELECTION_PATH = PACKAGE / "candidate-selection.json"
APPLICABILITY_PATH = PACKAGE / "household-applicability-review.json"
PUBLICATION_SPECS_PATH = PACKAGE / "publication-specs.json"

SELECTION_GIT_BLOB_SHA = "f7b4ca39f3dd8c4842492a95eb128b4a18193748"
APPLICABILITY_GIT_BLOB_SHA = "93002dc0aa0a9bf7b198b7c34dae8b8382897da7"
PUBLICATION_SPECS_GIT_BLOB_SHA = "9951b8105d6cabdf22e173ab1315f8f2418d5bf9"

R2_ACCEPTED_BASE = "8995e85e4cda2ae30fc62fdc63daaf441f4226bd"
SOURCE_PDF_SHA256 = "c9264cf521ae699fb30a964d5668caec8f31ff1efc1f13a3dd055df40ebafb5d"
SOURCE_ARCHIVE_SHA256 = (\n    "c0d90020798b2998e841328b9081f06f8197efda084b852aa8457fd41a5ce8ea"\n)

OMELET_RECIPE_CODE = "SCHOOL2022_54_1O_NATURAL_OMELET"
OAT_PORRIDGE_RECIPE_CODE = "SCHOOL2022_54_9K_MILK_OAT_PORRIDGE"
RECIPE_CODES = (OMELET_RECIPE_CODE, OAT_PORRIDGE_RECIPE_CODE)

MILK_FOOD_CODE = "MILK_2_5"
OAT_GROATS_FOOD_CODE = "OAT_GROATS"
IDENTITY_ONLY_FOOD_CODES = (MILK_FOOD_CODE, OAT_GROATS_FOOD_CODE)


@dataclass(frozen=True)
class R2BreakfastCapacityResult:
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
        raise ValueError(f"R2 frozen artifact changed: {path.name}.")
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise TypeError(f"R2 artifact must be a JSON object: {path.name}.")
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
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    selection = _checked_json(
        package / SELECTION_PATH.name,
        SELECTION_GIT_BLOB_SHA,
    )
    applicability = _checked_json(
        package / APPLICABILITY_PATH.name,
        APPLICABILITY_GIT_BLOB_SHA,
    )
    specs = _checked_json(
        package / PUBLICATION_SPECS_PATH.name,
        PUBLICATION_SPECS_GIT_BLOB_SHA,
    )

    if (
        selection.get("schema_version") != 1
        or selection.get("operation") != "R2_BREAKFAST_CAPACITY_SELECTION"
        or selection.get("accepted_base") != R2_ACCEPTED_BASE
        or tuple(row.get("canonical_code") for row in selection.get("selected", ()))
        != RECIPE_CODES
    ):
        raise ValueError("R2 candidate-selection contract identity changed.")

    if (
        applicability.get("schema_version") != 1
        or applicability.get("operation")
        != "R2_BREAKFAST_HOUSEHOLD_APPLICABILITY_REVIEW"
        or applicability.get("accepted_base") != R2_ACCEPTED_BASE
        or applicability.get("source", {}).get("archive_sha256")
        != SOURCE_ARCHIVE_SHA256
        or applicability.get("source", {}).get("source_pdf_sha256")
        != SOURCE_PDF_SHA256
    ):
        raise ValueError("R2 household-applicability contract identity changed.")

    applicability_rows = applicability.get("candidates")
    if (
        not isinstance(applicability_rows, list)
        or tuple(row.get("decision") for row in applicability_rows)
        != ("HOUSEHOLD_APPLICABLE", "HOUSEHOLD_APPLICABLE")
        or tuple(
            row.get("source_recipe_id")
            for row in applicability_rows
        )
        != ("ru-school2022:recipe:54-1о", "ru-school2022:recipe:54-9к")
    ):
        raise ValueError("R2 household-applicability decisions changed.")

    if (
        specs.get("schema_version") != 1
        or specs.get("operation") != "R2_BREAKFAST_PREPARED_PUBLICATION_SPECS"
        or specs.get("accepted_base") != R2_ACCEPTED_BASE
        or specs.get("authority_kind") != "PREPARED_OUTPUT_V1"
        or specs.get("recipe_calculation_version")
        != "RECIPE_PREPARED_OUTPUT_NUTRITION_V1"
    ):
        raise ValueError("R2 prepared publication contract identity changed.")

    nutrient_partition = specs.get("nutrient_partition")
    expected_unknown = tuple(code for code in NUTRIENT_CODES if code != "ENERGY_KCAL")
    if (
        not isinstance(nutrient_partition, dict)
        or nutrient_partition.get("frozen_code_count") != len(NUTRIENT_CODES)
        or nutrient_partition.get("available_codes") != ["ENERGY_KCAL"]
        or tuple(nutrient_partition.get("unknown_codes", ())) != expected_unknown
    ):
        raise ValueError("R2 frozen nutrient partition changed.")

    identities = specs.get("new_identity_only_foods")
    if (
        not isinstance(identities, list)
        or tuple(row.get("canonical_code") for row in identities)
        != IDENTITY_ONLY_FOOD_CODES
        or any(
            row.get("nutrition_profile") is not None
            or row.get("composition") is not None
            for row in identities
        )
    ):
        raise ValueError("R2 identity-only FoodIngredient contract changed.")

    recipes = specs.get("recipes")
    if not isinstance(recipes, dict) or tuple(recipes) != RECIPE_CODES:
        raise ValueError("R2 Recipe set or ordering changed.")

    for code in RECIPE_CODES:
        receipt = recipes[code].get("source_receipt", {})
        if (
            receipt.get("source_document_sha256") != SOURCE_PDF_SHA256
            or receipt.get("source_archive_sha256") != SOURCE_ARCHIVE_SHA256
            or receipt.get("rights_review_status") != "REVIEWED"
        ):
            raise ValueError(f"R2 source receipt changed for {code}.")

    return selection, applicability, specs


def _identity_seeds(\n    specs: dict[str, Any],\n) -> tuple[TrustedFoodIngredientIdentitySeed, ...]:
    return tuple(
        TrustedFoodIngredientIdentitySeed(
            canonical_code=row["canonical_code"],
            canonical_name=row["canonical_name"],
            category_code=row["category_code"],
            default_unit=row["default_unit"],
        )
        for row in specs["new_identity_only_foods"]
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
            f"Partial persisted R2 state for {seed.canonical_code}."
        )
    replay = nutrition.publish_prepared(spec)
    if replay.disposition is not PreparedPublicationDisposition.EXACT_REPLAY:
        raise RecipeNutritionV2ConflictError(
            f"Expected exact R2 prepared replay for {seed.canonical_code}."
        )


def seed_r2_breakfast_capacity(
    config: DatabaseConfig | None = None,
    *,
    package: Path = PACKAGE,
) -> R2BreakfastCapacityResult:
    _, _, specs_payload = _load_contract(package)

    apply_migrations(config)
    seed_r1h_school2022_main(config)

    engine = create_sqlite_engine(config)
    try:
        food = create_food_catalogue_service(engine)
        identity_summary = food.reconcile_identity_seed(_identity_seeds(specs_payload))
        catalogue = create_food_recipe_catalogue_service(engine)
        nutrition = create_recipe_nutrition_v2_service(engine)
        seeds, specs = _recipe_seeds_and_specs(specs_payload)

        for seed, spec in zip(seeds, specs, strict=True):
            _assert_replay_not_partial(engine, catalogue, nutrition, seed, spec)

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
                            "Fresh R2 Recipe did not publish fresh prepared authority."
                        )
                    projection = nutrition.prepared_consumption_projection_in_scope(
                        uow, published.authority.recipe_version_id
                    )
                    if (
                        not projection.exact_energy_ready
                        or projection.per_base_serving.kcal is None
                    ):
                        raise RecipeNutritionV2ConflictError(
                            f"R2 in-scope exact energy unavailable: {seed.canonical_code}."
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
                    f"R2 exact energy unavailable: {seed.canonical_code}."
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
                        f"R2 active admission failed: {seed.canonical_code}."
                    )
            elif admission.blockers != (PlannerAdmissionBlocker.INACTIVE,):
                raise RecipeNutritionV2ConflictError(
                    f"R2 replay admission has unexpected blockers: {seed.canonical_code}."
                )

        active_codes = tuple(
            row.canonical_code
            for row in planner.compose_candidate_admission()
            if row.canonical_code in set(RECIPE_CODES) and row.is_active
        )
        return R2BreakfastCapacityResult(
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
    result = seed_r2_breakfast_capacity()
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
