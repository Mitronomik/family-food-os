"""PR10-A1 read-only vertical proof, using actual persisted synthetic SQLite facts.

The generation-context witness is deliberately held by this test and matched
against PlannerTrace + readback. No Household table currently persists the
member semantic ordinal or exclusions; this is NOT a production proof of their
availability after a fresh process restart without that trusted witness.
"""

from __future__ import annotations

import json
import os
import shutil
import sqlite3
from collections import defaultdict
from dataclasses import dataclass, replace
from datetime import UTC, date, datetime, timedelta
from decimal import ROUND_CEILING, ROUND_HALF_EVEN, Decimal, localcontext
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from app.db.config import DatabaseConfig
from app.domain.meal_patterns import MealRole
from app.domain.meal_plans import MealPlanDetail, MealSourceKind
from app.domain.pantry import PantryLocation
from app.domain.planner import FixedPlannerEvent, PlannerConfig, PlannerSuccess
from app.domain.prep_diagnostic import (
    PrepDiagnosticError,
    PrepDiagnosticReason,
    PrepDiagnosticStatus,
    calculate_prep_diagnostic,
)
from app.domain.shopping_calculation import ShoppingPriceStatus, calculate_shopping
from app.domain.units import UnitCode
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
from app.persistence.sqlalchemy_core.nutrition_composition import (
    create_nutrition_service,
)
from app.persistence.sqlalchemy_core.pantry_composition import create_pantry_service
from app.persistence.sqlalchemy_core.pantry_uow import (
    SqlAlchemyPantryReadScope,
    SqlAlchemyPantryUnitOfWork,
)
from app.persistence.sqlalchemy_core.recipe_nutrition_v2 import (
    create_recipe_nutrition_v2_service,
)
from app.persistence.sqlalchemy_core.shopping_uow import SqlAlchemyShoppingReadScope
from app.seed.r2c_breakfast_grain_diversity import seed_r2c_breakfast_grain_diversity
from app.services.pantry import PantryService
from app.services.planner import (
    AuthoritativeGenerationRequest,
    GenerationMemberConstraints,
    PlannerService,
)
from app.tests.test_r2c_breakfast_grain_diversity import meal_plan_service

WEEK = date(2026, 11, 2)
AS_OF = datetime(2026, 11, 3, 9, tzinfo=UTC)
POLICY = "pr10-a1-ro-integration-test-context-v1"


class ProofBlocked(ValueError):
    """Missing/stale verification is not a success and cannot be defaulted."""


@dataclass(frozen=True)
class CapturedGenerationContext:
    """Test-only trusted input, captured *before* Planner persistence.

    Ordinals 1/2 refer to the explicitly assigned fixture member slots, not
    UUID sort, names, gender, or a reverse-engineered persisted MealPlan.
    """

    command: AuthoritativeGenerationRequest
    semantic_slots: tuple[UUID, ...]
    result: PlannerSuccess
    plan_id: UUID
    plan_revision: int


@pytest.fixture(scope="module")
def trusted_catalogue(tmp_path_factory):
    config = DatabaseConfig(
        path=tmp_path_factory.mktemp("prep-ro-source") / "r2c.sqlite"
    )
    seed_r2c_breakfast_grain_diversity(config)
    return config


