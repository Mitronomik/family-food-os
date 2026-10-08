"""DC4-A3 immutable Russian RecipeStep correction publication."""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from dataclasses import dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any
from uuid import UUID

from app.db.config import REPOSITORY_ROOT, DatabaseConfig
from app.domain.recipe_nutrition_v2 import RecipeNutritionAuthorityKind
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
from app.persistence.sqlalchemy_core.food_recipe_composition import (
    create_food_recipe_catalogue_service,
)
from app.persistence.sqlalchemy_core.recipe_nutrition_v2 import (
    SqlAlchemyRecipeNutritionV2UnitOfWork,
    create_recipe_nutrition_v2_service,
)
from app.seed.r3a_school2022_main_batch import (
    _load_contract as _load_r3a_contract,
    _prepared_spec as _r3a_prepared_spec,
    _recipe_seed as _r3a_recipe_seed,
    activate_r3a_school2022_main_batch,
    publish_r3a_school2022_main_batch,
)
from app.seed.r3d_final_dc3_batch import seed_r3d_final_dc3_batch
from app.services.food_recipes import RecipeCatalogueConflictError
from app.services.planner import PlannerService
from app.services.recipe_nutrition_v2 import (
    PreparedPublicationDisposition,
    RecipeNutritionV2ConflictError,
    RecipeNutritionV2UnavailableError,
)

PACKAGE = REPOSITORY_ROOT / "data/curation/dc4-a3-russian-step-corrections"
CORRECTIONS_PATH = PACKAGE / "corrections.json"
CORRECTIONS_GIT_BLOB_SHA = "ec1f8fca9ff8d3c4ac844f6eab0c3411ece54c68"
ASCII_WORD_RE = re.compile(r"[A-Za-z]{2,}")

CORRECTION_CODES = (
    "SCHOOL2022_54_1R_COD_CUTLET",
    "SCHOOL2022_54_2R_PINK_SALMON_CUTLET",
    "SCHOOL2022_54_3R_POLLOCK_CUTLET",
    "SCHOOL2022_54_10R_PINK_SALMON_TOMATO_VEGETABLES",
    "SCHOOL2022_54_11R_POLLOCK_TOMATO_VEGETABLES",
    "SCHOOL2022_54_8M_STEAMED_BEEF_MEATBALLS",
    "SCHOOL2022_54_11M_BEEF_PILAF",
)


@dataclass(frozen=True)
class A3RecipeCorrectionResult:
    canonical_code: str
    predecessor_version_id: UUID
    successor_version_id: UUID
    disposition: str
    exact_energy_kcal: Decimal


@dataclass(frozen=True)
class A3CorrectionResult:
    recipes: tuple[A3RecipeCorrectionResult, ...]
    active_recipe_count: int
    eligible_count: int
    meal_type_counts: tuple[tuple[str, int], ...]
    planner_version: str


def _git_blob_sha(raw: bytes) -> str:
    payload = b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw
    return hashlib.sha1(payload).hexdigest()


def _decimal(value: Any, *, field: str) -> Decimal:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a Decimal string.")
    parsed = Decimal(value)
    if not parsed.is_finite() or parsed < 0 or format(parsed, "f") != value:
        raise ValueError(f"{field} must be a canonical non-negative Decimal.")
    return parsed


