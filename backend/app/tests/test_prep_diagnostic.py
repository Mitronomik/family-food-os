"""PR10-A1 domain acceptance: non-executable diagnostics, never trusted Prep."""

import ast
import inspect
from dataclasses import replace
from datetime import UTC, date, datetime, timedelta
from decimal import ROUND_DOWN, ROUND_UP, Decimal, localcontext
from uuid import UUID, uuid4

import app.domain.prep_diagnostic as module
import pytest
from app.domain.food_recipes import RightsReviewStatus, VerificationStatus
from app.domain.meal_patterns import MealRole
from app.domain.meal_plans import (
    HouseholdMealEvent,
    MealPlan,
    MealPlanDetail,
    MealPlanMemberSelection,
    MealPlanStatus,
    MealSourceKind,
    Serving,
)
from app.domain.prep_diagnostic import (
    PrepDiagnosticError,
    PrepDiagnosticReason,
    PrepDiagnosticStatus,
    calculate_prep_diagnostic,
)
from app.domain.units import UnitCode
from app.tests.test_food_ingredient_domain import ingredient
from app.tests.test_food_recipe_domain import _detail

NOW = datetime(2026, 11, 3, 9, tzinfo=UTC)
WEEK = date(2026, 11, 2)
POLICY = "pr10-a1-diagnostic-v1"


def _input(
    *,
    portions=("1.500000", "2.500000"),
    kinds=(MealSourceKind.COOK_RECIPE,),
    dates=None,
    recipe=None,
):
    recipe = recipe or _detail()
    food_1 = ingredient(
        id=recipe.ingredients[0].food_ingredient_id,
        canonical_code="RICE",
        canonical_name="Рис",
        canonical_name_key="рис",
    )
    food_2 = ingredient(
        id=recipe.ingredients[1].food_ingredient_id,
        canonical_code="BAY_LEAF",
        canonical_name="Лавровый лист",
        canonical_name_key="лавровый лист",
        default_unit=UnitCode.PIECE,
    )
    plan = MealPlan(
        uuid4(), uuid4(), WEEK, 1, MealPlanStatus.CONFIRMED, "planner-v0.5", None, NOW
    )
    members = [uuid4() for _ in portions]
    selections = tuple(
        MealPlanMemberSelection(plan.id, member, uuid4()) for member in members
    )
    events = []
    servings = []
    dates = dates or tuple(WEEK for _ in kinds)
    for kind, local_date in zip(kinds, dates, strict=True):
        position = sum(event.local_date == local_date for event in events) + 1
        event = HouseholdMealEvent(
            uuid4(),
            plan.id,
            local_date,
            position,
            MealRole.BREAKFAST if position == 1 else MealRole.DINNER,
            kind,
            recipe.version.id if kind is MealSourceKind.COOK_RECIPE else None,
            None,
            NOW,
        )
        events.append(event)
        servings.extend(
            Serving(uuid4(), event.id, member, Decimal(portion), NOW)
            for member, portion in zip(members, portions, strict=True)
        )
    meal = MealPlanDetail(plan, selections, tuple(events), tuple(servings))
    return (
        meal,
        {recipe.version.id: recipe},
        {food_1.id: food_1, food_2.id: food_2},
        {member: frozenset() for member in members},
        {member: ordinal for ordinal, member in enumerate(members, start=1)},
    )


def _calculate(meal, recipes, foods, exclusions, ordinals, **kwargs):
    return calculate_prep_diagnostic(
        plan=meal,
        recipes=recipes,
        foods=foods,
        member_exclusions=exclusions,
        member_ordinals=ordinals,
        policy_version=kwargs.get("policy", POLICY),
    )