@pytest.fixture
def scenario(trusted_catalogue, tmp_path):
    config = DatabaseConfig(path=tmp_path / "prep-read-only-proof.sqlite")
    shutil.copyfile(trusted_catalogue.path, config.path)
    engine = create_sqlite_engine(config)
    try:
        households = create_household_service(engine)
        meal_plans = meal_plan_service(engine)
        recipes = create_food_recipe_catalogue_service(engine)
        nutrition = create_nutrition_service(engine)
        pantry = create_pantry_service(engine)
        recipe_nutrition = create_recipe_nutrition_v2_service(engine)
        food = create_food_catalogue_service(engine)
        planner = PlannerService(
            meal_plans,
            households,
            recipes,
            nutrition,
            pantry,
            PlannerConfig(version="planner-v0.5", max_recipe_repetitions=3),
            recipe_nutrition=recipe_nutrition,
        )

        household = households.create_household(
            name="Synthetic PR10-A1 integration",
            timezone_name="Europe/Moscow",
            city="Санкт-Петербург",
        )
        # Explicit *pre-generation* semantic slots — not recovered from UUID.
        member_1 = households.add_household_member(
            household.id,
            name="Участник 1",
            activity_level="active",
            goal="maintain",
            birth_date=date(1988, 4, 6),
            sex="female",
            height_cm=Decimal(164),
            weight_kg=Decimal(58),
        )
        member_2 = households.add_household_member(
            household.id,
            name="Участник 2",
            activity_level="active",
            goal="maintain",
            birth_date=date(1993, 5, 15),
            sex="male",
            height_cm=Decimal(190),
            weight_kg=Decimal(95),
        )
        semantic_slots = (member_1.id, member_2.id)
        for member in (member_1, member_2):
            meal_plans.accept_member_pattern(
                household_id=household.id,
                member_id=member.id,
                source_kind="CUSTOM",
                schedule={weekday: (MealRole.BREAKFAST,) for weekday in range(1, 8)},
                energy_shares={weekday: (Decimal("0.30"),) for weekday in range(1, 8)},
            )

        # Explicit nonempty exclusion comes from *this* trusted generation
        # input and PlannerTrace. It is NOT reconstructed from HouseholdMember.
        beef = food.get_by_code("BEEF_CATEGORY_1_RAW")
        assert beef is not None
        command = AuthoritativeGenerationRequest(
            household.id,
            WEEK,
            (
                GenerationMemberConstraints(member_1.id),
                GenerationMemberConstraints(
                    member_2.id, excluded_food_ingredient_ids=frozenset({beef.id})
                ),
            ),
            (
                FixedPlannerEvent(
                    WEEK,
                    MealRole.BREAKFAST,
                    1,
                    MealSourceKind.EAT_OUT,
                    "Семейное решение: вне дома",
                    frozenset({member_1.id}),
                    ((member_1.id, Decimal(1)),),
                ),
            ),
        )
        result, saved = planner.generate_authoritative(command)
        assert isinstance(result, PlannerSuccess)
        assert saved is not None
        persisted = meal_plans.get_current_plan(household.id, WEEK)
        assert persisted == saved
        assert any(e.source_kind is MealSourceKind.EAT_OUT for e in persisted.events)
        assert any(
            e.source_kind is MealSourceKind.COOK_RECIPE for e in persisted.events
        )
        assert len({p.member_id for p in persisted.member_selections}) == 2
        assert any(
            len(
                {
                    serving.member_id
                    for serving in persisted.servings
                    if serving.event_id == e.id
                }
            )
            == 2
            for e in persisted.events
            if e.source_kind is MealSourceKind.COOK_RECIPE
        )

        # Pantry is established once before the read-only proof, via the
        # authoritative PantryService and movement ledger.
        with SqlAlchemyShoppingReadScope(engine) as scope:
            for event in persisted.events:
                if event.source_kind is MealSourceKind.COOK_RECIPE:
                    detail = scope.recipes.get_detail(event.recipe_version_id)
                    assert detail is not None
                    chosen = next(
                        (
                            row
                            for row in detail.ingredients
                            if row.unit is UnitCode.GRAM
                        ),
                        None,
                    )
                    if chosen is not None:
                        break
            else:
                pytest.fail("No eligible source-backed gram ingredient")

        pantry_writes = PantryService(
            lambda: SqlAlchemyPantryUnitOfWork(engine),
            lambda: SqlAlchemyPantryReadScope(engine),
            clock=lambda: AS_OF,
        )
        stock = pantry_writes.add_stock(
            household.id,
            food_ingredient_id=chosen.food_ingredient_id,
            quantity=Decimal(5),
            unit=UnitCode.GRAM,
            location=PantryLocation.PANTRY,
            purchased_on=WEEK,
            expires_on=WEEK + timedelta(days=8),
        )
        witness = CapturedGenerationContext(
            command,
            semantic_slots,
            result,
            persisted.plan.id,
            persisted.plan.revision_number,
        )
        yield config, engine, households, witness, stock
    finally:
        engine.dispose()


def _db_dump(config: DatabaseConfig) -> str:
    with sqlite3.connect(config.path) as connection:
        return "\n".join(connection.iterdump())