def _load_corrections(path: Path = CORRECTIONS_PATH) -> dict[str, Any]:
    raw = path.read_bytes()
    if path == CORRECTIONS_PATH and _git_blob_sha(raw) != CORRECTIONS_GIT_BLOB_SHA:
        raise ValueError("DC4-A3 correction artifact Git blob changed.")
    payload = json.loads(raw.decode("utf-8"))
    if (
        payload.get("schema_version") != "DC4_A3_RUSSIAN_STEP_CORRECTION_V1"
        or payload.get("issue") != 176
        or payload.get("accepted_base")
        != "2a16521a69d48b6df6dcec944ef39fd270d0a95f"
        or payload.get("source_name") != "ru-school2022"
        or payload.get("source_document_sha256")
        != "c9264cf521ae699fb30a964d5668caec8f31ff1efc1f13a3dd055df40ebafb5d"
    ):
        raise ValueError("DC4-A3 correction artifact identity changed.")

    rows = payload.get("recipes")
    if not isinstance(rows, list):
        raise TypeError("DC4-A3 corrections must be a list.")
    codes = tuple(row.get("canonical_code") for row in rows)
    if codes != CORRECTION_CODES:
        raise ValueError("DC4-A3 correction recipe set/order changed.")

    for row in rows:
        old_steps = row.get("old_steps")
        new_steps = row.get("new_steps")
        if (
            not isinstance(old_steps, list)
            or not old_steps
            or not isinstance(new_steps, list)
            or len(old_steps) != len(new_steps)
            or old_steps == new_steps
            or any(not isinstance(step, str) or not step.strip() for step in new_steps)
            or any(ASCII_WORD_RE.search(step) for step in new_steps)
        ):
            raise ValueError(
                f"DC4-A3 Russian correction is invalid: {row.get('canonical_code')}."
            )
        _decimal(row.get("output_mass_g"), field="output_mass_g")
        _decimal(row.get("energy_kcal"), field="energy_kcal")
    return payload


def _r3a_payload() -> dict[str, Any]:
    _, _, _, _, specs, _, _ = _load_r3a_contract()
    return specs


def _assert_frozen_source_match(
    correction: dict[str, Any],
    old_seed,
    old_spec,
    artifact: dict[str, Any],
) -> None:
    if (
        old_seed.canonical_code != correction["canonical_code"]
        or old_seed.version.source_name != artifact["source_name"]
        or old_seed.version.source_recipe_id != correction["source_recipe_id"]
        or old_seed.version.source_version != artifact["source_version"]
        or old_seed.version.source_document_sha256
        != artifact["source_document_sha256"]
        or (old_seed.version.rights_basis or "") != artifact["rights_basis"]
        or tuple(old_seed.version.steps) != tuple(correction["old_steps"])
        or old_spec.output_mass_g
        != _decimal(correction["output_mass_g"], field="output_mass_g")
        or dict(old_spec.expected_available_amounts).get("ENERGY_KCAL")
        != _decimal(correction["energy_kcal"], field="energy_kcal")
    ):
        raise RecipeCatalogueConflictError(
            f"DC4-A3 frozen source contract drifted: {old_seed.canonical_code}."
        )


def _successor_seed(old_seed, correction: dict[str, Any], artifact: dict[str, Any]):
    return replace(
        old_seed,
        version=replace(
            old_seed.version,
            change_note=artifact["change_note"],
            steps=tuple(correction["new_steps"]),
        ),
    )


def _require_current_authority(nutrition, version_id: UUID, expected_energy: Decimal):
    try:
        canonical = nutrition.prepared_canonical_nutrition(version_id)
    except RecipeNutritionV2UnavailableError as exc:
        raise RecipeNutritionV2ConflictError(
            "DC4-A3 current successor prepared authority is unavailable."
        ) from exc
    projection = nutrition.neutral_consumption_projection(version_id)
    if (
        projection.authority_kind is not RecipeNutritionAuthorityKind.PREPARED_OUTPUT_V1
        or not projection.exact_energy_ready
        or projection.per_base_serving.kcal != expected_energy
        or canonical.per_serving_amount("ENERGY_KCAL") != expected_energy
    ):
        raise RecipeNutritionV2ConflictError(
            "DC4-A3 successor prepared energy/authority drifted."
        )
    return projection


