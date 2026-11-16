"""Internal-only complete-week diagnostic composition revision constructor.

No API/Planner caller is registered. The immutable previous revision is
read, matched to accepted member schedules, and cloned as a FULL week.
Only the target source-recipe event changes into a composed diagnostic event.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from typing import Callable
from uuid import UUID, uuid4

from app.domain.meal_compositions import (
    MealEventCompositionDraft,
    PersistedMealComponent,
    PersistedMealEventComposition,
    PersistedMemberComponentServing,
    DraftMealStructureRule,
    validate_composition_draft,
)
from app.domain.meal_plans import (
    MealPlanDetail,
    MealPlanStatus,
    MealSourceKind,
    MemberMealPatternSelectionDetail,
    validate_complete_plan,
)
from app.services.meal_plan_contracts import MealPlanPersistenceConflictError

IdFactory = Callable[[], UUID]


def make_complete_diagnostic_revision(
    *,
    prior: MealPlanDetail,
    proposal: MealEventCompositionDraft,
    rule: DraftMealStructureRule,
    selection_details: dict[UUID, MemberMealPatternSelectionDetail],
    created_at: datetime,
    id_factory: IdFactory = uuid4,
) -> MealPlanDetail:
    """Clone every event/Serving/pin; replace only one originally recipe-backed slot."""
    if prior.plan.status not in (MealPlanStatus.CONFIRMED, MealPlanStatus.DRAFT):
        raise MealPlanPersistenceConflictError("Unsupported previous plan state.")
    validate_complete_plan(prior, selection_details)
    validate_composition_draft(proposal, prior, rule)

    plan = replace(
        prior.plan,
        id=id_factory(),
        revision_number=prior.plan.revision_number + 1,
        supersedes_plan_id=prior.plan.id,
        status=MealPlanStatus.DRAFT,
        created_at=created_at,
    )
    if plan.id == prior.plan.id:
        raise MealPlanPersistenceConflictError("New plan requires a new identity.")
    mapping: dict[UUID, UUID] = {}
    events = []
    for old in sorted(prior.events, key=lambda x: (x.local_date, x.position)):
        new_id = id_factory()
        if new_id == old.id or new_id in mapping.values():
            raise MealPlanPersistenceConflictError("Event identity must not be reused.")
        mapping[old.id] = new_id
        if old.id == proposal.event_id:
            events.append(
                replace(
                    old,
                    id=new_id,
                    plan_id=plan.id,
                    source_kind=MealSourceKind.COOK_COMPOSITION,
                    recipe_version_id=None,
                    source_reference=None,
                    created_at=created_at,
                )
            )
        else:
            events.append(
                replace(old, id=new_id, plan_id=plan.id, created_at=created_at)
            )
    servings = tuple(
        replace(
            serving,
            id=id_factory(),
            event_id=mapping[serving.event_id],
            created_at=created_at,
        )
        for serving in prior.servings
        if serving.event_id != proposal.event_id
    )
    if len(servings) != len(prior.servings) - sum(
        serving.event_id == proposal.event_id for serving in prior.servings
    ):
        raise MealPlanPersistenceConflictError("A historical Serving was lost.")

    def components_from_proposal():
        target = mapping[proposal.event_id]
        components = tuple(
            PersistedMealComponent(
                id=id_factory(),
                event_id=target,
                position=item.position,
                course=item.course,
                recipe_version_id=item.recipe_version_id,
                created_at=created_at,
            )
            for item in sorted(proposal.components, key=lambda c: c.position)
        )
        positions = {c.position: c.id for c in components}
        member_servings = tuple(
            PersistedMemberComponentServing(
                component_id=positions[item.component_position],
                member_id=item.member_id,
                portion_servings=item.portion_servings,
                created_at=created_at,
            )
            for item in sorted(
                proposal.servings, key=lambda s: (s.component_position, s.member_id.hex)
            )
        )
        return PersistedMealEventComposition(
            event_id=target,
            rule=rule,
            components=components,
            servings=member_servings,
            created_at=created_at,
        )

    composition_rows = [components_from_proposal()]
    for previous in prior.compositions:
        target = mapping[previous.event_id]
        new_components = tuple(
            replace(
                c,
                id=id_factory(),
                event_id=target,
                created_at=created_at,
            )
            for c in previous.components
        )
        component_map = {
            old.id: new.id for old, new in zip(previous.components, new_components)
        }
        composition_rows.append(
            PersistedMealEventComposition(
                event_id=target,
                rule=previous.rule,
                components=new_components,
                servings=tuple(
                    replace(
                        serving,
                        component_id=component_map[serving.component_id],
                        created_at=created_at,
                    )
                    for serving in previous.servings
                ),
                created_at=created_at,
            )
        )
    detail = MealPlanDetail(
        plan=plan,
        member_selections=tuple(
            replace(pin, plan_id=plan.id) for pin in prior.member_selections
        ),
        events=tuple(events),
        servings=servings,
        reference_methodology_pins=tuple(
            replace(pin, plan_id=plan.id) for pin in prior.reference_methodology_pins
        ),
        compositions=tuple(
            sorted(composition_rows, key=lambda comp: (
                next(e.local_date for e in events if e.id == comp.event_id),
                next(e.position for e in events if e.id == comp.event_id),
            ))
        ),
    )
    validate_complete_plan(detail, selection_details)
    assert_complete_revision_preservation(prior, detail, proposal.event_id)
    return detail


def assert_complete_revision_preservation(
    prior: MealPlanDetail, new: MealPlanDetail, target_prior_event_id: UUID
) -> None:
    """Second line of defense for repository and independently reconstructed reads."""
    if (
        new.plan.household_id != prior.plan.household_id
        or new.plan.week_start != prior.plan.week_start
        or new.plan.revision_number != prior.plan.revision_number + 1
        or new.plan.supersedes_plan_id != prior.plan.id
        or new.plan.id == prior.plan.id
        or new.plan.status is not MealPlanStatus.DRAFT
        or len(new.events) != len(prior.events)
        or {pin.member_id: pin.selection_id for pin in new.member_selections}
        != {pin.member_id: pin.selection_id for pin in prior.member_selections}
    ):
        raise MealPlanPersistenceConflictError("New plan must preserve full week and pins.")
    old_refs = {
        pin.member_id: replace(pin, plan_id=new.plan.id)
        for pin in prior.reference_methodology_pins
    }
    if {pin.member_id: pin for pin in new.reference_methodology_pins} != old_refs:
        raise MealPlanPersistenceConflictError("Reference methodology pins changed.")
    old_slots = {(e.local_date, e.position): e for e in prior.events}
    new_slots = {(e.local_date, e.position): e for e in new.events}
    if set(old_slots) != set(new_slots) or len(old_slots) != len(prior.events):
        raise MealPlanPersistenceConflictError("Missing or repeated source weekly slot.")
    old_ids = {e.id for e in prior.events}
    new_ids = {e.id for e in new.events}
    if old_ids & new_ids:
        raise MealPlanPersistenceConflictError("A past event id was reused.")
    old_servings_by_event = {}
    new_servings_by_event = {}
    for row in prior.servings:
        old_servings_by_event.setdefault(row.event_id, {})[row.member_id] = row
    for row in new.servings:
        new_servings_by_event.setdefault(row.event_id, {})[row.member_id] = row
    old_composed = {c.event_id: c for c in prior.compositions}
    new_composed = {c.event_id: c for c in new.compositions}
    target_seen = 0
    for slot, old in old_slots.items():
        fresh = new_slots[slot]
        if old.id == target_prior_event_id:
            target_seen += 1
            if (
                old.source_kind is not MealSourceKind.COOK_RECIPE
                or fresh.source_kind is not MealSourceKind.COOK_COMPOSITION
                or fresh.recipe_version_id is not None
                or fresh.source_reference is not None
                or fresh.id not in new_composed
                or fresh.id in new_servings_by_event
                or {s.member_id for s in new_composed[fresh.id].servings}
                != set(old_servings_by_event.get(old.id, {}))
            ):
                raise MealPlanPersistenceConflictError("Target composite meal changed attendance.")
            continue
        if (
            fresh.role != old.role
            or fresh.source_kind != old.source_kind
            or fresh.recipe_version_id != old.recipe_version_id
            or fresh.source_reference != old.source_reference
        ):
            raise MealPlanPersistenceConflictError("An unrelated meal was changed.")
        old_rows = old_servings_by_event.get(old.id, {})
        new_rows = new_servings_by_event.get(fresh.id, {})
        if set(old_rows) != set(new_rows) or any(
            old_rows[mid].portion_servings != new_rows[mid].portion_servings
            or old_rows[mid].id == new_rows[mid].id
            for mid in old_rows
        ):
            raise MealPlanPersistenceConflictError("An unrelated Serving was changed.")
        old_comp = old_composed.get(old.id)
        new_comp = new_composed.get(fresh.id)
        if (old_comp is None) != (new_comp is None):
            raise MealPlanPersistenceConflictError("An unrelated composed meal was lost.")
        if old_comp is not None:
            if old_comp.rule != new_comp.rule or len(old_comp.components) != len(
                new_comp.components
            ):
                raise MealPlanPersistenceConflictError("Historical course rule changed.")
            old_components = sorted(old_comp.components, key=lambda c: c.position)
            fresh_components = sorted(new_comp.components, key=lambda c: c.position)
            for former, current in zip(old_components, fresh_components):
                if (
                    former.id == current.id
                    or former.position != current.position
                    or former.course != current.course
                    or former.recipe_version_id != current.recipe_version_id
                ):
                    raise MealPlanPersistenceConflictError("Historical component changed.")
                old_member_amounts = {
                    s.member_id: s.portion_servings
                    for s in old_comp.servings if s.component_id == former.id
                }
                fresh_member_amounts = {
                    s.member_id: s.portion_servings
                    for s in new_comp.servings if s.component_id == current.id
                }
                if old_member_amounts != fresh_member_amounts:
                    raise MealPlanPersistenceConflictError("Historical component Serving changed.")
    if target_seen != 1 or len(new_composed) != len(old_composed) + 1:
        raise MealPlanPersistenceConflictError("Exactly one event must be replaced.")