def _persisted_event_signature(plan):
    """Actual MealEvent and participant Serving identity from persisted readback."""
    per_event = defaultdict(list)
    for serving in plan.servings:
        per_event[serving.event_id].append(
            (serving.member_id, serving.portion_servings)
        )
    return tuple(
        (
            event.local_date,
            event.position,
            event.role,
            event.source_kind,
            event.recipe_version_id,
            event.source_reference,
            tuple(sorted(per_event[event.id])),
        )
        for event in sorted(
            plan.events, key=lambda event: (event.local_date, event.position)
        )
    )


def _planner_event_signature(result):
    """Separately captured deterministic Planner output (not reconstructed)."""
    return tuple(
        (
            event.local_date,
            event.position,
            event.role,
            event.source_kind,
            event.recipe_version_id,
            event.source_reference,
            tuple(sorted(event.portions)),
        )
        for event in sorted(
            result.events, key=lambda event: (event.local_date, event.position)
        )
    )


def _verified_generation_inputs(
    plan: MealPlanDetail, state, witness: CapturedGenerationContext
):
    """Reject if this isolated trusted witness cannot bind current persisted facts."""
    command = witness.command
    trace = witness.result.trace
    if (
        plan.plan.id != witness.plan_id
        or plan.plan.revision_number != witness.plan_revision
        or plan.plan.household_id != command.household_id
        or trace.household_id != command.household_id
        or trace.week_start != plan.plan.week_start
        or trace.config_version != plan.plan.config_version
    ):
        raise ProofBlocked("Stale or cross-Household plan revision")
    pinned = {pin.member_id: pin.selection_id for pin in plan.member_selections}
    trace_pins = dict(trace.member_selection_ids)
    actual_members = {member.id for member in state.members if member.active}
    source_members = {member.member_id for member in command.members}
    if (
        set(pinned) != source_members
        or trace_pins != pinned
        or not source_members <= actual_members
        or len(source_members) != len(command.members)
    ):
        raise ProofBlocked("Member selection or Household source drift")
    expected_exclusions = {
        member.member_id: member.excluded_food_ingredient_ids
        for member in command.members
    }
    traced_exclusions = {
        member_id: frozenset(foods) for member_id, foods in trace.applied_exclusions
    }
    if traced_exclusions != expected_exclusions:
        raise ProofBlocked("Untrusted, missing or stale exclusion context")
    if _persisted_event_signature(plan) != _planner_event_signature(witness.result):
        raise ProofBlocked("Persisted MealEvent/Serving differs from Planner witness")
    if (
        len(witness.semantic_slots) != len(source_members)
        or len(set(witness.semantic_slots)) != len(source_members)
        or set(witness.semantic_slots) != source_members
    ):
        raise ProofBlocked("Missing, stale or ambiguous semantic member slot mapping")
    # Only an explicitly supplied test-generation ordering has meaning.
    ordinals = {
        member_id: ordinal
        for ordinal, member_id in enumerate(witness.semantic_slots, 1)
    }
    return expected_exclusions, ordinals


def _read_only(
    scenario, *, witness=None, household_id=None, tamper_plan=None, drop_food=False
):
    _, engine, households, original, _ = scenario
    if witness is None:
        raise ProofBlocked("Missing captured generation witness")
    household_id = household_id or original.command.household_id
    state = households.get_household(household_id)
    with SqlAlchemyShoppingReadScope(engine) as scope:
        plan = scope.plans.get_detail(household_id, original.plan_id)
        current = scope.plans.get_current(household_id, WEEK)
        if plan is None or current is None or current.plan.id != plan.plan.id:
            raise ProofBlocked(
                "Missing, cross-Household or superseded persisted MealPlan"
            )
        if tamper_plan is not None:
            plan = tamper_plan(plan)
        exclusions, ordinals = _verified_generation_inputs(plan, state, witness)
        recipes = {}
        food_ids = set()
        for event in plan.events:
            if event.source_kind is MealSourceKind.COOK_RECIPE:
                detail = scope.recipes.get_detail(event.recipe_version_id)
                if detail is None or detail.version.id != event.recipe_version_id:
                    raise ProofBlocked("Missing source-pinned persisted RecipeVersion")
                recipes[event.recipe_version_id] = detail
                food_ids.update(row.food_ingredient_id for row in detail.ingredients)
        foods = {}
        for food_id in sorted(food_ids, key=str):
            food = scope.foods.get(food_id)
            if food is None:
                raise ProofBlocked("Missing canonical FoodIngredient")
            foods[food_id] = food
        if drop_food:
            foods.pop(next(iter(foods)))
        pantry_items = tuple(scope.pantry.list_items(household_id, include_empty=True))
        prep = calculate_prep_diagnostic(
            plan=plan,
            recipes=recipes,
            foods=foods,
            member_exclusions=exclusions,
            member_ordinals=ordinals,
            policy_version=POLICY,
        )
        shopping = calculate_shopping(
            plan=plan,
            recipes=recipes,
            foods=foods,
            pantry_items=pantry_items,
            household_timezone=state.household.timezone,
            captured_at=AS_OF,
        )
    return plan, prep, shopping


