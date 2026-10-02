import json
import shutil
from collections import Counter
from datetime import date, timedelta
from decimal import Decimal

import pytest
from app.db import migrations
from app.db.config import REPOSITORY_ROOT, DatabaseConfig
from app.domain.meal_patterns import MealRole
from app.domain.meal_plans import MealSourceKind, MemberMealPatternSourceKind
from app.domain.planner import (
    FixedPlannerEvent,
    PlannerConfig,
    PlannerFailure,
    PlannerFailureCode,
    PlannerRejectionCode,
    PlannerSuccess,
)
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
from app.persistence.sqlalchemy_core.food_ingredient_composition import (
    create_food_catalogue_service,
)
from app.persistence.sqlalchemy_core.food_recipe_composition import (
    create_food_recipe_catalogue_service,
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
    create_recipe_nutrition_v2_service,
)
from app.seed.r1f_prepared_output import CHICKEN_RECIPE_CODE, EGG_RECIPE_CODE
from app.seed.r1h_school2022_main import (
    BREAD_FOOD_CODE,
    GOULASH_RECIPE_CODE,
    MEATBALLS_RECIPE_CODE,
    seed_r1h_school2022_main,
)
from app.services.meal_plans import MealPlanNotFoundError, MealPlanService
from app.services.planner import (
    AuthoritativeGenerationRequest,
    GenerationMemberConstraints,
    PlannerService,
)

WEEK_START = date(2026, 10, 5)
PACKAGE = REPOSITORY_ROOT / "data/curation/r1c-production-planner-proof"
SUMMARY_PATH = PACKAGE / "summary.json"
R1G_DISPOSITIONS_PATH = (
    REPOSITORY_ROOT
    / "data/curation/r1g-catalogue-capacity-expansion/candidate-dispositions.json"
)
ACTIVE_CODES = frozenset(
    {
        EGG_RECIPE_CODE,
        CHICKEN_RECIPE_CODE,
        MEATBALLS_RECIPE_CODE,
        GOULASH_RECIPE_CODE,
    }
)
MAIN_CODES = frozenset(
    {
        CHICKEN_RECIPE_CODE,
        MEATBALLS_RECIPE_CODE,
        GOULASH_RECIPE_CODE,
    }
)
BLOCKED_SOURCE_CODES = frozenset(
    {
        "USSR82-1081",
        "USSR82-467",
        "USSR82-492",
        "USSR82-364",
        "USSR82-208",
    }
)


@pytest.fixture(scope="module")
def baseline(tmp_path_factory):
    config = DatabaseConfig(
        path=tmp_path_factory.mktemp("r1c-production-proof") / "baseline.sqlite"
    )
    seed_r1h_school2022_main(config)
    return config


@pytest.fixture
def database(baseline, tmp_path):
    config = DatabaseConfig(path=tmp_path / "r1c.sqlite")
    shutil.copyfile(baseline.path, config.path)
    return config


def _meal_plan_service(engine) -> MealPlanService:
    return MealPlanService(
        write_scope_factory=lambda: SqlAlchemyMealPlanUnitOfWork(engine),
        read_scope_factory=lambda: SqlAlchemyMealPlanReadScope(engine),
        household_read_scope_factory=lambda: SqlAlchemyHouseholdReadScope(engine),
        pattern_read_scope_factory=lambda: SqlAlchemyMealPatternCatalogueReadScope(
            engine
        ),
    )


def _planner(engine):
    meal_plans = _meal_plan_service(engine)
    households = create_household_service(engine)
    recipes = create_food_recipe_catalogue_service(engine)
    nutrition = create_nutrition_service(engine)
    pantry = create_pantry_service(engine)
    recipe_nutrition = create_recipe_nutrition_v2_service(engine)
    planner = PlannerService(
        meal_plans,
        households,
        recipes,
        nutrition,
        pantry,
        PlannerConfig(version="planner-v0.4", max_recipe_repetitions=3),
        recipe_nutrition=recipe_nutrition,
    )
    return planner, meal_plans, households, recipes, nutrition


def _add_member_with_pattern(
    *,
    households,
    meal_plans,
    household_id,
    member_name: str,
    roles_and_shares: tuple[tuple[MealRole, Decimal], ...],
):
    member = households.add_household_member(
        household_id,
        name=member_name,
        activity_level="active",
        goal="maintain",
        birth_date=date(1990, 5, 20),
        sex="female",
        height_cm=Decimal(168),
        weight_kg=Decimal(62),
    )
    roles = tuple(role for role, _ in roles_and_shares)
    shares = tuple(share for _, share in roles_and_shares)
    selection = meal_plans.accept_member_pattern(
        household_id=household_id,
        member_id=member.id,
        source_kind=MemberMealPatternSourceKind.CUSTOM,
        schedule={weekday: roles for weekday in range(1, 8)},
        energy_shares={weekday: shares for weekday in range(1, 8)},
    )
    return member, selection


