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
    assert_complete_revision_preservation,
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
