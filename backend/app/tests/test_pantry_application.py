from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest

from app.db.config import DatabaseConfig
from app.db.migrations import apply_migrations
from app.domain.errors import DomainValidationError
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
from app.persistence.sqlalchemy_core.food_ingredient_composition import (
    create_food_catalogue_service,
)
from app.persistence.sqlalchemy_core.food_ingredient_uow import (
    SqlAlchemyFoodCatalogueUnitOfWork,
)
from app.persistence.sqlalchemy_core.household_composition import (
    create_household_service,
)
from app.persistence.sqlalchemy_core.pantry_composition import create_pantry_service
from app.persistence.sqlalchemy_core.pantry_repositories import (
    SqlAlchemyPantryItemRepository,
    SqlAlchemyPantryMovementRepository,
)
from app.persistence.sqlalchemy_core.pantry_uow import SqlAlchemyPantryReadScope
from app.services.households import HouseholdNotFoundError
from app.services.pantry import (
    PantryFoodIngredientNotFoundError,
    PantryInactiveFoodIngredientError,
    PantryInsufficientStockError,
    PantryItemNotFoundError,
)
from app.services.pantry_contracts import PantryPersistenceConflictError
from app.tests.test_food_ingredient_domain import ingredient


@pytest.fixture
def pantry(tmp_path):
    config = DatabaseConfig(path=tmp_path / "pantry-application.sqlite")
    apply_migrations(config)
    engine = create_sqlite_engine(config)
    homes = create_household_service(engine)
    home = homes.create_household(name="Home A", timezone_name="Europe/Moscow")
    other = homes.create_household(name="Home B", timezone_name="UTC")
    eggs = ingredient(default_unit="pcs")
    with SqlAlchemyFoodCatalogueUnitOfWork(engine) as scope:
        scope.ingredients.add(eggs)
        scope.commit()
    try:
        yield engine, create_pantry_service(engine), home.id, other.id, eggs.id
    finally:
        engine.dispose()


def add(pantry, quantity="10", **overrides):
    _, service, household_id, _, ingredient_id = pantry
    values = dict(food_ingredient_id=ingredient_id, quantity=quantity, unit="pcs")
    values.update(overrides)
    return service.add_stock(household_id, **values)


def reconciled(pantry):
    """Independently derive every persisted balance from its immutable ledger."""
    engine, service, household_id, other_id, _ = pantry
    snapshots = {}
    signs = {
        "ADD": 1,
        "ADJUSTMENT_IN": 1,
        "CONSUMPTION": -1,
        "WASTE": -1,
        "ADJUSTMENT_OUT": -1,
    }
    for owner in (household_id, other_id):
        for item in service.list_items(owner, include_empty=True):
            with SqlAlchemyPantryReadScope(engine) as scope:
                history = scope.movements.list_for_item(owner, item.id)
            assert history
            assert all(row.quantity > 0 and row.unit == item.unit for row in history)
            assert all(
                row.household_id == owner and row.pantry_item_id == item.id
                for row in history
            )
            assert item.quantity >= 0
            assert item.quantity == sum(
                (signs[row.movement_type] * row.quantity for row in history), Decimal(0)
            )
            snapshots[item.id] = (item, history)
    return snapshots


def test_add_consume_and_repeated_insufficient_command_preserve_ledger(pantry):
    _, service, home, _, ingredient_id = pantry
    item = add(pantry)
    created = reconciled(pantry)[item.id]
    assert created[0].quantity == Decimal("10.000")
    assert [(row.movement_type, row.quantity) for row in created[1]] == [
        ("ADD", Decimal(10))
    ]

    movements = service.consume(
        home, food_ingredient_id=ingredient_id, quantity="4", unit="pcs"
    )
    after = reconciled(pantry)
    assert after[item.id][0].quantity == Decimal(6)
    assert [(row.movement_type, row.quantity) for row in movements] == [
        ("CONSUMPTION", Decimal(4))
    ]
    for _ in range(2):
        with pytest.raises(PantryInsufficientStockError):
            service.consume(
                home, food_ingredient_id=ingredient_id, quantity="10", unit="pcs"
            )
        assert reconciled(pantry) == after
    assert service.get_available_quantity(home, ingredient_id) == Decimal(6)


def test_fefo_consumption_spans_buckets_in_one_command(pantry):
    _, service, home, _, ingredient_id = pantry
    later = add(pantry, "4", expires_on=date(2026, 9, 10))
    first = add(pantry, "5", expires_on=date(2026, 9, 7))
    reconciled(pantry)
    movements = service.consume(
        home, food_ingredient_id=ingredient_id, quantity="7", unit="pcs"
    )
    state = reconciled(pantry)
    assert [(row.pantry_item_id, row.quantity) for row in movements] == [
        (first.id, Decimal(5)),
        (later.id, Decimal(2)),
    ]
    assert state[first.id][0].quantity == 0
    assert state[later.id][0].quantity == 2
    assert service.list_items(home) == [state[later.id][0]]
    assert service.get_item(home, first.id).quantity == 0


