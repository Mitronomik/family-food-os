from dataclasses import asdict
from decimal import Decimal
import json
from pathlib import Path
import shutil
import sqlite3

import pytest

from app.db.config import DatabaseConfig
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
from app.persistence.sqlalchemy_core.food_ingredient_composition import (
    create_food_catalogue_service,
)
from app.persistence.sqlalchemy_core.food_recipe_composition import (
    create_food_recipe_catalogue_service,
)
from app.seed.food_ingredients import seed_food_ingredients
from app.seed.food_recipes import (
    DEFAULT_SEED_DIRECTORY,
    FoodRecipeSeedError,
    load_seed_entries,
    seed_food_recipes,
)
from app.services.food_recipes import (
    FoodIngredientResolutionError,
    RecipeCatalogueConflictError,
)

EXPECTED_RECIPE_COUNT = 30
EXPECTED_INGREDIENT_COUNT = 365
EXPECTED_STEP_COUNT = 315
EXPECTED_EQUIPMENT_COUNT = 0


def _copy_seed(tmp_path: Path) -> Path:
    target = tmp_path / "recipes"
    shutil.copytree(DEFAULT_SEED_DIRECTORY, target)
    return target


def _change_quantity(seed_directory: Path) -> None:
    path = seed_directory / "recipes.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["recipes"][0]["version"]["ingredients"][0]["quantity"] = "999.000000"
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def test_checked_in_seed_matches_frozen_corpus_manifest_and_rights_review():
    entries = load_seed_entries()
    manifest = json.loads(
        (DEFAULT_SEED_DIRECTORY / "source-manifest.json").read_text(encoding="utf-8")
    )["sources"]

    assert len(entries) == len(manifest) == EXPECTED_RECIPE_COUNT
    assert len({entry.canonical_code for entry in entries}) == EXPECTED_RECIPE_COUNT
    assert (
        sum(len(entry.version.ingredients) for entry in entries)
        == EXPECTED_INGREDIENT_COUNT
    )
    assert sum(len(entry.version.steps) for entry in entries) == EXPECTED_STEP_COUNT
    assert (
        sum(len(entry.version.equipment_codes) for entry in entries)
        == EXPECTED_EQUIPMENT_COUNT
    )
    assert len({source["source_document_sha256"] for source in manifest}) == 30
    assert all(len(source["source_document_sha256"]) == 64 for source in manifest)
    assert all(source["source_original_servings"] == 6 for source in manifest)
    assert all(source["rights_review_status"] == "REVIEWED" for source in manifest)
    assert all(
        source["rights_basis"] and source["rights_evidence_url"] for source in manifest
    )


def test_source_manifest_matches_frozen_corpus_and_accepted_food_ingredient_subset():
    corpus = json.loads(
        (
            DEFAULT_SEED_DIRECTORY.parents[1]
            / "curation"
            / "pr4"
            / "recipe-corpus.json"
        ).read_text(encoding="utf-8")
    )
    manifest = json.loads(
        (DEFAULT_SEED_DIRECTORY / "source-manifest.json").read_text(encoding="utf-8")
    )["sources"]
    accepted_codes = {
        line.strip()
        for line in (
            DEFAULT_SEED_DIRECTORY.parents[1]
            / "curation"
            / "pr4"
            / "mvp0-food-ingredient-codes.txt"
        )
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    }
    entries = load_seed_entries()
    used_codes = {
        ingredient.food_ingredient_code
        for entry in entries
        for ingredient in entry.version.ingredients
    }

    assert {
        (item["recipe_source_id"], item["source_url"]) for item in corpus["recipes"]
    } == {(item["recipe_source_id"], item["source_url"]) for item in manifest}
    assert len(accepted_codes) == 119
    assert used_codes == accepted_codes


def test_every_seed_recipe_has_complete_ordered_structure_and_provenance():
    for entry in load_seed_entries():
        version = entry.version
        assert version.verification_status == "SOURCE_VERIFIED"
        assert version.rights_review_status == "REVIEWED"
        assert version.verified_at is not None
        assert version.rights_basis
        assert version.source_version == f"sha256:{version.source_document_sha256}"
        assert version.source_original_servings == Decimal("6")
        assert version.ingredients
        assert version.steps
        assert all(item.source_amount_text for item in version.ingredients)


def test_selected_alternatives_and_semicolon_plus_water_are_explicit():
    entries = {entry.canonical_code: entry for entry in load_seed_entries()}
    fajita = entries["CHICKEN_FAJITA"].version.ingredients
    selected_lime = next(
        item for item in fajita if item.food_ingredient_code == "LIME_JUICE"
    )
    assert selected_lime.quantity == Decimal("60")
    assert selected_lime.unit == "ml"
    assert "lime juice alternative" in selected_lime.normalization_note

    baked = entries["BAKED_SWEET_POTATOES_APPLES"].version.ingredients
    baked_water = [item for item in baked if item.food_ingredient_code == "WATER"]
    assert [(item.quantity, item.unit) for item in baked_water] == [
        (Decimal("56.699046"), "g"),
        (Decimal("7.5"), "ml"),
    ]
    assert all("semicolon-plus" in item.normalization_note for item in baked_water)


