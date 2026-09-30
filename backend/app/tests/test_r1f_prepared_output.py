import shutil
import sqlite3
from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import UUID

import pytest
from app.db import migrations
from app.db.config import DatabaseConfig
from app.domain.recipe_nutrition_v2 import RecipeNutritionAuthorityKind
from app.domain.food_recipes import MealTypeCode
from app.domain.meal_patterns import MealRole
from app.domain.meal_plans import (
    MemberMealPatternOpportunitySnapshot,
    MemberMealPatternSelection,
    MemberMealPatternSelectionDetail,
    MemberMealPatternSourceKind,
)
from app.domain.planner import (
    MemberPlannerConstraints,
    PlannerCandidate,
    PlannerConfig,
    PlannerFailure,
    PlannerRequest,
    PlannerRejectionCode,
    generate_week,
)
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
from app.persistence.sqlalchemy_core.food_recipe_composition import (
    create_food_recipe_catalogue_service,
)
from app.persistence.sqlalchemy_core.recipe_nutrition_v2 import (
    create_recipe_nutrition_v2_service,
)
from app.seed.food_ingredients import seed_food_ingredients
from app.seed.r1b_reviewed_recipes import seed_r1b_recipes
from app.seed.r1f_prepared_output import (
    CHICKEN_FOOD_CODE,
    CHICKEN_RECIPE_CODE,
    EGG_RECIPE_CODE,
    seed_r1f_prepared_output,
)
from app.seed.ru_food_data import seed_ru_food_data
from app.seed.ru_nut_db_r1a import seed_ru_nut_db_r1a
from app.seed.ru_nut_db_step4 import seed_ru_nut_db_step4
from app.services.planner import PlannerService


def uid(number: int) -> UUID:
    return UUID(f"00000000-0000-4000-8000-{number:012d}")


def selection(member_id: UUID, role: MealRole) -> MemberMealPatternSelectionDetail:
    now = datetime(2026, 9, 30, tzinfo=timezone.utc)
    selection_id = uid(9000 + int(member_id.hex[-2:], 16))
    selected = MemberMealPatternSelection(
        selection_id,
        uid(1),
        member_id,
        1,
        MemberMealPatternSourceKind.CUSTOM,
        None,
        None,
        False,
        now,
        None,
        now,
    )
    opportunities = tuple(
        MemberMealPatternOpportunitySnapshot(selection_id, weekday, 1, role)
        for weekday in range(1, 8)
    )
    return MemberMealPatternSelectionDetail(selected, opportunities)


def real_candidate(catalogue, nutrition, code: str) -> PlannerCandidate:
    recipe = catalogue.get_by_code(code)
    detail = catalogue.get_current_verified(recipe.id)
    projection = nutrition.neutral_consumption_projection(detail.version.id)
    return PlannerCandidate(
        detail.version.id,
        detail.version.meal_type_code,
        frozenset(row.food_ingredient_id for row in detail.ingredients),
        projection.per_base_serving.kcal,
        projection.legacy_status,
        True,
        detail.version.total_time_minutes,
        detail.version.batch_friendly,
        projection.exact_energy_ready,
    )


@pytest.fixture(scope="module")
def baseline(tmp_path_factory):
    config = DatabaseConfig(path=tmp_path_factory.mktemp("r1f-base") / "base.sqlite")
    migrations.apply_migrations(config)
    seed_food_ingredients(config)
    seed_ru_food_data(config)
    seed_ru_nut_db_step4(config)
    seed_ru_nut_db_r1a(config)
    seed_r1b_recipes(config)
    return config


@pytest.fixture
def database(baseline, tmp_path):
    config = DatabaseConfig(path=tmp_path / "r1f.sqlite")
    shutil.copyfile(baseline.path, config.path)
    return config


def db_dump(config):
    with sqlite3.connect(config.path) as db:
        return "\n".join(db.iterdump())


def historical_697(config):
    with sqlite3.connect(config.path) as db:
        return db.execute(
            """
            SELECT r.id, r.canonical_code, r.canonical_name, r.canonical_name_key,
                   r.is_active, v.id, v.version_number, v.source_name,
                   v.source_recipe_id, v.source_version, v.source_output_g,
                   v.source_output_text
            FROM food_recipes r
            JOIN food_recipe_versions v ON v.recipe_id = r.id
            WHERE r.canonical_code = 'USSR82_697_BOILED_CHICKEN'
            """
        ).fetchone()