def _create_member_with_pattern(
    *,
    households,
    meal_plans,
    name: str,
    roles_and_shares: tuple[tuple[MealRole, Decimal], ...],
):
    household = households.create_household(
        name=name,
        timezone_name="Europe/Moscow",
        city="Санкт-Петербург",
    )
    member, selection = _add_member_with_pattern(
        households=households,
        meal_plans=meal_plans,
        household_id=household.id,
        member_name="Анна",
        roles_and_shares=roles_and_shares,
    )
    return household, member, selection


def _semantic_plan(detail):
    servings_by_event = {
        event.id: tuple(
            sorted(
                (
                    str(serving.member_id),
                    format(serving.portion_servings, "f"),
                )
                for serving in detail.servings
                if serving.event_id == event.id
            )
        )
        for event in detail.events
    }
    return tuple(
        (
            event.local_date.isoformat(),
            event.position,
            event.role.value,
            event.source_kind.value,
            None if event.recipe_version_id is None else str(event.recipe_version_id),
            event.source_reference,
            servings_by_event[event.id],
        )
        for event in detail.events
    )


def _eligible_admissions(planner):
    return tuple(
        row
        for row in planner.compose_candidate_admission()
        if row.is_active and row.eligible and row.exact_energy_ready
    )


def test_r1c_catalogue_metrics_match_durable_receipt(database):
    engine = create_sqlite_engine(database)
    try:
        planner, _, _, _, _ = _planner(engine)
        eligible = _eligible_admissions(planner)
    finally:
        engine.dispose()

    by_code = {row.canonical_code: row for row in eligible}
    assert set(by_code) == ACTIVE_CODES
    assert sum(row.meal_type_code == "breakfast" for row in eligible) == 1
    assert sum(row.meal_type_code == "main" for row in eligible) == 3

    summary = json.loads(SUMMARY_PATH.read_text())
    assert summary["candidate_metrics"] == {
        "selected_r1_recipes_accepted": 4,
        "selected_r1_recipes_blocked": 5,
        "active_planner_eligible_recipe_versions": 4,
        "exact_energy_ready_active_recipe_versions": 4,
        "breakfast_candidate_count": 1,
        "main_candidate_count": 3,
    }
    assert frozenset(summary["remaining_authority_blockers"]) == BLOCKED_SOURCE_CODES
    assert summary["successful_persisted_complete_weeks"] == 2
    assert any(
        row["code"] == "DINNER_ONLY_MULTI_MEMBER_EXCLUSION_SHAREDNESS"
        and row["expected_outcome"] == "SUCCESS_PERSISTED"
        for row in summary["materially_different_repository_backed_patterns"]
    )

    dispositions = json.loads(R1G_DISPOSITIONS_PATH.read_text())
    assert all(
        dispositions["candidates"][code]["current_gate_disposition"].startswith(
            "BLOCKED_"
        )
        for code in ("USSR82-1081", "USSR82-467", "USSR82-492")
    )
    main_rows = {
        row["source_recipe_id"]: row
        for row in dispositions["main_capacity"][
            "accepted_r1e_explicit_main_candidates"
        ]
    }
    assert main_rows["USSR82-364"]["current_blockers"]
    assert main_rows["USSR82-208"]["current_blockers"]

    assert migrations.expected_migration_ids()[-1] == (
        "0042_recipe_prepared_output_nutrition"
    )


