import csv
from dataclasses import asdict
from decimal import Decimal
from pathlib import Path
import shutil
import sqlite3

import pytest

from app.db.config import DatabaseConfig
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
from app.persistence.sqlalchemy_core.food_ingredient_composition import (
    create_food_catalogue_service,
)
from app.persistence.sqlalchemy_core.food_ingredient_uow import (
    SqlAlchemyFoodCatalogueReadScope,
)
from app.seed.food_ingredients import (
    DEFAULT_SEED_DIRECTORY,
    FoodIngredientSeedError,
    load_seed_entries,
    seed_food_ingredients,
)
from app.services.food_ingredients import FoodCatalogueConflictError


def _copy_seed(tmp_path: Path) -> Path:
    target = tmp_path / "seed"
    shutil.copytree(DEFAULT_SEED_DIRECTORY, target)
    return target


def _append_csv(path: Path, row: dict[str, str]) -> None:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames
    assert fieldnames is not None
    with path.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writerow(row)


def _update_csv_row(
    path: Path, *, canonical_code: str, changes: dict[str, str]
) -> None:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames
        rows = list(reader)
    assert fieldnames is not None
    matched = False
    for row in rows:
        if row["canonical_code"] == canonical_code:
            row.update(changes)
            matched = True
    assert matched
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def test_checked_in_seed_has_100_quality_validated_authoritative_rows():
    entries = load_seed_entries()

    assert len(entries) == 100
    assert (
        sum(entry.nutrition.source_data_type == "Foundation" for entry in entries) == 87
    )
    assert (
        sum(entry.nutrition.source_data_type == "SR Legacy" for entry in entries) == 13
    )
    assert len({entry.canonical_code for entry in entries}) == 100
    assert (
        len({entry.canonical_name.casefold().replace("ё", "е") for entry in entries})
        == 100
    )
    assert all(entry.nutrition.source_name == "USDA_FDC" for entry in entries)
    assert all(entry.nutrition.source_id for entry in entries)
    assert all(entry.nutrition.source_version for entry in entries)
    assert all(entry.nutrition.basis_grams == Decimal("100") for entry in entries)
    assert all(entry.allergens_reviewed is False for entry in entries)
    assert all(entry.allergen_codes == () for entry in entries)


def test_seed_is_idempotent_and_every_active_item_has_current_provenance(tmp_path):
    config = DatabaseConfig(path=tmp_path / "seed.sqlite")

    first = seed_food_ingredients(config)
    second = seed_food_ingredients(config)

    assert asdict(first) == {
        "ingredients_inserted": 100,
        "ingredients_existing": 0,
        "aliases_inserted": 89,
        "aliases_existing": 0,
        "nutrition_profiles_inserted": 100,
        "nutrition_profiles_existing": 0,
        "conflicts": 0,
    }
    assert asdict(second) == {
        "ingredients_inserted": 0,
        "ingredients_existing": 100,
        "aliases_inserted": 0,
        "aliases_existing": 89,
        "nutrition_profiles_inserted": 0,
        "nutrition_profiles_existing": 100,
        "conflicts": 0,
    }
    with sqlite3.connect(config.path) as connection:
        active_count = connection.execute(
            "SELECT COUNT(*) FROM food_ingredients WHERE is_active=1"
        ).fetchone()[0]
        current_with_provenance = connection.execute(
            """
            SELECT COUNT(*)
            FROM food_ingredients AS i
            JOIN food_nutrition_profiles AS n
              ON n.food_ingredient_id=i.id AND n.is_current=1
            WHERE i.is_active=1
              AND length(trim(n.source_name)) > 0
              AND length(trim(n.source_id)) > 0
              AND length(trim(n.source_version)) > 0
              AND n.verified_at IS NOT NULL
            """
        ).fetchone()[0]
        assert (
            connection.execute(
                "SELECT COUNT(*) FROM food_ingredient_aliases"
            ).fetchone()[0]
            == 89
        )
        assert (
            connection.execute(
                "SELECT COUNT(*) FROM food_nutrition_profiles"
            ).fetchone()[0]
            == 100
        )
    assert active_count == current_with_provenance == 100


