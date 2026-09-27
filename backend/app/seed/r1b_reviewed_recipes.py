"""R1-B reviewed USSR82 RecipeVersion publication and Step 10 bindings."""

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, localcontext
import hashlib
import json
from pathlib import Path
from typing import Any

from app.db.config import DatabaseConfig, REPOSITORY_ROOT
from app.domain.food_composition import calculation_context
from app.domain.recipe_nutrition_v2 import NUTRIENT_CODES, RESULT_QUANTUM
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
from app.persistence.sqlalchemy_core.food_recipe_composition import (
    create_food_recipe_catalogue_service,
)
from app.persistence.sqlalchemy_core.food_recipe_uow import (
    SqlAlchemyRecipeCatalogueUnitOfWork,
)
from app.persistence.sqlalchemy_core.recipe_nutrition_v2 import (
    create_recipe_nutrition_v2_service,
)
from app.seed.ru_nut_db_r1a import load_ru_nut_db_r1a_bundles
from app.seed.ru_nut_db_r1b_dependencies import (
    load_ru_nut_db_r1b_dependency_bundles,
    seed_ru_nut_db_r1b_dependencies,
)
from app.seed.ru_nut_db_step4 import load_ru_nut_db_step4_bundles
from app.services.food_recipes import (
    RecipeSeedSummary,
    TrustedRecipeIngredientSeed,
    TrustedRecipeSeed,
    TrustedRecipeVersionSeed,
)
from app.services.recipe_nutrition_v2 import (
    BindingDisposition,
    ReviewedRecipeIngredientBindingSpec,
    project_recipe_nutrition_consumption,
)

PACKAGE = REPOSITORY_ROOT / "data/curation/r1b-reviewed-recipes"
PUBLICATION_SHA256 = "de469f3f1ef28b3844a92f76d7ed6d2f0c25e0d77d4479f7f4f6b013a0c80c04"
SOURCE_DOCUMENT_SHA256 = "6ac7dfb300844fd996aee6d20b4e7e6aa421dd517367ab1f59120812fee104d5"
SUPPORTING_MASS_SHA256 = "5ea78ead82568f8aff019a4076215c6598675783cb81e0d1d5b4f913016de4cc"
ARCHIVE_SHA256 = "c0d90020798b2998e841328b9081f06f8197efda084b852aa8457fd41a5ce8ea"
SOURCE_NAME = "USSR82"
SOURCE_VERSION = f"sha256:{SOURCE_DOCUMENT_SHA256}"
PUBLISH_IDS = ("USSR82-453", "USSR82-1081", "USSR82-697")
BLOCKED_IDS = ("USSR82-467", "USSR82-492")
BLOCKED_REASON = "UNQUANTIFIED_PROCESS_INGREDIENT_SALT"


@dataclass(frozen=True)
class R1BPublicationResult:
    recipe_summary: RecipeSeedSummary
    dependency_bundle_created_count: int
    binding_fresh_count: int
    binding_replay_count: int
    activated_count: int
    exact_energy_kcal: tuple[tuple[str, Decimal], ...]


def _checked_json(path: Path, digest: str) -> dict[str, Any]:
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != digest:
        raise ValueError(f"Изменён проверенный файл данных: {path.name}.")
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError("R1-B publication package должен быть JSON-объектом.")
    return value


def _decimal(value: object, *, field: str) -> Decimal:
    if not isinstance(value, str) or not value:
        raise ValueError(f"R1-B {field} должен быть canonical Decimal string.")
    try:
        result = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"R1-B {field} не является Decimal.") from exc
    if (
        not result.is_finite()
        or result < 0
        or format(result, "f") != value
    ):
        raise ValueError(f"R1-B {field} не является canonical Decimal string.")
    return result


def _accepted_authorities() -> dict[str, tuple[int, dict[str, Decimal]]]:
    accepted: dict[str, tuple[int, dict[str, Decimal]]] = {}

    for bundle in load_ru_nut_db_step4_bundles():
        accepted[bundle.ingredient.canonical_code] = (
            bundle.atomic_composition.version,
            {
                value.nutrient_code: value.amount
                for value in bundle.vector.values
            },
        )

    for bundle in load_ru_nut_db_r1a_bundles():
        accepted[bundle.ingredient.canonical_code] = (
            bundle.atomic_composition.version,
            {
                value.nutrient_code: value.amount
                for value in bundle.vector.values
            },
        )
    for bundle in load_ru_nut_db_r1b_dependency_bundles():
        accepted[bundle.ingredient.canonical_code] = (
            bundle.atomic_composition.version,
            {
                value.nutrient_code: value.amount
                for value in bundle.vector.values
            },
        )
    return accepted