def test_r1f_fresh_publication_activates_exact_energy_breakfast_and_main(database):
    historical_before = historical_697(database)
    assert historical_before is not None
    assert historical_before[4] == 0

    result = seed_r1f_prepared_output(database)

    assert result.chicken_food_inserted == 1
    assert result.chicken_food_existing == 0
    assert set(result.active_recipe_codes) == {EGG_RECIPE_CODE, CHICKEN_RECIPE_CODE}
    assert dict(result.authority_dispositions) == {
        EGG_RECIPE_CODE: "FRESH",
        CHICKEN_RECIPE_CODE: "FRESH",
    }
    assert dict(result.exact_energy_kcal) == {
        EGG_RECIPE_CODE: Decimal("63.000000"),
        CHICKEN_RECIPE_CODE: Decimal("167.700000"),
    }

    engine = create_sqlite_engine(database)
    try:
        catalogue = create_food_recipe_catalogue_service(engine)
        nutrition = create_recipe_nutrition_v2_service(engine)
        planner = PlannerService(
            None,
            None,
            catalogue,
            None,
            None,
            recipe_nutrition=nutrition,  # type: ignore[arg-type]
        )
        admissions = {
            row.canonical_code: row for row in planner.compose_candidate_admission()
        }
        for code in (EGG_RECIPE_CODE, CHICKEN_RECIPE_CODE):
            assert admissions[code].eligible is True
            assert admissions[code].exact_energy_ready is True
            detail = catalogue.get_current_verified(admissions[code].recipe_id)
            projection = nutrition.neutral_consumption_projection(detail.version.id)
            assert (
                projection.authority_kind
                is RecipeNutritionAuthorityKind.PREPARED_OUTPUT_V1
            )
            assert projection.exact_energy_ready is True
            assert projection.legacy_status.value == "INCOMPLETE"

        egg_detail = catalogue.get_current_verified(
            catalogue.get_by_code(EGG_RECIPE_CODE).id
        )
        chicken_detail = catalogue.get_current_verified(
            catalogue.get_by_code(CHICKEN_RECIPE_CODE).id
        )
        assert egg_detail.version.source_output_g == Decimal("40.000000")
        assert chicken_detail.version.source_output_g == Decimal("75.000000")
        assert (
            egg_detail.ingredients[0].food_ingredient_id
            != chicken_detail.ingredients[0].food_ingredient_id
        )
    finally:
        engine.dispose()

    with sqlite3.connect(database.path) as db:
        assert (
            db.execute(
                "SELECT COUNT(*) FROM recipe_prepared_nutrition_authorities"
            ).fetchone()[0]
            == 2
        )
        assert (
            db.execute(
                "SELECT COUNT(*) FROM recipe_prepared_nutrient_values"
            ).fetchone()[0]
            == 2
        )
        assert (
            db.execute(
                """
                SELECT COUNT(*)
                FROM food_nutrition_profiles p
                JOIN food_ingredients i ON i.id = p.food_ingredient_id
                WHERE i.canonical_code = ?
                """,
                (CHICKEN_FOOD_CODE,),
            ).fetchone()[0]
            == 0
        )
        names = db.execute(
            """
            SELECT canonical_code, canonical_name_key
            FROM food_recipes
            WHERE canonical_code IN ('USSR82_697_BOILED_CHICKEN', ?)
            ORDER BY canonical_code
            """,
            (CHICKEN_RECIPE_CODE,),
        ).fetchall()
        assert len(names) == 2
        assert names[0][1] != names[1][1]
        assert db.execute("PRAGMA foreign_key_check").fetchall() == []

    assert historical_697(database) == historical_before


def test_r1f_exact_replay_is_zero_write_and_does_not_duplicate(database):
    seed_r1f_prepared_output(database)
    before = db_dump(database)

    replay = seed_r1f_prepared_output(database)

    assert replay.chicken_food_inserted == 0
    assert replay.chicken_food_existing == 1
    assert dict(replay.authority_dispositions) == {
        EGG_RECIPE_CODE: "EXACT_REPLAY",
        CHICKEN_RECIPE_CODE: "EXACT_REPLAY",
    }
    assert set(replay.active_recipe_codes) == {EGG_RECIPE_CODE, CHICKEN_RECIPE_CODE}
    assert db_dump(database) == before


def test_r1f_publication_replay_does_not_reactivate_deliberately_deactivated_recipe(
    database,
):
    seed_r1f_prepared_output(database)
    engine = create_sqlite_engine(database)
    try:
        catalogue = create_food_recipe_catalogue_service(engine)
        breakfast = catalogue.get_by_code(EGG_RECIPE_CODE)
        catalogue.deactivate(breakfast.id)
    finally:
        engine.dispose()

    replay = seed_r1f_prepared_output(database)

    assert EGG_RECIPE_CODE not in replay.active_recipe_codes
    assert CHICKEN_RECIPE_CODE in replay.active_recipe_codes

    engine = create_sqlite_engine(database)
    try:
        catalogue = create_food_recipe_catalogue_service(engine)
        assert catalogue.get_by_code(EGG_RECIPE_CODE).is_active is False
        detail = catalogue.get_latest_verified(
            catalogue.get_by_code(EGG_RECIPE_CODE).id
        )
        projection = create_recipe_nutrition_v2_service(
            engine
        ).neutral_consumption_projection(detail.version.id)
        assert projection.exact_energy_ready is True
    finally:
        engine.dispose()


