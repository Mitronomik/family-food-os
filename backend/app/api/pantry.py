"""Thin Household-selected Pantry boundary; selection is not authorization."""

from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import asdict
from uuid import UUID

from fastapi import APIRouter, HTTPException

from app.domain.errors import DomainValidationError
from app.domain.pantry import PantryLocation
from app.schemas.pantry import (
    CalendarDate,
    PantryAdjustRequest,
    PantryConsumptionResponse,
    PantryConsumeRequest,
    PantryCreateRequest,
    PantryItemResponse,
    PantryItemsResponse,
    PantryMetadataRequest,
    PantryMovementResponse,
    PantryQuantityRequest,
)
from app.services.households import HouseholdNotFoundError
from app.services.pantry import (
    PantryFoodIngredientNotFoundError,
    PantryInactiveFoodIngredientError,
    PantryInsufficientStockError,
    PantryItemNotFoundError,
    PantryService,
)
from app.services.pantry_contracts import PantryPersistenceConflictError


@contextmanager
def _errors():
    try:
        yield
    except DomainValidationError as exc:
        raise HTTPException(422, detail=exc.issue.__dict__) from exc
    except (
        HouseholdNotFoundError,
        PantryItemNotFoundError,
        PantryFoodIngredientNotFoundError,
    ) as exc:
        raise HTTPException(404, detail=str(exc)) from exc
    except (
        PantryInactiveFoodIngredientError,
        PantryInsufficientStockError,
        PantryPersistenceConflictError,
    ) as exc:
        raise HTTPException(409, detail=str(exc)) from exc


def _item_response(item):
    return PantryItemResponse(**{**asdict(item), "quantity": str(item.quantity)})


def _items_response(items):
    return PantryItemsResponse(items=[_item_response(item) for item in items])


def create_pantry_router(service_provider: Callable[[], PantryService]) -> APIRouter:
    router = APIRouter(prefix="/households/{household_id}/pantry", tags=["pantry"])

    @router.post("/items", response_model=PantryItemResponse, status_code=201)
    def add(household_id: UUID, payload: PantryCreateRequest):
        with _errors():
            return _item_response(
                service_provider().add_stock(household_id, **payload.model_dump())
            )

    @router.get("/items", response_model=PantryItemsResponse)
    def list_items(
        household_id: UUID,
        food_ingredient_id: UUID | None = None,
        location: PantryLocation | None = None,
        include_empty: bool = False,
    ):
        with _errors():
            return _items_response(
                service_provider().list_items(
                    household_id,
                    food_ingredient_id=food_ingredient_id,
                    location=location,
                    include_empty=include_empty,
                )
            )

    @router.get("/items/{item_id}", response_model=PantryItemResponse)
    def get(household_id: UUID, item_id: UUID):
        with _errors():
            return _item_response(service_provider().get_item(household_id, item_id))

    @router.patch("/items/{item_id}", response_model=PantryItemResponse)
    def metadata(household_id: UUID, item_id: UUID, payload: PantryMetadataRequest):
        with _errors():
            return _item_response(
                service_provider().update_metadata(
                    household_id, item_id, payload.model_dump(exclude_unset=True)
                )
            )

    @router.post("/consume", response_model=PantryConsumptionResponse)
    def consume(household_id: UUID, payload: PantryConsumeRequest):
        with _errors():
            movements = service_provider().consume(household_id, **payload.model_dump())
            return PantryConsumptionResponse(
                movements=[
                    PantryMovementResponse(**{**asdict(m), "quantity": str(m.quantity)})
                    for m in movements
                ]
            )

    @router.post("/items/{item_id}/waste", response_model=PantryItemResponse)
    def waste(household_id: UUID, item_id: UUID, payload: PantryQuantityRequest):
        with _errors():
            return _item_response(
                service_provider().waste(household_id, item_id, **payload.model_dump())
            )

    @router.post("/items/{item_id}/adjust", response_model=PantryItemResponse)
    def adjust(household_id: UUID, item_id: UUID, payload: PantryAdjustRequest):
        with _errors():
            return _item_response(
                service_provider().adjust(household_id, item_id, **payload.model_dump())
            )

    @router.get("/expiring", response_model=PantryItemsResponse)
    def expiring(household_id: UUID, on_or_before: CalendarDate):
        with _errors():
            return _items_response(
                service_provider().list_expiring(household_id, on_or_before)
            )

    return router