def _publish_one(
    *,
    engine,
    catalogue,
    nutrition,
    old_seed,
    old_spec,
    correction: dict[str, Any],
    artifact: dict[str, Any],
) -> A3RecipeCorrectionResult:
    _assert_frozen_source_match(correction, old_seed, old_spec, artifact)
    if catalogue.preflight_trusted_seed(old_seed).value != "EXACT_REPLAY":
        raise RecipeCatalogueConflictError(
            f"DC4-A3 predecessor is not exact replay: {old_seed.canonical_code}."
        )

    historical = nutrition.publish_prepared(old_spec)
    if historical.disposition is not PreparedPublicationDisposition.EXACT_REPLAY:
        raise RecipeNutritionV2ConflictError(
            f"DC4-A3 predecessor authority is not exact replay: "
            f"{old_seed.canonical_code}."
        )
    predecessor_id = historical.authority.recipe_version_id
    predecessor = catalogue.get_version_detail(predecessor_id)
    recipe = catalogue.get_by_code(old_seed.canonical_code)
    current = catalogue.get_latest_verified(recipe.id)
    versions = catalogue.list_versions(recipe.id)
    expected_number = predecessor.version.version_number + 1
    expected_energy = _decimal(correction["energy_kcal"], field="energy_kcal")
    successor_seed = _successor_seed(old_seed, correction, artifact)
    successor_spec = replace(
        old_spec,
        trusted_recipe_seed=successor_seed,
        recipe_version_number=expected_number,
        require_recipe_inactive=False,
    )

    later = tuple(
        version
        for version in versions
        if version.version_number > predecessor.version.version_number
    )
    if current.version.id == predecessor_id:
        if later:
            raise RecipeCatalogueConflictError(
                f"DC4-A3 unexpected later RecipeVersion exists: "
                f"{old_seed.canonical_code}."
            )
        with SqlAlchemyRecipeNutritionV2UnitOfWork(engine) as uow:
            successor = catalogue.append_trusted_version_in_scope(
                uow,
                recipe.id,
                successor_seed.version,
            )
            if (
                successor.version.version_number != expected_number
                or successor.version.created_from_version_id != predecessor_id
            ):
                raise RecipeCatalogueConflictError(
                    f"DC4-A3 successor lineage drifted: {old_seed.canonical_code}."
                )
            published = nutrition.publish_prepared_in_scope(uow, successor_spec)
            if (
                published.disposition is not PreparedPublicationDisposition.FRESH
                or published.authority.recipe_version_id != successor.version.id
            ):
                raise RecipeNutritionV2ConflictError(
                    f"DC4-A3 fresh prepared authority was not fresh/exact: "
                    f"{old_seed.canonical_code}."
                )
            projection = nutrition.prepared_consumption_projection_in_scope(
                uow,
                successor.version.id,
            )
            if (
                not projection.exact_energy_ready
                or projection.per_base_serving.kcal != expected_energy
            ):
                raise RecipeNutritionV2ConflictError(
                    f"DC4-A3 in-scope exact energy drifted: "
                    f"{old_seed.canonical_code}."
                )
            uow.commit()
        successor_id = successor.version.id
        disposition = PreparedPublicationDisposition.FRESH.value
    else:
        if (
            len(later) != 1
            or current.version.version_number != expected_number
            or current.version.created_from_version_id != predecessor_id
        ):
            raise RecipeCatalogueConflictError(
                f"DC4-A3 current RecipeVersion is not the exact successor: "
                f"{old_seed.canonical_code}."
            )
        _require_current_authority(nutrition, current.version.id, expected_energy)
        replay = nutrition.publish_prepared(successor_spec)
        if (
            replay.disposition is not PreparedPublicationDisposition.EXACT_REPLAY
            or replay.authority.recipe_version_id != current.version.id
        ):
            raise RecipeNutritionV2ConflictError(
                f"DC4-A3 successor authority replay drifted: "
                f"{old_seed.canonical_code}."
            )
        successor_id = current.version.id
        disposition = PreparedPublicationDisposition.EXACT_REPLAY.value

    current = catalogue.get_latest_verified(recipe.id)
    if current.version.id != successor_id:
        raise RecipeCatalogueConflictError(
            f"DC4-A3 successor did not remain current: {old_seed.canonical_code}."
        )
    if any(ASCII_WORD_RE.search(step.instruction) for step in current.steps):
        raise RecipeCatalogueConflictError(
            f"DC4-A3 current RecipeStep is not Russian-ready: "
            f"{old_seed.canonical_code}."
        )
    _require_current_authority(nutrition, successor_id, expected_energy)
    return A3RecipeCorrectionResult(
        canonical_code=old_seed.canonical_code,
        predecessor_version_id=predecessor_id,
        successor_version_id=successor_id,
        disposition=disposition,
        exact_energy_kcal=expected_energy,
    )