def test_exact_decimal_scaling_multiple_members_source_base_and_no_execution():
    meal, recipes, foods, exclusions, ordinals = _input()
    result = _calculate(meal, recipes, foods, exclusions, ordinals)

    assert result.status is PrepDiagnosticStatus.INCOMPLETE
    assert result.engine_version == "prep-diagnostic-a1-v1"
    assert result.executable_tasks == ()
    assert len(result.event_ingredient_quantities) == 2
    by_code = {item.food_code: item for item in result.event_ingredient_quantities}
    # Existing RecipeVersion has base_servings=6; total member Servings=4.
    assert by_code["RICE"].source_quantity == Decimal(600)
    assert by_code["RICE"].total_servings == Decimal(4)
    assert by_code["RICE"].required_quantity == Decimal(400)
    assert by_code["BAY_LEAF"].required_quantity == Decimal(
        "0.66666666666666666666666666666666666666666666666667"
    )
    assert all(item.meal_event_id == meal.events[0].id for item in by_code.values())
    assert (
        result.candidate_step_references[0].recipe_step_id
        == recipes[meal.events[0].recipe_version_id].steps[0].id
    )
    assert not hasattr(result.candidate_step_references[0], "instruction")
    assert result.unresolved == (
        module.PrepUnresolvedDiagnostic(
            meal.events[0].id,
            PrepDiagnosticReason.STEP_ELIGIBILITY_UNVERIFIED,
            recipes[meal.events[0].recipe_version_id].steps[0].id,
        ),
    )
    assert len(result.content_fingerprint) == len(result.source_fingerprint) == 64


def test_multiple_genuine_events_not_grouped_and_repeat_is_identical():
    meal, recipes, foods, exclusions, ordinals = _input(
        kinds=(MealSourceKind.COOK_RECIPE, MealSourceKind.COOK_RECIPE)
    )
    before = (meal, dict(recipes), dict(foods), dict(exclusions), dict(ordinals))
    first = _calculate(meal, recipes, foods, exclusions, ordinals)
    second = _calculate(meal, recipes, foods, exclusions, ordinals)
    assert first == second
    assert before == (
        meal,
        dict(recipes),
        dict(foods),
        dict(exclusions),
        dict(ordinals),
    )
    assert len(first.event_ingredient_quantities) == 4
    assert len({item.meal_event_id for item in first.event_ingredient_quantities}) == 2
    assert len(first.unresolved) == 2
    assert first.executable_tasks == ()


def test_base_servings_noninteger_and_zero_rounding_never_assumed():
    detail = _detail()
    detail = replace(
        detail, version=replace(detail.version, base_servings=Decimal("2.5"))
    )
    meal, recipes, foods, exclusions, ordinals = _input(
        portions=("0.250000", "1.250000"), recipe=detail
    )
    got = _calculate(meal, recipes, foods, exclusions, ordinals)
    amounts = {
        x.food_code: x.required_quantity for x in got.event_ingredient_quantities
    }
    assert amounts == {"RICE": Decimal(360), "BAY_LEAF": Decimal("0.6")}


@pytest.mark.parametrize(
    ("kind", "reason"),
    [
        (MealSourceKind.ASSEMBLY, PrepDiagnosticReason.ASSEMBLY_UNSUPPORTED),
        (MealSourceKind.LEFTOVER, PrepDiagnosticReason.LEFTOVER_SUPPLY_UNVERIFIED),
        (MealSourceKind.PREPARED, PrepDiagnosticReason.PREPARED_SUPPLY_UNVERIFIED),
        (MealSourceKind.READY_MEAL, PrepDiagnosticReason.READY_MEAL_UNRESOLVED),
    ],
)
def test_unverified_mixed_source_has_explicit_unresolved_not_fake_demand(kind, reason):
    meal, recipes, foods, exclusions, ordinals = _input(kinds=(kind,))
    result = _calculate(meal, recipes, foods, exclusions, ordinals)
    assert result.status == PrepDiagnosticStatus.INCOMPLETE
    assert result.unresolved[0].reason is reason
    assert result.event_ingredient_quantities == ()
    assert result.candidate_step_references == ()
    assert result.executable_tasks == ()


@pytest.mark.parametrize("kind", [MealSourceKind.ORDER_OUT, MealSourceKind.EAT_OUT])
def test_outside_home_does_not_invent_home_prep_or_unresolved(kind):
    meal, recipes, foods, exclusions, ordinals = _input(kinds=(kind,))
    result = _calculate(meal, recipes, foods, exclusions, ordinals)
    assert not result.unresolved
    assert result.event_ingredient_quantities == ()
    assert result.executable_tasks == ()
    assert result.status is PrepDiagnosticStatus.INCOMPLETE


