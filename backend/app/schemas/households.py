"""Explicit HTTP contracts for the Household bounded context."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, StrictBool, field_validator

DecimalInput = Decimal | int | str


class HouseholdCreateRequest(BaseModel):
    name: str
    timezone: str
    city: str | None = None
    default_weekly_budget: DecimalInput | None = None
    default_cooking_profile: str | None = None

    model_config = ConfigDict(extra="forbid")

    @field_validator("default_weekly_budget", mode="before")
    @classmethod
    def reject_float(cls, value):
        if isinstance(value, float) or isinstance(value, bool):
            raise ValueError(
                "Decimal values must be strings, integers, Decimal, or null; float is not allowed."
            )
        return value


class HouseholdUpdateRequest(BaseModel):
    name: str | None = None
    timezone: str | None = None
    city: str | None = None
    default_weekly_budget: DecimalInput | None = None
    default_cooking_profile: str | None = None

    model_config = ConfigDict(extra="forbid")

    @field_validator("default_weekly_budget", mode="before")
    @classmethod
    def reject_float(cls, value):
        if isinstance(value, float) or isinstance(value, bool):
            raise ValueError(
                "Decimal values must be strings, integers, Decimal, or null; float is not allowed."
            )
        return value


class HouseholdMemberCreateRequest(BaseModel):
    name: str
    activity_level: str
    goal: str
    active: StrictBool = True
    birth_date: date | None = None
    sex: str | None = None
    height_cm: DecimalInput | None = None
    weight_kg: DecimalInput | None = None

    model_config = ConfigDict(extra="forbid")

    @field_validator("height_cm", "weight_kg", mode="before")
    @classmethod
    def reject_float(cls, value):
        if isinstance(value, float) or isinstance(value, bool):
            raise ValueError(
                "Decimal values must be strings, integers, Decimal, or null; float is not allowed."
            )
        return value


class HouseholdMemberUpdateRequest(BaseModel):
    name: str | None = None
    activity_level: str | None = None
    goal: str | None = None
    active: StrictBool | None = None
    birth_date: date | None = None
    sex: str | None = None
    height_cm: DecimalInput | None = None
    weight_kg: DecimalInput | None = None

    model_config = ConfigDict(extra="forbid")

    @field_validator("height_cm", "weight_kg", mode="before")
    @classmethod
    def reject_float(cls, value):
        if isinstance(value, float) or isinstance(value, bool):
            raise ValueError(
                "Decimal values must be strings, integers, Decimal, or null; float is not allowed."
            )
        return value


class HouseholdResponse(BaseModel):
    id: UUID
    name: str
    timezone: str
    city: str | None
    default_weekly_budget: str | None
    default_cooking_profile: str | None
    created_at: datetime
    updated_at: datetime


class HouseholdMemberResponse(BaseModel):
    id: UUID
    household_id: UUID
    name: str
    active: bool
    birth_date: date | None
    sex: str | None
    height_cm: str | None
    weight_kg: str | None
    activity_level: str
    goal: str
    created_at: datetime
    updated_at: datetime


class HouseholdStateResponse(HouseholdResponse):
    members: list[HouseholdMemberResponse]


class HouseholdMembersResponse(BaseModel):
    members: list[HouseholdMemberResponse]