def _raw_requirements(prep):
    totals = defaultdict(lambda: Decimal(0))
    with localcontext() as ctx:
        ctx.prec = 50
        ctx.rounding = ROUND_HALF_EVEN
        for row in prep.event_ingredient_quantities:
            totals[(row.food_ingredient_id, row.unit)] += row.required_quantity
    return totals


def test_authoritative_planner_to_prep_and_shopping_is_read_only(scenario, capsys):
    config, _, _, _, stock = scenario
    before = _db_dump(config)
    plan, prep, shopping = _read_only(scenario, witness=scenario[3])
    second_plan, second_prep, second_shopping = _read_only(
        scenario, witness=scenario[3]
    )
    assert (plan, prep, shopping) == (second_plan, second_prep, second_shopping)
    assert _db_dump(config) == before

    assert plan.plan.revision_number == 1
    assert plan.plan.config_version == "planner-v0.5"
    assert prep.source_plan_revision_number == plan.plan.revision_number
    assert prep.status is PrepDiagnosticStatus.INCOMPLETE
    assert prep.executable_tasks == ()
    assert not hasattr(prep, "gate2_pass")
    assert prep.candidate_step_references
    assert all(
        obligation.reason is PrepDiagnosticReason.STEP_ELIGIBILITY_UNVERIFIED
        for obligation in prep.unresolved
    )
    assert len({r.meal_event_id for r in prep.event_ingredient_quantities}) > 1

    shared = [
        event
        for event in plan.events
        if event.source_kind is MealSourceKind.COOK_RECIPE
        and sum(s.event_id == event.id for s in plan.servings) == 2
    ]
    assert shared
    assert any(
        len({s.portion_servings for s in plan.servings if s.event_id == event.id}) == 2
        for event in shared
    )
    assert any(event.source_kind is MealSourceKind.EAT_OUT for event in plan.events)
    assert shopping.price_status is ShoppingPriceStatus.UNKNOWN

    totals = _raw_requirements(prep)
    assert {item.food_ingredient_id for item in shopping.items} == {
        food_id for food_id, _ in totals
    }
    for item in shopping.items:
        exact_raw = totals[(item.food_ingredient_id, item.unit)]
        # Shopping applies aggregate CEILING 0.001 and separate FEFO stock
        # allocation; Prep keeps the unrounded source demand.
        with localcontext() as ctx:
            ctx.prec = 50
            expected_required = exact_raw.quantize(
                Decimal("0.001"), rounding=ROUND_CEILING
            )
        assert item.required_quantity == expected_required
        assert item.purchase_quantity >= Decimal(0)
        assert item.pantry_available_quantity >= Decimal(0)

    stocked = next(
        item
        for item in shopping.items
        if item.food_ingredient_id == stock.food_ingredient_id
    )
    assert stocked.pantry_available_quantity > Decimal(0)
    assert stocked.purchase_quantity < stocked.required_quantity
    assert any(a.pantry_item_id == stock.id for a in shopping.allocations)

    # Test-only receipts: exact run-local source hashes are visible in CI logs,
    # NOT committed as stable authority or reused as executable Task approvals.
    receipt = {
        "schema": "PR10_A1_READ_ONLY_INTEGRATION_PROOF_V1",
        "context": "SYNTHETIC_PERSISTED_SQLITE_AND_CAPTURED_GENERATION_WITNESS_ONLY",
        "plan_revision": plan.plan.revision_number,
        "plan_id": str(plan.plan.id),
        "prep_source_fingerprint": prep.source_fingerprint,
        "prep_content_fingerprint": prep.content_fingerprint,
        "shopping_source_fingerprint": shopping.source_fingerprint,
        "shopping_content_fingerprint": shopping.content_fingerprint,
        "source_ingredient_quantities": [
            {
                "event_id": str(row.meal_event_id),
                "food_code": row.food_code,
                "unit": row.unit.value,
                "exact_source_demand": format(row.required_quantity, "f"),
            }
            for row in sorted(
                prep.event_ingredient_quantities,
                key=lambda row: (str(row.meal_event_id), row.food_code),
            )
        ],
        "shopping_gross_pantry_net": [
            {
                "food_ingredient_id": str(row.food_ingredient_id),
                "unit": row.unit.value,
                "gross_required_rounded": format(row.required_quantity, "f"),
                "pantry_available": format(row.pantry_available_quantity, "f"),
                "purchase_required": format(row.purchase_quantity, "f"),
            }
            for row in shopping.items
        ],
        "unresolved_reason_codes": sorted(row.reason.value for row in prep.unresolved),
        "unresolved_step_count": len(prep.unresolved),
        "executable_task_count": len(prep.executable_tasks),
        "comparison": {
            "source_gross_matches_shopping_rounded_gross": True,
            "confirmed_pantry_reduces_purchases_not_source_demand": True,
            "sqlite_unchanged_during_read_only_proof": _db_dump(config) == before,
        },
        "gate2_pass": False,
    }
    encoded = json.dumps(receipt, sort_keys=True, ensure_ascii=False)
    print("PR10_A1_RO_PROOF=" + encoded)
    # A local JSON witness is produced only by an explicitly configured CI
    # run. It carries synthetic run-local IDs; never grant data/Step authority.
    if target := os.environ.get("PR10_A1_RO_PROOF_PATH"):
        Path(target).write_text(encoded + "\n", encoding="utf-8")


