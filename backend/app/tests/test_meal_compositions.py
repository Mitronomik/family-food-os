"""MealPlan-only course proposal: membership, source and explicit role structure."""

from dataclasses import replace
from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest

from app.domain.errors import DomainValidationError
from app.domain.meal_compositions import (
    DRAFT_STATUS,
    CourseCardinality,
    DraftMealStructureRule,
    MealComponentDraft,
    MealCourseKind,
    MealEventCompositionDraft,
    MemberComponentServingDraft,
    validate_composition_draft,
)
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

NOW = datetime(2026, 11, 3, tzinfo=timezone.utc)


def _case(*, role=MealRole.LUNCH, members=1):
    plan_id, event_id, household_id = uuid4(), uuid4(), uuid4()
    people = [uuid4() for _ in range(members)]
    old_recipe_id, first_id, dessert_id = uuid4(), uuid4(), uuid4()
    plan = MealPlan(
        id=plan_id,
        household_id=household_id,
        week_start=date(2026, 11, 2),
        revision_number=1,
        status=MealPlanStatus.DRAFT,
        config_version="planner-v0.5",
        supersedes_plan_id=None,
        created_at=NOW,
    )
    event = HouseholdMealEvent(
        id=event_id,
        plan_id=plan_id,
        local_date=date(2026, 11, 3),
        position=1,
        role=role,
        source_kind=MealSourceKind.COOK_RECIPE,
        recipe_version_id=old_recipe_id,
        source_reference=None,
        created_at=NOW,
    )
    original = MealPlanDetail(
        plan=plan,
        member_selections=tuple(
            MealPlanMemberSelection(plan_id, person, uuid4()) for person in people
        ),
        events=(event,),
        servings=tuple(
            Serving(
                id=uuid4(),
                event_id=event_id,
                member_id=person,
                portion_servings=Decimal("2.031139"),
                created_at=NOW,
            )
            for person in people
        ),
    )
    return original, people, (first_id, old_recipe_id, dessert_id)


def _lunch_draft(original, people, recipes, *, with_dessert=True):
    event_id = original.events[0].id
    first, second, dessert = recipes
    components = (
        MealComponentDraft(event_id, 1, MealCourseKind.FIRST, first),
        MealComponentDraft(event_id, 2, MealCourseKind.SECOND, second),
    )
    if with_dessert:
        components += (MealComponentDraft(event_id, 3, MealCourseKind.DESSERT, dessert),)
    servings = (
        MemberComponentServingDraft(event_id, 1, people[0], Decimal("1.000000")),
        MemberComponentServingDraft(event_id, 2, people[0], Decimal("1.000000")),
    )
    if with_dessert:
        servings += (
            MemberComponentServingDraft(event_id, 3, people[0], Decimal("0.500000")),
        )
    return MealEventCompositionDraft(
        plan_id=original.plan.id,
        event_id=event_id,
        components=components,
        servings=servings,
    )


def _lunch_rule():
    return DraftMealStructureRule(
        code="DEV_LUNCH_FIRST_SECOND_OPTIONAL_DESSERT",
        version=1,
        meal_role=MealRole.LUNCH,
        requirements=(
            CourseCardinality(MealCourseKind.FIRST, 1, 1),
            CourseCardinality(MealCourseKind.SECOND, 1, 1),
            CourseCardinality(MealCourseKind.DESSERT, 0, 1),
        ),
    )


def test_three_course_lunch_is_one_event_and_one_at_home_participant():
    original, people, recipes = _case()
    draft = _lunch_draft(original, people, recipes)
    assert len(draft.components) == 3
    assert len(draft.servings) == 3
    assert {s.member_id for s in draft.servings} == {people[0]}
    assert DRAFT_STATUS == "NON_PERSISTENT_RESEARCH_PROPOSAL"
    assert validate_composition_draft(draft, original, _lunch_rule()) is None
    assert len(original.events) == 1
    assert original.events[0].recipe_version_id == recipes[1]
    assert original.servings[0].portion_servings == Decimal("2.031139")


def test_desert_is_optional_and_guest_can_skip_one_component():
    original, people, recipes = _case(members=2)
    draft = _lunch_draft(original, people, recipes)
    additional = (
        MemberComponentServingDraft(draft.event_id, 1, people[1], Decimal(1)),
        MemberComponentServingDraft(draft.event_id, 2, people[1], Decimal(1)),
    )
    draft = replace(draft, servings=draft.servings + additional)
    assert validate_composition_draft(draft, original, _lunch_rule()) is None
    no_dessert = _lunch_draft(original, people[:1], recipes, with_dessert=False)
    no_dessert = replace(no_dessert, servings=no_dessert.servings + additional)
    assert validate_composition_draft(no_dessert, original, _lunch_rule()) is None