def seed_dc4_a3_russian_step_corrections(
    config: DatabaseConfig | None = None,
) -> A3CorrectionResult:
    artifact = _load_corrections()
    seed_r3d_final_dc3_batch(config)
    specs_payload = _r3a_payload()
    corrections = {
        row["canonical_code"]: row for row in artifact["recipes"]
    }

    engine = create_sqlite_engine(config)
    try:
        catalogue = create_food_recipe_catalogue_service(engine)
        nutrition = create_recipe_nutrition_v2_service(engine)
        results = []
        for code in CORRECTION_CODES:
            source_row = specs_payload["recipes"][code]
            old_seed = _r3a_recipe_seed(source_row)
            old_spec = _r3a_prepared_spec(source_row, old_seed)
            results.append(
                _publish_one(
                    engine=engine,
                    catalogue=catalogue,
                    nutrition=nutrition,
                    old_seed=old_seed,
                    old_spec=old_spec,
                    correction=corrections[code],
                    artifact=artifact,
                )
            )

        planner = PlannerService(
            None,
            None,
            catalogue,
            None,
            None,
            recipe_nutrition=nutrition,  # type: ignore[arg-type]
        )
        admissions = tuple(planner.compose_candidate_admission())
        eligible = tuple(row for row in admissions if row.eligible and not row.blockers)
        meal_counts = Counter(row.meal_type_code for row in eligible)
        expected_counts = Counter({"breakfast": 17, "main": 33, "sandwich": 1})
        if len(eligible) != 51 or meal_counts != expected_counts:
            raise RecipeCatalogueConflictError(
                "DC4-A3 Planner exact-energy baseline drifted."
            )
        active_count = sum(recipe.is_active for recipe in catalogue.list_all())
        if active_count != 51:
            raise RecipeCatalogueConflictError(
                "DC4-A3 active Recipe catalogue cardinality drifted."
            )
        return A3CorrectionResult(
            recipes=tuple(results),
            active_recipe_count=active_count,
            eligible_count=len(eligible),
            meal_type_counts=tuple(sorted(meal_counts.items())),
            planner_version=planner._config.version,
        )
    finally:
        engine.dispose()


def verify_historical_r3a_zero_write(
    config: DatabaseConfig | None = None,
) -> None:
    """Replay historical R3-A publication/activation without mutating A3 state."""

    publish_r3a_school2022_main_batch(config)
    changed = activate_r3a_school2022_main_batch(config)
    if changed:
        raise RecipeCatalogueConflictError(
            "Historical R3-A activation must be zero-write after DC4-A3."
        )


if __name__ == "__main__":
    result = seed_dc4_a3_russian_step_corrections()
    print(
        json.dumps(
            {
                "recipes": [
                    {
                        "canonical_code": row.canonical_code,
                        "predecessor_version_id": str(row.predecessor_version_id),
                        "successor_version_id": str(row.successor_version_id),
                        "disposition": row.disposition,
                        "exact_energy_kcal": format(row.exact_energy_kcal, "f"),
                    }
                    for row in result.recipes
                ],
                "active_recipe_count": result.active_recipe_count,
                "eligible_count": result.eligible_count,
                "meal_type_counts": dict(result.meal_type_counts),
                "planner_version": result.planner_version,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