def test_missing_context_and_wrong_household_fail_closed_without_writes(scenario):
    config, _, _, witness, _ = scenario
    before = _db_dump(config)
    command = witness.command
    cases = [
        replace(witness, semantic_slots=()),
        replace(witness, semantic_slots=(witness.semantic_slots[0],) * 2),
        replace(witness, plan_revision=witness.plan_revision + 1),
        replace(witness, command=replace(command, members=(command.members[0],))),
        replace(
            witness,
            result=replace(
                witness.result,
                trace=replace(witness.result.trace, applied_exclusions=()),
            ),
        ),
    ]
    for invalid in cases:
        with pytest.raises(ProofBlocked):
            _read_only(scenario, witness=invalid)
    with pytest.raises(ProofBlocked, match="Missing captured"):
        _read_only(scenario)
    with pytest.raises((ProofBlocked, LookupError)):
        _read_only(scenario, witness=witness, household_id=uuid4())
    assert _db_dump(config) == before


def _wrong_recipe_version(plan):
    events = list(plan.events)
    index = next(
        i
        for i, event in enumerate(events)
        if event.source_kind is MealSourceKind.COOK_RECIPE
    )
    events[index] = replace(events[index], recipe_version_id=uuid4())
    return replace(plan, events=tuple(events))


def test_stale_revision_and_missing_canonical_food_are_rejected(scenario):
    config, _, _, witness, _ = scenario
    before = _db_dump(config)
    with pytest.raises(ProofBlocked, match="Stale"):
        _read_only(
            scenario,
            witness=witness,
            tamper_plan=lambda plan: replace(
                plan,
                plan=replace(plan.plan, revision_number=plan.plan.revision_number + 1),
            ),
        )
    with pytest.raises(PrepDiagnosticError, match="Неизвестная форма"):
        _read_only(scenario, witness=witness, drop_food=True)
    with pytest.raises(ProofBlocked, match="MealEvent/Serving"):
        _read_only(
            scenario,
            witness=witness,
            tamper_plan=_wrong_recipe_version,
        )
    with pytest.raises(ProofBlocked, match="MealEvent/Serving"):
        _read_only(
            scenario,
            witness=witness,
            tamper_plan=lambda plan: replace(
                plan,
                servings=(
                    replace(
                        plan.servings[0],
                        portion_servings=plan.servings[0].portion_servings
                        + Decimal("0.125"),
                    ),
                    *plan.servings[1:],
                ),
            ),
        )
    assert _db_dump(config) == before