def test_r1c_persists_complete_week_and_replays_semantically(database):
    engine = create_sqlite_engine(database)
    try:
        planner, meal_plans, households, _, nutrition = _planner(engine)
        household, member, selection = _create_member_with_pattern(
            households=households,
            meal_plans=meal_plans,
            name="R1-C success",
            roles_and_shares=((MealRole.DINNER, Decimal("0.25")),),
        )
        command = AuthoritativeGenerationRequest(
            household.id,
            WEEK_START,
            (GenerationMemberConstraints(member.id),),
        )

        first, first_detail = planner.generate_authoritative(command)
        assert isinstance(first, PlannerSuccess)
        assert first_detail is not None
        assert first.trace.config_version == "planner-v0.4"
        assert first.trace.compatibility_version == "meal-role-recipe-v2"
        assert len(first.events) == 7
        assert len(first_detail.events) == 7
        assert len(first_detail.servings) == 7
        assert first_detail.plan.config_version == "planner-v0.4"
        assert first_detail.member_selections[0].selection_id == selection.selection.id
        assert all(
            event.source_kind is MealSourceKind.COOK_RECIPE
            for event in first_detail.events
        )
        assert all(serving.portion_servings > 0 for serving in first_detail.servings)

        persisted = meal_plans.get_current_plan(household.id, WEEK_START)
        assert persisted.plan.id == first_detail.plan.id
        assert _semantic_plan(persisted) == _semantic_plan(first_detail)

        eligible = _eligible_admissions(planner)
        version_to_code = {
            row.recipe_version_id: row.canonical_code
            for row in eligible
            if row.recipe_version_id is not None
        }
        selected = Counter(
            version_to_code[event.recipe_version_id] for event in first.events
        )
        assert set(selected) == MAIN_CODES
        assert sum(selected.values()) == 7
        assert max(selected.values()) <= 3

        target = nutrition.member_reference_target(
            household.id, member.id, as_of_date=WEEK_START
        ).reference_energy_kcal
        expected_dinner_kcal = (target * Decimal("0.25")).quantize(Decimal("0.000001"))
        assert len(first.trace.allocations) == 7
        for allocation in first.trace.allocations:
            assert allocation.energy_share == Decimal("0.250000")
            assert allocation.allocated_kcal == expected_dinner_kcal
            assert allocation.recipe_kcal_per_base_serving is not None
            assert allocation.recipe_kcal_per_base_serving > 0
            assert allocation.portion_servings > 0

        repeated, repeated_detail = planner.generate_authoritative(command)
        assert isinstance(repeated, PlannerSuccess)
        assert repeated_detail is not None
        assert repeated.events == first.events
        assert repeated.trace.fingerprint == first.trace.fingerprint
        assert _semantic_plan(repeated_detail) == _semantic_plan(first_detail)
        assert repeated_detail.plan.revision_number == 2
        assert repeated_detail.plan.supersedes_plan_id == first_detail.plan.id

        current = meal_plans.get_current_plan(household.id, WEEK_START)
        assert current.plan.id == repeated_detail.plan.id
        assert current.plan.revision_number == 2
    finally:
        engine.dispose()


def test_r1c_materially_different_breakfast_dinner_pattern_fails_without_partial_plan(
    database,
):
    engine = create_sqlite_engine(database)
    try:
        planner, meal_plans, households, _, _ = _planner(engine)
        household, member, _ = _create_member_with_pattern(
            households=households,
            meal_plans=meal_plans,
            name="R1-C bounded infeasible",
            roles_and_shares=(
                (MealRole.BREAKFAST, Decimal("0.30")),
                (MealRole.DINNER, Decimal("0.25")),
            ),
        )
        command = AuthoritativeGenerationRequest(
            household.id,
            WEEK_START,
            (GenerationMemberConstraints(member.id),),
        )

        result, detail = planner.generate_authoritative(command)
        assert isinstance(result, PlannerFailure)
        assert result.code is PlannerFailureCode.NO_ELIGIBLE_CANDIDATE
        assert detail is None

        egg_version = next(
            row.recipe_version_id
            for row in _eligible_admissions(planner)
            if row.canonical_code == EGG_RECIPE_CODE
        )
        egg_traces = [
            row
            for row in result.trace.candidates
            if row.recipe_version_id == egg_version
        ]
        assert egg_traces
        assert any(
            PlannerRejectionCode.MAX_REPETITIONS in row.rejection_codes
            for row in egg_traces
        )

        with pytest.raises(MealPlanNotFoundError):
            meal_plans.get_current_plan(household.id, WEEK_START)
    finally:
        engine.dispose()


def test_r1c_hard_food_exclusion_removes_candidate_and_persists_nothing(database):
    engine = create_sqlite_engine(database)
    try:
        planner, meal_plans, households, recipes, _ = _planner(engine)
        food = create_food_catalogue_service(engine)
        household, member, _ = _create_member_with_pattern(
            households=households,
            meal_plans=meal_plans,
            name="R1-C exclusion",
            roles_and_shares=((MealRole.DINNER, Decimal("0.25")),),
        )
        bread_id = food.get_by_code(BREAD_FOOD_CODE).id
        command = AuthoritativeGenerationRequest(
            household.id,
            WEEK_START + timedelta(weeks=2),
            (
                GenerationMemberConstraints(
                    member.id,
                    excluded_food_ingredient_ids=frozenset({bread_id}),
                ),
            ),
        )

        result, detail = planner.generate_authoritative(command)
        assert isinstance(result, PlannerFailure)
        assert result.code is PlannerFailureCode.NO_ELIGIBLE_CANDIDATE
        assert detail is None

        versions = {
            code: recipes.get_current_verified(recipes.get_by_code(code).id).version.id
            for code in MAIN_CODES
        }
        meatball_traces = [
            row
            for row in result.trace.candidates
            if row.recipe_version_id == versions[MEATBALLS_RECIPE_CODE]
        ]
        assert meatball_traces
        assert any(
            PlannerRejectionCode.MEMBER_EXCLUDED_INGREDIENT in row.rejection_codes
            for row in meatball_traces
        )
        for code in (CHICKEN_RECIPE_CODE, GOULASH_RECIPE_CODE):
            unaffected = [
                row
                for row in result.trace.candidates
                if row.recipe_version_id == versions[code]
            ]
            assert unaffected
            assert all(
                PlannerRejectionCode.MEMBER_EXCLUDED_INGREDIENT
                not in row.rejection_codes
                for row in unaffected
            )

        with pytest.raises(MealPlanNotFoundError):
            meal_plans.get_current_plan(household.id, command.week_start)
    finally:
        engine.dispose()


