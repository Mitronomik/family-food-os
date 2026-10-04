import shutil
import sqlite3
from collections import Counter
from datetime import date
from decimal import Decimal

import pytest
from app.db import migrations
from app.db.config import DatabaseConfig
from app.domain.meal_patterns import MealRole
from app.domain.meal_plans import MemberMealPatternSourceKind
from app.domain.planner import PlannerConfig, PlannerRejectionCode, PlannerSuccess
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
from app.persistence.sqlalchemy_core.household_composition import (
    create_household_service,
)
from app.persistence.sqlalchemy_core.household_uow import SqlAlchemyHouseholdReadScope
from app.persistence.sqlalchemy_core.meal_pattern_uow import (
    SqlAlchemyMealPatternCatalogueReadScope,
)
from app.persistence.sqlalchemy_core.meal_plan_uow import (
    SqlAlchemyMealPlanReadScope,
    SqlAlchemyMealPlanUnitOfWork,
)
from app.persistence.sqlalchemy_core.nutrition_composition import (
    create_nutrition_service,
)
from app.persistence.sqlalchemy_core.pantry_composition import create_pantry_service
from app.persistence.sqlalchemy_core.recipe_nutrition_v2 import (
    SqlAlchemyPreparedRecipeNutritionRepository,
    create_recipe_nutrition_v2_service,
)
from app.seed.r3a_school2022_main_batch import (
    RECIPE_CODES as R3A_RECIPE_CODES,
    seed_r3a_school2022_main_batch,
)
from app.seed.r3b_school2022_breakfast_batch import (
    APPLICABILITY_PATH,
    IDENTITY_ONLY_FOOD_CODES,
    IDENTITY_REVIEW_PATH,
    MILK_UNAFFECTED_BREAKFAST_CODES,
    OMELET_CODES,
    OMELET_NON_SELECTED_BRANCH,
    OMELET_SELECTED_BRANCH,
    PACKAGE,
    PROCESS_BINDING_PATH,
    PUBLICATION_SPECS_PATH,
    RECIPE_CODES,
    SELECTION_PATH,
    SOURCE_VERIFICATION_PATH,
    SUMMARY_PATH,
    _load_contract,
    activate_r3b_school2022_breakfast_batch,
    publish_r3b_school2022_breakfast_batch,
    seed_r3b_school2022_breakfast_batch,
)
from app.services.meal_plans import MealPlanService
from app.services.planner import (
    AuthoritativeGenerationRequest,
    GenerationMemberConstraints,
    PlannerService,
)
from app.services.prepared_recipe_activation import PreparedRecipeActivationError

WEEK_START = date(2026, 10, 5)
MILK_FOOD_CODE = "MILK_2_5"


@pytest.fixture(scope="session")
def baseline(tmp_path_factory):
    config = DatabaseConfig(path=tmp_path_factory.mktemp("r3b-base") / "base.sqlite")
    seed_r3a_school2022_main_batch(config)
    return config


@pytest.fixture
def database(baseline, tmp_path):
    config = DatabaseConfig(path=tmp_path / "r3b.sqlite")
    shutil.copyfile(baseline.path, config.path)
    return config


def db_dump(config: DatabaseConfig) -> str:
    with sqlite3.connect(config.path) as db:
        return "\n".join(db.iterdump())


def r3b_recipe_states(config: DatabaseConfig) -> dict[str, int]:
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


def r3b_counts(config: DatabaseConfig) -> dict[str, int]:
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


def meal_plan_service(engine) -> MealPlanService:
    return MealPlanService(
        write_scope_factory=lambda: SqlAlchemyMealPlanUnitOfWork(engine),
        read_scope_factory=lambda: SqlAlchemyMealPlanReadScope(engine),
        household_read_scope_factory=lambda: SqlAlchemyHouseholdReadScope(engine),
        pattern_read_scope_factory=lambda: SqlAlchemyMealPatternCatalogueReadScope(
            engine
        ),
    )


