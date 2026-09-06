import json
import shutil
import sqlite3
from dataclasses import asdict
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

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
    CURATION_DIRECTORY,
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
EXPECTED_INGREDIENT_COUNT = 189
EXPECTED_STEP_COUNT = 169
EXPECTED_EQUIPMENT_COUNT = 86
EXPECTED_FOOD_INGREDIENT_COUNT = 81


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


def test_checked_in_seed_matches_accepted_data2_contract():
    entries = load_seed_entries()
    manifest = json.loads(
        (DEFAULT_SEED_DIRECTORY / "source-manifest.json").read_text(encoding="utf-8")
    )["sources"]
    corpus = json.loads(
        (CURATION_DIRECTORY / "recipe-corpus.json").read_text(encoding="utf-8")
    )["recipes"]

    assert len(entries) == len(manifest) == len(corpus) == EXPECTED_RECIPE_COUNT
    assert {entry.version.source_recipe_id for entry in entries} == {
        row["recipe_source_id"] for row in corpus
    }
    assert (
        sum(len(entry.version.ingredients) for entry in entries)
        == EXPECTED_INGREDIENT_COUNT
    )
    assert sum(len(entry.version.steps) for entry in entries) == EXPECTED_STEP_COUNT
    assert (
        sum(len(entry.version.equipment_codes) for entry in entries)
        == EXPECTED_EQUIPMENT_COUNT
    )
    assert (
        len(
            {
                ingredient.food_ingredient_code
                for entry in entries
                for ingredient in entry.version.ingredients
            }
        )
        == EXPECTED_FOOD_INGREDIENT_COUNT
    )
    assert all(source["rights_review_status"] == "REVIEWED" for source in manifest)
    assert all(source["rights_basis"] for source in manifest)
    assert all(source["rights_evidence_urls"] for source in manifest)


def test_source_manifest_preserves_accepted_hashes_and_optional_retrieval_instants():
    manifest = json.loads(
        (DEFAULT_SEED_DIRECTORY / "source-manifest.json").read_text(encoding="utf-8")
    )["sources"]
    corpus = json.loads(
        (CURATION_DIRECTORY / "recipe-corpus.json").read_text(encoding="utf-8")
    )["recipes"]
    corpus_by_id = {row["recipe_source_id"]: row for row in corpus}

    for source in manifest:
        accepted = corpus_by_id[source["recipe_source_id"]]
        assert source["source_url"] == accepted["source_url"]
        assert source["source_document_sha256"] == accepted["source_sha256"]
        assert source["accepted_data2_sha256"] == accepted["source_sha256"]
        assert source["source_version"] == f"sha256:{accepted['source_sha256']}"
        assert Decimal(str(source["source_original_servings"])) == Decimal(
            str(accepted["source_servings"])
        )
    assert sum(source["source_retrieved_at"] is not None for source in manifest) == 3
    assert sum(source["source_retrieved_at"] is None for source in manifest) == 27


def test_every_seed_recipe_has_complete_ordered_structure_and_reviewed_provenance():
    for entry in load_seed_entries():
        version = entry.version
        assert version.verification_status == "SOURCE_VERIFIED"
        assert version.rights_review_status == "REVIEWED"
        assert version.verified_at is not None
        assert version.rights_basis
        assert version.source_version == f"sha256:{version.source_document_sha256}"
        assert version.base_servings == version.source_original_servings
        assert version.ingredients
        assert version.steps
        assert all(item.source_amount_text for item in version.ingredients)
        assert len(version.equipment_codes) == len(set(version.equipment_codes))


def test_conditional_direction_water_is_preserved_without_hiding_condition():
    entries = {entry.canonical_code: entry for entry in load_seed_entries()}
    ingredients = entries["SNAP4_SPRING_VEGETABLE_SAUTE"].version.ingredients
    water = next(item for item in ingredients if item.food_ingredient_code == "WATER")
    assert water.quantity == Decimal(30)
    assert water.unit == "ml"
    assert water.optional is True
    assert "1–2 tablespoons" in water.normalization_note
    assert "only if vegetables start to brown" in water.prep_note


