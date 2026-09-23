from dataclasses import dataclass, field, replace
from datetime import date, datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest

from app.domain.households import Household, HouseholdMember
from app.domain.reference_methodology import MemberReferenceMethodologySelection
from app.seed.russian_reference_table_step5 import russian_reference_table_provider
from app.services.reference_methodology import (
    BASELINE_NUTRITION_CONFIG_VERSION,
    RUSSIAN_GROUP_REFERENCE_VERSION,
    ReferenceMethodologyConflictError,
    ReferenceMethodologyService,
    ReferenceMethodologyUnsupportedError,
)
from app.services.reference_methodology_contracts import (
    ReferenceMethodologyPersistenceConflictError,
)


NOW = datetime(2026, 9, 23, 9, 0, tzinfo=timezone.utc)


def household(household_id: UUID) -> Household:
    return Household(
        id=household_id,
        name="Home",
        timezone="Europe/Moscow",
        city=None,
        default_weekly_budget=None,
        default_cooking_profile=None,
        created_at=NOW,
        updated_at=NOW,
    )


def member(
    household_id: UUID,
    member_id: UUID,
    *,
    age: int = 30,
    sex: str | None = "female",
) -> HouseholdMember:
    return HouseholdMember(
        id=member_id,
        household_id=household_id,
        name="Anna",
        active=True,
        birth_date=date(2026 - age, 1, 1),
        sex=sex,
        height_cm=None,
        weight_kg=None,
        activity_level="moderate",
        goal="maintain",
        created_at=NOW,
        updated_at=NOW,
    )


@dataclass
class MemoryStore:
    households: dict[UUID, Household]
    members: dict[tuple[UUID, UUID], HouseholdMember]
    selections: dict[UUID, MemberReferenceMethodologySelection] = field(
        default_factory=dict
    )


class HouseholdRepo:
    def __init__(self, values, *, mutate_on_second_get=False):
        self.values = values
        self.mutate_on_second_get = mutate_on_second_get
        self.calls = 0

    def get_household(self, household_id):
        self.calls += 1
        value = self.values.get(household_id)
        if value is not None and self.mutate_on_second_get and self.calls == 2:
            value = replace(value, updated_at=value.updated_at + timedelta(seconds=1))
            self.values[household_id] = value
        return value


class MemberRepo:
    def __init__(self, values, *, mutate_on_second_get=False):
        self.values = values
        self.mutate_on_second_get = mutate_on_second_get
        self.calls = 0

    def get_member(self, household_id, member_id):
        self.calls += 1
        key = (household_id, member_id)
        value = self.values.get(key)
        if value is not None and self.mutate_on_second_get and self.calls == 2:
            value = replace(value, updated_at=value.updated_at + timedelta(seconds=1))
            self.values[key] = value
        return value


class SelectionRepo:
    def __init__(self, values):
        self.values = values

    def add(self, value):
        self.values[value.id] = value

    def get(self, household_id, selection_id):
        value = self.values.get(selection_id)
        return (
            value
            if value is not None and value.household_id == household_id
            else None
        )

    def get_by_request_id(self, household_id, member_id, request_id):
        return next(
            (
                value
                for value in self.values.values()
                if value.household_id == household_id
                and value.member_id == member_id
                and value.acceptance_request_id == request_id
            ),
            None,
        )

    def get_current(self, household_id, member_id):
        matches = [
            value
            for value in self.values.values()
            if value.household_id == household_id and value.member_id == member_id
        ]
        return max(matches, key=lambda value: value.version_number, default=None)

    def list_history(self, household_id, member_id):
        return sorted(
            (
                value
                for value in self.values.values()
                if value.household_id == household_id
                and value.member_id == member_id
            ),
            key=lambda value: value.version_number,
        )


class MemoryWriteScope:
    def __init__(
        self,
        store,
        *,
        mutate_member_on_second_get=False,
        mutate_household_on_second_get=False,
    ):
        self.store = store
        self.working_households = dict(store.households)
        self.working_members = dict(store.members)
        self.working_selections = dict(store.selections)
        self.households = HouseholdRepo(
            self.working_households,
            mutate_on_second_get=mutate_household_on_second_get,
        )
        self.members = MemberRepo(
            self.working_members,
            mutate_on_second_get=mutate_member_on_second_get,
        )
        self.selections = SelectionRepo(self.working_selections)
        self.completed = False

    def __enter__(self):
        return self

    def revalidate_authoritative_state(
        self,
        *,
        household_id,
        household_updated_at,
        member_id,
        member_updated_at,
    ):
        household_value = self.households.get_household(household_id)
        member_value = self.members.get_member(household_id, member_id)
        if (
            household_value is None
            or member_value is None
            or household_value.updated_at != household_updated_at
            or member_value.updated_at != member_updated_at
        ):
            raise ReferenceMethodologyPersistenceConflictError(
                "Household/member state changed during methodology acceptance."
            )

    def commit(self):
        self.store.households = self.working_households
        self.store.members = self.working_members
        self.store.selections = self.working_selections
        self.completed = True

    def rollback(self):
        self.completed = True

    def __exit__(self, exc_type, exc_value, traceback):
        if not self.completed:
            self.rollback()


