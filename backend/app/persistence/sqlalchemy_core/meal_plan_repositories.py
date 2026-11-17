"""SQLAlchemy Core repositories for Household MealPlan / Serving state."""

from collections.abc import Mapping
from datetime import date
from typing import Any
from uuid import UUID

from sqlalchemy import insert, select
from sqlalchemy.engine import Connection
from sqlalchemy.exc import DBAPIError, IntegrityError, OperationalError

from app.domain.errors import DomainValidationError
from app.domain.meal_compositions import (
    COMPOSITION_ADMISSION,
    PersistedMealComponent,
    PersistedMealEventComposition,
    PersistedMemberComponentServing,
    assert_complete_revision_preservation,
    restore_rule_snapshot,
    rule_snapshot_digest,
    serialized_requirements,
)
from app.domain.meal_plans import (
    HouseholdMealEvent,
    MealPlan,
    MealPlanDetail,
    MealPlanStatus,
    MealSourceKind,
    MealPlanMemberReferenceMethodologyPin,
    MealPlanMemberSelection,
    MemberMealPatternOpportunitySnapshot,
    MemberMealPatternSelection,
    MemberMealPatternSelectionDetail,
    Serving,
    validate_complete_plan,
)
from app.persistence.sqlalchemy_core.food_ingredient_tables import food_ingredients_table
from app.persistence.sqlalchemy_core.food_recipe_tables import (
    food_recipe_ingredients_table,
    food_recipe_versions_table,
    food_recipes_table,
)
from app.persistence.sqlalchemy_core.household_tables import household_members_table
from app.persistence.sqlalchemy_core.meal_plan_tables import (
    meal_plan_component_servings_table,
    meal_plan_event_components_table,
    meal_plan_event_compositions_table,
    meal_plan_events_table,
    meal_plan_member_reference_methodology_pins_table,
    meal_plan_member_selections_table,
    meal_plans_table,
    member_meal_pattern_opportunities_table,
    member_meal_pattern_selections_table,
    servings_table,
)
from app.persistence.sqlalchemy_core.reference_methodology_tables import (
    member_reference_methodology_selections_table,
)
from app.persistence.sqlalchemy_core.sqlite_errors import (
    is_sqlite_concurrency_conflict,
)
from app.services.meal_plan_contracts import (
    MealPlanPersistenceConflictError,
    MealPlanPersistenceError,
)