def test_mixed_shared_recipe_and_nonrecipe_is_not_fabricated_or_double_counted():
    meal, recipes, foods, exclusions, ordinals = _input(
        kinds=(
            MealSourceKind.COOK_RECIPE,
            MealSourceKind.PREPARED,
            MealSourceKind.EAT_OUT,
        )
    )
    result = _calculate(meal, recipes, foods, exclusions, ordinals)
    assert len(result.event_ingredient_quantities) == 2
    assert len(result.unresolved) == 2  # One unapproved step, one unknown stock.
    assert result.executable_tasks == ()


def test_all_unknown_and_forged_policy_label_cannot_grant_executable_status():
    meal, recipes, foods, exclusions, ordinals = _input(
        kinds=(MealSourceKind.ASSEMBLY, MealSourceKind.PREPARED)
    )
    result = _calculate(
        meal, recipes, foods, exclusions, ordinals, policy="APPROVED_IMMEDIATE_TRUE"
    )
    assert result.status is PrepDiagnosticStatus.INCOMPLETE
    assert result.executable_tasks == ()
    assert not hasattr(result, "gate2_pass")
    with pytest.raises(ValueError):
        replace(result, executable_tasks=("FORGED",))


def test_member_exclusions_explicit_and_per_participant_fail_closed():
    meal, recipes, foods, exclusions, ordinals = _input()
    leaf = recipes[meal.events[0].recipe_version_id].ingredients[1].food_ingredient_id
    excluded = dict(exclusions)
    excluded[meal.servings[-1].member_id] = frozenset({leaf})
    with pytest.raises(PrepDiagnosticError, match="исключения"):
        _calculate(meal, recipes, foods, excluded, ordinals)

    missing = dict(exclusions)
    missing.pop(next(iter(missing)))
    with pytest.raises(PrepDiagnosticError, match="охватывать"):
        _calculate(meal, recipes, foods, missing, ordinals)
    with pytest.raises(PrepDiagnosticError):
        _calculate(meal, recipes, foods, {k: set() for k in exclusions}, ordinals)


def test_change_in_exclusions_changes_source_fingerprint_without_mutation():
    meal, recipes, foods, exclusions, ordinals = _input()
    original = _calculate(meal, recipes, foods, exclusions, ordinals)
    extra = dict(exclusions)
    extra[meal.servings[0].member_id] = frozenset({uuid4()})
    changed = _calculate(meal, recipes, foods, extra, ordinals)
    assert changed.source_fingerprint != original.source_fingerprint
    assert changed.event_ingredient_quantities == original.event_ingredient_quantities


@pytest.mark.parametrize(
    "invalid",
    [
        Decimal(0),
        Decimal(-1),
        Decimal("NaN"),
        1.5,
        Decimal("Infinity"),
        Decimal("1E+999999"),
    ],
)
def test_invalid_serving_or_source_decimal_is_rejected_even_if_snapshot_forged(invalid):
    meal, recipes, foods, exclusions, ordinals = _input()
    serving = meal.servings[0]
    object.__setattr__(serving, "portion_servings", invalid)
    with pytest.raises(PrepDiagnosticError):
        _calculate(meal, recipes, foods, exclusions, ordinals)


def test_invalid_recipe_source_rights_status_and_optional_ingredient_are_rejected():
    meal, recipes, foods, exclusions, ordinals = _input()
    detail = next(iter(recipes.values()))
    variants = (
        replace(
            detail,
            version=replace(
                detail.version, verification_status=VerificationStatus.UNVERIFIED
            ),
        ),
        replace(
            detail,
            version=replace(
                detail.version,
                verification_status=VerificationStatus.UNVERIFIED,
                rights_review_status=RightsReviewStatus.BLOCKED,
            ),
        ),
        replace(
            detail,
            ingredients=(
                replace(detail.ingredients[0], optional=True),
                *detail.ingredients[1:],
            ),
        ),
    )
    for modified in variants:
        with pytest.raises(PrepDiagnosticError):
            _calculate(meal, {detail.version.id: modified}, foods, exclusions, ordinals)