def test_loader_rejects_same_count_ingredient_mapping_drift(tmp_path):
    changed = _copy_seed(tmp_path)
    path = changed / "recipes.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    ingredients = payload["recipes"][0]["version"]["ingredients"]
    ingredients[0]["food_ingredient_code"], ingredients[1]["food_ingredient_code"] = (
        ingredients[1]["food_ingredient_code"],
        ingredients[0]["food_ingredient_code"],
    )
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    with pytest.raises(FoodRecipeSeedError, match="ingredient 1 differs"):
        load_seed_entries(changed)


def test_loader_rejects_same_count_equipment_drift(tmp_path):
    changed = _copy_seed(tmp_path)
    path = changed / "recipes.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    equipment = payload["recipes"][0]["version"]["equipment_codes"]
    assert len(equipment) >= 2
    equipment[0], equipment[1] = equipment[1], equipment[0]
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    with pytest.raises(FoodRecipeSeedError, match="equipment differs"):
        load_seed_entries(changed)


def test_loader_rejects_same_count_step_or_step_lineage_drift(tmp_path):
    changed = _copy_seed(tmp_path)
    recipes_path = changed / "recipes.json"
    recipes = json.loads(recipes_path.read_text(encoding="utf-8"))
    recipes["recipes"][0]["version"]["steps"][0] += " altered"
    recipes_path.write_text(
        json.dumps(recipes, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    with pytest.raises(FoodRecipeSeedError, match="steps differ"):
        load_seed_entries(changed)

    changed = _copy_seed(tmp_path / "lineage")
    manifest_path = changed / "source-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["sources"][0]["step_comparison_result"] = "STALE"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    with pytest.raises(FoodRecipeSeedError, match="step lineage differs"):
        load_seed_entries(changed)


def test_seed_is_atomic_idempotent_and_has_exact_production_counts(tmp_path):
    config = DatabaseConfig(path=tmp_path / "seed.sqlite")

    first = seed_food_recipes(config)
    second = seed_food_recipes(config)

    assert asdict(first) == {
        "recipes_inserted": 30,
        "recipes_existing": 0,
        "versions_inserted": 30,
        "versions_existing": 0,
        "ingredients_inserted": 189,
        "ingredients_existing": 0,
        "steps_inserted": 169,
        "steps_existing": 0,
        "equipment_inserted": 86,
        "equipment_existing": 0,
        "conflicts": 0,
    }
    assert asdict(second) == {
        "recipes_inserted": 0,
        "recipes_existing": 30,
        "versions_inserted": 0,
        "versions_existing": 30,
        "ingredients_inserted": 0,
        "ingredients_existing": 189,
        "steps_inserted": 0,
        "steps_existing": 169,
        "equipment_inserted": 0,
        "equipment_existing": 86,
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
    assert counts == (30, 30, 189, 169, 86)


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
            == 189
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
        recipe = service.get_by_code("CACFP6_CORN_EDAMAME_BLEND")
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


def test_seeded_recipe_scales_non_six_serving_source_without_persistence(tmp_path):
    config = DatabaseConfig(path=tmp_path / "scale.sqlite")
    seed_food_recipes(config)
    engine = create_sqlite_engine(config)
    try:
        service = create_food_recipe_catalogue_service(engine)
        recipe = service.get_by_code("SNAP4_SPANISH_FRITTATA")
        original = service.get_current_verified(recipe.id)
        assert original.version.base_servings == Decimal(4)
        half = service.scale_version(original.version.id, Decimal(2))
        one_and_half = service.scale_version(original.version.id, Decimal(6))
        assert half.ingredients[0].quantity == (
            original.ingredients[0].quantity / 2
        ).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)
        assert one_and_half.ingredients[0].quantity == (
            original.ingredients[0].quantity * Decimal("1.5")
        ).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)
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