def _validate_authorities(package: dict[str, Any]) -> None:
    raw = package.get("composition_authorities")
    if not isinstance(raw, dict):
        raise ValueError("R1-B composition_authorities отсутствуют.")
    accepted = _accepted_authorities()
    if set(raw) - set(accepted):
        raise ValueError("R1-B package ссылается на неизвестную Composition authority.")

    for code, value in raw.items():
        if not isinstance(value, dict):
            raise ValueError(f"R1-B authority {code} повреждена.")
        version, actual_values = accepted[code]
        if value.get("version") != version:
            raise ValueError(f"R1-B Composition version изменена для {code}.")
        expected_values = value.get("values")
        if not isinstance(expected_values, dict):
            raise ValueError(f"R1-B authority values отсутствуют для {code}.")
        parsed = {
            nutrient_code: _decimal(amount, field=f"{code}.{nutrient_code}")
            for nutrient_code, amount in expected_values.items()
        }
        if parsed != actual_values:
            raise ValueError(f"R1-B reviewed vector отличается от accepted authority: {code}.")


def _require_package_identity(package: dict[str, Any]) -> None:
    if package.get("schema_version") != 1 or package.get("operation") != (
        "R1B_REVIEWED_USSR82_RECIPE_PUBLICATION"
    ):
        raise ValueError("Неизвестная R1-B publication schema/operation.")
    if package.get("accepted_base") != "fb89cfeb84f4052233f82daa7dcc2d1c07aa971a":
        raise ValueError("R1-B accepted base изменён.")

    source = package.get("source")
    if not isinstance(source, dict) or {
        "archive_sha256": source.get("archive_sha256"),
        "source_name": source.get("source_name"),
        "source_document_sha256": source.get("source_document_sha256"),
        "source_version": source.get("source_version"),
        "supporting_mass_sha256": source.get("supporting_mass_sha256"),
    } != {
        "archive_sha256": ARCHIVE_SHA256,
        "source_name": SOURCE_NAME,
        "source_document_sha256": SOURCE_DOCUMENT_SHA256,
        "source_version": SOURCE_VERSION,
        "supporting_mass_sha256": SUPPORTING_MASS_SHA256,
    }:
        raise ValueError("R1-B source identity расходится с merged Contract Gate.")

    candidates = package.get("candidates")
    if not isinstance(candidates, list) or len(candidates) != 5:
        raise ValueError("R1-B должен содержать ровно пять reviewed dispositions.")
    by_id = {
        row.get("source_recipe_id"): row
        for row in candidates
        if isinstance(row, dict)
    }
    if set(by_id) != set(PUBLISH_IDS) | set(BLOCKED_IDS):
        raise ValueError("R1-B candidate identities изменены.")
    if any(by_id[key].get("disposition") != "PUBLISH" for key in PUBLISH_IDS):
        raise ValueError("R1-B publish disposition изменена.")
    for key in BLOCKED_IDS:
        if (
            by_id[key].get("disposition") != "BLOCKED"
            or by_id[key].get("reason") != BLOCKED_REASON
        ):
            raise ValueError("R1-B process blocker изменён.")
    _validate_authorities(package)