class SqlAlchemyMemberMealPatternSelectionRepository:
    def __init__(self, connection: Connection) -> None:
        self._connection = connection

    def add_detail(self, detail: MemberMealPatternSelectionDetail) -> None:
        selection = detail.selection
        member_household = self._connection.scalar(
            select(household_members_table.c.household_id).where(
                household_members_table.c.id == selection.member_id
            )
        )
        if member_household != selection.household_id:
            raise MealPlanPersistenceConflictError(
                "Meal-pattern selection member must belong to the selection Household."
            )
        if selection.version_number == 1:
            if selection.supersedes_selection_id is not None:
                raise MealPlanPersistenceConflictError(
                    "Selection version 1 must not supersede another selection."
                )
        elif selection.supersedes_selection_id is None:
            raise MealPlanPersistenceConflictError(
                "Selection revisions after version 1 require the previous selection."
            )
        if selection.supersedes_selection_id is not None:
            previous = (
                self._connection.execute(
                    select(member_meal_pattern_selections_table).where(
                        member_meal_pattern_selections_table.c.id
                        == selection.supersedes_selection_id
                    )
                )
                .mappings()
                .one_or_none()
            )
            if (
                previous is None
                or previous["household_id"] != selection.household_id
                or previous["member_id"] != selection.member_id
                or previous["version_number"] != selection.version_number - 1
            ):
                raise MealPlanPersistenceConflictError(
                    "supersedes_selection_id must reference the immediately previous selection version."
                )
        try:
            self._connection.execute(
                insert(member_meal_pattern_selections_table).values(
                    **_selection_values(selection)
                )
            )
            self._connection.execute(
                insert(member_meal_pattern_opportunities_table),
                [_opportunity_values(item) for item in detail.opportunities],
            )
        except IntegrityError as exc:
            raise MealPlanPersistenceConflictError(
                "Meal-pattern selection identity, version, schedule, or reference conflicts."
            ) from exc
        except OperationalError as exc:
            if is_sqlite_concurrency_conflict(exc):
                raise MealPlanPersistenceConflictError(
                    "Meal-pattern selection is concurrently being changed."
                ) from exc
            raise MealPlanPersistenceError(
                "Meal-pattern selection persistence failed."
            ) from exc
        except DBAPIError as exc:
            raise MealPlanPersistenceError(
                "Meal-pattern selection persistence failed."
            ) from exc

    def get_detail(
        self, household_id: UUID, selection_id: UUID
    ) -> MemberMealPatternSelectionDetail | None:
        row = (
            self._connection.execute(
                select(member_meal_pattern_selections_table).where(
                    member_meal_pattern_selections_table.c.id == selection_id,
                    member_meal_pattern_selections_table.c.household_id == household_id,
                )
            )
            .mappings()
            .one_or_none()
        )
        return None if row is None else self._detail_from_row(row)

    def get_current(
        self, household_id: UUID, member_id: UUID
    ) -> MemberMealPatternSelectionDetail | None:
        row = (
            self._connection.execute(
                select(member_meal_pattern_selections_table)
                .where(
                    member_meal_pattern_selections_table.c.household_id == household_id,
                    member_meal_pattern_selections_table.c.member_id == member_id,
                )
                .order_by(member_meal_pattern_selections_table.c.version_number.desc())
                .limit(1)
            )
            .mappings()
            .one_or_none()
        )
        return None if row is None else self._detail_from_row(row)

    def list_history(
        self, household_id: UUID, member_id: UUID
    ) -> list[MemberMealPatternSelection]:
        rows = self._connection.execute(
            select(member_meal_pattern_selections_table)
            .where(
                member_meal_pattern_selections_table.c.household_id == household_id,
                member_meal_pattern_selections_table.c.member_id == member_id,
            )
            .order_by(member_meal_pattern_selections_table.c.version_number)
        ).mappings()
        return [_selection_from_row(row) for row in rows]

    def _detail_from_row(
        self, row: Mapping[str, Any]
    ) -> MemberMealPatternSelectionDetail:
        opportunities = self._connection.execute(
            select(member_meal_pattern_opportunities_table)
            .where(
                member_meal_pattern_opportunities_table.c.selection_id == row["id"]
            )
            .order_by(
                member_meal_pattern_opportunities_table.c.weekday,
                member_meal_pattern_opportunities_table.c.position,
            )
        ).mappings()
        return MemberMealPatternSelectionDetail(
            selection=_selection_from_row(row),
            opportunities=tuple(_opportunity_from_row(item) for item in opportunities),
        )