def test_mismatched_unit_missing_food_and_missing_recipe_are_blocking():
    meal, recipes, foods, exclusions, ordinals = _input()
    detail = next(iter(recipes.values()))
    wrong_unit = replace(
        detail,
        ingredients=(
            replace(detail.ingredients[0], unit=UnitCode.MILLILITER),
            *detail.ingredients[1:],
        ),
    )
    for invalid_recipes, invalid_foods in (
        ({}, foods),
        ({detail.version.id: wrong_unit}, foods),
        (recipes, {}),
    ):
        with pytest.raises(PrepDiagnosticError):
            _calculate(meal, invalid_recipes, invalid_foods, exclusions, ordinals)


def test_stale_revision_and_step_content_invalidate_fingerprints():
    meal, recipes, foods, exclusions, ordinals = _input()
    baseline = _calculate(meal, recipes, foods, exclusions, ordinals)
    modified_meal = replace(meal, plan=replace(meal.plan, revision_number=2))
    revised = _calculate(modified_meal, recipes, foods, exclusions, ordinals)
    assert baseline.source_fingerprint != revised.source_fingerprint
    assert baseline.content_fingerprint == revised.content_fingerprint

    detail = next(iter(recipes.values()))
    modified_detail = replace(
        detail,
        steps=(replace(detail.steps[0], instruction="Другая исходная инструкция."),),
    )
    step_changed = _calculate(
        meal, {detail.version.id: modified_detail}, foods, exclusions, ordinals
    )
    assert step_changed.content_fingerprint != baseline.content_fingerprint
    assert step_changed.source_fingerprint != baseline.source_fingerprint


def test_new_runtime_ids_do_not_change_semantic_content_fingerprint():
    first = _input(portions=("1", "1"))
    second = _input(portions=("1", "1"))
    one = _calculate(*first)
    two = _calculate(*second)
    assert one.content_fingerprint == two.content_fingerprint
    assert one.source_fingerprint != two.source_fingerprint


def test_timestamp_and_tuple_order_do_not_change_fingerprints():
    meal, recipes, foods, exclusions, ordinals = _input()
    original = _calculate(meal, recipes, foods, exclusions, ordinals)
    edited = replace(
        meal,
        plan=replace(meal.plan, created_at=NOW + timedelta(days=1)),
        servings=tuple(reversed(meal.servings)),
        member_selections=tuple(reversed(meal.member_selections)),
    )
    assert (
        _calculate(edited, recipes, foods, exclusions, ordinals).content_fingerprint
        == original.content_fingerprint
    )
    assert (
        _calculate(edited, recipes, foods, exclusions, ordinals).source_fingerprint
        == original.source_fingerprint
    )


def _with_member_ids(snapshot, member_ids):
    """Two SQLite-like run-local IDs with the SAME explicit semantic ordinals."""
    meal, recipes, foods, exclusions, ordinals = snapshot
    old_ids = [pin.member_id for pin in meal.member_selections]
    binding = dict(zip(old_ids, member_ids, strict=True))
    remapped = replace(
        meal,
        member_selections=tuple(
            replace(pin, member_id=binding[pin.member_id])
            for pin in meal.member_selections
        ),
        servings=tuple(
            replace(serving, member_id=binding[serving.member_id])
            for serving in meal.servings
        ),
    )
    return (
        remapped,
        recipes,
        foods,
        {binding[mid]: value for mid, value in exclusions.items()},
        {binding[mid]: ordinal for mid, ordinal in ordinals.items()},
    )


def test_unequal_servings_and_inverted_runtime_uuid_order_keep_semantic_hash():
    low = UUID("11111111-1111-4111-8111-111111111111")
    high = UUID("eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee")
    one_snapshot = _with_member_ids(_input(portions=("1.5", "2.5")), (low, high))
    two_snapshot = _with_member_ids(_input(portions=("1.5", "2.5")), (high, low))
    assert low.hex < high.hex
    assert one_snapshot[4][low] == 1 and two_snapshot[4][low] == 2
    one = _calculate(*one_snapshot)
    two = _calculate(*two_snapshot)
    assert one.content_fingerprint == two.content_fingerprint
    assert one.source_fingerprint != two.source_fingerprint
    assert one.event_ingredient_quantities[0].required_quantity == (
        two.event_ingredient_quantities[0].required_quantity
    )
    assert one.executable_tasks == two.executable_tasks == ()

    # Swapping logical portions (not just UUID assignments) MUST change content.
    changed = _with_member_ids(_input(portions=("2.5", "1.5")), (high, low))
    assert _calculate(*changed).content_fingerprint != one.content_fingerprint