def test_insufficient_total_rolls_back_all_buckets(pantry):
    _, service, home, _, ingredient_id = pantry
    add(pantry, "5")
    add(pantry, "4")
    before = reconciled(pantry)
    with pytest.raises(PantryInsufficientStockError):
        service.consume(
            home, food_ingredient_id=ingredient_id, quantity="10", unit="pcs"
        )
    assert reconciled(pantry) == before


def test_waste_adjust_both_directions_noop_and_zero_are_exact(pantry):
    _, service, home, _, _ = pantry
    item = add(pantry, "500")
    reconciled(pantry)
    service.adjust(home, item.id, target_quantity="420", unit="pcs")
    state = reconciled(pantry)[item.id]
    assert state[0].quantity == 420
    assert (state[1][-1].movement_type, state[1][-1].quantity) == ("ADJUSTMENT_OUT", 80)
    service.adjust(home, item.id, target_quantity="500", unit="pcs")
    state = reconciled(pantry)[item.id]
    assert (state[1][-1].movement_type, state[1][-1].quantity) == ("ADJUSTMENT_IN", 80)
    service.adjust(home, item.id, target_quantity="500", unit="pcs")
    assert reconciled(pantry)[item.id] == state
    service.waste(home, item.id, quantity="2", unit="pcs")
    state = reconciled(pantry)[item.id]
    assert state[0].quantity == 498
    assert (state[1][-1].movement_type, state[1][-1].quantity) == ("WASTE", 2)
    with pytest.raises(PantryInsufficientStockError):
        service.waste(home, item.id, quantity="499", unit="pcs")
    assert reconciled(pantry)[item.id] == state
    service.adjust(home, item.id, target_quantity="0", unit="pcs")
    assert reconciled(pantry)[item.id][0].quantity == 0


@pytest.mark.parametrize("quantity", ["0", "0.0004", "-1", "NaN", "Infinity", 1.2])
def test_invalid_initial_quantity_never_creates_an_item_or_movement(pantry, quantity):
    with pytest.raises(DomainValidationError):
        add(pantry, quantity)
    assert reconciled(pantry) == {}


def test_missing_inactive_and_wrong_unit_ingredients_fail_without_writes(pantry):
    engine, _, _, _, ingredient_id = pantry
    with pytest.raises(PantryFoodIngredientNotFoundError):
        add(pantry, food_ingredient_id=uuid4())
    with pytest.raises(DomainValidationError):
        add(pantry, unit="g")
    create_food_catalogue_service(engine).deactivate(ingredient_id)
    with pytest.raises(PantryInactiveFoodIngredientError):
        add(pantry)
    assert reconciled(pantry) == {}


def test_deactivation_keeps_history_and_confirmed_consumption_accessible(pantry):
    engine, service, home, _, ingredient_id = pantry
    item = add(pantry)
    before = reconciled(pantry)
    create_food_catalogue_service(engine).deactivate(ingredient_id)
    assert reconciled(pantry) == before
    assert service.get_item(home, item.id) == item
    assert service.get_available_quantity(home, ingredient_id) == 10
    service.consume(home, food_ingredient_id=ingredient_id, quantity="1", unit="pcs")
    assert reconciled(pantry)[item.id][0].quantity == 9


@pytest.mark.parametrize("operation", ["get", "metadata", "waste", "adjust"])
def test_foreign_item_is_indistinguishable_from_missing_item(pantry, operation):
    _, service, _, other, _ = pantry
    owned = add(pantry)
    before = reconciled(pantry)

    def command(item_id):
        if operation == "get":
            return service.get_item(other, item_id)
        if operation == "metadata":
            return service.update_metadata(other, item_id, {"location": "FRIDGE"})
        if operation == "waste":
            return service.waste(other, item_id, quantity="1", unit="pcs")
        return service.adjust(other, item_id, target_quantity="1", unit="pcs")

    errors = []
    for candidate in (owned.id, uuid4()):
        with pytest.raises(PantryItemNotFoundError) as error:
            command(candidate)
        errors.append(str(error.value))
    assert errors[0] == errors[1]
    assert reconciled(pantry) == before


def test_foreign_household_stock_is_never_in_consumption_or_queries(pantry):
    _, service, _, other, ingredient_id = pantry
    add(pantry, expires_on=date(2026, 9, 7))
    before = reconciled(pantry)
    assert service.get_available_quantity(other, ingredient_id) == 0
    assert service.list_items(other) == []
    assert service.list_expiring(other, date(2026, 9, 8)) == []
    with pytest.raises(PantryInsufficientStockError):
        service.consume(
            other, food_ingredient_id=ingredient_id, quantity="1", unit="pcs"
        )
    assert reconciled(pantry) == before


