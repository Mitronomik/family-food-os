import shutil
import sqlite3
from collections import Counter
from datetime import date, datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from uuid import UUID

import pytest
from app.db import migrations
from app.db.config import DatabaseConfig
from app.domain.meal_patterns import MealRole
from app.domain.meal_plans import (
    MemberMealPatternOpportunitySnapshot,
    MemberMealPatternSelection,
    MemberMealPatternSelectionDetail,
    MemberMealPatternSourceKind,
)
from app.domain.planner import (
    PlannerConfig,
    PlannerRejectionCode,
    PlannerSuccess,
    generate_week,
)
from app.domain.recipe_nutrition_v2 import (
    NUTRIENT_CODES,
    RecipeNutritionAuthorityKind,
    RecipeNutritionV2Status,
)
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
from app.persistence.sqlalchemy_core.food_ingredient_composition import (
    create_food_catalogue_service,
)
from app.persistence.sqlalchemy_core.food_recipe_composition import (
    create_food_recipe_catalogue_service,
)
from app.persistence.sqlalchemy_core.recipe_nutrition_v2 import (
    SqlAlchemyRecipeNutritionV2ReadScope,
    create_recipe_nutrition_v2_service,
)
from app.seed.food_ingredients import seed_food_ingredients
from app.seed.r1f_prepared_output import (
    CHICKEN_RECIPE_CODE,
    EGG_RECIPE_CODE,
    seed_r1f_prepared_output,
)
from app.seed.r1h_school2022_main import (
    BREAD_FOOD_CODE,
    GOULASH_RECIPE_CODE,
    IDENTITY_ONLY_FOOD_CODES,
    MEATBALLS_RECIPE_CODE,
    TOMATO_PUREE_FOOD_CODE,
    _load_contract,
    seed_r1h_school2022_main,
)
from app.seed.ru_nut_db_r1a import seed_ru_nut_db_r1a
from app.seed.ru_nut_db_step4 import seed_ru_nut_db_step4
from app.seed.ru_nut_db_step8_butter import seed_ru_nut_db_step8_butter
from app.services.meal_plans import MealPlanNotFoundError
from app.services.planner import (
    AuthoritativeGenerationRequest,
    GenerationMemberConstraints,
    PlannerService,
)


def uid(number: int) -> UUID:
    return UUID(f"00000000-0000-4000-8000-{number:012d}")


def selection(member_id: UUID, role: MealRole) -> MemberMealPatternSelectionDetail:
    now = datetime(2026, 10, 2, tzinfo=timezone.utc)
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


@pytest.fixture(scope="module")
def baseline(tmp_path_factory):
    config = DatabaseConfig(path=tmp_path_factory.mktemp("r1h-base") / "base.sqlite")
    migrations.apply_migrations(config)
    seed_food_ingredients(config)
    seed_ru_nut_db_step4(config)
    seed_ru_nut_db_r1a(config)
    seed_ru_nut_db_step8_butter(config)
    seed_r1f_prepared_output(config)
    return config


@pytest.fixture
def database(baseline, tmp_path):
    config = DatabaseConfig(path=tmp_path / "r1h.sqlite")
    shutil.copyfile(baseline.path, config.path)
    return config


def db_dump(config: DatabaseConfig) -> str:
    with sqlite3.connect(config.path) as db:
        return "\n".join(db.iterdump())


def r1f_snapshot(config: DatabaseConfig):
    with sqlite3.connect(config.path) as db:
        return db.execute(
            """
            SELECT r.canonical_code, r.canonical_name, r.is_active,
                   v.version_number, v.source_name, v.source_recipe_id,
                   v.source_version, v.source_output_g, v.source_output_text
            FROM food_recipes r
            JOIN food_recipe_versions v ON v.recipe_id = r.id
            WHERE r.canonical_code IN (?, ?)
            ORDER BY r.canonical_code
            """,
            (EGG_RECIPE_CODE, CHICKEN_RECIPE_CODE),
        ).fetchall()