def production_planner(engine):
    meal_plans = meal_plan_service(engine)
    households = create_household_service(engine)
    catalogue = create_food_recipe_catalogue_service(engine)
    nutrition = create_nutrition_service(engine)
    pantry = create_pantry_service(engine)
    recipe_nutrition = create_recipe_nutrition_v2_service(engine)
    planner = PlannerService(
        meal_plans,
        households,
        catalogue,
        nutrition,
        pantry,
        PlannerConfig(version="planner-v0.4", max_recipe_repetitions=3),
        recipe_nutrition=recipe_nutrition,
    )
    return planner, meal_plans, households, catalogue


def create_breakfast_household(households, meal_plans):
    household = households.create_household(
        name="R3-B milk exclusion proof",
        timezone_name="Europe/Moscow",
        city="Санкт-Петербург",
    )
    member = households.add_household_member(
        household.id,
        name="Анна",
        activity_level="active",
        goal="maintain",
        birth_date=date(1990, 5, 20),
        sex="female",
        height_cm=Decimal(168),
        weight_kg=Decimal(62),
    )
    selection = meal_plans.accept_member_pattern(
        household_id=household.id,
        member_id=member.id,
        source_kind=MemberMealPatternSourceKind.CUSTOM,
        schedule={weekday: (MealRole.BREAKFAST,) for weekday in range(1, 8)},
        energy_shares={weekday: (Decimal("0.30"),) for weekday in range(1, 8)},
    )
    return household, member, selection


def test_r3b_fresh_publication_and_batch_activation(database):
    result = seed_r3b_school2022_breakfast_batch(database)

    assert result.publication.identity_food_inserted == 3
    assert result.publication.identity_food_existing == 0
    assert result.activation_changed is True
    assert result.active_recipe_codes == RECIPE_CODES
    assert (
        tuple(code for code, _ in result.publication.recipe_version_ids) == RECIPE_CODES
    )
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
            assert detail.version.meal_type_code.value == "breakfast"
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

    assert (
        migrations.expected_migration_ids()[-1]
        == "0042_recipe_prepared_output_nutrition"
    )


def test_r3b_publication_phase_keeps_all_recipes_inactive(database):
    result = publish_r3b_school2022_breakfast_batch(database)

    assert tuple(code for code, _ in result.recipe_version_ids) == RECIPE_CODES
    assert r3b_recipe_states(database) == {code: 0 for code in sorted(RECIPE_CODES)}

    changed = activate_r3b_school2022_breakfast_batch(database)
    assert changed is True
    assert r3b_recipe_states(database) == {code: 1 for code in sorted(RECIPE_CODES)}


def test_r3b_exact_full_replay_is_zero_write(database):
    seed_r3b_school2022_breakfast_batch(database)
    before = db_dump(database)

    replay = seed_r3b_school2022_breakfast_batch(database)

    assert replay.publication.identity_food_inserted == 0
    assert replay.publication.identity_food_existing == 3
    assert replay.activation_changed is False
    assert all(
        disposition == "EXACT_REPLAY"
        for _code, disposition in replay.publication.authority_dispositions
    )
    assert db_dump(database) == before


def test_r3b_preserves_deliberate_deactivation_in_prior_r3a_batch(database):
    engine = create_sqlite_engine(database)
    try:
        catalogue = create_food_recipe_catalogue_service(engine)
        prior = catalogue.get_by_code(R3A_RECIPE_CODES[0])
        catalogue.deactivate(prior.id)
        assert catalogue.get_by_code(R3A_RECIPE_CODES[0]).is_active is False
    finally:
        engine.dispose()

    result = seed_r3b_school2022_breakfast_batch(database)

    assert result.active_recipe_codes == RECIPE_CODES
    engine = create_sqlite_engine(database)
    try:
        catalogue = create_food_recipe_catalogue_service(engine)
        assert catalogue.get_by_code(R3A_RECIPE_CODES[0]).is_active is False
    finally:
        engine.dispose()