class SqlAlchemyMealPlanRepository:
    def __init__(
        self, connection: Connection, *, allow_internal_composition_write: bool = False
    ) -> None:
        self._connection = connection
        self._allow_composition_write = allow_internal_composition_write

    def add_detail(
        self, detail: MealPlanDetail, *, _diagnostic_composition: bool = False
    ) -> None:
        composite_ids = {
            event.id for event in detail.events
            if event.source_kind is MealSourceKind.COOK_COMPOSITION
        }
        registered_ids = {composition.event_id for composition in detail.compositions}
        if composite_ids != registered_ids:
            raise MealPlanPersistenceConflictError(
                "Each COOK_COMPOSITION event must have exactly one typed composition."
            )
        if composite_ids and not (
            _diagnostic_composition and self._allow_composition_write
        ):
            raise MealPlanPersistenceConflictError(
                "Only the explicitly enabled internal diagnostic writer may save a composite."
            )
        if composite_ids and (
            detail.plan.status is not MealPlanStatus.DRAFT
            or any(serving.event_id in composite_ids for serving in detail.servings)
        ):
            raise MealPlanPersistenceConflictError(
                "Composed events must be DRAFT and cannot carry legacy Servings."
            )
        plan = detail.plan
        for pin in detail.member_selections:
            member_household = self._connection.scalar(
                select(household_members_table.c.household_id).where(
                    household_members_table.c.id == pin.member_id
                )
            )
            selection = (
                self._connection.execute(
                    select(member_meal_pattern_selections_table).where(
                        member_meal_pattern_selections_table.c.id == pin.selection_id
                    )
                )
                .mappings()
                .one_or_none()
            )
            if (
                member_household != plan.household_id
                or selection is None
                or selection["household_id"] != plan.household_id
                or selection["member_id"] != pin.member_id
            ):
                raise MealPlanPersistenceConflictError(
                    "MealPlan member selection pins must remain inside one Household."
                )
        for pin in detail.reference_methodology_pins:
            member_row = (
                self._connection.execute(
                    select(household_members_table).where(
                        household_members_table.c.id == pin.member_id
                    )
                )
                .mappings()
                .one_or_none()
            )
            reference_selection = (
                self._connection.execute(
                    select(member_reference_methodology_selections_table).where(
                        member_reference_methodology_selections_table.c.id
                        == pin.reference_methodology_selection_id
                    )
                )
                .mappings()
                .one_or_none()
            )
            if (
                member_row is None
                or member_row["household_id"] != plan.household_id
                or reference_selection is None
                or reference_selection["household_id"] != plan.household_id
                or reference_selection["member_id"] != pin.member_id
                or reference_selection["accepted_at"] > plan.created_at
            ):
                raise MealPlanPersistenceConflictError(
                    "MealPlan reference-methodology pins must reference an "
                    "accepted selection for the same Household/member."
                )
            snapshot = (
                member_row["birth_date"],
                member_row["sex"],
                member_row["height_cm"],
                member_row["weight_kg"],
                member_row["activity_level"],
                member_row["goal"],
                member_row["updated_at"],
            )
            pin_snapshot = (
                pin.birth_date,
                pin.sex,
                pin.height_cm,
                pin.weight_kg,
                pin.activity_level,
                pin.goal,
                pin.member_updated_at,
            )
            if snapshot != pin_snapshot:
                raise MealPlanPersistenceConflictError(
                    "MealPlan reference-methodology snapshot must match the "
                    "authoritative HouseholdMember state."
                )
        if plan.revision_number == 1:
            if plan.supersedes_plan_id is not None:
                raise MealPlanPersistenceConflictError(
                    "MealPlan revision 1 must not supersede another plan."
                )
        elif plan.supersedes_plan_id is None:
            raise MealPlanPersistenceConflictError(
                "MealPlan revisions after revision 1 require the previous plan."
            )
        if plan.supersedes_plan_id is not None:
            previous = (
                self._connection.execute(
                    select(
                        meal_plans_table.c.household_id,
                        meal_plans_table.c.week_start,
                        meal_plans_table.c.revision_number,
                    ).where(meal_plans_table.c.id == plan.supersedes_plan_id)
                )
                .mappings()
                .one_or_none()
            )
            if (
                previous is None
                or previous["household_id"] != plan.household_id
                or previous["week_start"] != plan.week_start
                or previous["revision_number"] != plan.revision_number - 1
            ):
                raise MealPlanPersistenceConflictError(
                    "supersedes_plan_id must reference the immediately previous MealPlan revision."
                )
        try:
            self._connection.execute(
                insert(meal_plans_table).values(**_plan_values(plan))
            )
            if detail.member_selections:
                self._connection.execute(
                    insert(meal_plan_member_selections_table),
                    [_pin_values(item) for item in detail.member_selections],
                )
            if detail.reference_methodology_pins:
                self._connection.execute(
                    insert(meal_plan_member_reference_methodology_pins_table),
                    [
                        _reference_pin_values(item)
                        for item in detail.reference_methodology_pins
                    ],
                )
            if detail.events:
                self._connection.execute(
                    insert(meal_plan_events_table),
                    [_event_values(item) for item in detail.events],
                )
            if detail.servings:
                self._connection.execute(
                    insert(servings_table),
                    [_serving_values(item) for item in detail.servings],
                )
            if detail.compositions:
                for comp in detail.compositions:
                    self._connection.execute(
                        insert(meal_plan_event_compositions_table).values(
                            event_id=comp.event_id,
                            structure_rule_code=comp.rule.code,
                            structure_rule_version=comp.rule.version,
                            required_coverage=comp.rule.coverage.value,
                            rule_snapshot_schema_version=1,
                            requirements_json=serialized_requirements(comp.rule),
                            rule_snapshot_sha256=rule_snapshot_digest(comp.rule),
                            admission_status=comp.admission_status,
                            created_at=comp.created_at,
                        )
                    )
                    self._connection.execute(
                        insert(meal_plan_event_components_table),
                        [
                            {
                                "id": part.id,
                                "event_id": part.event_id,
                                "position": part.position,
                                "course_kind": part.course.value,
                                "recipe_version_id": part.recipe_version_id,
                                "created_at": part.created_at,
                            }
                            for part in comp.components
                        ],
                    )
                    self._connection.execute(
                        insert(meal_plan_component_servings_table),
                        [
                            {
                                "component_id": item.component_id,
                                "member_id": item.member_id,
                                "portion_servings": item.portion_servings,
                                "created_at": item.created_at,
                            }
                            for item in comp.servings
                        ],
                    )
        except IntegrityError as exc:
            raise MealPlanPersistenceConflictError(
                "MealPlan revision identity, order, source, or Serving conflicts."
            ) from exc
        except DBAPIError as exc:
            raise MealPlanPersistenceError("MealPlan persistence failed.") from exc

    def add_diagnostic_composition_revision(
        self,
        detail: MealPlanDetail,
        *,
        excluded_food_codes_by_member: Mapping[UUID, frozenset[str]],
    ) -> None:
        """Internal synthetic-only write; not wired to API or Planner.

        The explicit exclusions map is a diagnostic fixture input, not a
        substitute for real Household preference / allergy authority.
        """
        if not self._allow_composition_write:
            raise MealPlanPersistenceConflictError(
                "Composition writes are disabled outside internal test UoW."
            )
        if (
            detail.plan.status is not MealPlanStatus.DRAFT
            or not detail.compositions
            or detail.plan.supersedes_plan_id is None
        ):
            raise MealPlanPersistenceConflictError(
                "Only complete diagnostic DRAFT revisions are supported."
            )
        previous = self.get_current(detail.plan.household_id, detail.plan.week_start)
        if previous is None or previous.plan.id != detail.plan.supersedes_plan_id:
            raise MealPlanPersistenceConflictError(
                "Composition revision must supersede exact current plan."
            )
        try:
            target_events = {
                event.id for event in detail.events
                if event.source_kind is MealSourceKind.COOK_COMPOSITION
            }
            old_comp_count = len(previous.compositions)
            if len(target_events) != old_comp_count + 1:
                raise MealPlanPersistenceConflictError(
                    "Exactly one additional composed event is required."
                )
            old_slots = {(e.local_date, e.position): e for e in previous.events}
            new_slots = {(e.local_date, e.position): e for e in detail.events}
            target = [
                old_slots[slot].id for slot, event in new_slots.items()
                if event.source_kind is MealSourceKind.COOK_COMPOSITION
                and old_slots.get(slot) is not None
                and old_slots[slot].source_kind is MealSourceKind.COOK_RECIPE
            ]
            if len(target) != 1:
                raise MealPlanPersistenceConflictError(
                    "Missing exactly one original recipe-backed target."
                )
            assert_complete_revision_preservation(previous, detail, target[0])
            accepted = {
                pin.selection_id: SqlAlchemyMemberMealPatternSelectionRepository(
                    self._connection
                ).get_detail(detail.plan.household_id, pin.selection_id)
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

        pinned_members = {item.member_id for item in detail.member_selections}
        if (
            set(excluded_food_codes_by_member) != pinned_members
            or any(
                not isinstance(codes, frozenset)
                or any(not isinstance(code, str) or not code for code in codes)
                for codes in excluded_food_codes_by_member.values()
            )
        ):
            raise MealPlanPersistenceConflictError(
                "Explicit synthetic participant exclusions are required."
            )
        for comp in detail.compositions:
            if comp.admission_status != COMPOSITION_ADMISSION:
                raise MealPlanPersistenceConflictError("No published composition rule.")
            existing = self._connection.execute(
                select(meal_plan_event_compositions_table.c.rule_snapshot_sha256)
                .where(
                    meal_plan_event_compositions_table.c.structure_rule_code
                    == comp.rule.code,
                    meal_plan_event_compositions_table.c.structure_rule_version
                    == comp.rule.version,
                )
            ).scalars().all()
            current_digest = rule_snapshot_digest(comp.rule)
            if any(sha != current_digest for sha in existing):
                raise MealPlanPersistenceConflictError(
                    "Changed rule requirements under the same code/version."
                )
            for part in comp.components:
                version = (
                    self._connection.execute(
                        select(food_recipe_versions_table)
                        .where(food_recipe_versions_table.c.id == part.recipe_version_id)
                    )
                    .mappings()
                    .one_or_none()
                )
                if (
                    version is None
                    or version["verification_status"] != "SOURCE_VERIFIED"
                    or version["rights_review_status"] != "REVIEWED"
                    or not version["source_document_sha256"]
                ):
                    raise MealPlanPersistenceConflictError(
                        "Component RecipeVersion is not source/right verified."
                    )
                active = self._connection.scalar(
                    select(food_recipes_table.c.is_active)
                    .where(food_recipes_table.c.id == version["recipe_id"])
                )
                if active is not True:
                    raise MealPlanPersistenceConflictError(
                        "Component source Recipe is not active."
                    )
                ingredient_rows = (
                    self._connection.execute(
                        select(
                            food_recipe_ingredients_table.c.food_ingredient_id,
                            food_recipe_ingredients_table.c.unit,
                            food_recipe_ingredients_table.c.quantity,
                            food_recipe_ingredients_table.c.optional,
                            food_ingredients_table.c.default_unit,
                            food_ingredients_table.c.is_active,
                            food_ingredients_table.c.canonical_code,
                        )
                        .join(
                            food_ingredients_table,
                            food_recipe_ingredients_table.c.food_ingredient_id
                            == food_ingredients_table.c.id,
                        )
                        .where(
                            food_recipe_ingredients_table.c.recipe_version_id
                            == part.recipe_version_id
                        )
                    )
                    .mappings()
                    .all()
                )
                if not ingredient_rows or any(
                    row["optional"]
                    or not row["is_active"]
                    or row["unit"] != row["default_unit"]
                    or row["quantity"] <= 0
                    for row in ingredient_rows
                ):
                    raise MealPlanPersistenceConflictError(
                        "Component FoodIngredient source/unit is not verified."
                    )
                for serving in comp.servings:
                    if serving.component_id != part.id:
                        continue
                    excluded = excluded_food_codes_by_member[serving.member_id]
                    if any(row["canonical_code"] in excluded for row in ingredient_rows):
                        raise MealPlanPersistenceConflictError(
                            "Member hard food exclusion violated by a component."
                        )
        # Actual write is one shared UoW transaction; never commit from repository.
        self.add_detail(detail, _diagnostic_composition=True)

    def get_detail(self, household_id: UUID, plan_id: UUID) -> MealPlanDetail | None:
        row = (
            self._connection.execute(
                select(meal_plans_table).where(
                    meal_plans_table.c.id == plan_id,
                    meal_plans_table.c.household_id == household_id,
                )
            )
            .mappings()
            .one_or_none()
        )
        return None if row is None else self._detail_from_row(row)

    def get_current(
        self, household_id: UUID, week_start: date
    ) -> MealPlanDetail | None:
        row = (
            self._connection.execute(
                select(meal_plans_table)
                .where(
                    meal_plans_table.c.household_id == household_id,
                    meal_plans_table.c.week_start == week_start,
                )
                .order_by(meal_plans_table.c.revision_number.desc())
                .limit(1)
            )
            .mappings()
            .one_or_none()
        )
        return None if row is None else self._detail_from_row(row)

    def list_history(self, household_id: UUID, week_start: date) -> list[MealPlan]:
        rows = self._connection.execute(
            select(meal_plans_table)
            .where(
                meal_plans_table.c.household_id == household_id,
                meal_plans_table.c.week_start == week_start,
            )
            .order_by(meal_plans_table.c.revision_number)
        ).mappings()
        return [_plan_from_row(row) for row in rows]

    def _detail_from_row(self, row: Mapping[str, Any]) -> MealPlanDetail:
        plan_id = row["id"]
        pins = self._connection.execute(
            select(meal_plan_member_selections_table)
            .where(meal_plan_member_selections_table.c.plan_id == plan_id)
            .order_by(meal_plan_member_selections_table.c.member_id)
        ).mappings()
        reference_pins = self._connection.execute(
            select(meal_plan_member_reference_methodology_pins_table)
            .where(
                meal_plan_member_reference_methodology_pins_table.c.plan_id
                == plan_id
            )
            .order_by(
                meal_plan_member_reference_methodology_pins_table.c.member_id
            )
        ).mappings()
        events = list(
            self._connection.execute(
                select(meal_plan_events_table)
                .where(meal_plan_events_table.c.plan_id == plan_id)
                .order_by(
                    meal_plan_events_table.c.local_date,
                    meal_plan_events_table.c.position,
                )
            ).mappings()
        )
        event_ids = [event["id"] for event in events]
        servings: list[Mapping[str, Any]] = []
        if event_ids:
            servings = list(
                self._connection.execute(
                    select(servings_table).where(servings_table.c.event_id.in_(event_ids))
                ).mappings()
            )
            event_order = {event_id: index for index, event_id in enumerate(event_ids)}
            servings.sort(
                key=lambda item: (
                    event_order[item["event_id"]],
                    item["member_id"].hex,
                )
            )
        compositions = self._read_compositions(
            event_ids, {event["id"]: event for event in events}
        )
        return MealPlanDetail(
            plan=_plan_from_row(row),
            member_selections=tuple(_pin_from_row(item) for item in pins),
            events=tuple(_event_from_row(item) for item in events),
            servings=tuple(_serving_from_row(item) for item in servings),
            reference_methodology_pins=tuple(
                _reference_pin_from_row(item) for item in reference_pins
            ),
            compositions=compositions,
        )

    def _read_compositions(self, event_ids, events):
        if not event_ids:
            return ()
        headers = (
            self._connection.execute(
                select(meal_plan_event_compositions_table)
                .where(meal_plan_event_compositions_table.c.event_id.in_(event_ids))
                .order_by(meal_plan_event_compositions_table.c.event_id)
            )
            .mappings()
            .all()
        )
        result = []
        for header in headers:
            parent = events.get(header["event_id"])
            if parent is None:
                raise MealPlanPersistenceError("Orphan composed meal header.")
            try:
                rule = restore_rule_snapshot(
                    code=header["structure_rule_code"],
                    version=header["structure_rule_version"],
                    meal_role=parent["role_code"],
                    coverage=header["required_coverage"],
                    schema_version=header["rule_snapshot_schema_version"],
                    requirements_json=header["requirements_json"],
                    sha256_hex=header["rule_snapshot_sha256"],
                )
                parts = (
                    self._connection.execute(
                        select(meal_plan_event_components_table)
                        .where(
                            meal_plan_event_components_table.c.event_id
                            == header["event_id"]
                        )
                        .order_by(meal_plan_event_components_table.c.position)
                    )
                    .mappings()
                    .all()
                )
                components = tuple(
                    PersistedMealComponent(
                        id=part["id"],
                        event_id=part["event_id"],
                        position=part["position"],
                        course=part["course_kind"],
                        recipe_version_id=part["recipe_version_id"],
                        created_at=part["created_at"],
                    )
                    for part in parts
                )
                ids = [item.id for item in components]
                raw_servings = (
                    self._connection.execute(
                        select(meal_plan_component_servings_table)
                        .where(
                            meal_plan_component_servings_table.c.component_id.in_(ids)
                        )
                        .order_by(
                            meal_plan_component_servings_table.c.component_id,
                            meal_plan_component_servings_table.c.member_id,
                        )
                    )
                    .mappings()
                    .all()
                    if ids
                    else []
                )
                # Replay canonical course order, not random component UUID order.
                component_positions = {part.id: part.position for part in components}
                raw_servings = sorted(
                    raw_servings,
                    key=lambda item: (
                        component_positions[item["component_id"]],
                        item["member_id"].hex,
                    ),
                )
                result.append(
                    PersistedMealEventComposition(
                        event_id=header["event_id"],
                        rule=rule,
                        components=components,
                        servings=tuple(
                            PersistedMemberComponentServing(
                                component_id=item["component_id"],
                                member_id=item["member_id"],
                                portion_servings=item["portion_servings"],
                                created_at=item["created_at"],
                            )
                            for item in raw_servings
                        ),
                        created_at=header["created_at"],
                        admission_status=header["admission_status"],
                    )
                )
            except (ValueError, TypeError) as exc:
                raise MealPlanPersistenceError(
                    "Persisted composition rule/servings cannot be replayed."
                ) from exc
        return tuple(result)


def _selection_values(value: MemberMealPatternSelection) -> dict[str, object]:
    return {
        "id": value.id,
        "household_id": value.household_id,
        "member_id": value.member_id,
        "version_number": value.version_number,
        "source_kind": value.source_kind.value,
        "program_version_id": value.program_version_id,
        "recommender_version": value.recommender_version,
        "has_user_overrides": value.has_user_overrides,
        "accepted_at": value.accepted_at,
        "supersedes_selection_id": value.supersedes_selection_id,
        "created_at": value.created_at,
    }


def _selection_from_row(row: Mapping[str, Any]) -> MemberMealPatternSelection:
    return MemberMealPatternSelection(
        id=row["id"],
        household_id=row["household_id"],
        member_id=row["member_id"],
        version_number=row["version_number"],
        source_kind=row["source_kind"],
        program_version_id=row["program_version_id"],
        recommender_version=row["recommender_version"],
        has_user_overrides=row["has_user_overrides"],
        accepted_at=row["accepted_at"],
        supersedes_selection_id=row["supersedes_selection_id"],
        created_at=row["created_at"],
    )


def _opportunity_values(
    value: MemberMealPatternOpportunitySnapshot,
) -> dict[str, object]:
    return {
        "selection_id": value.selection_id,
        "weekday": value.weekday,
        "position": value.position,
        "role_code": value.role.value,
        "energy_share": value.energy_share,
    }


def _opportunity_from_row(
    row: Mapping[str, Any],
) -> MemberMealPatternOpportunitySnapshot:
    return MemberMealPatternOpportunitySnapshot(
        selection_id=row["selection_id"],
        weekday=row["weekday"],
        position=row["position"],
        role=row["role_code"],
        energy_share=row.get("energy_share"),
    )


def _plan_values(value: MealPlan) -> dict[str, object]:
    return {
        "id": value.id,
        "household_id": value.household_id,
        "week_start": value.week_start,
        "revision_number": value.revision_number,
        "status": value.status.value,
        "config_version": value.config_version,
        "supersedes_plan_id": value.supersedes_plan_id,
        "created_at": value.created_at,
    }


def _plan_from_row(row: Mapping[str, Any]) -> MealPlan:
    return MealPlan(
        id=row["id"],
        household_id=row["household_id"],
        week_start=row["week_start"],
        revision_number=row["revision_number"],
        status=row["status"],
        config_version=row["config_version"],
        supersedes_plan_id=row["supersedes_plan_id"],
        created_at=row["created_at"],
    )


def _pin_values(value: MealPlanMemberSelection) -> dict[str, object]:
    return {
        "plan_id": value.plan_id,
        "member_id": value.member_id,
        "selection_id": value.selection_id,
    }


def _pin_from_row(row: Mapping[str, Any]) -> MealPlanMemberSelection:
    return MealPlanMemberSelection(
        plan_id=row["plan_id"],
        member_id=row["member_id"],
        selection_id=row["selection_id"],
    )


def _reference_pin_values(
    value: MealPlanMemberReferenceMethodologyPin,
) -> dict[str, object]:
    return {
        "plan_id": value.plan_id,
        "member_id": value.member_id,
        "reference_methodology_selection_id": (
            value.reference_methodology_selection_id
        ),
        "birth_date": value.birth_date,
        "sex": value.sex,
        "height_cm": value.height_cm,
        "weight_kg": value.weight_kg,
        "activity_level": value.activity_level,
        "goal": value.goal,
        "member_updated_at": value.member_updated_at,
    }


def _reference_pin_from_row(
    row: Mapping[str, Any],
) -> MealPlanMemberReferenceMethodologyPin:
    return MealPlanMemberReferenceMethodologyPin(
        plan_id=row["plan_id"],
        member_id=row["member_id"],
        reference_methodology_selection_id=row[
            "reference_methodology_selection_id"
        ],
        birth_date=row["birth_date"],
        sex=row["sex"],
        height_cm=row["height_cm"],
        weight_kg=row["weight_kg"],
        activity_level=row["activity_level"],
        goal=row["goal"],
        member_updated_at=row["member_updated_at"],
    )


def _event_values(value: HouseholdMealEvent) -> dict[str, object]:
    return {
        "id": value.id,
        "plan_id": value.plan_id,
        "local_date": value.local_date,
        "position": value.position,
        "role_code": value.role.value,
        "source_kind": value.source_kind.value,
        "recipe_version_id": value.recipe_version_id,
        "source_reference": value.source_reference,
        "created_at": value.created_at,
    }


def _event_from_row(row: Mapping[str, Any]) -> HouseholdMealEvent:
    return HouseholdMealEvent(
        id=row["id"],
        plan_id=row["plan_id"],
        local_date=row["local_date"],
        position=row["position"],
        role=row["role_code"],
        source_kind=row["source_kind"],
        recipe_version_id=row["recipe_version_id"],
        source_reference=row["source_reference"],
        created_at=row["created_at"],
    )


def _serving_values(value: Serving) -> dict[str, object]:
    return {
        "id": value.id,
        "event_id": value.event_id,
        "member_id": value.member_id,
        "portion_servings": value.portion_servings,
        "created_at": value.created_at,
    }


def _serving_from_row(row: Mapping[str, Any]) -> Serving:
    return Serving(
        id=row["id"],
        event_id=row["event_id"],
        member_id=row["member_id"],
        portion_servings=row["portion_servings"],
        created_at=row["created_at"],
    )
