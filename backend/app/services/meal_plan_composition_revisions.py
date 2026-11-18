"""Internal-only complete-week diagnostic composition revision constructor.

No API/Planner caller is registered. The immutable previous revision is
read, matched to accepted member schedules, and cloned as a FULL week.
Only the target source-recipe event changes into a composed diagnostic event.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from datetime import datetime
from uuid import UUID, uuid4

from app.domain.errors import DomainValidationError
from app.domain.food_ingredients import normalize_allergen_code
from app.domain.meal_compositions import (
    COMPOSITION_ADMISSION,
    DraftMealStructureRule,
    MealEventCompositionDraft,
    PersistedMealComponent,
    PersistedMealEventComposition,
    PersistedMemberComponentServing,
    assert_complete_revision_preservation,
    rule_snapshot_digest,
    validate_composition_draft,
)
from app.domain.meal_plans import (
    MealPlanDetail,
    MealPlanStatus,
    MealSourceKind,
    MemberMealPatternSelectionDetail,
    validate_complete_plan,
)
from app.services.meal_plan_contracts import (
    DiagnosticRecipeFacts,
    MealPlanPersistenceConflictError,
    MealPlanUnitOfWork,
)

IdFactory = Callable[[], UUID]


def _is_normalized_allergen(code: object) -> bool:
    if not isinstance(code, str):
        return False
    try:
        return normalize_allergen_code(code) == code
    except DomainValidationError:
        return False


def persist_diagnostic_composition_revision(
    uow: MealPlanUnitOfWork,
    detail: MealPlanDetail,
    *,
    excluded_food_codes_by_member: dict[UUID, frozenset[str]],
    excluded_allergen_codes_by_member: dict[UUID, frozenset[str]],
) -> None:
    """Validate a synthetic complete-week revision and insert in ONE active UoW.

    The repository supplies pinned database facts only. Admission decisions are
    service/domain-owned; this helper never commits and has no API/Planner route.
    """
    if (
        detail.plan.status is not MealPlanStatus.DRAFT
        or not detail.compositions
        or detail.plan.supersedes_plan_id is None
    ):
        raise MealPlanPersistenceConflictError(
            "Only complete diagnostic DRAFT revisions are supported."
        )
    previous = uow.plans.get_current(
        detail.plan.household_id, detail.plan.week_start
    )
    if previous is None or previous.plan.id != detail.plan.supersedes_plan_id:
        raise MealPlanPersistenceConflictError(
            "Composition revision must supersede exact current plan."
        )
    try:
        target_events = {
            event.id
            for event in detail.events
            if event.source_kind is MealSourceKind.COOK_COMPOSITION
        }
        if len(target_events) != len(previous.compositions) + 1:
            raise MealPlanPersistenceConflictError(
                "Exactly one additional composed event is required."
            )
        old_slots = {
            (event.local_date, event.position): event for event in previous.events
        }
        new_slots = {
            (event.local_date, event.position): event for event in detail.events
        }
        targets = [
            prior.id
            for slot, prior in old_slots.items()
            if prior.source_kind is MealSourceKind.COOK_RECIPE
            and slot in new_slots
            and new_slots[slot].source_kind is MealSourceKind.COOK_COMPOSITION
        ]
        if len(targets) != 1:
            raise MealPlanPersistenceConflictError(
                "Missing exactly one original recipe-backed target."
            )
        assert_complete_revision_preservation(previous, detail, targets[0])
        accepted = {
            pin.selection_id: uow.selections.get_detail(
                detail.plan.household_id, pin.selection_id
            )
            for pin in detail.member_selections
        }
        if any(value is None for value in accepted.values()):
            raise MealPlanPersistenceConflictError(
                "Missing accepted pinned member selection."
            )
        validate_complete_plan(detail, accepted)
    except DomainValidationError as exc:
        raise MealPlanPersistenceConflictError(
            "Incomplete/changed source week or member meal-pattern coverage."
        ) from exc

    pinned_members = {pin.member_id for pin in detail.member_selections}
    if set(excluded_food_codes_by_member) != pinned_members or any(
        not isinstance(codes, frozenset)
        or any(not isinstance(code, str) or not code for code in codes)
        for codes in excluded_food_codes_by_member.values()
    ):
        raise MealPlanPersistenceConflictError(
            "Explicit synthetic participant exclusions are required."
        )
    if set(excluded_allergen_codes_by_member) != pinned_members or any(
        not isinstance(codes, frozenset)
        or any(not _is_normalized_allergen(code) for code in codes)
        for codes in excluded_allergen_codes_by_member.values()
    ):
        raise MealPlanPersistenceConflictError(
            "Explicit normalized allergen exclusions are required for every participant."
        )

    identities = {(comp.rule.code, comp.rule.version) for comp in detail.compositions}
    rule_hashes = uow.plans.get_diagnostic_rule_digests(identities)
    source_ids = {
        part.recipe_version_id
        for comp in detail.compositions
        for part in comp.components
    }
    recipes = uow.plans.get_diagnostic_recipe_facts(source_ids)
    for comp in detail.compositions:
        if comp.admission_status != COMPOSITION_ADMISSION:
            raise MealPlanPersistenceConflictError("No published composition rule.")
        digest = rule_snapshot_digest(comp.rule)
        if any(
            saved != digest
            for saved in rule_hashes.get((comp.rule.code, comp.rule.version), ())
        ):
            raise MealPlanPersistenceConflictError(
                "Changed rule requirements under the same code/version."
            )
        for part in comp.components:
            facts: DiagnosticRecipeFacts | None = recipes.get(part.recipe_version_id)
            if (
                facts is None
                or facts.verification_status != "SOURCE_VERIFIED"
                or facts.rights_review_status != "REVIEWED"
                or not facts.source_document_sha256
            ):
                raise MealPlanPersistenceConflictError(
                    "Component RecipeVersion is not source/right verified."
                )
            if not facts.is_active:
                raise MealPlanPersistenceConflictError(
                    "Component source Recipe is not active."
                )
            if not facts.ingredients or any(
                ingredient.optional
                or not ingredient.is_active
                or ingredient.unit != ingredient.default_unit
                or ingredient.quantity <= 0
                for ingredient in facts.ingredients
            ):
                raise MealPlanPersistenceConflictError(
                    "Component FoodIngredient source/unit is not verified."
                )
            if any(not ingredient.allergens_reviewed for ingredient in facts.ingredients):
                raise MealPlanPersistenceConflictError(
                    "Component ingredient allergen review is incomplete."
                )
            if any(
                not _is_normalized_allergen(code)
                for ingredient in facts.ingredients
                for code in ingredient.allergen_codes
            ):
                raise MealPlanPersistenceConflictError(
                    "Component ingredient allergen catalogue contains invalid codes."
                )
            present_foods = {ingredient.canonical_code for ingredient in facts.ingredients}
            present_allergens = {
                code
                for ingredient in facts.ingredients
                for code in ingredient.allergen_codes
            }
            for serving in comp.servings:
                if serving.component_id != part.id:
                    continue
                if present_foods & excluded_food_codes_by_member[serving.member_id]:
                    raise MealPlanPersistenceConflictError(
                        "Member hard food exclusion violated by a component."
                    )
                if present_allergens & excluded_allergen_codes_by_member[serving.member_id]:
                    raise MealPlanPersistenceConflictError(
                        "Member hard allergen exclusion violated by a component."
                    )
    uow.plans.add_validated_diagnostic_detail(detail)


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
            sorted(
                composition_rows,
                key=lambda comp: (
                    next(e.local_date for e in events if e.id == comp.event_id),
                    next(e.position for e in events if e.id == comp.event_id),
                ),
            )
        ),
    )
    validate_complete_plan(detail, selection_details)
    assert_complete_revision_preservation(prior, detail, proposal.event_id)
    return detail