def test_r3b_mixed_activation_state_fails_closed_and_preserves_deactivation(database):
    seed_r3b_school2022_breakfast_batch(database)
    engine = create_sqlite_engine(database)
    try:
        catalogue = create_food_recipe_catalogue_service(engine)
        recipe = catalogue.get_by_code(RECIPE_CODES[0])
        catalogue.deactivate(recipe.id)
    finally:
        engine.dispose()
    before = db_dump(database)

    with pytest.raises(PreparedRecipeActivationError, match="mixed active/inactive"):
        seed_r3b_school2022_breakfast_batch(database)

    assert db_dump(database) == before
    states = r3b_recipe_states(database)
    assert states[RECIPE_CODES[0]] == 0
    assert sum(states.values()) == 9


def test_r3b_partial_publication_failure_resumes_missing_recipes(database, monkeypatch):
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
            publish_r3b_school2022_breakfast_batch(database)

    assert r3b_counts(database) == {"recipes": 3, "authorities": 3, "values": 3}
    assert set(r3b_recipe_states(database).values()) == {0}

    resumed = seed_r3b_school2022_breakfast_batch(database)
    dispositions = dict(resumed.publication.authority_dispositions)
    assert tuple(dispositions[code] for code in RECIPE_CODES[:3]) == (
        "EXACT_REPLAY",
        "EXACT_REPLAY",
        "EXACT_REPLAY",
    )
    assert all(dispositions[code] == "FRESH" for code in RECIPE_CODES[3:])
    assert resumed.active_recipe_codes == RECIPE_CODES