def test_seed_search_cyrillic_yo_and_decimal_roundtrip(tmp_path):
    config = DatabaseConfig(path=tmp_path / "search.sqlite")
    seed_food_ingredients(config)
    engine = create_sqlite_engine(config)
    try:
        service = create_food_catalogue_service(engine)
        assert service.search("греч")[0].canonical_code == "BUCKWHEAT"
        assert service.search("ГРЕЧКА")[0].canonical_code == "BUCKWHEAT"
        assert service.search("СВЕКЛА")[0].canonical_code == "BEET"
        buckwheat = service.get_by_code("BUCKWHEAT")
        with SqlAlchemyFoodCatalogueReadScope(engine) as scope:
            nutrition = scope.nutrition_profiles.get_current(buckwheat.id)
        assert nutrition is not None
        assert nutrition.kcal == Decimal("331.600521")
        assert nutrition.protein_g == Decimal("11.065340")
    finally:
        engine.dispose()


def test_seed_rerun_never_reactivates_deactivated_item(tmp_path):
    config = DatabaseConfig(path=tmp_path / "deactivate.sqlite")
    seed_food_ingredients(config)
    engine = create_sqlite_engine(config)
    try:
        service = create_food_catalogue_service(engine)
        buckwheat = service.get_by_code("BUCKWHEAT")
        service.deactivate(buckwheat.id)
    finally:
        engine.dispose()

    summary = seed_food_ingredients(config)
    engine = create_sqlite_engine(config)
    try:
        service = create_food_catalogue_service(engine)
        assert summary.ingredients_existing == 100
        assert all(
            result.canonical_code != "BUCKWHEAT" for result in service.search("греч")
        )
        assert service.get(buckwheat.id).is_active is False
    finally:
        engine.dispose()


def test_duplicate_alias_validation_happens_before_schema_or_data_mutation(tmp_path):
    seed_directory = _copy_seed(tmp_path)
    database = tmp_path / "invalid.sqlite"
    _append_csv(
        seed_directory / "aliases.csv",
        {
            "canonical_code": "RICE_WHITE",
            "alias": "гречка",
            "language_code": "ru",
        },
    )

    with pytest.raises(FoodIngredientSeedError, match="duplicated"):
        seed_food_ingredients(
            DatabaseConfig(path=database), seed_directory=seed_directory
        )

    assert not database.exists()


def test_persisted_nutrition_conflict_rolls_back_alias_inserted_earlier_in_seed(
    tmp_path,
):
    config = DatabaseConfig(path=tmp_path / "rollback.sqlite")
    seed_food_ingredients(config)
    seed_directory = _copy_seed(tmp_path)
    _append_csv(
        seed_directory / "aliases.csv",
        {
            "canonical_code": "BUCKWHEAT",
            "alias": "ядрица тестовая",
            "language_code": "ru",
        },
    )
    _update_csv_row(
        seed_directory / "nutrition.csv",
        canonical_code="RICE_WHITE",
        changes={"kcal": "370.000000"},
    )

    with pytest.raises(FoodCatalogueConflictError, match="different"):
        seed_food_ingredients(config, seed_directory=seed_directory)

    with sqlite3.connect(config.path) as connection:
        assert (
            connection.execute(
                "SELECT COUNT(*) FROM food_ingredient_aliases WHERE alias_key=?",
                ("ядрица тестовая",),
            ).fetchone()[0]
            == 0
        )
        assert (
            connection.execute("SELECT COUNT(*) FROM food_ingredients").fetchone()[0]
            == 100
        )
        assert (
            connection.execute(
                "SELECT COUNT(*) FROM food_nutrition_profiles"
            ).fetchone()[0]
            == 100
        )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("kcal", "NaN"),
        ("protein_g", "Infinity"),
        ("fat_g", "-Infinity"),
        ("carbohydrates_g", "-1"),
        ("fiber_g", "101"),
        ("kcal", "1E+999999"),
    ],
)
def test_seed_rejects_hostile_numeric_source_rows(field, value, tmp_path):
    seed_directory = _copy_seed(tmp_path)
    _update_csv_row(
        seed_directory / "nutrition.csv",
        canonical_code="BUCKWHEAT",
        changes={field: value},
    )

    with pytest.raises((FoodIngredientSeedError, ValueError)):
        load_seed_entries(seed_directory)
