import shutil
import sqlite3

import pytest

from app.db import migrations
from app.db.config import DatabaseConfig
from app.domain.recipe_nutrition_v2 import NUTRIENT_CODES
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
from app.persistence.sqlalchemy_core.food_ingredient_composition import (
    create_food_catalogue_service,
)
from app.persistence.sqlalchemy_core.food_recipe_composition import (
    create_food_recipe_catalogue_service,
)
from app.persistence.sqlalchemy_core.food_recipe_repositories import (
    SqlAlchemyRecipeRepository,
    SqlAlchemyRecipeVersionRepository,
)
from app.persistence.sqlalchemy_core.recipe_nutrition_v2 import (
    SqlAlchemyPreparedRecipeNutritionRepository,
    create_recipe_nutrition_v2_service,
)
from app.seed.r2f_cheese_sandwich import seed_r2f_cheese_sandwich
from app.seed.r3a_school2022_main_batch import (
    APPLICABILITY_PATH,
    IDENTITY_ONLY_FOOD_CODES,
    IDENTITY_REVIEW_PATH,
    PACKAGE,
    PROCESS_BINDING_PATH,
    PUBLICATION_SPECS_PATH,
    RECIPE_CODES,
    SELECTION_PATH,
    SOURCE_VERIFICATION_PATH,
    SUMMARY_PATH,
    _load_contract,
    activate_r3a_school2022_main_batch,
    publish_r3a_school2022_main_batch,
    seed_r3a_school2022_main_batch,
)
from app.services.prepared_recipe_activation import PreparedRecipeActivationError


@pytest.fixture(scope="session")
def baseline(tmp_path_factory):
    config = DatabaseConfig(path=tmp_path_factory.mktemp("r3a-base") / "base.sqlite")
    seed_r2f_cheese_sandwich(config)
    return config


@pytest.fixture
def database(baseline, tmp_path):
    config = DatabaseConfig(path=tmp_path / "r3a.sqlite")
    shutil.copyfile(baseline.path, config.path)
    return config


def db_dump(config: DatabaseConfig) -> str:
    with sqlite3.connect(config.path) as db:
        return "\n".join(db.iterdump())


def r3a_recipe_states(config: DatabaseConfig) -> dict[str, int]:
    placeholders = ",".join("?" for _ in RECIPE_CODES)
    with sqlite3.connect(config.path) as db:
        rows = db.execute(
            f"""
            SELECT canonical_code, is_active
            FROM food_recipes
            WHERE canonical_code IN ({placeholders})
            ORDER BY canonical_code
            """,
            RECIPE_CODES,
        ).fetchall()
    return {code: active for code, active in rows}


def r3a_counts(config: DatabaseConfig) -> dict[str, int]:
    placeholders = ",".join("?" for _ in RECIPE_CODES)
    with sqlite3.connect(config.path) as db:
        recipe_rows = db.execute(
            f"""
            SELECT id FROM food_recipes
            WHERE canonical_code IN ({placeholders})
            """,
            RECIPE_CODES,
        ).fetchall()
        recipe_ids = tuple(row[0] for row in recipe_rows)
        if not recipe_ids:
            return {"recipes": 0, "authorities": 0, "values": 0}
        recipe_placeholders = ",".join("?" for _ in recipe_ids)
        version_ids = tuple(
            row[0]
            for row in db.execute(
                f"""
                SELECT id FROM food_recipe_versions
                WHERE recipe_id IN ({recipe_placeholders})
                """,
                recipe_ids,
            ).fetchall()
        )
        version_placeholders = ",".join("?" for _ in version_ids)
        authorities = db.execute(
            f"""
            SELECT COUNT(*) FROM recipe_prepared_nutrition_authorities
            WHERE recipe_version_id IN ({version_placeholders})
            """,
            version_ids,
        ).fetchone()[0]
        values = db.execute(
            f"""
            SELECT COUNT(*) FROM recipe_prepared_nutrient_values
            WHERE recipe_version_id IN ({version_placeholders})
            """,
            version_ids,
        ).fetchone()[0]
    return {
        "recipes": len(recipe_ids),
        "authorities": authorities,
        "values": values,
    }


