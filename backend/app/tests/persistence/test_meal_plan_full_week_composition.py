"""P2: actual persistence replay of one *complete* heterogeneous 21/42 week.

The fixture is a synthetic at-home 3-member MealPattern with exactly the same
21 MealEvents / 42 persisted Serving shape as the accepted Planner proof; only
the event being replaced is composed. It is not a substitute for the existing
separately verified production 2-process Planner semantic receipt.
"""

import subprocess
import sys
from dataclasses import replace
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import pytest

from app.db.config import DatabaseConfig
from app.db.migrations import apply_migrations
from app.domain.meal_patterns import MealRole
from app.domain.meal_plans import (
    HouseholdMealEvent,
    MealPlan,
    MealPlanDetail,
    MealPlanMemberReferenceMethodologyPin,
    MealPlanMemberSelection,
    MealPlanStatus,
    MealSourceKind,
    MemberMealPatternOpportunitySnapshot,
    Serving,
)
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
from app.persistence.sqlalchemy_core.meal_plan_uow import (
    SqlAlchemyMealPlanReadScope,
    SqlAlchemyMealPlanUnitOfWork,
)
from app.persistence.sqlalchemy_core.reference_methodology_uow import (
    SqlAlchemyReferenceMethodologyUnitOfWork,
)
from app.services.meal_plan_composition_revisions import (
    assert_complete_revision_preservation,
)
from app.tests.persistence.test_meal_plan_composition_persistence import (
    _compose,
    _source_recipes,
    _write,
)
from app.tests.persistence.test_meal_plan_reference_methodology_repository import (
    _reference,
)
from app.tests.persistence.test_meal_plan_repository import (
    _household,
    _member,
    _seed_household,
    _selection,
)

WEEK_START = date(2026, 11, 2)
CREATED = datetime(2026, 11, 15, 15, 0, tzinfo=UTC)
ROLES = (
    (MealRole.BREAKFAST, (0, 1)),
    (MealRole.LUNCH, (0,)),
    (MealRole.DINNER, (0, 1, 2)),
)


def _week_21_42(tmp_path):
    config = DatabaseConfig(path=tmp_path / "full-week-21-42.sqlite")
    apply_migrations(config)
    recipes = _source_recipes(config)
    engine = create_sqlite_engine(config)
    home = _household()
    people = [_member(home.id, f"Member {n}") for n in range(1, 4)]
    _seed_household(engine, home, *people)
    selections = {}
    references = {}
    pins = []
    reference_pins = []
    for idx, person in enumerate(people):
        selected_roles = tuple(
            role for role, participants in ROLES if idx in participants
        )
        template = _selection(home.id, person.id)
        selection = replace(
            template,
            opportunities=tuple(
                MemberMealPatternOpportunitySnapshot(
                    template.selection.id,
                    weekday,
                    position,
                    role,
                )
                for weekday in range(1, 8)
                for position, role in enumerate(selected_roles, 1)
            ),
        )
        selections[selection.selection.id] = selection
        reference = _reference(home, person)
        references[person.id] = reference
        pins.append(
            MealPlanMemberSelection(
                plan_id=uuid4(), member_id=person.id, selection_id=selection.selection.id
            )
        )
    with SqlAlchemyMealPlanUnitOfWork(engine) as uow:
        for selection in selections.values():
            uow.selections.add_detail(selection)
        uow.commit()
    with SqlAlchemyReferenceMethodologyUnitOfWork(engine) as uow:
        for ref in references.values():
            uow.selections.add(ref)
        uow.commit()
    plan = MealPlan(
        id=uuid4(),
        household_id=home.id,
        week_start=WEEK_START,
        revision_number=1,
        status=MealPlanStatus.CONFIRMED,
        config_version="test-heterogeneous-21-42",
        supersedes_plan_id=None,
        created_at=CREATED,
    )
    pins = tuple(
        sorted(
            (replace(pin, plan_id=plan.id) for pin in pins),
            key=lambda item: item.member_id.hex,
        )
    )
    for person in people:
        ref = references[person.id]
        reference_pins.append(
            MealPlanMemberReferenceMethodologyPin(
                plan_id=plan.id,
                member_id=person.id,
                reference_methodology_selection_id=ref.id,
                birth_date=person.birth_date,
                sex=person.sex,
                height_cm=person.height_cm,
                weight_kg=person.weight_kg,
                activity_level=person.activity_level,
                goal=person.goal,
                member_updated_at=person.updated_at,
            )
        )
    events = []
    servings = []
    for day in range(7):
        for position, (role, participant_indexes) in enumerate(ROLES, 1):
            event = HouseholdMealEvent(
                id=uuid4(),
                plan_id=plan.id,
                local_date=WEEK_START + timedelta(days=day),
                position=position,
                role=role,
                source_kind=MealSourceKind.COOK_RECIPE,
                recipe_version_id=recipes["SECOND_TEST"],
                source_reference=None,
                created_at=CREATED,
            )
            events.append(event)
            for idx in participant_indexes:
                servings.append(
                    Serving(
                        id=uuid4(),
                        event_id=event.id,
                        member_id=people[idx].id,
                        portion_servings=Decimal("1.250000"),
                        created_at=CREATED,
                    )
                )
    assert len(events) == 21
    assert len(servings) == 42
    # The SQL read-model is deterministic by event slot and member UUID,
    # not by the test fixture's human ordinal. Build that canonical snapshot
    # before comparing persisted/reloaded immutable revisions.
    event_order = {event.id: pos for pos, event in enumerate(events)}
    servings.sort(key=lambda item: (event_order[item.event_id], item.member_id.hex))
    reference_pins.sort(key=lambda item: item.member_id.hex)
    old = MealPlanDetail(
        plan=plan,
        member_selections=pins,
        events=tuple(events),
        servings=tuple(servings),
        reference_methodology_pins=tuple(reference_pins),
    )
    with SqlAlchemyMealPlanUnitOfWork(engine) as uow:
        uow.plans.add_detail(old)
        uow.commit()
    return config, engine, home, people, old, recipes, selections