@pytest.mark.parametrize("failure_point", ("version", "values", "authority"))
def test_r3b_first_recipe_publication_failure_rolls_back_recipe_atomically(
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
            publish_r3b_school2022_breakfast_batch(database)

    assert r3b_counts(database) == {"recipes": 0, "authorities": 0, "values": 0}
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


def test_r3b_batch_activation_failure_rolls_back_every_staged_write(
    database,
    monkeypatch,
):
    publish_r3b_school2022_breakfast_batch(database)
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
        activate_r3b_school2022_breakfast_batch(database)

    assert r3b_recipe_states(database) == {code: 0 for code in sorted(RECIPE_CODES)}


@pytest.mark.parametrize(
    ("artifact_name", "old", "new"),
    (
        (SELECTION_PATH.name, '"153.5"', '"153.6"'),
        (IDENTITY_REVIEW_PATH.name, '"CORN_GROATS"', '"CORN_FLOUR"'),
        (APPLICABILITY_PATH.name, '"REVIEWED_PASS"', '"BLOCKED"'),
        (
            PROCESS_BINDING_PATH.name,
            '"PASS_EXACT_TOTAL_INTERNAL_SPLIT_UNKNOWN"',
            '"ASSUMED_WATER_SPLIT"',
        ),
        (PUBLICATION_SPECS_PATH.name, '"274.9"', '"275.0"'),
        (
            SOURCE_VERIFICATION_PATH.name,
            '"source_pdf_size_bytes": 4102547',
            '"source_pdf_size_bytes": 4102548',
        ),
        (SUMMARY_PATH.name, '"selected_count": 10', '"selected_count": 9'),
    ),
)
def test_r3b_hash_pinned_contract_rejects_tampered_artifact(
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

    with pytest.raises(ValueError, match="R3-B"):
        _load_contract(package)


def test_r3b_russian_steps_and_omelet_source_branch_are_published_verbatim(database):
    publish_r3b_school2022_breakfast_batch(database)
    engine = create_sqlite_engine(database)
    try:
        catalogue = create_food_recipe_catalogue_service(engine)

        forbidden_consumer_terms = (
            "authority",
            "retained-water",
            "yield inference",
            "quantified RecipeIngredient",
            "exact WATER",
        )
        for code in RECIPE_CODES:
            detail = catalogue.get_latest_verified(catalogue.get_by_code(code).id)
            assert all(
                not any(term in step.instruction for term in forbidden_consumer_terms)
                for step in detail.steps
            )

        for code in OMELET_CODES:
            detail = catalogue.get_latest_verified(catalogue.get_by_code(code).id)
            instructions = tuple(step.instruction for step in detail.steps)
            assert any("180–200 °C 8–10 минут" in step for step in instructions)
            assert not any("25–30" in step and "пар" in step for step in instructions)

        _, _, applicability, process, specs, _, _ = _load_contract()
        process_by_code = {row["canonical_code"]: row for row in process["selected"]}
        applicability_by_code = {
            row["canonical_code"]: row for row in applicability["candidates"]
        }
        for code in OMELET_CODES:
            assert (
                specs["recipes"][code]["source_branch_selection"][
                    "selected_process_branch"
                ]
                == OMELET_SELECTED_BRANCH
            )
            assert (
                specs["recipes"][code]["source_branch_selection"][
                    "non_selected_source_branches"
                ][0]["code"]
                == OMELET_NON_SELECTED_BRANCH
            )
            assert (
                process_by_code[code]["selected_process_branch"]
                == OMELET_SELECTED_BRANCH
            )
            assert (
                process_by_code[code]["non_selected_source_branch"]["code"]
                == OMELET_NON_SELECTED_BRANCH
            )
            assert (
                applicability_by_code[code]["selected_process_branch"]["code"]
                == OMELET_SELECTED_BRANCH
            )
    finally:
        engine.dispose()


def test_r3b_hard_milk_exclusion_rejects_all_batch_and_preserves_capacity_nine(
    database,
):
    seed_r3b_school2022_breakfast_batch(database)
    engine = create_sqlite_engine(database)
    try:
        planner, meal_plans, households, catalogue = production_planner(engine)
        food = create_food_catalogue_service(engine)
        household, member, selection = create_breakfast_household(
            households,
            meal_plans,
        )
        milk_id = food.get_by_code(MILK_FOOD_CODE).id
        request = AuthoritativeGenerationRequest(
            household.id,
            WEEK_START,
            (
                GenerationMemberConstraints(
                    member.id,
                    excluded_food_ingredient_ids=frozenset({milk_id}),
                ),
            ),
        )

        result, detail = planner.generate_authoritative(request)

        assert isinstance(result, PlannerSuccess)
        assert detail is not None
        assert detail.member_selections[0].selection_id == selection.selection.id

        relevant_codes = set(RECIPE_CODES) | set(MILK_UNAFFECTED_BREAKFAST_CODES)
        admissions = {
            row.recipe_version_id: row
            for row in planner.compose_candidate_admission()
            if row.canonical_code in relevant_codes
        }
        selected = Counter(
            admissions[event.recipe_version_id].canonical_code
            for event in result.events
        )

        assert set(selected) == set(MILK_UNAFFECTED_BREAKFAST_CODES)
        assert sum(selected.values()) == 7
        assert max(selected.values()) <= 3

        persisted = meal_plans.get_current_plan(household.id, WEEK_START)
        assert persisted.plan.id == detail.plan.id
        assert len(persisted.events) == 7
        assert len(persisted.servings) == 7

        versions = {
            code: catalogue.get_current_verified(
                catalogue.get_by_code(code).id
            ).version.id
            for code in relevant_codes
        }
        for code in RECIPE_CODES:
            traces = [
                row
                for row in result.trace.candidates
                if row.recipe_version_id == versions[code]
            ]
            assert traces
            assert any(
                PlannerRejectionCode.MEMBER_EXCLUDED_INGREDIENT in row.rejection_codes
                for row in traces
            )

        for code in MILK_UNAFFECTED_BREAKFAST_CODES:
            traces = [
                row
                for row in result.trace.candidates
                if row.recipe_version_id == versions[code]
            ]
            assert traces
            assert all(
                PlannerRejectionCode.MEMBER_EXCLUDED_INGREDIENT
                not in row.rejection_codes
                for row in traces
            )

        r3b_version_ids = {versions[code] for code in RECIPE_CODES}
        assert all(
            event.recipe_version_id not in r3b_version_ids for event in result.events
        )
    finally:
        engine.dispose()
