"""Thin FastAPI boundary for Household application operations."""

from collections.abc import Callable
from uuid import UUID

from fastapi import APIRouter, HTTPException, Response, status

from app.domain.errors import DomainValidationError
from app.domain.households import Household, HouseholdMember, HouseholdState
from app.schemas.households import (
    HouseholdCreateRequest,
    HouseholdMemberCreateRequest,
    HouseholdMemberExclusionsReplaceRequest,
    HouseholdMemberExclusionsResponse,
    HouseholdMemberExclusionsWriteResponse,
    HouseholdMemberResponse,
    HouseholdMembersResponse,
    HouseholdMemberUpdateRequest,
    HouseholdResponse,
    HouseholdStateResponse,
    HouseholdUpdateRequest,
)
from app.services.household_contracts import (
    HouseholdPersistenceConflictError,
    HouseholdPersistenceError,
)
from app.services.households import (
    HouseholdExclusionInputError,
    HouseholdMemberNotFoundError,
    HouseholdNotFoundError,
    HouseholdService,
    HouseholdUpdateRequiredError,
)

HouseholdServiceProvider = Callable[[], HouseholdService]


def create_households_router(
    service_provider: HouseholdServiceProvider,
) -> APIRouter:
    router = APIRouter(prefix="/households", tags=["households"])

    @router.post(
        "", response_model=HouseholdResponse, status_code=status.HTTP_201_CREATED
    )
    def create_household(payload: HouseholdCreateRequest) -> HouseholdResponse:
        values = payload.model_dump()
        timezone_name = values.pop("timezone")
        try:
            household = service_provider().create_household(
                timezone_name=timezone_name, **values
            )
        except DomainValidationError as exc:
            raise _validation_http_error(exc) from exc
        except HouseholdPersistenceConflictError as exc:
            raise HTTPException(status.HTTP_409_CONFLICT, detail=str(exc)) from exc
        return _household_response(household)

    @router.get("/{household_id}", response_model=HouseholdStateResponse)
    def get_household(household_id: UUID) -> HouseholdStateResponse:
        try:
            state = service_provider().get_household(household_id)
        except HouseholdNotFoundError as exc:
            raise _household_not_found() from exc
        return _household_state_response(state)

    @router.patch("/{household_id}", response_model=HouseholdResponse)
    def update_household_route(
        household_id: UUID, payload: HouseholdUpdateRequest
    ) -> HouseholdResponse:
        try:
            household = service_provider().update_household(
                household_id, payload.model_dump(exclude_unset=True)
            )
        except DomainValidationError as exc:
            raise _validation_http_error(exc) from exc
        except HouseholdUpdateRequiredError as exc:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
            ) from exc
        except HouseholdNotFoundError as exc:
            raise _household_not_found() from exc
        except HouseholdPersistenceConflictError as exc:
            raise HTTPException(status.HTTP_409_CONFLICT, detail=str(exc)) from exc
        return _household_response(household)

    @router.post(
        "/{household_id}/members",
        response_model=HouseholdMemberResponse,
        status_code=status.HTTP_201_CREATED,
    )
    def add_household_member(
        household_id: UUID, payload: HouseholdMemberCreateRequest
    ) -> HouseholdMemberResponse:
        try:
            member = service_provider().add_household_member(
                household_id, **payload.model_dump()
            )
        except DomainValidationError as exc:
            raise _validation_http_error(exc) from exc
        except HouseholdNotFoundError as exc:
            raise _household_not_found() from exc
        except HouseholdPersistenceConflictError as exc:
            raise HTTPException(status.HTTP_409_CONFLICT, detail=str(exc)) from exc
        return _member_response(member)

    @router.get("/{household_id}/members", response_model=HouseholdMembersResponse)
    def list_household_members(
        household_id: UUID,
    ) -> HouseholdMembersResponse:
        try:
            members = service_provider().list_household_members(household_id)
        except HouseholdNotFoundError as exc:
            raise _household_not_found() from exc
        return HouseholdMembersResponse(
            members=[_member_response(member) for member in members]
        )

    @router.patch(
        "/{household_id}/members/{member_id}",
        response_model=HouseholdMemberResponse,
    )
    def update_household_member(
        household_id: UUID,
        member_id: UUID,
        payload: HouseholdMemberUpdateRequest,
    ) -> HouseholdMemberResponse:
        try:
            member = service_provider().update_household_member(
                household_id,
                member_id,
                payload.model_dump(exclude_unset=True),
            )
        except DomainValidationError as exc:
            raise _validation_http_error(exc) from exc
        except HouseholdUpdateRequiredError as exc:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
            ) from exc
        except HouseholdNotFoundError as exc:
            raise _household_not_found() from exc
        except HouseholdMemberNotFoundError as exc:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                detail="Household member was not found in this Household.",
            ) from exc
        except HouseholdPersistenceConflictError as exc:
            raise HTTPException(status.HTTP_409_CONFLICT, detail=str(exc)) from exc
        return _member_response(member)

    @router.get(
        "/{household_id}/members/{member_id}/food-exclusions",
        response_model=HouseholdMemberExclusionsResponse,
    )
    def get_member_food_exclusions(
        household_id: UUID, member_id: UUID, response: Response
    ) -> HouseholdMemberExclusionsResponse:
        response.headers["Cache-Control"] = "no-store"
        try:
            selected = service_provider().list_member_excluded_food_ids(
                household_id, member_id
            )
        except (HouseholdNotFoundError, HouseholdMemberNotFoundError) as exc:
            raise _exclusions_not_found() from exc
        except HouseholdPersistenceConflictError as exc:
            raise _exclusions_conflict() from exc
        except HouseholdPersistenceError as exc:
            raise _exclusions_persistence_failure() from exc
        return HouseholdMemberExclusionsResponse(
            excluded_food_ingredient_ids=sorted(selected)
        )

    @router.put(
        "/{household_id}/members/{member_id}/food-exclusions",
        response_model=HouseholdMemberExclusionsWriteResponse,
    )
    def replace_member_food_exclusions(
        household_id: UUID,
        member_id: UUID,
        payload: HouseholdMemberExclusionsReplaceRequest,
        response: Response,
    ) -> HouseholdMemberExclusionsWriteResponse:
        response.headers["Cache-Control"] = "no-store"
        selected = frozenset(payload.excluded_food_ingredient_ids)
        try:
            changed = service_provider().replace_member_excluded_food_ids(
                household_id,
                member_id,
                expected=frozenset(payload.expected_excluded_food_ingredient_ids),
                selected=selected,
            )
        except (HouseholdNotFoundError, HouseholdMemberNotFoundError) as exc:
            raise _exclusions_not_found() from exc
        except HouseholdExclusionInputError as exc:
            raise HTTPException(
                422,
                detail={
                    "code": "MEMBER_EXCLUSIONS_INVALID",
                    "message": "Нельзя изменить исключения для этого участника.",
                    "next_action": "Проверьте данные участника и повторите запрос.",
                },
                headers={"Cache-Control": "no-store"},
            ) from exc
        except HouseholdPersistenceConflictError as exc:
            raise _exclusions_conflict() from exc
        except HouseholdPersistenceError as exc:
            raise _exclusions_persistence_failure() from exc
        # Return the committed selection, not a second potentially racing read.
        return HouseholdMemberExclusionsWriteResponse(
            excluded_food_ingredient_ids=sorted(selected), changed=changed
        )

    return router