def test_r3a_fresh_publication_and_batch_activation(database):
    result = seed_r3a_school2022_main_batch(database)

    assert result.publication.identity_food_inserted == 3
    assert result.publication.identity_food_existing == 0
    assert result.activation_changed is True
    assert result.active_recipe_codes == RECIPE_CODES
    assert tuple(code for code, _ in result.publication.recipe_version_ids) == RECIPE_CODES
    assert all(
        disposition == "FRESH"
        for _code, disposition in result.publication.authority_dispositions
    )

    engine = create_sqlite_engine(database)
    try:
        food = create_food_catalogue_service(engine)
        catalogue = create_food_recipe_catalogue_service(engine)
        nutrition = create_recipe_nutrition_v2_service(engine)
        for code, version_id in result.publication.recipe_version_ids:
            recipe = catalogue.get_by_code(code)
            assert recipe.is_active is True
            detail = catalogue.get_current_verified(recipe.id)
            assert detail.version.id == version_id
            assert detail.version.meal_type_code.value == "main"
            projection = nutrition.neutral_consumption_projection(version_id)
            assert projection.exact_energy_ready is True
            assert projection.per_base_serving.kcal is not None
            canonical = nutrition.prepared_canonical_nutrition(version_id)
            assert len(canonical.required_total) == len(NUTRIENT_CODES) == 54
            assert canonical.total_amount("ENERGY_KCAL") is not None
            unknown = tuple(
                row for row in canonical.required_total if row.code != "ENERGY_KCAL"
            )
            assert len(unknown) == 53
            assert all(row.amount is None for row in unknown)

        for code in IDENTITY_ONLY_FOOD_CODES:
            identity = food.get_by_code(code)
            assert identity.is_active is True
    finally:
        engine.dispose()

    with sqlite3.connect(database.path) as db:
        for code in IDENTITY_ONLY_FOOD_CODES:
            row = db.execute(
                """
                SELECT i.canonical_code,
                       (SELECT COUNT(*) FROM food_nutrition_profiles p
                        WHERE p.food_ingredient_id = i.id),
                       (SELECT COUNT(*) FROM food_composition_versions c
                        WHERE c.food_ingredient_id = i.id)
                FROM food_ingredients i
                WHERE i.canonical_code = ?
                """,
                (code,),
            ).fetchone()
            assert row == (code, 0, 0)

    assert migrations.expected_migration_ids()[-1] == "0042_recipe_prepared_output_nutrition"


def test_r3a_publication_phase_keeps_all_recipes_inactive(database):
    result = publish_r3a_school2022_main_batch(database)

    assert tuple(code for code, _ in result.recipe_version_ids) == RECIPE_CODES
    assert r3a_recipe_states(database) == {code: 0 for code in sorted(RECIPE_CODES)}

    changed = activate_r3a_school2022_main_batch(database)
    assert changed is True
    assert r3a_recipe_states(database) == {code: 1 for code in sorted(RECIPE_CODES)}


def test_r3a_exact_full_replay_is_zero_write(database):
    seed_r3a_school2022_main_batch(database)
    before = db_dump(database)

    replay = seed_r3a_school2022_main_batch(database)

    assert replay.publication.identity_food_inserted == 0
    assert replay.publication.identity_food_existing == 3
    assert replay.activation_changed is False
    assert all(
        disposition == "EXACT_REPLAY"
        for _code, disposition in replay.publication.authority_dispositions
    )
    assert db_dump(database) == before


def test_r3a_mixed_activation_state_fails_closed_and_preserves_deactivation(database):
    seed_r3a_school2022_main_batch(database)
    engine = create_sqlite_engine(database)
    try:
        catalogue = create_food_recipe_catalogue_service(engine)
        recipe = catalogue.get_by_code(RECIPE_CODES[0])
        catalogue.deactivate(recipe.id)
    finally:
        engine.dispose()
    before = db_dump(database)

    with pytest.raises(PreparedRecipeActivationError, match="mixed active/inactive"):
        seed_r3a_school2022_main_batch(database)

    assert db_dump(database) == before
    states = r3a_recipe_states(database)
    assert states[RECIPE_CODES[0]] == 0
    assert sum(states.values()) == 9


def test_r3a_partial_publication_failure_resumes_missing_recipes(database, monkeypatch):
    original = SqlAlchemyPreparedRecipeNutritionRepository.add_authority
    calls = 0

    def fail_fourth(self, authority):
        nonlocal calls
        calls += 1
        if calls == 4:
            raise RuntimeError("injected fourth publication failure")
        return original(self, authority)

    with monkeypatch.context() as scoped:
        scoped.setattr(
            SqlAlchemyPreparedRecipeNutritionRepository,
            "add_authority",
            fail_fourth,
        )
        with pytest.raises(RuntimeError, match="fourth publication"):
            publish_r3a_school2022_main_batch(database)

    assert r3a_counts(database) == {"recipes": 3, "authorities": 3, "values": 3}
    assert set(r3a_recipe_states(database).values()) == {0}

    resumed = seed_r3a_school2022_main_batch(database)
    dispositions = dict(resumed.publication.authority_dispositions)
    assert tuple(dispositions[code] for code in RECIPE_CODES[:3]) == (
        "EXACT_REPLAY",
        "EXACT_REPLAY",
        "EXACT_REPLAY",
    )
    assert all(dispositions[code] == "FRESH" for code in RECIPE_CODES[3:])
    assert resumed.active_recipe_codes == RECIPE_CODES


