"""Minimal read-only canonical food selection HTTP contracts."""

from uuid import UUID

from pydantic import BaseModel


class FoodIngredientSelectionResponse(BaseModel):
    id: UUID
    canonical_name: str
    is_active: bool


class FoodIngredientSearchResponse(BaseModel):
    items: list[FoodIngredientSelectionResponse]