def test_r1c_multi_member_exclusion_preserves_other_member_and_sharedness(database):
    engine = create_sqlite_engine(database)
    try:
        planner, meal_plans, households, recipes, _ = _planner(engine)
        food = create_food_catalogue_service(engine)
        household = households.create_household(
            name="R1-C shared exclusion",
            timezone_name="Europe/Moscow",
            city="Санкт-Петербург",
        )
        roles_and_shares = ((MealRole.DINNER, Decimal("0.25")),)
        excluded_member, _ = _add_member_with_pattern(
            households=households,
            meal_plans=meal_plans,
            household_id=household.id,
            member_name="Анна",
            roles_and_shares=roles_and_shares,
        )
        unaffected_member, _ = _add_member_with_pattern(
            households=households,
            meal_plans=meal_plans,
            household_id=household.id,
            member_name="Мария",
            roles_and_shares=roles_and_shares,
        )

        bread_id = food.get_by_code(BREAD_FOOD_CODE).id
        week_start = WEEK_START + timedelta(weeks=3)
        fixed_out = FixedPlannerEvent(
            week_start + timedelta(days=6),
            MealRole.DINNER,
            1,
            MealSourceKind.EAT_OUT,
            "решение пользователя",
            frozenset({excluded_member.id}),
            ((excluded_member.id, Decimal(1)),),
        )
        command = AuthoritativeGenerationRequest(
            household.id,
            week_start,
            (
                GenerationMemberConstraints(
                    excluded_member.id,
                    excluded_food_ingredient_ids=frozenset({bread_id}),
                ),
                GenerationMemberConstraints(unaffected_member.id),
            ),
            fixed_events=(fixed_out,),
        )

        result, detail = planner.generate_authoritative(command)
        assert isinstance(result, PlannerSuccess)
        assert detail is not None

        versions = {
            code: recipes.get_current_verified(recipes.get_by_code(code).id).version.id
            for code in MAIN_CODES
        }
        meatball_version = versions[MEATBALLS_RECIPE_CODE]

        cooked = tuple(
            event
            for event in result.events
            if event.source_kind is MealSourceKind.COOK_RECIPE
        )
        shared = tuple(
            event
            for event in cooked
            if set(event.participant_member_ids)
            == {excluded_member.id, unaffected_member.id}
        )
        meatball_events = tuple(
            event for event in cooked if event.recipe_version_id == meatball_version
        )

        assert len(cooked) == 7
        assert len(shared) == 6
        assert all(event.recipe_version_id != meatball_version for event in shared)
        assert meatball_events
        assert all(
            excluded_member.id not in event.participant_member_ids
            for event in meatball_events
        )
        assert all(
            unaffected_member.id in event.participant_member_ids
            for event in meatball_events
        )
        assert any(
            event.participant_member_ids == (unaffected_member.id,)
            for event in meatball_events
        )

        fixed_events = tuple(
            event
            for event in result.events
            if event.source_kind is MealSourceKind.EAT_OUT
        )
        assert len(fixed_events) == 1
        assert fixed_events[0].participant_member_ids == (excluded_member.id,)

        meatball_traces = tuple(
            row
            for row in result.trace.candidates
            if row.recipe_version_id == meatball_version
        )
        assert meatball_traces
        assert any(
            PlannerRejectionCode.MEMBER_EXCLUDED_INGREDIENT in row.rejection_codes
            for row in meatball_traces
        )

        persisted = meal_plans.get_current_plan(household.id, week_start)
        assert persisted.plan.id == detail.plan.id
        assert len(persisted.member_selections) == 2
        assert _semantic_plan(persisted) == _semantic_plan(detail)
        assert any(
            len(
                {
                    serving.member_id
                    for serving in persisted.servings
                    if serving.event_id == event.id
                }
            )
            == 2
            for event in persisted.events
            if event.source_kind is MealSourceKind.COOK_RECIPE
        )
    finally:
        engine.dispose()