class MemoryReadScope:
    def __init__(self, store):
        self.selections = SelectionRepo(store.selections)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return None


def make_service(
    store,
    *,
    ids=(),
    mutate_member_on_second_get=False,
    mutate_household_on_second_get=False,
):
    id_iter = iter(ids)
    return ReferenceMethodologyService(
        write_scope_factory=lambda: MemoryWriteScope(
            store,
            mutate_member_on_second_get=mutate_member_on_second_get,
            mutate_household_on_second_get=mutate_household_on_second_get,
        ),
        read_scope_factory=lambda: MemoryReadScope(store),
        russian_reference_tables=russian_reference_table_provider,
        id_factory=lambda: next(id_iter),
        clock=lambda: NOW + timedelta(hours=1),
    )


def baseline_kwargs(household_id, member_id, request_id, expected=None):
    return {
        "household_id": household_id,
        "member_id": member_id,
        "acceptance_request_id": request_id,
        "expected_current_selection_id": expected,
        "nutrition_config_version": BASELINE_NUTRITION_CONFIG_VERSION,
        "group_reference_methodology_version": None,
    }


def test_fresh_replay_noop_change_and_history_are_versioned():
    household_id, member_id = uuid4(), uuid4()
    store = MemoryStore(
        {household_id: household(household_id)},
        {(household_id, member_id): member(household_id, member_id)},
    )
    ids = (uuid4(), uuid4())
    service = make_service(store, ids=ids)
    request_a, request_b, request_noop = uuid4(), uuid4(), uuid4()

    first = service.accept_member_selection(
        **baseline_kwargs(household_id, member_id, request_a)
    )
    replay = service.accept_member_selection(
        **baseline_kwargs(
            household_id,
            member_id,
            request_a,
            expected=uuid4(),
        )
    )
    noop = service.accept_member_selection(
        **baseline_kwargs(
            household_id,
            member_id,
            request_noop,
            expected=first.id,
        )
    )
    second = service.accept_member_selection(
        household_id=household_id,
        member_id=member_id,
        acceptance_request_id=request_b,
        expected_current_selection_id=first.id,
        nutrition_config_version=BASELINE_NUTRITION_CONFIG_VERSION,
        group_reference_methodology_version=RUSSIAN_GROUP_REFERENCE_VERSION,
    )

    assert replay == first
    assert noop == first
    assert second.version_number == 2
    assert second.supersedes_selection_id == first.id
    assert len(store.selections) == 2
    assert service.get_current_selection(household_id, member_id) == second
    assert service.get_selection_history(household_id, member_id) == (
        first,
        second,
    )


def test_semantic_noop_request_id_is_not_consumed():
    household_id, member_id = uuid4(), uuid4()
    store = MemoryStore(
        {household_id: household(household_id)},
        {(household_id, member_id): member(household_id, member_id)},
    )
    service = make_service(store, ids=(uuid4(), uuid4()))
    first = service.accept_member_selection(
        **baseline_kwargs(household_id, member_id, uuid4())
    )
    noop_request_id = uuid4()

    noop = service.accept_member_selection(
        **baseline_kwargs(
            household_id,
            member_id,
            noop_request_id,
            expected=first.id,
        )
    )
    assert noop == first
    assert all(
        value.acceptance_request_id != noop_request_id
        for value in store.selections.values()
    )

    changed = service.accept_member_selection(
        household_id=household_id,
        member_id=member_id,
        acceptance_request_id=noop_request_id,
        expected_current_selection_id=first.id,
        nutrition_config_version=BASELINE_NUTRITION_CONFIG_VERSION,
        group_reference_methodology_version=RUSSIAN_GROUP_REFERENCE_VERSION,
    )
    assert changed.version_number == 2
    assert changed.acceptance_request_id == noop_request_id


def test_request_id_reuse_with_changed_bundle_fails_closed():
    household_id, member_id = uuid4(), uuid4()
    store = MemoryStore(
        {household_id: household(household_id)},
        {(household_id, member_id): member(household_id, member_id)},
    )
    service = make_service(store, ids=(uuid4(),))
    request_id = uuid4()
    first = service.accept_member_selection(
        **baseline_kwargs(household_id, member_id, request_id)
    )

    with pytest.raises(ReferenceMethodologyConflictError, match="request"):
        service.accept_member_selection(
            household_id=household_id,
            member_id=member_id,
            acceptance_request_id=request_id,
            expected_current_selection_id=first.id,
            nutrition_config_version=BASELINE_NUTRITION_CONFIG_VERSION,
            group_reference_methodology_version=RUSSIAN_GROUP_REFERENCE_VERSION,
        )
    assert tuple(store.selections.values()) == (first,)


