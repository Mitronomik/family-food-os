"""SQLAlchemy Core repositories for Household MealPlan / Serving state."""

from collections.abc import Mapping
from datetime import date
from typing import Any
from uuid import UUID

from sqlalchemy import insert, select
from sqlalchemy.engine import Connection
from sqlalchemy.exc import DBAPIError, IntegrityError

from app.domain.meal_plans import (
    HouseholdMealEvent,
    MealPlan,
    MealPlanDetail,
    MealPlanMemberSelection,
    MemberMealPatternOpportunitySnapshot,
    MemberMealPatternSelection,
    MemberMealPatternSelectionDetail,
    Serving,
)
from app.persistence.sqlalchemy_core.household_tables import household_members_table
from app.persistence.sqlalchemy_core.meal_plan_tables import (
    meal_plan_events_table,
    meal_plan_member_selections_table,
    meal_plans_table,
    member_meal_pattern_opportunities_table,
    member_meal_pattern_selections_table,
    servings_table,
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
    def __init__(self, connection: Connection) -> None:
        self._connection = connection

    def add_detail(self, detail: MealPlanDetail) -> None:
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
        except IntegrityError as exc:
            raise MealPlanPersistenceConflictError(
                "MealPlan revision identity, order, source, or Serving conflicts."
            ) from exc
        except DBAPIError as exc:
            raise MealPlanPersistenceError("MealPlan persistence failed.") from exc

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
        return MealPlanDetail(
            plan=_plan_from_row(row),
            member_selections=tuple(_pin_from_row(item) for item in pins),
            events=tuple(_event_from_row(item) for item in events),
            servings=tuple(_serving_from_row(item) for item in servings),
        )


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
    }


def _opportunity_from_row(
    row: Mapping[str, Any],
) -> MemberMealPatternOpportunitySnapshot:
    return MemberMealPatternOpportunitySnapshot(
        selection_id=row["selection_id"],
        weekday=row["weekday"],
        position=row["position"],
        role=row["role_code"],
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
