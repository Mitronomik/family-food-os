"""PR9-B Shopping application service: consistent snapshots, idempotency and history.

The persistence UoW owns BEGIN IMMEDIATE and every authoritative read.
This module does not import SQLAlchemy, DBAPI connections or table definitions.
"""

import json
from collections.abc import Callable, Mapping
from dataclasses import asdict, is_dataclass
from datetime import date, datetime, timezone
from decimal import Decimal
from enum import Enum
from hashlib import sha256
from uuid import UUID, uuid4

from app.domain.meal_plans import MealSourceKind
from app.domain.shopping_calculation import (
    ShoppingCalculation,
    ShoppingCalculationError,
    calculate_shopping,
)
from app.domain.shopping_lists import (
    ShoppingCurrent,
    ShoppingList,
    ShoppingListDetail,
    ShoppingListItem,
    ShoppingUnresolvedObligation,
)
from app.services.shopping_contracts import (
    ShoppingNotFoundError,
    ShoppingPersistenceConflictError,
    ShoppingReadScope,
    ShoppingUnitOfWork,
)

WriteFactory = Callable[[], ShoppingUnitOfWork]
ReadFactory = Callable[[], ShoppingReadScope]


def _canonical(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return _canonical(asdict(value))
    if isinstance(value, Mapping):
        return {
            str(k): _canonical(v)
            for k, v in sorted(value.items(), key=lambda x: str(x[0]))
        }
    if isinstance(value, (list, tuple)):
        return [_canonical(v) for v in value]
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Enum):
        return str(value.value)
    return value


def _json(value: object) -> str:
    return json.dumps(
        _canonical(value),
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
        allow_nan=False,
    )


def _digest(value: object) -> str:
    return sha256(_json(value).encode("utf-8")).hexdigest()


