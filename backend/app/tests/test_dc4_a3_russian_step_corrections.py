"""DC4-A3 immutable Russian RecipeStep correction acceptance."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest
from app.db.config import DatabaseConfig
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
from app.persistence.sqlalchemy_core.food_recipe_composition import (
    create_food_recipe_catalogue_service,
)
from app.persistence.sqlalchemy_core.recipe_nutrition_v2 import (
    create_recipe_nutrition_v2_service,
)
from app.seed import dc4_a3_russian_step_corrections as a3
from app.seed.r3a_school2022_main_batch import (
    _load_contract as _load_r3a_contract,
)
from app.seed.r3a_school2022_main_batch import (
    _prepared_spec as _r3a_prepared_spec,
)
from app.seed.r3a_school2022_main_batch import (
    _recipe_seed as _r3a_recipe_seed,
)
from app.seed.r3a_school2022_main_batch import (
    activate_r3a_school2022_main_batch,
    publish_r3a_school2022_main_batch,
)
from app.seed.r3d_final_dc3_batch import seed_r3d_final_dc3_batch
from app.services.food_recipes import RecipeCatalogueConflictError
from app.services.recipe_nutrition_v2 import PreparedPublicationDisposition
from sqlalchemy import event


def db_dump(config: DatabaseConfig) -> str:
    with sqlite3.connect(config.path) as db:
        return "\n".join(db.iterdump())


def r3a_source_rows():
    _, _, _, _, specs, _, _ = _load_r3a_contract()
    return specs["recipes"]


def version_semantics(detail):
    version = detail.version
    return (
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
        version.source_output_g,
        version.source_output_text,
        version.rights_review_status,
        version.rights_basis,
    )


def ingredient_semantics(detail):
    return tuple(
        (
            row.food_ingredient_id,
            row.position,
            row.quantity,
            row.unit,
            row.source_amount_text,
            row.normalization_note,
            row.prep_note,
            row.optional,
        )
        for row in detail.ingredients
    )


def equipment_semantics(detail):
    return tuple((row.position, row.equipment_code) for row in detail.equipment)


def test_a3_fresh_publication_preserves_immutable_recipe_and_nutrition_truth(
    tmp_path: Path,
) -> None:
    config = DatabaseConfig(path=tmp_path / "a3.sqlite")
    result = a3.seed_dc4_a3_russian_step_corrections(config)

    assert len(result.recipes) == 7
    assert {row.disposition for row in result.recipes} == {"FRESH"}
    assert result.active_recipe_count == 51
    assert result.eligible_count == 51
    assert dict(result.meal_type_counts) == {
        "breakfast": 17,
        "main": 33,
        "sandwich": 1,
    }
    assert result.planner_version == "planner-v0.5"

    artifact = a3._load_corrections()
    corrections = {row["canonical_code"]: row for row in artifact["recipes"]}
    engine = create_sqlite_engine(config)
    try:
        catalogue = create_food_recipe_catalogue_service(engine)
        nutrition = create_recipe_nutrition_v2_service(engine)
        for row in result.recipes:
            recipe = catalogue.get_by_code(row.canonical_code)
            assert recipe.is_active is True
            predecessor = catalogue.get_version_detail(row.predecessor_version_id)
            successor = catalogue.get_version_detail(row.successor_version_id)
            current = catalogue.get_latest_verified(recipe.id)

            assert current.version.id == successor.version.id
            assert successor.version.created_from_version_id == predecessor.version.id
            assert (
                successor.version.version_number
                == predecessor.version.version_number + 1
            )
            assert version_semantics(successor) == version_semantics(predecessor)
            assert ingredient_semantics(successor) == ingredient_semantics(predecessor)
            assert equipment_semantics(successor) == equipment_semantics(predecessor)
            assert tuple(step.instruction for step in predecessor.steps) == tuple(
                corrections[row.canonical_code]["old_steps"]
            )
            assert tuple(step.instruction for step in successor.steps) == tuple(
                corrections[row.canonical_code]["new_steps"]
            )
            assert (
                successor.version.change_note
                == artifact["change_note"]
                != predecessor.version.change_note
            )

            canonical = nutrition.prepared_canonical_nutrition(successor.version.id)
            required = canonical.required_total
            assert sum(item.amount is not None for item in required) == 1
            assert sum(item.amount is None for item in required) == 53
            assert (
                canonical.per_serving_amount("ENERGY_KCAL")
                == row.exact_energy_kcal
            )
    finally:
        engine.dispose()


def test_a3_exact_replay_is_zero_write(tmp_path: Path) -> None:
    config = DatabaseConfig(path=tmp_path / "a3-replay.sqlite")
    first = a3.seed_dc4_a3_russian_step_corrections(config)
    before = db_dump(config)
    second = a3.seed_dc4_a3_russian_step_corrections(config)

    assert {row.disposition for row in first.recipes} == {"FRESH"}
    assert {row.disposition for row in second.recipes} == {"EXACT_REPLAY"}
    assert [
        (row.canonical_code, row.predecessor_version_id, row.successor_version_id)
        for row in second.recipes
    ] == [
        (row.canonical_code, row.predecessor_version_id, row.successor_version_id)
        for row in first.recipes
    ]
    assert db_dump(config) == before


def test_historical_r3a_replay_after_a3_is_zero_write_and_keeps_successors_current(
    tmp_path: Path,
) -> None:
    config = DatabaseConfig(path=tmp_path / "a3-r3a-replay.sqlite")
    result = a3.seed_dc4_a3_russian_step_corrections(config)
    successor_ids = {
        row.canonical_code: row.successor_version_id for row in result.recipes
    }
    before = db_dump(config)

    publication = publish_r3a_school2022_main_batch(config)
    activation_changed = activate_r3a_school2022_main_batch(config)

    assert activation_changed is False
    assert db_dump(config) == before
    engine = create_sqlite_engine(config)
    try:
        catalogue = create_food_recipe_catalogue_service(engine)
        nutrition = create_recipe_nutrition_v2_service(engine)
        source_rows = r3a_source_rows()
        for code, successor_id in successor_ids.items():
            recipe = catalogue.get_by_code(code)
            assert catalogue.get_latest_verified(recipe.id).version.id == successor_id
            old_seed = _r3a_recipe_seed(source_rows[code])
            old_spec = _r3a_prepared_spec(source_rows[code], old_seed)
            replay = nutrition.publish_prepared(old_spec)
            assert replay.disposition is PreparedPublicationDisposition.EXACT_REPLAY
            assert replay.authority.recipe_version_id != successor_id
            assert nutrition.prepared_canonical_nutrition(successor_id)
        assert dict(publication.recipe_version_ids).items() >= successor_ids.items()
    finally:
        engine.dispose()


def test_same_source_duplicate_structural_match_fails_closed(tmp_path: Path) -> None:
    config = DatabaseConfig(path=tmp_path / "a3-ambiguous.sqlite")
    seed_r3d_final_dc3_batch(config)
    source_rows = r3a_source_rows()
    code = a3.CORRECTION_CODES[0]
    old_seed = _r3a_recipe_seed(source_rows[code])

    engine = create_sqlite_engine(config)
    try:
        catalogue = create_food_recipe_catalogue_service(engine)
        recipe = catalogue.get_by_code(code)
        catalogue.append_trusted_version(recipe.id, old_seed.version)
        with pytest.raises(RecipeCatalogueConflictError, match="exactly one"):
            catalogue.preflight_trusted_seed(old_seed)
    finally:
        engine.dispose()


def test_a3_injected_prepared_write_failure_rolls_back_successor(
    tmp_path: Path,
    monkeypatch,
) -> None:
    config = DatabaseConfig(path=tmp_path / "a3-rollback.sqlite")
    seed_r3d_final_dc3_batch(config)
    before = db_dump(config)
    engine = create_sqlite_engine(config)
    monkeypatch.setattr(a3, "create_sqlite_engine", lambda _config: engine)

    def fail(connection, cursor, statement, parameters, context, executemany):
        del connection, cursor, parameters, context, executemany
        if statement.strip().startswith(
            "INSERT INTO recipe_prepared_nutrient_values"
        ):
            raise RuntimeError("injected DC4-A3 prepared authority failure")

    event.listen(engine, "before_cursor_execute", fail)
    try:
        with pytest.raises(RuntimeError, match="injected DC4-A3"):
            a3.seed_dc4_a3_russian_step_corrections(config)
    finally:
        event.remove(engine, "before_cursor_execute", fail)
        engine.dispose()

    assert db_dump(config) == before


def test_a3_artifact_rejects_english_consumer_regression(tmp_path: Path) -> None:
    payload = a3._load_corrections()
    payload["recipes"][0]["new_steps"][-1] += " source total"
    changed = tmp_path / "changed.json"
    changed.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    with pytest.raises(ValueError, match="Russian correction"):
        a3._load_corrections(changed)