def load_r1b_recipe_seeds(
    package_path: Path = PACKAGE,
) -> tuple[tuple[TrustedRecipeSeed, ...], dict[str, Any]]:
    package = _checked_json(package_path / "publication.json", PUBLICATION_SHA256)
    _require_package_identity(package)
    rights_basis = package.get("rights_basis")
    if not isinstance(rights_basis, str) or not rights_basis.strip():
        raise ValueError("R1-B rights_basis отсутствует.")

    seeds: list[TrustedRecipeSeed] = []
    for row in package["candidates"]:
        if row["disposition"] != "PUBLISH":
            continue
        ingredients_raw = row.get("ingredients")
        source_steps = row.get("source_steps")
        published_steps = row.get("published_steps")
        if (
            not isinstance(ingredients_raw, list)
            or not ingredients_raw
            or not isinstance(source_steps, list)
            or not source_steps
            or not isinstance(published_steps, list)
            or not published_steps
        ):
            raise ValueError(f"R1-B structure неполна для {row['source_recipe_id']}.")

        ingredients = tuple(
            TrustedRecipeIngredientSeed(
                food_ingredient_code=item["food_code"],
                quantity=_decimal(
                    item["quantity_g"],
                    field=f"{row['source_recipe_id']}.ingredient.quantity",
                ),
                unit="g",
                source_amount_text=item["source_amount_text"],
                normalization_note=item["normalization_note"],
                prep_note=None,
                optional=False,
            )
            for item in ingredients_raw
        )
        output = _decimal(
            row["source_output_g"], field=f"{row['source_recipe_id']}.source_output_g"
        )
        if output <= 0:
            raise ValueError("R1-B source output должен быть положительным.")
        if row.get("activation") != "ACTIVE_AFTER_BINDING_VALIDATION":
            raise ValueError("R1-B activation disposition изменена.")

        seeds.append(
            TrustedRecipeSeed(
                canonical_code=row["canonical_code"],
                canonical_name=row["canonical_name"],
                initial_is_active=False,
                version=TrustedRecipeVersionSeed(
                    base_servings=Decimal("1"),
                    meal_type_code=row["meal_type_code"],
                    prep_time_minutes=None,
                    cook_time_minutes=None,
                    total_time_minutes=None,
                    difficulty_code=None,
                    batch_friendly=None,
                    freezable=None,
                    storage_days_fridge=None,
                    storage_days_freezer=None,
                    verification_status="SOURCE_VERIFIED",
                    verified_at=datetime(2026, 9, 27, tzinfo=timezone.utc),
                    source_name=SOURCE_NAME,
                    source_recipe_id=row["source_recipe_id"],
                    source_url=row["source_url"],
                    source_version=SOURCE_VERSION,
                    source_retrieved_at=None,
                    source_document_sha256=SOURCE_DOCUMENT_SHA256,
                    source_original_servings=Decimal("1"),
                    rights_review_status="REVIEWED",
                    rights_basis=rights_basis,
                    change_note=(
                        "R1-B reviewed publication from retained USSR82 source; "
                        f"selected branch: {row['source_variant']}."
                    ),
                    ingredients=ingredients,
                    steps=tuple(published_steps),
                    equipment_codes=(),
                    source_output_g=output,
                    source_output_text=row["source_output_text"],
                ),
            )
        )
    if tuple(seed.version.source_recipe_id for seed in seeds) != PUBLISH_IDS:
        raise ValueError("R1-B publish order изменён.")
    return tuple(seeds), package


def _binding_specs(
    seeds: tuple[TrustedRecipeSeed, ...],
    package: dict[str, Any],
) -> tuple[ReviewedRecipeIngredientBindingSpec, ...]:
    by_source = {
        row["source_recipe_id"]: row
        for row in package["candidates"]
        if row["disposition"] == "PUBLISH"
    }
    authorities = package["composition_authorities"]
    specs: list[ReviewedRecipeIngredientBindingSpec] = []

    for seed in seeds:
        source_row = by_source[seed.version.source_recipe_id]
        for position, ingredient in enumerate(seed.version.ingredients, start=1):
            authority = authorities[ingredient.food_ingredient_code]
            per_100 = {
                code: _decimal(
                    amount,
                    field=f"{ingredient.food_ingredient_code}.{code}",
                )
                for code, amount in authority["values"].items()
            }
            with localcontext(calculation_context()):
                available = tuple(
                    (
                        code,
                        (
                            per_100[code]
                            * ingredient.quantity
                            / Decimal("100")
                        ).quantize(RESULT_QUANTUM),
                    )
                    for code in NUTRIENT_CODES
                    if code in per_100
                )
            unknown = tuple(code for code in NUTRIENT_CODES if code not in per_100)
            specs.append(
                ReviewedRecipeIngredientBindingSpec(
                    trusted_recipe_seed=seed,
                    recipe_code=seed.canonical_code,
                    source_name=SOURCE_NAME,
                    source_recipe_id=seed.version.source_recipe_id,
                    source_version=SOURCE_VERSION,
                    recipe_version_number=1,
                    ingredient_position=position,
                    food_ingredient_code=ingredient.food_ingredient_code,
                    quantity=ingredient.quantity,
                    unit="g",
                    composition_version=int(authority["version"]),
                    composition_kind="ATOMIC",
                    composition_input_state="INPUT",
                    expected_available_amounts=available,
                    expected_unknown_codes=unknown,
                    require_recipe_inactive=False,
                )
            )

        energy = _decimal(
            source_row["expected_energy_kcal"],
            field=f"{seed.version.source_recipe_id}.expected_energy_kcal",
        )
        if energy <= 0:
            raise ValueError("R1-B expected energy должна быть положительной.")
    return tuple(specs)