def _exclusions_not_found() -> HTTPException:
    return HTTPException(
        404,
        detail={
            "code": "MEMBER_EXCLUSIONS_NOT_FOUND",
            "message": "Участник семьи не найден.",
            "next_action": "Откройте актуальный список членов семьи.",
        },
        headers={"Cache-Control": "no-store"},
    )


def _exclusions_conflict() -> HTTPException:
    return HTTPException(
        409,
        detail={
            "code": "MEMBER_EXCLUSIONS_CONFLICT",
            "message": "Не удалось сохранить или прочитать исключения.",
            "next_action": "Обновите список исключений и проверьте доступность продуктов.",
        },
        headers={"Cache-Control": "no-store"},
    )


def _exclusions_persistence_failure() -> HTTPException:
    return HTTPException(
        503,
        detail={
            "code": "MEMBER_EXCLUSIONS_PERSISTENCE_FAILURE",
            "message": "Не удалось выполнить операцию с исключениями.",
            "next_action": "Обновите список исключений перед повторной попыткой.",
        },
        headers={"Cache-Control": "no-store"},
    )


def _validation_http_error(exc: DomainValidationError) -> HTTPException:
    return HTTPException(
        status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail=exc.issue.__dict__,
    )


def _household_not_found() -> HTTPException:
    return HTTPException(
        status.HTTP_404_NOT_FOUND,
        detail="Household was not found.",
    )


def _household_response(household: Household) -> HouseholdResponse:
    return HouseholdResponse(
        id=household.id,
        name=household.name,
        timezone=household.timezone,
        city=household.city,
        default_weekly_budget=(
            None
            if household.default_weekly_budget is None
            else str(household.default_weekly_budget)
        ),
        default_cooking_profile=household.default_cooking_profile,
        created_at=household.created_at,
        updated_at=household.updated_at,
    )


def _member_response(member: HouseholdMember) -> HouseholdMemberResponse:
    return HouseholdMemberResponse(
        id=member.id,
        household_id=member.household_id,
        name=member.name,
        active=member.active,
        birth_date=member.birth_date,
        sex=member.sex,
        height_cm=None if member.height_cm is None else str(member.height_cm),
        weight_kg=None if member.weight_kg is None else str(member.weight_kg),
        activity_level=member.activity_level,
        goal=member.goal,
        created_at=member.created_at,
        updated_at=member.updated_at,
    )


def _household_state_response(state: HouseholdState) -> HouseholdStateResponse:
    household = _household_response(state.household)
    return HouseholdStateResponse(
        **household.model_dump(),
        members=[_member_response(member) for member in state.members],
    )