def test_stale_expected_id_fails_even_when_current_bundle_matches():
    household_id, member_id = uuid4(), uuid4()
    store = MemoryStore(
        {household_id: household(household_id)},
        {(household_id, member_id): member(household_id, member_id)},
    )
    service = make_service(store, ids=(uuid4(), uuid4(), uuid4()))
    first = service.accept_member_selection(
        **baseline_kwargs(household_id, member_id, uuid4())
    )
    second = service.accept_member_selection(
        household_id=household_id,
        member_id=member_id,
        acceptance_request_id=uuid4(),
        expected_current_selection_id=first.id,
        nutrition_config_version=BASELINE_NUTRITION_CONFIG_VERSION,
        group_reference_methodology_version=RUSSIAN_GROUP_REFERENCE_VERSION,
    )
    third = service.accept_member_selection(
        **baseline_kwargs(
            household_id,
            member_id,
            uuid4(),
            expected=second.id,
        )
    )

    assert third.reference_bundle == first.reference_bundle
    with pytest.raises(ReferenceMethodologyConflictError, match="changed"):
        service.accept_member_selection(
            **baseline_kwargs(
                household_id,
                member_id,
                uuid4(),
                expected=first.id,
            )
        )
    assert len(store.selections) == 3


@pytest.mark.parametrize(
    "age,sex",
    [
        (18, "female"),
        (30, None),
        (30, "other"),
    ],
)
def test_russian_group_reference_requires_current_step5_applicability(age, sex):
    household_id, member_id = uuid4(), uuid4()
    store = MemoryStore(
        {household_id: household(household_id)},
        {
            (household_id, member_id): member(
                household_id,
                member_id,
                age=age,
                sex=sex,
            )
        },
    )
    service = make_service(store, ids=(uuid4(),))

    with pytest.raises(ReferenceMethodologyUnsupportedError, match="applicable"):
        service.accept_member_selection(
            household_id=household_id,
            member_id=member_id,
            acceptance_request_id=uuid4(),
            expected_current_selection_id=None,
            nutrition_config_version=BASELINE_NUTRITION_CONFIG_VERSION,
            group_reference_methodology_version=RUSSIAN_GROUP_REFERENCE_VERSION,
        )
    assert store.selections == {}


@pytest.mark.parametrize(
    "config_version,group_version",
    [
        ("UNKNOWN_CONFIG", None),
        (BASELINE_NUTRITION_CONFIG_VERSION, "UNKNOWN_GROUP"),
    ],
)
def test_unknown_reference_versions_fail_closed(config_version, group_version):
    household_id, member_id = uuid4(), uuid4()
    store = MemoryStore(
        {household_id: household(household_id)},
        {(household_id, member_id): member(household_id, member_id)},
    )
    service = make_service(store)

    with pytest.raises(ReferenceMethodologyUnsupportedError):
        service.accept_member_selection(
            household_id=household_id,
            member_id=member_id,
            acceptance_request_id=uuid4(),
            expected_current_selection_id=None,
            nutrition_config_version=config_version,
            group_reference_methodology_version=group_version,
        )


@pytest.mark.parametrize(
    "member_stale,household_stale",
    [(True, False), (False, True)],
)
def test_state_token_change_during_acceptance_conflicts_without_write(
    member_stale, household_stale
):
    household_id, member_id = uuid4(), uuid4()
    store = MemoryStore(
        {household_id: household(household_id)},
        {(household_id, member_id): member(household_id, member_id)},
    )
    service = make_service(
        store,
        ids=(uuid4(),),
        mutate_member_on_second_get=member_stale,
        mutate_household_on_second_get=household_stale,
    )

    with pytest.raises(ReferenceMethodologyConflictError, match="changed"):
        service.accept_member_selection(
            **baseline_kwargs(household_id, member_id, uuid4())
        )
    assert store.selections == {}


def test_acceptance_retains_household_local_date_and_state_tokens():
    household_id, member_id = uuid4(), uuid4()
    home = household(household_id)
    person = member(household_id, member_id)
    store = MemoryStore(
        {household_id: home},
        {(household_id, member_id): person},
    )
    service = make_service(store, ids=(uuid4(),))

    result = service.accept_member_selection(
        **baseline_kwargs(household_id, member_id, uuid4())
    )

    assert result.accepted_local_date == date(2026, 9, 23)
    assert result.household_timezone_at_acceptance == "Europe/Moscow"
    assert result.household_updated_at_at_acceptance == home.updated_at
    assert result.member_updated_at_at_acceptance == person.updated_at