def _activate_recipes(engine, seeds: tuple[TrustedRecipeSeed, ...]) -> int:
    activated = 0
    now = datetime.now(timezone.utc)
    with SqlAlchemyRecipeCatalogueUnitOfWork(engine) as uow:
        for seed in seeds:
            recipe = uow.recipes.get_by_code(seed.canonical_code)
            if recipe is None:
                raise ValueError(f"R1-B Recipe отсутствует: {seed.canonical_code}.")
            if recipe.is_active:
                continue
            uow.recipes.set_active(recipe.id, active=True, updated_at=now)
            activated += 1
        if activated:
            uow.commit()
        else:
            uow.rollback()
    return activated


def seed_r1b_recipes(
    config: DatabaseConfig | None = None,
    *,
    package_path: Path = PACKAGE,
) -> R1BPublicationResult:
    seeds, package = load_r1b_recipe_seeds(package_path)

    preflight_engine = create_sqlite_engine(config)
    try:
        preflight_catalogue = create_food_recipe_catalogue_service(preflight_engine)
        dispositions = tuple(
            preflight_catalogue.preflight_trusted_seed(seed) for seed in seeds
        )
        if len(set(dispositions)) != 1:
            raise ValueError(
                "Частично опубликованный R1-B Recipe batch нельзя дозаполнять."
            )
    finally:
        preflight_engine.dispose()

    dependency_result = seed_ru_nut_db_r1b_dependencies(config)
    engine = create_sqlite_engine(config)
    try:
        catalogue = create_food_recipe_catalogue_service(engine)
        recipe_summary = catalogue.reconcile_seed(seeds, strict_history=True)

        nutrition = create_recipe_nutrition_v2_service(engine)
        fresh = replay = 0
        for spec in _binding_specs(seeds, package):
            result = nutrition.publish_binding(spec)
            if result.disposition is BindingDisposition.FRESH:
                fresh += 1
            else:
                replay += 1

        energies: list[tuple[str, Decimal]] = []
        package_by_source = {
            row["source_recipe_id"]: row
            for row in package["candidates"]
            if row["disposition"] == "PUBLISH"
        }
        for seed in seeds:
            recipe = catalogue.get_by_code(seed.canonical_code)
            versions = catalogue.list_versions(recipe.id)
            if len(versions) != 1:
                raise ValueError("R1-B ожидает ровно одну fresh RecipeVersion.")
            canonical = nutrition.calculate(versions[0].id)
            projection = project_recipe_nutrition_consumption(canonical)
            expected = _decimal(
                package_by_source[seed.version.source_recipe_id]["expected_energy_kcal"],
                field=f"{seed.version.source_recipe_id}.expected_energy_kcal",
            )
            actual = canonical.total_amount("ENERGY_KCAL")
            if actual != expected or not projection.exact_energy_ready:
                raise ValueError(
                    f"R1-B exact energy validation failed: {seed.version.source_recipe_id}."
                )
            energies.append((seed.version.source_recipe_id, actual))

        activated = _activate_recipes(engine, seeds)
        return R1BPublicationResult(
            recipe_summary=recipe_summary,
            dependency_bundle_created_count=dependency_result.bundle_created_count,
            binding_fresh_count=fresh,
            binding_replay_count=replay,
            activated_count=activated,
            exact_energy_kcal=tuple(energies),
        )
    finally:
        engine.dispose()


if __name__ == "__main__":
    result = seed_r1b_recipes()
    print(
        json.dumps(
            {
                "recipes_inserted": result.recipe_summary.recipes_inserted,
                "versions_inserted": result.recipe_summary.versions_inserted,
                "dependency_bundle_created_count": result.dependency_bundle_created_count,
                "binding_fresh_count": result.binding_fresh_count,
                "binding_replay_count": result.binding_replay_count,
                "activated_count": result.activated_count,
                "exact_energy_kcal": [
                    [source_id, format(amount, "f")]
                    for source_id, amount in result.exact_energy_kcal
                ],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