def test_r1f_prepared_authority_tables_are_immutable(database):
    seed_r1f_prepared_output(database)
    with sqlite3.connect(database.path) as db:
        recipe_version_id = db.execute(
            """
            SELECT v.id
            FROM food_recipe_versions v
            JOIN food_recipes r ON r.id = v.recipe_id
            WHERE r.canonical_code = ?
            """,
            (EGG_RECIPE_CODE,),
        ).fetchone()[0]

        with pytest.raises(sqlite3.IntegrityError, match="неизменя"):
            db.execute(
                """
                UPDATE recipe_prepared_nutrition_authorities
                SET source_name='changed'
                WHERE recipe_version_id=?
                """,
                (recipe_version_id,),
            )
        db.rollback()

        with pytest.raises(sqlite3.IntegrityError, match="неизменя"):
            db.execute(
                """
                UPDATE recipe_prepared_nutrient_values
                SET amount='999'
                WHERE recipe_version_id=?
                """,
                (recipe_version_id,),
            )
        db.rollback()

        with pytest.raises(sqlite3.IntegrityError, match="запечатан"):
            db.execute(
                """
                INSERT INTO recipe_prepared_nutrient_values (
                    recipe_version_id, registry_version, nutrient_code,
                    amount, provenance_json
                ) VALUES (?, 'RU_NUTRIENT_REGISTRY_V2', 'PROTEIN', '1', '{}')
                """,
                (recipe_version_id,),
            )
        db.rollback()


def test_migration_0042_is_registered_and_required_tables_exist(database):
    assert migrations.expected_migration_ids()[-1] == (
        "0042_recipe_prepared_output_nutrition"
    )
    with sqlite3.connect(database.path) as db:
        tables = {
            row[0]
            for row in db.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
    assert {
        "recipe_prepared_nutrition_authorities",
        "recipe_prepared_nutrient_values",
    } <= tables

def test_r1f_real_planner_candidates_honor_ingredient_exclusions(database):
    seed_r1f_prepared_output(database)
    engine = create_sqlite_engine(database)
    try:
        catalogue = create_food_recipe_catalogue_service(engine)
        nutrition = create_recipe_nutrition_v2_service(engine)

        cases = (
            (EGG_RECIPE_CODE, MealRole.BREAKFAST),
            (CHICKEN_RECIPE_CODE, MealRole.DINNER),
        )
        for offset, (code, role) in enumerate(cases, start=1):
            candidate = real_candidate(catalogue, nutrition, code)
            assert candidate.food_ingredient_ids
            member_id = uid(100 + offset)
            request = PlannerRequest(
                uid(1),
                date(2026, 9, 28),
                (
                    MemberPlannerConstraints(
                        member_id,
                        selection(member_id, role),
                        Decimal("2000"),
                        candidate.food_ingredient_ids,
                    ),
                ),
                (candidate,),
            )
            result = generate_week(
                request,
                PlannerConfig(max_recipe_repetitions=10),
            )
            assert isinstance(result, PlannerFailure)
            matching = [
                trace
                for trace in result.trace.candidates
                if trace.recipe_version_id == candidate.recipe_version_id
            ]
            assert matching
            assert any(
                PlannerRejectionCode.MEMBER_EXCLUDED_INGREDIENT
                in trace.rejection_codes
                for trace in matching
            )
    finally:
        engine.dispose()


def test_r1f_serving_scaling_reuses_recipe_and_recipeversion_identity(database):
    seed_r1f_prepared_output(database)
    engine = create_sqlite_engine(database)
    try:
        catalogue = create_food_recipe_catalogue_service(engine)
        for code in (EGG_RECIPE_CODE, CHICKEN_RECIPE_CODE):
            recipe = catalogue.get_by_code(code)
            original = catalogue.get_current_verified(recipe.id)
            scaled = catalogue.scale_version(
                original.version.id, Decimal("2")
            )
            assert scaled.recipe.id == original.recipe.id == recipe.id
            assert scaled.version.id == original.version.id
            assert scaled.version.base_servings == original.version.base_servings
            assert tuple(row.quantity for row in scaled.ingredients) == tuple(
                row.quantity * Decimal("2")
                for row in original.ingredients
            )
            assert catalogue.get_by_code(code).id == recipe.id
            assert len(catalogue.list_versions(recipe.id)) == 1
    finally:
        engine.dispose()

