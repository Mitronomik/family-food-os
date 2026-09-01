from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest

from app.domain.households import Household, HouseholdMember
from app.services.households import (
    HouseholdMemberNotFoundError,
    HouseholdService,
)

NOW = datetime(2026, 9, 1, 10, 0, tzinfo=timezone.utc)


@dataclass
class MemoryStore:
    households: dict[UUID, Household] = field(default_factory=dict)
    members: dict[tuple[UUID, UUID], HouseholdMember] = field(default_factory=dict)


class MemoryHouseholdRepository:
    def __init__(self, households):
        self.households = households

    def add_household(self, household):
        self.households[household.id] = household

    def get_household(self, household_id):
        return self.households.get(household_id)

    def update_household(self, household):
        self.households[household.id] = household


class MemoryMemberRepository:
    def __init__(self, members, *, fail_after_add=False):
        self.members = members
        self.fail_after_add = fail_after_add

    def add_member(self, member):
        self.members[(member.household_id, member.id)] = member
        if self.fail_after_add:
            raise RuntimeError("simulated repository failure")

    def get_member(self, household_id, member_id):
        return self.members.get((household_id, member_id))

    def list_members(self, household_id):
        return [
            member
            for (owner_id, _), member in self.members.items()
            if owner_id == household_id
        ]

    def update_member(self, member):
        self.members[(member.household_id, member.id)] = member


class MemoryWriteScope:
    def __init__(self, store, record, *, fail_after_add=False):
        self.store = store
        self.record = record
        self.working_households = dict(store.households)
        self.working_members = dict(store.members)
        self.households = MemoryHouseholdRepository(self.working_households)
        self.members = MemoryMemberRepository(
            self.working_members, fail_after_add=fail_after_add
        )
        self.completed = False
        self.committed = False
        self.rolled_back = False

    def __enter__(self):
        self.record.append(self)
        return self

    def commit(self):
        self.store.households = self.working_households
        self.store.members = self.working_members
        self.completed = True
        self.committed = True

    def rollback(self):
        self.completed = True
        self.rolled_back = True

    def __exit__(self, exc_type, exc_value, traceback):
        if not self.completed:
            self.rollback()


class MemoryReadScope:
    def __init__(self, store):
        self.households = MemoryHouseholdRepository(store.households)
        self.members = MemoryMemberRepository(store.members)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return None


def service(store, scopes, ids, *, fail_after_add=False):
    id_values = iter(ids)
    clock_values = iter([NOW + timedelta(minutes=i) for i in range(20)])
    return HouseholdService(
        write_scope_factory=lambda: MemoryWriteScope(
            store, scopes, fail_after_add=fail_after_add
        ),
        read_scope_factory=lambda: MemoryReadScope(store),
        id_factory=lambda: next(id_values),
        clock=lambda: next(clock_values),
    )


def test_application_create_add_update_and_complete_read_commit_explicitly():
    store = MemoryStore()
    scopes = []
    household_id, member_id = uuid4(), uuid4()
    application = service(store, scopes, [household_id, member_id])

    created = application.create_household(name="Home", timezone_name="Europe/Moscow")
    added = application.add_household_member(
        created.id,
        name="Anna",
        activity_level="moderate",
        goal="maintain",
    )
    updated_household = application.update_household(
        created.id, {"name": "Updated Home"}
    )
    updated_member = application.update_household_member(
        created.id, added.id, {"active": False}
    )
    state = application.get_household(created.id)

    assert [scope.committed for scope in scopes] == [True, True, True, True]
    assert [scope.rolled_back for scope in scopes] == [False, False, False, False]
    assert updated_household.name == "Updated Home"
    assert updated_member.active is False
    assert state.household == updated_household
    assert state.members == (updated_member,)


def test_application_failure_rolls_back_partial_repository_state():
    store = MemoryStore()
    scopes = []
    household_id, member_id = uuid4(), uuid4()
    normal = service(store, scopes, [household_id])
    household = normal.create_household(name="Home", timezone_name="UTC")

    failing = service(
        store,
        scopes,
        [member_id],
        fail_after_add=True,
    )
    with pytest.raises(RuntimeError, match="simulated repository failure"):
        failing.add_household_member(
            household.id,
            name="Anna",
            activity_level="moderate",
            goal="maintain",
        )

    assert store.members == {}
    assert scopes[-1].committed is False
    assert scopes[-1].rolled_back is True


def test_application_member_lookup_never_crosses_household_boundary():
    store = MemoryStore()
    scopes = []
    household_a, household_b, member_id = uuid4(), uuid4(), uuid4()
    application = service(store, scopes, [household_a, household_b, member_id])
    first = application.create_household(name="A", timezone_name="UTC")
    second = application.create_household(name="B", timezone_name="UTC")
    member = application.add_household_member(
        first.id,
        name="Anna",
        activity_level="moderate",
        goal="maintain",
    )

    with pytest.raises(HouseholdMemberNotFoundError):
        application.update_household_member(second.id, member.id, {"active": False})

    assert store.members[(first.id, member.id)].active is True
