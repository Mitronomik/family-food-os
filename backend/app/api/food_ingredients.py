"""Read-only canonical catalogue selection; never expose retailer or nutrition data."""

from collections.abc import Callable
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query

from app.domain.errors import DomainValidationError
from app.domain.food_ingredients import FoodIngredient
from app.schemas.food_ingredients import (
    FoodIngredientSearchResponse,
    FoodIngredientSelectionResponse,
)
from app.services.food_ingredients import (
    MAX_CATALOGUE_RESULT_LIMIT,
    FoodCatalogueService,
    FoodIngredientNotFoundError,
)


def _selection(ingredient: FoodIngredient) -> FoodIngredientSelectionResponse:
    return FoodIngredientSelectionResponse(
        id=ingredient.id,
        canonical_name=ingredient.canonical_name,
        is_active=ingredient.is_active,
    )


def create_food_ingredients_router(
    service_provider: Callable[[], FoodCatalogueService],
) -> APIRouter:
    router = APIRouter(prefix="/food-ingredients", tags=["food-ingredients"])

    @router.get("", response_model=FoodIngredientSearchResponse)
    def search_food_ingredients(
        q: str = Query(min_length=1, max_length=240),
        limit: int = Query(default=20, ge=1, le=MAX_CATALOGUE_RESULT_LIMIT),
    ) -> FoodIngredientSearchResponse:
        try:
            ingredients = service_provider().search(q, limit=limit)
        except DomainValidationError as exc:
            raise HTTPException(
                422,
                detail={
                    "code": "FOOD_INGREDIENT_SEARCH_INVALID",
                    "message": "Введите название продукта.",
                    "next_action": "Уточните поисковый запрос.",
                },
            ) from exc
        return FoodIngredientSearchResponse(
            items=[_selection(ingredient) for ingredient in ingredients]
        )

    @router.get("/{ingredient_id}", response_model=FoodIngredientSelectionResponse)
    def get_food_ingredient(ingredient_id: UUID) -> FoodIngredientSelectionResponse:
        try:
            return _selection(service_provider().get(ingredient_id))
        except FoodIngredientNotFoundError as exc:
            raise HTTPException(
                404,
                detail={
                    "code": "FOOD_INGREDIENT_NOT_FOUND",
                    "message": "Продукт не найден.",
                    "next_action": "Найдите другой продукт в каталоге.",
                },
            ) from exc

    return router
