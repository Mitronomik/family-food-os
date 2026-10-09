"""Immutable Shopping snapshots: scoped Core readers and atomic inserts."""
from dataclasses import asdict
from uuid import UUID

from sqlalchemy import insert, select
from sqlalchemy.engine import Connection

from app.domain.shopping_lists import (
    ShoppingList,
    ShoppingListDetail,
    ShoppingListItem,
    ShoppingUnresolvedObligation,
)
from app.persistence.sqlalchemy_core.shopping_tables import (
    shopping_list_items_table as items,
    shopping_lists_table as lists,
    shopping_unresolved_obligations_table as unresolved,
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
        self._connection.execute(insert(lists).values(**asdict(header)))
        if detail.items:
            self._connection.execute(
                insert(items), [asdict(row) for row in detail.items]
            )
        if detail.unresolved:
            self._connection.execute(
                insert(unresolved), [asdict(row) for row in detail.unresolved]
            )

    def get_detail(
        self, household_id: UUID, list_id: UUID
    ) -> ShoppingListDetail | None:
        header = (
            self._connection.execute(
                select(lists).where(
                    lists.c.id == list_id, lists.c.household_id == household_id
                )
            ).mappings().one_or_none()
        )
        if header is None:
            return None
        stored_items = self._connection.execute(
            select(items).where(
                items.c.shopping_list_id == list_id,
                items.c.household_id == household_id,
            ).order_by(items.c.ordinal)
        ).mappings().all()
        stored_unresolved = self._connection.execute(
            select(unresolved).where(
                unresolved.c.shopping_list_id == list_id,
                unresolved.c.household_id == household_id,
            ).order_by(unresolved.c.ordinal)
        ).mappings().all()
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

    def get_latest_for_plan(
        self, household_id: UUID, plan_id: UUID
    ) -> ShoppingListDetail | None:
        uid = self._connection.scalar(
            select(lists.c.id).where(
                lists.c.household_id == household_id,
                lists.c.meal_plan_id == plan_id,
            ).order_by(lists.c.created_at.desc(), lists.c.id.desc()).limit(1)
        )
        return None if uid is None else self.get_detail(household_id, uid)

    def list_history(
        self, household_id: UUID, plan_id: UUID
    ) -> list[ShoppingListDetail]:
        ids = self._connection.scalars(
            select(lists.c.id).where(
                lists.c.household_id == household_id,
                lists.c.meal_plan_id == plan_id,
            ).order_by(lists.c.created_at, lists.c.id)
        ).all()
        return [
            detail for uid in ids
            if (detail := self.get_detail(household_id, uid)) is not None
        ]
