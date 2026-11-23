"""Deterministic FoodIngredient exclusions: persisted member proof and fail-closed week.

This is a synthetic technical integration test, not consumer allergy clearance.
The trusted generation input is not a persisted Household preference contract.
"""

from dataclasses import replace
from datetime import date
from decimal import Decimal

from app.domain.food_recipes import MealTypeCode
from app.domain.meal_patterns import MealRole
from app.domain.meal_plans import MealSourceKind
from app.domain.planner import (
    MemberPlannerConstraints,
    PlannerConfig,
    PlannerFailure,
    PlannerFailureCode,
    PlannerRejectionCode,
    PlannerRequest,
    PlannerSuccess,
    generate_week,
)
from app.persistence.sqlalchemy_core.food_ingredient_tables import (
    food_ingredients_table,
)
from app.persistence.sqlalchemy_core.food_recipe_composition import (
    create_food_recipe_catalogue_service,
)
from app.persistence.sqlalchemy_core.household_composition import (
    create_household_service,
)
from app.persistence.sqlalchemy_core.nutrition_composition import (
    create_nutrition_service,
)
from app.persistence.sqlalchemy_core.pantry_composition import create_pantry_service
from app.persistence.sqlalchemy_core.recipe_nutrition_v2 import (
    create_recipe_nutrition_v2_service,
)
from app.persistence.sqlalchemy_core.shopping_uow import SqlAlchemyShoppingReadScope
from app.services.planner import PlannerService
from app.tests.test_prep_read_only_integration import WEEK, _db_dump
from app.tests.test_planner import candidate, selection, uid
from app.tests.test_r2c_breakfast_grain_diversity import meal_plan_service
from sqlalchemy import select

pytest_plugins = ("app.tests.test_prep_read_only_integration",)


def test_persisted_recipe_participants_respect_exact_member_exclusions(scenario):
    """Actual version ingredient IDs, not names, are checked for each serving."""
    config, engine, _, witness, _ = scenario
    before = _db_dump(config)
    accepted = {
        member.member_id: member.excluded_food_ingredient_ids
        for member in witness.command.members
    }
    assert any(accepted.values()), "The scenario must exercise nonempty exclusions"

    with SqlAlchemyShoppingReadScope(engine) as scope:
        plan = scope.plans.get_current(witness.command.household_id, WEEK)
        assert plan is not None
        assert plan.plan.id == witness.plan_id
        participant_by_event = {}
        for serving in plan.servings:
            participant_by_event.setdefault(serving.event_id, set()).add(
                serving.member_id
            )
        covered = 0
        for event in plan.events:
            if event.source_kind is not MealSourceKind.COOK_RECIPE:
                continue
            detail = scope.recipes.get_detail(event.recipe_version_id)
            assert detail is not None
            food_ids = {part.food_ingredient_id for part in detail.ingredients}
            for member_id in participant_by_event.get(event.id, ()):
                assert not food_ids.intersection(accepted[member_id])
                covered += 1

    assert covered > 0
    assert _db_dump(config) == before


def test_excluding_all_canonical_foods_returns_typed_failure_without_writes(
    scenario,
):
    """The planner must not relax exclusions or persist an empty accepted week."""
    config, engine, _, witness, _ = scenario
    with engine.connect() as connection:
        all_food_ids = frozenset(
            connection.scalars(select(food_ingredients_table.c.id)).all()
        )
    assert len(all_food_ids) > 10

    impossible = replace(
        witness.command,
        members=tuple(
            replace(member, excluded_food_ingredient_ids=all_food_ids)
            for member in witness.command.members
        ),
    )
    planner = PlannerService(
        meal_plan_service(engine),
        create_household_service(engine),
        create_food_recipe_catalogue_service(engine),
        create_nutrition_service(engine),
        create_pantry_service(engine),
        PlannerConfig(version="planner-v0.5", max_recipe_repetitions=3),
        recipe_nutrition=create_recipe_nutrition_v2_service(engine),
    )
    before = _db_dump(config)
    result, persisted = planner.generate_authoritative(impossible)
    assert isinstance(result, PlannerFailure)
    assert result.code is PlannerFailureCode.NO_ELIGIBLE_CANDIDATE
    assert persisted is None
    assert _db_dump(config) == before


def test_exclusion_changes_selection_of_proven_eligible_candidate():
    """Adversarial A/B: favored source is chosen unless its ingredient is excluded."""
    member_id = uid(2)
    forbidden_food_id = uid(50)
    favored = replace(
        candidate(
            11,
            MealTypeCode.MAIN,
            ingredients=frozenset({forbidden_food_id}),
        ),
        exact_energy_ready=True,
    )
    alternative = replace(
        candidate(12, MealTypeCode.MAIN, ingredients=frozenset({uid(51)})),
        exact_energy_ready=True,
    )
    member = MemberPlannerConstraints(
        member_id,
        selection(member_id, (MealRole.DINNER,)),
        Decimal("2000"),
        preferred_recipe_version_ids=frozenset({favored.recipe_version_id}),
    )
    request = PlannerRequest(
        uid(1),
        date(2026, 9, 14),
        (member,),
        (favored, alternative),
    )
    config = PlannerConfig(version="planner-v0.3", max_recipe_repetitions=7)

    baseline = generate_week(request, config)
    assert isinstance(baseline, PlannerSuccess)
    assert len(baseline.events) == 7
    # Baseline must prove that the forbidden candidate is genuinely selectable.
    # Later meals may use the alternative due to ordinary repetition penalties.
    assert baseline.events[0].recipe_version_id == favored.recipe_version_id
    assert any(
        event.recipe_version_id == favored.recipe_version_id
        for event in baseline.events
    )

    excluded = generate_week(
        replace(
            request,
            members=(
                replace(
                    member,
                    excluded_food_ingredient_ids=frozenset({forbidden_food_id}),
                ),
            ),
        ),
        config,
    )
    assert isinstance(excluded, PlannerSuccess)
    assert len(excluded.events) == 7
    assert {event.recipe_version_id for event in excluded.events} == {
        alternative.recipe_version_id
    }
    rejected = [
        trace
        for trace in excluded.trace.candidates
        if trace.recipe_version_id == favored.recipe_version_id
    ]
    assert rejected
    assert all(
        PlannerRejectionCode.MEMBER_EXCLUDED_INGREDIENT in trace.rejection_codes
        and not trace.selected
        for trace in rejected
    )
    assert excluded.trace.fingerprint != baseline.trace.fingerprint