def test_r1h_fresh_publication_activates_exact_school2022_mains(database):
    r1f_before = r1f_snapshot(database)
    specs, _ = _load_contract()

    result = seed_r1h_school2022_main(database)

    assert result.identity_food_inserted == 4
    assert result.identity_food_existing == 0
    assert set(result.active_recipe_codes) == {
        MEATBALLS_RECIPE_CODE,
        GOULASH_RECIPE_CODE,
    }
    assert dict(result.authority_dispositions) == {
        MEATBALLS_RECIPE_CODE: "FRESH",
        GOULASH_RECIPE_CODE: "FRESH",
    }
    assert dict(result.exact_energy_kcal) == {
        MEATBALLS_RECIPE_CODE: Decimal("153.000000"),
        GOULASH_RECIPE_CODE: Decimal("185.600000"),
    }

    engine = create_sqlite_engine(database)
    try:
        food = create_food_catalogue_service(engine)
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

        for code in (MEATBALLS_RECIPE_CODE, GOULASH_RECIPE_CODE):
            admission = admissions[code]
            assert admission.eligible is True
            assert admission.exact_energy_ready is True
            detail = catalogue.get_current_verified(admission.recipe_id)
            expected = specs["recipes"][code]["trusted_recipe_seed"]["version"]

            assert detail.version.base_servings == Decimal(expected["base_servings"])
            assert detail.version.source_original_servings == Decimal(
                expected["source_original_servings"]
            )
            assert detail.version.source_name == expected["source_name"]
            assert detail.version.source_recipe_id == expected["source_recipe_id"]
            assert detail.version.source_url == expected["source_url"]
            assert detail.version.source_version == expected["source_version"]
            assert detail.version.rights_review_status.value == expected[
                "rights_review_status"
            ]
            assert detail.version.verification_status.value == expected[
                "verification_status"
            ]
            assert (
                detail.version.source_document_sha256
                == expected["source_document_sha256"]
            )
            assert detail.version.source_output_g == Decimal(
                expected["source_output_g"]
            )
            assert detail.version.rights_basis == expected["rights_basis"]
            assert tuple(step.instruction for step in detail.steps) == tuple(
                expected["steps"]
            )
            assert tuple(
                food.get(row.food_ingredient_id).canonical_code
                for row in detail.ingredients
            ) == tuple(row["food_ingredient_code"] for row in expected["ingredients"])
            assert tuple(row.quantity for row in detail.ingredients) == tuple(
                Decimal(row["quantity"]) for row in expected["ingredients"]
            )

            prepared_expected = specs["recipes"][code]["prepared_spec"]
            with SqlAlchemyRecipeNutritionV2ReadScope(engine) as scope:
                authority = scope.prepared.get_authority(detail.version.id)
            assert authority is not None
            assert authority.output_mass_g == Decimal(
                prepared_expected["output_mass_g"]
            )
            assert authority.source_name == prepared_expected["source_name"]
            assert authority.source_id == prepared_expected["source_recipe_id"]
            assert authority.source_version == prepared_expected["source_version"]
            assert authority.source_locator == prepared_expected["source_locator"]
            assert (
                authority.source_document_sha256
                == prepared_expected["source_document_sha256"]
            )
            assert authority.source_data_type == prepared_expected["source_data_type"]
            assert (
                authority.rights_review_status
                == prepared_expected["rights_review_status"]
            )
            assert authority.rights_basis == prepared_expected["rights_basis"]
            assert authority.review_reference == prepared_expected["review_reference"]
            assert authority.value_count == 1

            projection = nutrition.neutral_consumption_projection(detail.version.id)
            assert (
                projection.authority_kind
                is RecipeNutritionAuthorityKind.PREPARED_OUTPUT_V1
            )
            assert projection.exact_energy_ready is True
            canonical = nutrition.prepared_canonical_nutrition(detail.version.id)
            assert canonical.status is RecipeNutritionV2Status.PARTIAL
            assert (
                tuple(item.code for item in canonical.required_total) == NUTRIENT_CODES
            )
            assert len(canonical.required_total) == 54
            assert (
                canonical.total_amount("ENERGY_KCAL")
                == dict(result.exact_energy_kcal)[code]
            )
            unknown = tuple(
                item for item in canonical.required_total if item.code != "ENERGY_KCAL"
            )
            assert len(unknown) == 53
            assert all(
                item.amount is None and item.availability == "UNKNOWN"
                for item in unknown
            )

        for code in IDENTITY_ONLY_FOOD_CODES:
            ingredient = food.get_by_code(code)
            assert ingredient.is_active is True
    finally:
        engine.dispose()

    with sqlite3.connect(database.path) as db:
        rows = db.execute(
            f"""
            SELECT i.canonical_code,
                   (SELECT COUNT(*) FROM food_nutrition_profiles p
                    WHERE p.food_ingredient_id = i.id),
                   (SELECT COUNT(*) FROM food_composition_versions c
                    WHERE c.food_ingredient_id = i.id)
            FROM food_ingredients i
            WHERE i.canonical_code IN ({",".join("?" for _ in IDENTITY_ONLY_FOOD_CODES)})
            ORDER BY i.canonical_code
            """,
            IDENTITY_ONLY_FOOD_CODES,
        ).fetchall()
        assert len(rows) == 4
        assert all(
            profile_count == 0 and composition_count == 0
            for _, profile_count, composition_count in rows
        )
        assert db.execute("PRAGMA foreign_key_check").fetchall() == []

    assert migrations.expected_migration_ids()[-1] == (
        "0042_recipe_prepared_output_nutrition"
    )
    assert r1f_snapshot(database) == r1f_before


def test_r1h_exact_replay_is_zero_write_and_does_not_duplicate(database):
    seed_r1h_school2022_main(database)
    before = db_dump(database)

    replay = seed_r1h_school2022_main(database)

    assert replay.identity_food_inserted == 0
    assert replay.identity_food_existing == 4
    assert dict(replay.authority_dispositions) == {
        MEATBALLS_RECIPE_CODE: "EXACT_REPLAY",
        GOULASH_RECIPE_CODE: "EXACT_REPLAY",
    }
    assert set(replay.active_recipe_codes) == {
        MEATBALLS_RECIPE_CODE,
        GOULASH_RECIPE_CODE,
    }
    assert db_dump(database) == before