def test_seed_is_atomic_idempotent_and_has_exact_production_counts(tmp_path):
    config = DatabaseConfig(path=tmp_path / "seed.sqlite")

    first = seed_food_recipes(config)
    second = seed_food_recipes(config)

    assert asdict(first) == {
        "recipes_inserted": 30,
        "recipes_existing": 0,
        "versions_inserted": 30,
        "versions_existing": 0,
        "ingredients_inserted": 365,
        "ingredients_existing": 0,
        "steps_inserted": 315,
        "steps_existing": 0,
        "equipment_inserted": 0,
        "equipment_existing": 0,
        "conflicts": 0,
    }
    assert asdict(second) == {
        "recipes_inserted": 0,
        "recipes_existing": 30,
        "versions_inserted": 0,
        "versions_existing": 30,
        "ingredients_inserted": 0,
        "ingredients_existing": 365,
        "steps_inserted": 0,
        "steps_existing": 315,
        "equipment_inserted": 0,
        "equipment_existing": 0,
        "conflicts": 0,
    }
    with sqlite3.connect(config.path) as connection:
        counts = tuple(
            connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in (
                "food_recipes",
                "food_recipe_versions",
                "food_recipe_ingredients",
                "food_recipe_steps",
                "food_recipe_equipment",
            )
        )
        active_current = connection.execute(
            """
            SELECT COUNT(*) FROM food_recipes AS r
            JOIN food_recipe_versions AS v ON v.recipe_id=r.id
            WHERE r.is_active=1 AND v.verification_status='SOURCE_VERIFIED'
              AND v.version_number=(
                  SELECT MAX(v2.version_number) FROM food_recipe_versions AS v2
                  WHERE v2.recipe_id=r.id AND v2.verification_status='SOURCE_VERIFIED'
              )
            """
        ).fetchone()[0]
    assert counts == (30, 30, 365, 315, 0)
    assert active_current == 30


def test_seed_conflicts_when_same_provenance_has_changed_structure(tmp_path):
    config = DatabaseConfig(path=tmp_path / "conflict.sqlite")
    seed_food_recipes(config)
    changed = _copy_seed(tmp_path)
    _change_quantity(changed)

    with pytest.raises(RecipeCatalogueConflictError, match="Same-provenance"):
        seed_food_recipes(config, seed_directory=changed)

    with sqlite3.connect(config.path) as connection:
        assert (
            connection.execute("SELECT COUNT(*) FROM food_recipe_versions").fetchone()[
                0
            ]
            == 30
        )
        assert (
            connection.execute(
                "SELECT COUNT(*) FROM food_recipe_ingredients"
            ).fetchone()[0]
            == 365
        )


def test_inactive_required_food_ingredient_rolls_back_entire_recipe_seed(tmp_path):
    config = DatabaseConfig(path=tmp_path / "inactive.sqlite")
    seed_food_ingredients(config)
    engine = create_sqlite_engine(config)
    try:
        food_service = create_food_catalogue_service(engine)
        food_service.deactivate(food_service.get_by_code("WATER").id)
    finally:
        engine.dispose()

    with pytest.raises(FoodIngredientResolutionError, match="WATER"):
        seed_food_recipes(config)

    with sqlite3.connect(config.path) as connection:
        assert (
            connection.execute("SELECT COUNT(*) FROM food_recipes").fetchone()[0] == 0
        )
        assert (
            connection.execute("SELECT COUNT(*) FROM food_recipe_versions").fetchone()[
                0
            ]
            == 0
        )


def test_seed_rerun_does_not_reactivate_deactivated_recipe(tmp_path):
    config = DatabaseConfig(path=tmp_path / "inactive-recipe.sqlite")
    seed_food_recipes(config)
    engine = create_sqlite_engine(config)
    try:
        service = create_food_recipe_catalogue_service(engine)
        recipe = service.get_by_code("SPICED_OATMEAL")
        service.deactivate(recipe.id)
    finally:
        engine.dispose()

    seed_food_recipes(config)
    engine = create_sqlite_engine(config)
    try:
        service = create_food_recipe_catalogue_service(engine)
        assert service.get(recipe.id).is_active is False
        assert all(item.id != recipe.id for item in service.list_active())
    finally:
        engine.dispose()


def test_seeded_recipe_scales_six_to_three_and_nine_without_persistence(tmp_path):
    config = DatabaseConfig(path=tmp_path / "scale.sqlite")
    seed_food_recipes(config)
    engine = create_sqlite_engine(config)
    try:
        service = create_food_recipe_catalogue_service(engine)
        recipe = service.get_by_code("SPICED_OATMEAL")
        original = service.get_current_verified(recipe.id)
        half = service.scale_version(original.version.id, Decimal("3"))
        one_and_half = service.scale_version(original.version.id, Decimal("9"))
        assert half.ingredients[0].quantity == original.ingredients[0].quantity / 2
        assert one_and_half.ingredients[0].quantity == original.ingredients[
            0
        ].quantity * Decimal("1.5")
        assert service.get_version_detail(original.version.id) == original
    finally:
        engine.dispose()


def test_invalid_seed_is_rejected_before_database_creation(tmp_path):
    changed = _copy_seed(tmp_path)
    payload_path = changed / "source-manifest.json"
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    payload["sources"][0]["source_document_sha256"] = "bad"
    payload_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    with pytest.raises(FoodRecipeSeedError):
        seed_food_recipes(
            DatabaseConfig(path=tmp_path / "invalid.sqlite"), seed_directory=changed
        )

    assert not (tmp_path / "invalid.sqlite").exists()