@pytest.mark.parametrize(
    "operation",
    [
        "add",
        "get",
        "list",
        "available",
        "expiring",
        "consume",
        "waste",
        "adjust",
        "metadata",
    ],
)
def test_every_application_operation_requires_existing_household(pantry, operation):
    _, service, _, _, ingredient_id = pantry
    missing = uuid4()
    calls = {
        "add": lambda: service.add_stock(
            missing, food_ingredient_id=ingredient_id, quantity="1", unit="pcs"
        ),
        "get": lambda: service.get_item(missing, uuid4()),
        "list": lambda: service.list_items(missing),
        "available": lambda: service.get_available_quantity(missing, ingredient_id),
        "expiring": lambda: service.list_expiring(missing, date(2026, 9, 6)),
        "consume": lambda: service.consume(
            missing, food_ingredient_id=ingredient_id, quantity="1", unit="pcs"
        ),
        "waste": lambda: service.waste(missing, uuid4(), quantity="1", unit="pcs"),
        "adjust": lambda: service.adjust(
            missing, uuid4(), target_quantity="1", unit="pcs"
        ),
        "metadata": lambda: service.update_metadata(
            missing, uuid4(), {"estimated": True}
        ),
    }
    with pytest.raises(HouseholdNotFoundError):
        calls[operation]()
    assert reconciled(pantry) == {}


def test_metadata_dates_can_be_updated_and_cleared_without_movements(pantry):
    _, service, home, _, _ = pantry
    item = add(pantry)
    initial = reconciled(pantry)[item.id]
    changes = dict(
        location="FREEZER",
        estimated=True,
        purchased_on=date(2026, 9, 1),
        opened_on=date(2026, 9, 2),
        expires_on=date(2026, 10, 1),
    )
    updated = service.update_metadata(home, item.id, changes)
    assert all(getattr(updated, key) == value for key, value in changes.items())
    assert reconciled(pantry)[item.id][1] == initial[1]
    cleared = service.update_metadata(home, item.id, {"expires_on": None})
    assert cleared.expires_on is None
    assert reconciled(pantry)[item.id][1] == initial[1]


@pytest.mark.parametrize(
    "field,value",
    [
        ("quantity", "1"),
        ("unit", "g"),
        ("food_ingredient_id", uuid4()),
        ("household_id", uuid4()),
    ],
)
def test_metadata_command_rejects_stock_identity_and_quantity(pantry, field, value):
    _, service, home, _, _ = pantry
    item = add(pantry)
    before = reconciled(pantry)
    with pytest.raises(DomainValidationError):
        service.update_metadata(home, item.id, {field: value})
    assert reconciled(pantry) == before


def test_fefo_dates_include_expired_stock_without_inventing_safety_policy(pantry):
    _, service, home, _, ingredient_id = pantry
    no_expiry = add(pantry, "1", purchased_on=date(2025, 1, 1))
    later_purchase = add(
        pantry, "1", expires_on=date(2026, 9, 7), purchased_on=date(2026, 9, 3)
    )
    unknown_purchase = add(pantry, "1", expires_on=date(2026, 9, 7))
    older_purchase = add(
        pantry, "1", expires_on=date(2026, 9, 7), purchased_on=date(2026, 9, 1)
    )
    expired = add(pantry, "1", expires_on=date(2026, 8, 31))
    reconciled(pantry)
    assert [row.id for row in service.list_expiring(home, date(2026, 9, 7))] == [
        expired.id,
        older_purchase.id,
        later_purchase.id,
        unknown_purchase.id,
    ]
    rows = service.consume(
        home, food_ingredient_id=ingredient_id, quantity="5", unit="pcs"
    )
    assert [row.pantry_item_id for row in rows] == [
        expired.id,
        older_purchase.id,
        later_purchase.id,
        unknown_purchase.id,
        no_expiry.id,
    ]
    assert all(value[0].quantity == 0 for value in reconciled(pantry).values())
    assert service.list_expiring(home, date(2026, 9, 7)) == []


def test_initial_movement_failure_rolls_back_new_bucket(pantry, monkeypatch):
    original = SqlAlchemyPantryMovementRepository.add

    def fail_after_insert(repository, row):
        original(repository, row)
        raise RuntimeError("injected movement failure")

    with monkeypatch.context() as patch:
        patch.setattr(SqlAlchemyPantryMovementRepository, "add", fail_after_insert)
        with pytest.raises(RuntimeError, match="injected movement failure"):
            add(pantry)
    assert reconciled(pantry) == {}
    add(pantry)
    assert len(reconciled(pantry)) == 1