def test_r1h_replay_does_not_reactivate_deliberately_deactivated_recipe(database):
    seed_r1h_school2022_main(database)
    engine = create_sqlite_engine(database)
    try:
        catalogue = create_food_recipe_catalogue_service(engine)
        meatballs = catalogue.get_by_code(MEATBALLS_RECIPE_CODE)
        catalogue.deactivate(meatballs.id)
    finally:
        engine.dispose()

    replay = seed_r1h_school2022_main(database)

    assert MEATBALLS_RECIPE_CODE not in replay.active_recipe_codes
    assert GOULASH_RECIPE_CODE in replay.active_recipe_codes


def test_r1h_authoritative_planner_loads_new_mains_exclusions_and_week_capacity(
    database,
):
    seed_r1h_school2022_main(database)
    engine = create_sqlite_engine(database)
    try:
        food = create_food_catalogue_service(engine)
        catalogue = create_food_recipe_catalogue_service(engine)
        recipe_nutrition = create_recipe_nutrition_v2_service(engine)
        household_id = uid(1)
        member_id = uid(101)

        class Households:
            def get_household(self, requested_household_id):
                assert requested_household_id == household_id
                return SimpleNamespace(
                    household=SimpleNamespace(id=household_id),
                    members=(SimpleNamespace(id=member_id, active=True),),
                )

        class MealPlans:
            def get_current_member_pattern(
                self, requested_household_id, requested_member_id
            ):
                assert requested_household_id == household_id
                assert requested_member_id == member_id
                return selection(member_id, MealRole.DINNER)

            def get_current_plan(self, requested_household_id, week_start):
                del requested_household_id, week_start
                raise MealPlanNotFoundError()

        class Targets:
            def member_reference_target(
                self, requested_household_id, requested_member_id, *, as_of_date
            ):
                del as_of_date
                assert requested_household_id == household_id
                assert requested_member_id == member_id
                return SimpleNamespace(reference_energy_kcal=Decimal(2000))

        class Pantry:
            def list_items(self, requested_household_id):
                assert requested_household_id == household_id
                return []

        config = PlannerConfig(max_recipe_repetitions=3)
        planner = PlannerService(
            MealPlans(),
            Households(),
            catalogue,
            Targets(),
            Pantry(),
            config,
            recipe_nutrition=recipe_nutrition,
        )
        command = AuthoritativeGenerationRequest(
            household_id,
            date(2026, 9, 28),
            (GenerationMemberConstraints(member_id),),
        )
        request = planner.compose_authoritative_request(command)

        main_codes = (
            CHICKEN_RECIPE_CODE,
            MEATBALLS_RECIPE_CODE,
            GOULASH_RECIPE_CODE,
        )
        version_by_code = {
            code: catalogue.get_current_verified(
                catalogue.get_by_code(code).id
            ).version.id
            for code in main_codes
        }
        request_ids = {candidate.recipe_version_id for candidate in request.candidates}
        assert set(version_by_code.values()) <= request_ids

        result = generate_week(request, config)
        assert isinstance(result, PlannerSuccess)
        selected = Counter(
            event.recipe_version_id
            for event in result.events
            if event.recipe_version_id in set(version_by_code.values())
        )
        assert sum(selected.values()) == 7
        assert set(selected) == set(version_by_code.values())
        assert max(selected.values()) <= 3

        expected_energy = {
            MEATBALLS_RECIPE_CODE: Decimal("153.000000"),
            GOULASH_RECIPE_CODE: Decimal("185.600000"),
        }
        for code, energy in expected_energy.items():
            candidate = next(
                row
                for row in request.candidates
                if row.recipe_version_id == version_by_code[code]
            )
            assert candidate.kcal_per_serving == energy
            assert candidate.exact_energy_ready is True

        exclusions = (
            (MEATBALLS_RECIPE_CODE, BREAD_FOOD_CODE),
            (GOULASH_RECIPE_CODE, TOMATO_PUREE_FOOD_CODE),
        )
        for code, food_code in exclusions:
            excluded_id = food.get_by_code(food_code).id
            excluded_command = AuthoritativeGenerationRequest(
                household_id,
                command.week_start,
                (
                    GenerationMemberConstraints(
                        member_id,
                        excluded_food_ingredient_ids=frozenset({excluded_id}),
                    ),
                ),
            )
            excluded_request = planner.compose_authoritative_request(excluded_command)
            excluded_result = generate_week(excluded_request, config)
            matching = [
                trace
                for trace in excluded_result.trace.candidates
                if trace.recipe_version_id == version_by_code[code]
            ]
            assert matching
            assert any(
                PlannerRejectionCode.MEMBER_EXCLUDED_INGREDIENT in trace.rejection_codes
                for trace in matching
            )
    finally:
        engine.dispose()