def test_breakfast_or_dinner_can_each_use_single_course_without_lunch_policy():
    for role in (MealRole.BREAKFAST, MealRole.DINNER):
        original, people, (_, recipe_id, _) = _case(role=role)
        event_id = original.events[0].id
        draft = MealEventCompositionDraft(
            original.plan.id,
            event_id,
            (MealComponentDraft(event_id, 1, MealCourseKind.MAIN, recipe_id),),
            (
                MemberComponentServingDraft(
                    event_id, 1, people[0], Decimal("1.000000")
                ),
            ),
        )
        rule = DraftMealStructureRule(
            code=f"TEST_{role.value}",
            version=1,
            meal_role=role,
            requirements=(CourseCardinality(MealCourseKind.MAIN, 1, 1),),
        )
        assert validate_composition_draft(draft, original, rule) is None
        with pytest.raises(DomainValidationError):
            validate_composition_draft(draft, original, _lunch_rule())


@pytest.mark.parametrize(
    "mutation",
    [
        "other_plan",
        "missing_source_recipe",
        "different_event",
        "phantom_participant",
        "missing_member",
        "no_serving_for_component",
        "unknown_component",
        "wrong_course_order",
        "duplicate_component",
        "duplicate_member_serving",
        "source_kind_eat_out",
        "unexpected_dessert",
        "missing_second",
        "wrong_role_rule",
    ],
)
def test_proposal_rejects_invalid_source_or_partial_schedule(mutation):
    original, people, recipes = _case()
    draft = _lunch_draft(original, people, recipes)
    rule = _lunch_rule()
    event_id = draft.event_id
    with pytest.raises(DomainValidationError):
        if mutation == "other_plan":
            draft = replace(draft, plan_id=uuid4())
        elif mutation == "missing_source_recipe":
            draft = replace(
                draft,
                components=tuple(
                    replace(c, recipe_version_id=uuid4()) if c.position == 2 else c
                    for c in draft.components
                ),
            )
        elif mutation == "different_event":
            draft = replace(draft, event_id=uuid4())
        elif mutation == "phantom_participant":
            draft = replace(
                draft,
                servings=draft.servings
                + (MemberComponentServingDraft(event_id, 2, uuid4(), Decimal(1)),),
            )
        elif mutation == "missing_member":
            draft = replace(draft, servings=())
        elif mutation == "no_serving_for_component":
            draft = replace(
                draft, servings=tuple(s for s in draft.servings if s.component_position != 3)
            )
        elif mutation == "unknown_component":
            draft = replace(
                draft,
                servings=draft.servings + (
                    MemberComponentServingDraft(event_id, 4, people[0], Decimal(1)),
                ),
            )
        elif mutation == "wrong_course_order":
            draft = replace(
                draft,
                components=(
                    replace(draft.components[0], course=MealCourseKind.SECOND),
                    replace(draft.components[1], course=MealCourseKind.FIRST),
                    draft.components[2],
                ),
            )
        elif mutation == "duplicate_component":
            draft = replace(
                draft,
                components=draft.components + (draft.components[0],),
            )
        elif mutation == "duplicate_member_serving":
            draft = replace(draft, servings=draft.servings + (draft.servings[0],))
        elif mutation == "source_kind_eat_out":
            original = replace(
                original,
                events=(replace(
                    original.events[0],
                    source_kind=MealSourceKind.EAT_OUT,
                    recipe_version_id=None,
                ),),
            )
        elif mutation == "unexpected_dessert":
            rule = DraftMealStructureRule(
                code="LUNCH_NO_DESSERT",
                version=1,
                meal_role=MealRole.LUNCH,
                requirements=(
                    CourseCardinality(MealCourseKind.FIRST, 1, 1),
                    CourseCardinality(MealCourseKind.SECOND, 1, 1),
                ),
            )
        elif mutation == "missing_second":
            draft = replace(
                draft,
                components=(
                    draft.components[0],
                    replace(draft.components[1], course=MealCourseKind.DESSERT),
                ),
            )
        elif mutation == "wrong_role_rule":
            rule = replace(rule, meal_role=MealRole.DINNER)
        validate_composition_draft(draft, original, rule)


@pytest.mark.parametrize(
    "amount",
    [Decimal(0), Decimal("-1"), Decimal("NaN"), Decimal("Infinity"), Decimal("0.0000001"), 1.0, "1.000000"],
)
def test_member_component_serving_requires_supported_decimal(amount):
    with pytest.raises(DomainValidationError):
        MemberComponentServingDraft(uuid4(), 1, uuid4(), amount)


def test_missing_or_duplicate_rule_does_not_silently_choose_default_structure():
    with pytest.raises(DomainValidationError):
        DraftMealStructureRule(
            "", 1, MealRole.LUNCH, (CourseCardinality(MealCourseKind.FIRST, 1, 1),)
        )
    with pytest.raises(DomainValidationError):
        DraftMealStructureRule(
            "TEST",
            1,
            MealRole.LUNCH,
            (
                CourseCardinality(MealCourseKind.FIRST, 1, 1),
                CourseCardinality(MealCourseKind.FIRST, 0, 1),
            ),
        )