def test_missing_or_ambiguous_semantic_ordinals_fail_closed():
    meal, recipes, foods, exclusions, ordinals = _input()
    members = list(ordinals)
    bad = (
        {members[0]: 1},
        {members[0]: 1, members[1]: 1},
        {members[0]: 1, members[1]: 3},
        {members[0]: True, members[1]: 2},
        {members[0]: "1", members[1]: 2},
        {members[0]: 0, members[1]: 1},
        {**ordinals, uuid4(): 3},
    )
    for mapping in bad:
        with pytest.raises(PrepDiagnosticError, match="номера|нумерация"):
            _calculate(meal, recipes, foods, exclusions, mapping)
    with pytest.raises(PrepDiagnosticError, match="нумерация"):
        calculate_prep_diagnostic(
            plan=meal,
            recipes=recipes,
            foods=foods,
            member_exclusions=exclusions,
            member_ordinals=None,
            policy_version=POLICY,
        )


@pytest.mark.parametrize("kind", [MealSourceKind.EAT_OUT, MealSourceKind.READY_MEAL])
def test_nonrecipe_source_reference_is_pinned_and_normalized(kind):
    meal, recipes, foods, exclusions, ordinals = _input(kinds=(kind,))
    baseline = _calculate(meal, recipes, foods, exclusions, ordinals)
    event = meal.events[0]
    updated = replace(
        meal,
        events=(replace(event, source_reference="  order   reference A  "),),
    )
    changed = _calculate(updated, recipes, foods, exclusions, ordinals)
    assert changed.source_fingerprint != baseline.source_fingerprint
    assert changed.content_fingerprint != baseline.content_fingerprint
    normalized = replace(
        meal,
        events=(replace(event, source_reference="order reference A"),),
    )
    normalized_receipt = _calculate(normalized, recipes, foods, exclusions, ordinals)
    assert changed.source_fingerprint == normalized_receipt.source_fingerprint
    assert changed.content_fingerprint == normalized_receipt.content_fingerprint
    assert changed.executable_tasks == baseline.executable_tasks == ()


def test_decimal_rounding_is_fixed_and_independent_of_ambient_context():
    meal, recipes, foods, exclusions, ordinals = _input()
    assert module.QUANTITY_PRECISION == 50
    assert module.QUANTITY_ROUNDING == "ROUND_HALF_EVEN"

    with localcontext() as ctx:
        ctx.prec = 6
        ctx.rounding = ROUND_DOWN
        under_low_context = _calculate(meal, recipes, foods, exclusions, ordinals)
    with localcontext() as ctx:
        ctx.prec = 80
        ctx.rounding = ROUND_UP
        under_high_context = _calculate(meal, recipes, foods, exclusions, ordinals)

    assert under_low_context == under_high_context
    leaf = next(
        value.required_quantity
        for value in under_low_context.event_ingredient_quantities
        if value.food_code == "BAY_LEAF"
    )
    # 4/6 is a repeating rational. The result is a documented 50-significant-
    # digit HALF_EVEN approximation, NEVER an exact 2/3 or a package count.
    assert leaf == Decimal("0.66666666666666666666666666666666666666666666666667")


def test_calculator_has_no_repo_sql_clock_network_or_inventory_side_effect_import():
    tree = ast.parse(inspect.getsource(module))
    imports = [
        item.module or "" for item in ast.walk(tree) if isinstance(item, ast.ImportFrom)
    ]
    forbidden = (
        "app.services",
        "app.persistence",
        "sqlalchemy",
        "sqlite3",
        "socket",
        "requests",
        "app.domain.shopping_calculation",
    )
    assert not any(
        name.startswith(forbidden_namespace)
        for name in imports
        for forbidden_namespace in forbidden
    )
    assert (
        module.PrepDiagnosticResult.__dataclass_fields__["executable_tasks"].init
        is False
    )
