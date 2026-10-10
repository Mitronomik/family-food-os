"""Immutable Shopping snapshots: scoped Core readers and atomic inserts."""

from dataclasses import asdict
from uuid import UUID

from sqlalchemy import insert, select
from sqlalchemy.engine import Connection
from sqlalchemy.exc import DBAPIError, IntegrityError, OperationalError

from app.domain.shopping_lists import (
    ShoppingList,
    ShoppingListDetail,
    ShoppingListItem,
    ShoppingUnresolvedObligation,
)
from app.persistence.sqlalchemy_core.shopping_tables import (
    shopping_list_items_table as items,
)
from app.persistence.sqlalchemy_core.shopping_tables import (
    shopping_lists_table as lists,
)
from app.persistence.sqlalchemy_core.shopping_tables import (
    shopping_unresolved_obligations_table as unresolved,
)
from app.persistence.sqlalchemy_core.sqlite_errors import is_sqlite_concurrency_conflict
from app.services.shopping_contracts import (
    ShoppingPersistenceConflictError,
    ShoppingPersistenceError,
)


class SqlAlchemyShoppingListRepository:
    def __init__(self, connection: Connection) -> None:
        self._connection = connection

    def add_detail(self, detail: ShoppingListDetail) -> None:
        header = detail.shopping_list
        if any(
            row.shopping_list_id != header.id or row.household_id != header.household_id
            for row in (*detail.items, *detail.unresolved)
        ):
            raise ValueError("Shopping children must belong to one Household list")
        try:
            self._connection.execute(insert(lists).values(**asdict(header)))
            if detail.items:
                self._connection.execute(
                    insert(items), [asdict(row) for row in detail.items]
                )
            if detail.unresolved:
                self._connection.execute(
                    insert(unresolved), [asdict(row) for row in detail.unresolved]
                )
        except IntegrityError as exc:
            # The UoW owns rollback; callers must not see driver exceptions.
            raise ShoppingPersistenceConflictError(
                "Невозможно сохранить список покупок: конфликт ограничений данных."
            ) from exc
        except OperationalError as exc:
            if is_sqlite_concurrency_conflict(exc):
                raise ShoppingPersistenceConflictError(
                    "Запись списка покупок занята; повторите попытку."
                ) from exc
            raise ShoppingPersistenceError(
                "Не удалось сохранить список покупок."
            ) from exc
        except DBAPIError as exc:
            raise ShoppingPersistenceError(
                "Не удалось сохранить список покупок."
            ) from exc

    def get_detail(
        self, household_id: UUID, list_id: UUID
    ) -> ShoppingListDetail | None:
        header = (
            self._connection.execute(
                select(lists).where(
                    lists.c.id == list_id, lists.c.household_id == household_id
                )
            )
            .mappings()
            .one_or_none()
        )
        if header is None:
            return None
        stored_items = (
            self._connection.execute(
                select(items)
                .where(
                    items.c.shopping_list_id == list_id,
                    items.c.household_id == household_id,
                )
                .order_by(items.c.ordinal)
            )
            .mappings()
            .all()
        )
        stored_unresolved = (
            self._connection.execute(
                select(unresolved)
                .where(
                    unresolved.c.shopping_list_id == list_id,
                    unresolved.c.household_id == household_id,
                )
                .order_by(unresolved.c.ordinal)
            )
            .mappings()
            .all()
        )
        return ShoppingListDetail(
            ShoppingList(**header),
            tuple(ShoppingListItem(**row) for row in stored_items),
            tuple(ShoppingUnresolvedObligation(**row) for row in stored_unresolved),
        )

    def get_by_source(
        self, household_id: UUID, plan_id: UUID, fingerprint: str
    ) -> ShoppingListDetail | None:
        uid = self._connection.scalar(
            select(lists.c.id).where(
                lists.c.household_id == household_id,
                lists.c.meal_plan_id == plan_id,
                lists.c.source_fingerprint == fingerprint,
            )
        )
        return None if uid is None else self.get_detail(household_id, uid)

    def _history_ids(self, household_id: UUID, plan_id: UUID) -> list[UUID]:
        """Follow immutable supersedes links, never a random UUID/timestamp tie."""
        rows = (
            self._connection.execute(
                select(lists.c.id, lists.c.supersedes_list_id).where(
                    lists.c.household_id == household_id,
                    lists.c.meal_plan_id == plan_id,
                )
            )
            .mappings()
            .all()
        )
        if not rows:
            return []
        children: dict[UUID, UUID] = {}
        roots: list[UUID] = []
        for row in rows:
            parent = row["supersedes_list_id"]
            if parent is None:
                roots.append(row["id"])
            elif parent in children:
                raise ShoppingPersistenceError("Shopping successor history has a fork")
            else:
                children[parent] = row["id"]
        if len(roots) != 1:
            raise ShoppingPersistenceError(
                "Shopping successor history has no unique root"
            )
        result: list[UUID] = []
        seen: set[UUID] = set()
        current = roots[0]
        while current is not None:
            if current in seen:
                raise ShoppingPersistenceError("Shopping successor history has a cycle")
            seen.add(current)
            result.append(current)
            current = children.get(current)
        if len(seen) != len(rows):
            raise ShoppingPersistenceError("Shopping successor history is disconnected")
        return result

    def get_latest_for_plan(
        self, household_id: UUID, plan_id: UUID
    ) -> ShoppingListDetail | None:
        ids = self._history_ids(household_id, plan_id)
        return None if not ids else self.get_detail(household_id, ids[-1])

    def list_history(
        self, household_id: UUID, plan_id: UUID
    ) -> list[ShoppingListDetail]:
        return [
            detail
            for uid in self._history_ids(household_id, plan_id)
            if (detail := self.get_detail(household_id, uid)) is not None
        ]