@pytest.mark.parametrize("failure", ["second_movement", "second_atomic_decrease"])
def test_mid_allocation_failure_rolls_back_every_balance_and_movement(
    pantry, monkeypatch, failure
):
    _, service, home, _, ingredient_id = pantry
    add(pantry, "5", expires_on=date(2026, 9, 7))
    add(pantry, "4", expires_on=date(2026, 9, 8))
    before = reconciled(pantry)
    calls = 0
    if failure == "second_movement":
        target, method = SqlAlchemyPantryMovementRepository, "add"
        expected_error = RuntimeError
    else:
        target, method = (
            SqlAlchemyPantryItemRepository,
            "decrease_quantity_if_sufficient",
        )
        expected_error = PantryPersistenceConflictError
    original = getattr(target, method)

    def injected(repository, *args, **kwargs):
        nonlocal calls
        calls += 1
        if failure == "second_atomic_decrease" and calls == 2:
            return False
        result = original(repository, *args, **kwargs)
        if calls == 2:
            raise RuntimeError("injected second movement failure")
        return result

    with monkeypatch.context() as patch:
        patch.setattr(target, method, injected)
        with pytest.raises(expected_error):
            service.consume(
                home, food_ingredient_id=ingredient_id, quantity="7", unit="pcs"
            )
    assert calls == 2
    assert reconciled(pantry) == before
    service.consume(home, food_ingredient_id=ingredient_id, quantity="7", unit="pcs")
    assert sum(value[0].quantity for value in reconciled(pantry).values()) == 2


@pytest.mark.parametrize(
    "boundary", [None, "2026-09-06", datetime(2026, 9, 6, tzinfo=timezone.utc)]
)
def test_expiry_boundary_is_required_calendar_date(pantry, boundary):
    _, service, home, _, _ = pantry
    with pytest.raises(DomainValidationError):
        service.list_expiring(home, boundary)


@pytest.mark.parametrize("operation", ["consume", "waste", "adjust"])
def test_command_unit_mismatch_rejects_without_partial_accounting(pantry, operation):
    _, service, home, _, ingredient_id = pantry
    item = add(pantry)
    before = reconciled(pantry)
    with pytest.raises(DomainValidationError):
        if operation == "consume":
            service.consume(
                home, food_ingredient_id=ingredient_id, quantity="1", unit="ml"
            )
        elif operation == "waste":
            service.waste(home, item.id, quantity="1", unit="g")
        else:
            service.adjust(home, item.id, target_quantity="1", unit="g")
    assert reconciled(pantry) == before


@pytest.mark.parametrize(
    "target", ["-0.00001", "-1", "NaN", "Infinity", "1000000000000"]
)
def test_invalid_adjustment_target_preserves_item_and_ledger(pantry, target):
    _, service, home, _, _ = pantry
    item = add(pantry)
    before = reconciled(pantry)
    with pytest.raises(DomainValidationError):
        service.adjust(home, item.id, target_quantity=target, unit="pcs")
    assert reconciled(pantry) == before


@pytest.mark.parametrize("unit", ["g", "ml", "pcs"])
def test_fractional_precision_and_large_balances_reconcile_without_float(pantry, unit):
    engine, service, home, _, _ = pantry
    food = ingredient(
        canonical_code="EXACT_STOCK",
        canonical_name="Exact stock",
        canonical_name_key="exact stock",
        default_unit=unit,
    )
    with SqlAlchemyFoodCatalogueUnitOfWork(engine) as scope:
        scope.ingredients.add(food)
        scope.commit()
    item = add(pantry, "999999999999.999", food_ingredient_id=food.id, unit=unit)
    reconciled(pantry)
    service.consume(home, food_ingredient_id=food.id, quantity="0.001", unit=unit)
    state = reconciled(pantry)[item.id]
    assert state[0].quantity == Decimal("999999999999.998")
    assert state[1][-1].quantity == Decimal("0.001")
    service.adjust(home, item.id, target_quantity="0.1235", unit=unit)
    assert reconciled(pantry)[item.id][0].quantity == Decimal("0.124")


def test_bounded_filters_and_empty_bucket_visibility(pantry):
    _, service, home, _, ingredient_id = pantry
    first = add(pantry, location="FRIDGE")
    second = add(pantry, location="FREEZER")
    reconciled(pantry)
    assert service.list_items(
        home, food_ingredient_id=ingredient_id, location="FRIDGE"
    ) == [first]
    service.adjust(home, first.id, target_quantity="0", unit="pcs")
    state = reconciled(pantry)
    assert service.list_items(home) == [second]
    assert service.list_items(home, location="FRIDGE", include_empty=True) == [
        state[first.id][0]
    ]
    assert service.get_available_quantity(home, ingredient_id) == second.quantity