def _semantic_rows(plan, *, exclude_slot=None):
    grouped = {}
    for serving in plan.servings:
        grouped.setdefault(serving.event_id, []).append(
            (serving.member_id, serving.portion_servings)
        )
    return {
        (event.local_date, event.position): (
            event.role,
            event.source_kind,
            event.recipe_version_id,
            event.source_reference,
            tuple(sorted(grouped.get(event.id, []))),
        )
        for event in plan.events
        if (event.local_date, event.position) != exclude_slot
    }


def test_p2_full_persisted_21_event_42_serving_week_survives_one_lunch_edit(tmp_path):
    config, engine, home, people, old, recipes, selections = _week_21_42(tmp_path)
    try:
        # Tuesday LUNCH is slot (2026-11-03,2) -> index 4.
        changed = _compose(old, people[:1], recipes, selections, target_index=4)
        assert len(changed.events) == 21
        assert len(changed.servings) == 41
        assert len(changed.compositions) == 1
        assert len(changed.compositions[0].servings) == 3
        assert len(changed.member_selections) == 3
        assert len(changed.reference_methodology_pins) == 3
        changed_slot = (date(2026, 11, 3), 2)
        assert _semantic_rows(old, exclude_slot=changed_slot) == _semantic_rows(
            changed, exclude_slot=changed_slot
        )
        assert_complete_revision_preservation(old, changed, old.events[4].id)
        assert all(
            old_event.id != new_event.id
            for old_event, new_event in zip(old.events, changed.events)
        )
        assert {
            pin.member_id: pin.selection_id for pin in old.member_selections
        } == {
            pin.member_id: pin.selection_id for pin in changed.member_selections
        }
        assert {
            pin.member_id: replace(pin, plan_id=changed.plan.id)
            for pin in old.reference_methodology_pins
        } == {
            pin.member_id: pin for pin in changed.reference_methodology_pins
        }

        _write(engine, changed, people)
        with SqlAlchemyMealPlanReadScope(engine) as scope:
            assert scope.plans.get_detail(home.id, old.plan.id) == old
            assert scope.plans.get_detail(home.id, changed.plan.id) == changed
            assert scope.plans.get_current(home.id, WEEK_START) == changed
        engine.dispose()
        engine = create_sqlite_engine(config)
        with SqlAlchemyMealPlanReadScope(engine) as scope:
            reopened = scope.plans.get_detail(home.id, changed.plan.id)
            old_reopened = scope.plans.get_detail(home.id, old.plan.id)
        assert reopened == changed
        assert old_reopened == old
        assert _semantic_rows(old_reopened, exclude_slot=changed_slot) == _semantic_rows(
            reopened, exclude_slot=changed_slot
        )
        # Reader starts in a separate Python process; no in-memory rule cache.
        script = """
import sys
from pathlib import Path
from uuid import UUID
from app.db.config import DatabaseConfig
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
from app.persistence.sqlalchemy_core.meal_plan_uow import SqlAlchemyMealPlanReadScope
from app.domain.meal_compositions import rule_snapshot_digest
engine = create_sqlite_engine(DatabaseConfig(path=Path(sys.argv[1])))
try:
    with SqlAlchemyMealPlanReadScope(engine) as scope:
        detail = scope.plans.get_detail(UUID(sys.argv[2]), UUID(sys.argv[3]))
    assert len(detail.events) == 21
    assert len(detail.servings) == 41
    assert len(detail.reference_methodology_pins) == 3
    assert len(detail.compositions[0].servings) == 3
    assert len(detail.compositions[0].rule.requirements) == 3
    print(rule_snapshot_digest(detail.compositions[0].rule))
finally:
    engine.dispose()
"""
        completed = subprocess.run(
            [
                sys.executable,
                "-c",
                script,
                str(config.path),
                str(home.id),
                str(changed.plan.id),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        assert len(completed.stdout.strip()) == 64
    finally:
        engine.dispose()


def test_p2_truncated_new_revision_fails_before_any_write(tmp_path):
    config, engine, home, people, old, recipes, selections = _week_21_42(tmp_path)
    try:
        changed = _compose(old, people[:1], recipes, selections, target_index=4)
        with pytest.raises(Exception):
            replace(
                changed,
                events=tuple(
                    event for event in changed.events
                    if event.local_date != date(2026, 11, 4)
                ),
            )
        with SqlAlchemyMealPlanReadScope(engine) as scope:
            assert scope.plans.get_current(home.id, WEEK_START) == old
    finally:
        engine.dispose()