@pytest.mark.parametrize("failure_point", ("version", "values", "authority"))
def test_r3a_first_recipe_publication_failure_rolls_back_recipe_atomically(
    database,
    monkeypatch,
    failure_point,
):
    def fail(*args, **kwargs):
        del args, kwargs
        raise RuntimeError(f"injected {failure_point} failure")

    with monkeypatch.context() as scoped:
        if failure_point == "version":
            scoped.setattr(SqlAlchemyRecipeVersionRepository, "add_detail", fail)
        elif failure_point == "values":
            scoped.setattr(
                SqlAlchemyPreparedRecipeNutritionRepository,
                "add_values",
                fail,
            )
        else:
            scoped.setattr(
                SqlAlchemyPreparedRecipeNutritionRepository,
                "add_authority",
                fail,
            )
        with pytest.raises(RuntimeError, match=f"injected {failure_point}"):
            publish_r3a_school2022_main_batch(database)

    assert r3a_counts(database) == {"recipes": 0, "authorities": 0, "values": 0}
    with sqlite3.connect(database.path) as db:
        placeholders = ",".join("?" for _ in IDENTITY_ONLY_FOOD_CODES)
        count = db.execute(
            f"""
            SELECT COUNT(*) FROM food_ingredients
            WHERE canonical_code IN ({placeholders})
            """,
            IDENTITY_ONLY_FOOD_CODES,
        ).fetchone()[0]
    assert count == 3


def test_r3a_batch_activation_failure_rolls_back_every_staged_write(
    database,
    monkeypatch,
):
    publish_r3a_school2022_main_batch(database)
    original = SqlAlchemyRecipeRepository.set_active
    calls = 0

    def fail_fifth(self, recipe_id, *, active, updated_at):
        nonlocal calls
        calls += 1
        if calls == 5:
            raise RuntimeError("injected fifth activation failure")
        return original(self, recipe_id, active=active, updated_at=updated_at)

    monkeypatch.setattr(SqlAlchemyRecipeRepository, "set_active", fail_fifth)

    with pytest.raises(RuntimeError, match="fifth activation"):
        activate_r3a_school2022_main_batch(database)

    assert r3a_recipe_states(database) == {code: 0 for code in sorted(RECIPE_CODES)}


@pytest.mark.parametrize(
    ("artifact_name", "old", "new"),
    (
        (SELECTION_PATH.name, '"112.6"', '"112.7"'),
        (IDENTITY_REVIEW_PATH.name, '"COD_FILLET_RAW"', '"COD_WHOLE_RAW"'),
        (APPLICABILITY_PATH.name, '"REVIEWED_PASS"', '"BLOCKED"'),
        (
            PROCESS_BINDING_PATH.name,
            '"PARTIAL_SOURCE_PLACEMENT"',
            '"ASSUMED_WATER_PLACEMENT"',
        ),
        (PUBLICATION_SPECS_PATH.name, '"348.3"', '"348.4"'),
        (
            SOURCE_VERIFICATION_PATH.name,
            '"source_pdf_size_bytes": 4102547',
            '"source_pdf_size_bytes": 4102548',
        ),
        (SUMMARY_PATH.name, '"selected_count": 10', '"selected_count": 9'),
    ),
)
def test_r3a_hash_pinned_contract_rejects_tampered_artifact(
    tmp_path,
    artifact_name,
    old,
    new,
):
    package = tmp_path / "package"
    shutil.copytree(PACKAGE, package)
    artifact = package / artifact_name
    text = artifact.read_text()
    assert old in text
    artifact.write_text(text.replace(old, new, 1))

    with pytest.raises(ValueError, match="R3-A"):
        _load_contract(package)


def test_r3a_source_process_review_corrections_are_published_verbatim(database):
    publish_r3a_school2022_main_batch(database)
    engine = create_sqlite_engine(database)
    try:
        catalogue = create_food_recipe_catalogue_service(engine)

        r8 = catalogue.get_by_code("SCHOOL2022_54_8M_STEAMED_BEEF_MEATBALLS")
        r8_detail = catalogue.get_latest_verified(r8.id)
        r8_steps = tuple(step.instruction for step in r8_detail.steps)
        assert not any("замоченным в воде" in step for step in r8_steps)
        assert any("не указывает жидкость" in step for step in r8_steps)

        r11 = catalogue.get_by_code("SCHOOL2022_54_11M_BEEF_PILAF")
        r11_detail = catalogue.get_latest_verified(r11.id)
        r11_steps = tuple(step.instruction for step in r11_detail.steps)
        assert not any("частью воды" in step for step in r11_steps)
        assert any("5–10 минут" in step for step in r11_steps)
        assert any("160 °C 30–40 минут" in step for step in r11_steps)
    finally:
        engine.dispose()