class ShoppingService:
    def __init__(
        self,
        write_scope_factory: WriteFactory,
        read_scope_factory: ReadFactory,
        *,
        clock: Callable[[], datetime] | None = None,
        id_factory: Callable[[], UUID] = uuid4,
    ) -> None:
        self._write = write_scope_factory
        self._read = read_scope_factory
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._id = id_factory

    def _calculate(
        self,
        scope: ShoppingReadScope,
        household_id: UUID,
        plan_id: UUID,
        captured_at: datetime,
    ) -> tuple[ShoppingCalculation, dict]:
        household = scope.households.get_household(household_id)
        plan = scope.plans.get_detail(household_id, plan_id)
        if household is None or plan is None:
            raise ShoppingNotFoundError("План питания не найден для этой семьи.")
        current = scope.plans.get_current(household_id, plan.plan.week_start)
        if current is None or current.plan.id != plan.plan.id:
            raise ShoppingPersistenceConflictError(
                "План обновился: требуется актуальная ревизия."
            )
        recipes = {}
        food_ids = set()
        for event in plan.events:
            if event.source_kind is MealSourceKind.COOK_RECIPE:
                if event.recipe_version_id is None:
                    raise ShoppingPersistenceConflictError(
                        "Отсутствует закреплённая версия рецепта."
                    )
                detail = scope.recipes.get_detail(event.recipe_version_id)
                if detail is None:
                    raise ShoppingPersistenceConflictError(
                        "Закреплённый рецепт больше недоступен."
                    )
                recipes[event.recipe_version_id] = detail
                food_ids.update(x.food_ingredient_id for x in detail.ingredients)
        foods = {}
        for food_id in sorted(food_ids, key=str):
            ingredient = scope.foods.get(food_id)
            if ingredient is None:
                raise ShoppingPersistenceConflictError(
                    "Канонический ингредиент отсутствует."
                )
            foods[food_id] = ingredient
        pantry = tuple(scope.pantry.list_items(household_id, include_empty=True))
        computed = calculate_shopping(
            plan=plan,
            recipes=recipes,
            foods=foods,
            pantry_items=pantry,
            household_timezone=household.timezone,
            captured_at=captured_at,
        )
        provenance = {
            "schema": "SHOPPING_SOURCE_SNAPSHOT_V1",
            "calculation": {
                "household_id": household_id,
                "plan_id": plan_id,
                "plan_revision": plan.plan.revision_number,
                "config_version": plan.plan.config_version,
                "as_of_date": computed.as_of_date,
                "engine": computed.engine_version,
                "policy": computed.pantry_policy_version,
                "pantry_hash": computed.pantry_snapshot_hash,
                "source_hash": computed.source_fingerprint,
                "content_hash": computed.content_fingerprint,
                "timezone": household.timezone,
            },
            "plan_events": plan.events,
            "servings": plan.servings,
            "recipe_inputs": [
                {
                    "recipe_version_id": k,
                    "version": v.version,
                    "ingredients": v.ingredients,
                }
                for k, v in sorted(recipes.items(), key=lambda x: str(x[0]))
            ],
            "foods": [foods[k] for k in sorted(foods, key=str)],
            "pantry_items": pantry,
            "warnings": computed.warnings,
            "allocations": computed.allocations,
        }
        return computed, provenance

    def generate(self, household_id: UUID, plan_id: UUID) -> ShoppingListDetail:
        captured = self._clock()
        # The write UoW obtains a physical SQLite writer reservation before
        # _calculate reads any source facts or another ShoppingList.
        with self._write() as scope:
            computed, provenance = self._calculate(
                scope, household_id, plan_id, captured
            )
            existing = scope.shopping.get_by_source(
                household_id, plan_id, computed.source_fingerprint
            )
            if existing is not None:
                if (
                    existing.shopping_list.content_fingerprint
                    != computed.content_fingerprint
                ):
                    raise ShoppingPersistenceConflictError(
                        "Повторный Shopping snapshot отличается при тех же входных данных."
                    )
                return existing
            previous = scope.shopping.get_latest_for_plan(household_id, plan_id)
            detail_id = self._id()
            header = ShoppingList(
                id=detail_id,
                household_id=household_id,
                meal_plan_id=plan_id,
                source_plan_revision_number=computed.source_plan_revision_number,
                source_pantry_snapshot_hash=computed.pantry_snapshot_hash,
                as_of_date=computed.as_of_date,
                engine_version=computed.engine_version,
                pantry_policy_version=computed.pantry_policy_version,
                config_fingerprint=_digest(
                    [
                        plan_id,
                        provenance["calculation"]["config_version"],
                        computed.engine_version,
                        computed.pantry_policy_version,
                    ]
                ),
                source_fingerprint=computed.source_fingerprint,
                content_fingerprint=computed.content_fingerprint,
                status=computed.status,
                price_status=computed.price_status,
                provenance_json=_json(provenance),
                supersedes_list_id=previous.shopping_list.id if previous else None,
                created_at=captured,
            )
            items = tuple(
                ShoppingListItem(
                    id=self._id(),
                    shopping_list_id=detail_id,
                    household_id=household_id,
                    food_ingredient_id=row.food_ingredient_id,
                    form_basis=row.form_basis,
                    unit=row.unit,
                    required_quantity=row.required_quantity,
                    pantry_available_quantity=row.pantry_available_quantity,
                    purchase_quantity=row.purchase_quantity,
                    ordinal=i,
                )
                for i, row in enumerate(computed.items, 1)
            )
            obligations = tuple(
                ShoppingUnresolvedObligation(
                    id=self._id(),
                    shopping_list_id=detail_id,
                    household_id=household_id,
                    meal_event_id=row.meal_event_id,
                    source_kind=row.source_kind,
                    reason=row.reason,
                    ordinal=i,
                )
                for i, row in enumerate(computed.unresolved, 1)
            )
            detail = ShoppingListDetail(header, items, obligations)
            scope.shopping.add_detail(detail)
            # Validate against same locked source revision before one commit.
            again = scope.plans.get_detail(household_id, plan_id)
            if (
                again is None
                or again.plan.revision_number != header.source_plan_revision_number
            ):
                raise ShoppingPersistenceConflictError(
                    "Ревизия плана изменилась во время сохранения."
                )
            scope.commit()
            return detail

    def get_detail(self, household_id: UUID, list_id: UUID) -> ShoppingListDetail:
        with self._read() as scope:
            detail = scope.shopping.get_detail(household_id, list_id)
            if detail is None:
                raise ShoppingNotFoundError("Список покупок не найден.")
            return detail

    def list_history(
        self, household_id: UUID, plan_id: UUID
    ) -> list[ShoppingListDetail]:
        with self._read() as scope:
            if scope.plans.get_detail(household_id, plan_id) is None:
                raise ShoppingNotFoundError("План питания не найден.")
            return scope.shopping.list_history(household_id, plan_id)

    def get_current(self, household_id: UUID, plan_id: UUID) -> ShoppingCurrent:
        captured = self._clock()
        with self._read() as scope:
            plan = scope.plans.get_detail(household_id, plan_id)
            if plan is None:
                raise ShoppingNotFoundError("План питания не найден.")
            latest = scope.shopping.get_latest_for_plan(household_id, plan_id)
            if latest is None:
                return ShoppingCurrent(None, False, "MISSING")
            try:
                calculated, _ = self._calculate(scope, household_id, plan_id, captured)
            except ShoppingPersistenceConflictError:
                return ShoppingCurrent(latest, True, "PLAN_REVISION_CHANGED")
            except ShoppingCalculationError:
                # The original derived snapshot stays readable even if a
                # later catalogue/recipe edit makes recalculation fail closed.
                return ShoppingCurrent(latest, True, "SOURCE_INVALID")
            # Input equality, not insertion order, determines CURRENT. If
            # Pantry returns to an earlier exact snapshot, its original
            # immutable list can be current again without duplicating rows.
            matching = scope.shopping.get_by_source(
                household_id, plan_id, calculated.source_fingerprint
            )
            if matching is not None:
                stored = matching.shopping_list
                matches = (
                    stored.source_pantry_snapshot_hash == calculated.pantry_snapshot_hash
                    and stored.as_of_date == calculated.as_of_date
                    and stored.content_fingerprint == calculated.content_fingerprint
                    and stored.engine_version == calculated.engine_version
                    and stored.pantry_policy_version == calculated.pantry_policy_version
                )
                if matches:
                    return ShoppingCurrent(matching, False, None)
            return ShoppingCurrent(latest, True, "SOURCE_CHANGED")

    def regenerate(self, household_id: UUID, plan_id: UUID) -> ShoppingListDetail:
        return self.generate(household_id, plan_id)
