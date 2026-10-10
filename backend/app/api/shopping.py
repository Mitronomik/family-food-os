"""PR9-C: thin, household-scoped Shopping HTTP adapter.

No client quantity is authoritative; no Pantry mutation or SQL happens here.
Machine codes and Russian user-facing explanations are separate properties.
"""

import json
from collections.abc import Callable
from contextlib import contextmanager
from decimal import Decimal, InvalidOperation
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, Request

from app.domain.shopping_calculation import ShoppingCalculationError
from app.domain.shopping_lists import ShoppingCurrent, ShoppingListDetail
from app.schemas.shopping import (
    ShoppingAllocationResponse,
    ShoppingCurrentResponse,
    ShoppingDetailResponse,
    ShoppingGenerateRequest,
    ShoppingHistoryResponse,
    ShoppingItemResponse,
    ShoppingLifecycle,
    ShoppingUnresolvedResponse,
    ShoppingWarningResponse,
)
from app.services.shopping import ShoppingService
from app.services.shopping_contracts import (
    ShoppingNotFoundError,
    ShoppingPersistenceConflictError,
    ShoppingPersistenceError,
)

ShoppingServiceProvider = Callable[[], ShoppingService]
# Module-level Body object avoids constructing dependency metadata per endpoint.
_EMPTY_SHOPPING_COMMAND = Body(default_factory=ShoppingGenerateRequest)

_LIFECYCLE_MESSAGES = {
    ShoppingLifecycle.MISSING: "Список покупок пока не сформирован.",
    ShoppingLifecycle.CURRENT: "Список покупок актуален.",
    ShoppingLifecycle.STALE: "Список покупок требует обновления.",
}
_STALE_MESSAGES = {
    "PLAN_REVISION_CHANGED": "План питания изменился.",
    "SOURCE_INVALID": "Исходные данные больше не подходят для расчёта.",
    "SOURCE_CHANGED": "Продукты дома или другие исходные данные изменились.",
}
_STATUS_MESSAGES = {
    "COMPLETE": "Все необходимые количества продуктов рассчитаны.",
    "INCOMPLETE": "Часть потребностей требует уточнения.",
}
_UNRESOLVED_MESSAGES = {
    "ASSEMBLY_UNSUPPORTED": "Состав блюда пока невозможно определить.",
    "LEFTOVER_SUPPLY_UNVERIFIED": "Наличие готового остатка не подтверждено.",
    "PREPARED_SUPPLY_UNVERIFIED": "Наличие заготовки не подтверждено.",
    "READY_MEAL_UNRESOLVED": "Не удалось определить покупку готовой еды.",
}
_WARNING_MESSAGES = {
    "ESTIMATED_STOCK": "Количество продукта дома указано приблизительно.",
    "EXPIRY_UNKNOWN": "Срок хранения продукта дома неизвестен.",
    "EXPIRED_STOCK": "Срок хранения продукта дома истёк.",
    "INCOMPATIBLE_UNIT": "Единица учёта продукта дома несовместима.",
    "EXPIRES_BEFORE_REQUIRED_DATE": (
        "Продукт дома утратит пригодность до нужного дня."
    ),
}


def _message(mapping: dict[str, str], code: str) -> str:
    try:
        return mapping[code]
    except KeyError as exc:
        # Unknown machine codes cannot become English consumer labels.
        raise ShoppingPersistenceError(
            "Отсутствует русское описание состояния списка покупок."
        ) from exc


def _error_detail(code: str, message: str, next_action: str) -> dict[str, str]:
    return {"code": code, "message": message, "next_action": next_action}


def _reject_unsupported_query_parameters(request: Request) -> None:
    """PR9-C defines no query parameters on any Shopping endpoint."""
    if request.query_params:
        raise HTTPException(
            status_code=422,
            detail=_error_detail(
                "SHOPPING_INVALID_REQUEST",
                "Некорректные параметры списка покупок.",
                "Проверьте идентификаторы и формат запроса.",
            ),
        )


@contextmanager
def _errors():
    try:
        yield
    except ShoppingNotFoundError as exc:
        raise HTTPException(
            404,
            detail=_error_detail(
                "SHOPPING_NOT_FOUND",
                "Список покупок или план питания не найден.",
                "Проверьте выбранную семью и план питания.",
            ),
        ) from exc
    except (ShoppingPersistenceConflictError, ShoppingCalculationError) as exc:
        raise HTTPException(
            409,
            detail=_error_detail(
                "SHOPPING_CONFLICT",
                "Список покупок не удалось рассчитать из текущих данных.",
                "Обновите план и повторите попытку.",
            ),
        ) from exc
    except ShoppingPersistenceError as exc:
        raise HTTPException(
            503,
            detail=_error_detail(
                "SHOPPING_UNAVAILABLE",
                "Не удалось получить список покупок.",
                "Попробуйте ещё раз позднее.",
            ),
        ) from exc


def _provenance(
    detail: ShoppingListDetail,
) -> tuple[list[ShoppingWarningResponse], list[ShoppingAllocationResponse]]:
    """Strict, allowlisted public projection; never expose raw provenance JSON."""
    try:
        source = json.loads(detail.shopping_list.provenance_json)
        if (
            not isinstance(source, dict)
            or source["schema"] != "SHOPPING_SOURCE_SNAPSHOT_V1"
        ):
            raise ValueError("Unsupported Shopping source snapshot")
        raw_warnings = source["warnings"]
        raw_allocations = source["allocations"]
        if not isinstance(raw_warnings, list) or not isinstance(raw_allocations, list):
            raise TypeError("Invalid Shopping provenance collections")
        warnings = [
            ShoppingWarningResponse(
                code=entry["code"],
                message=_message(_WARNING_MESSAGES, entry["code"]),
                pantry_item_id=entry["pantry_item_id"],
                meal_event_id=entry["meal_event_id"],
                required_date=entry["required_date"],
            )
            for entry in raw_warnings
        ]
        allocations = [
            ShoppingAllocationResponse(
                meal_event_id=entry["meal_event_id"],
                pantry_item_id=entry["pantry_item_id"],
                food_ingredient_id=entry["food_ingredient_id"],
                quantity=_exact_quantity(entry["quantity"]),
            )
            for entry in raw_allocations
        ]
        return warnings, allocations
    except ShoppingPersistenceError:
        raise
    except (KeyError, TypeError, ValueError, InvalidOperation) as exc:
        raise ShoppingPersistenceError(
            "Некорректные сохранённые данные происхождения списка покупок."
        ) from exc


def _exact_quantity(value: object) -> str:
    if not isinstance(value, str):
        raise TypeError("Shopping provenance quantity must be a decimal string")
    decimal = Decimal(value)
    if not decimal.is_finite() or decimal < 0:
        raise ValueError("Shopping provenance quantity is invalid")
    return value


def _detail_response(
    detail: ShoppingListDetail,
    current: ShoppingCurrent,
) -> ShoppingDetailResponse:
    header = detail.shopping_list
    current_id = current.detail.shopping_list.id if current.detail else None
    lifecycle = (
        ShoppingLifecycle.CURRENT
        if not current.stale and current_id == header.id
        else ShoppingLifecycle.STALE
    )
    reason = current.reason if current.stale else None
    # A different immutable historical list is noncurrent despite a current
    # source match elsewhere; its reason is HISTORY rather than an invented
    # Pantry change.
    if lifecycle is ShoppingLifecycle.STALE and reason is None:
        reason = "HISTORICAL_SNAPSHOT"
    reason_message = (
        "Сохранена другая версия списка покупок."
        if reason == "HISTORICAL_SNAPSHOT"
        else _message(_STALE_MESSAGES, reason)
        if reason
        else None
    )
    warnings, allocations = _provenance(detail)
    return ShoppingDetailResponse(
        id=header.id,
        household_id=header.household_id,
        meal_plan_id=header.meal_plan_id,
        source_plan_revision_number=header.source_plan_revision_number,
        source_pantry_snapshot_hash=header.source_pantry_snapshot_hash,
        as_of_date=header.as_of_date,
        engine_version=header.engine_version,
        pantry_policy_version=header.pantry_policy_version,
        config_fingerprint=header.config_fingerprint,
        source_fingerprint=header.source_fingerprint,
        content_fingerprint=header.content_fingerprint,
        status=header.status,
        status_message=_message(_STATUS_MESSAGES, str(header.status)),
        price_status=header.price_status,
        price_status_message="Стоимость продуктов пока неизвестна.",
        lifecycle=lifecycle,
        lifecycle_message=_LIFECYCLE_MESSAGES[lifecycle],
        stale_reason=reason,
        stale_reason_message=reason_message,
        supersedes_list_id=header.supersedes_list_id,
        created_at=header.created_at,
        items=[
            ShoppingItemResponse(
                id=row.id,
                shopping_list_id=row.shopping_list_id,
                food_ingredient_id=row.food_ingredient_id,
                form_basis=row.form_basis,
                unit=row.unit,
                required_quantity=str(row.required_quantity),
                pantry_available_quantity=str(row.pantry_available_quantity),
                purchase_quantity=str(row.purchase_quantity),
                ordinal=row.ordinal,
            )
            for row in detail.items
        ],
        unresolved=[
            ShoppingUnresolvedResponse(
                id=row.id,
                shopping_list_id=row.shopping_list_id,
                meal_event_id=row.meal_event_id,
                source_kind=row.source_kind,
                reason=row.reason,
                message=_message(_UNRESOLVED_MESSAGES, str(row.reason)),
                ordinal=row.ordinal,
            )
            for row in detail.unresolved
        ],
        warnings=warnings,
        allocations=allocations,
    )


def _current_response(current: ShoppingCurrent) -> ShoppingCurrentResponse:
    if current.detail is None:
        return ShoppingCurrentResponse(
            lifecycle=ShoppingLifecycle.MISSING,
            lifecycle_message=_LIFECYCLE_MESSAGES[ShoppingLifecycle.MISSING],
            stale_reason=None,
            stale_reason_message=None,
            detail=None,
        )
    lifecycle = ShoppingLifecycle.STALE if current.stale else ShoppingLifecycle.CURRENT
    detail = _detail_response(current.detail, current)
    return ShoppingCurrentResponse(
        lifecycle=lifecycle,
        lifecycle_message=_LIFECYCLE_MESSAGES[lifecycle],
        stale_reason=detail.stale_reason,
        stale_reason_message=detail.stale_reason_message,
        detail=detail,
    )


def create_shopping_router(service_provider: ShoppingServiceProvider) -> APIRouter:
    router = APIRouter(
        prefix="/households/{household_id}",
        tags=["shopping"],
        dependencies=[Depends(_reject_unsupported_query_parameters)],
    )

    @router.post(
        "/meal-plans/{plan_id}/shopping-lists",
        response_model=ShoppingDetailResponse,
    )
    def generate(
        household_id: UUID,
        plan_id: UUID,
        payload: ShoppingGenerateRequest = _EMPTY_SHOPPING_COMMAND,
    ) -> ShoppingDetailResponse:
        del payload
        with _errors():
            service = service_provider()
            detail = service.generate(household_id, plan_id)
            return _detail_response(detail, service.get_current(household_id, plan_id))

    @router.get(
        "/shopping-lists/{list_id}",
        response_model=ShoppingDetailResponse,
    )
    def get_detail(household_id: UUID, list_id: UUID) -> ShoppingDetailResponse:
        with _errors():
            service = service_provider()
            detail = service.get_detail(household_id, list_id)
            return _detail_response(
                detail,
                service.get_current(household_id, detail.shopping_list.meal_plan_id),
            )

    @router.get(
        "/meal-plans/{plan_id}/shopping-lists/current",
        response_model=ShoppingCurrentResponse,
    )
    def get_current(household_id: UUID, plan_id: UUID) -> ShoppingCurrentResponse:
        with _errors():
            return _current_response(
                service_provider().get_current(household_id, plan_id)
            )

    @router.post(
        "/meal-plans/{plan_id}/shopping-lists/regenerate",
        response_model=ShoppingDetailResponse,
    )
    def regenerate(
        household_id: UUID,
        plan_id: UUID,
        payload: ShoppingGenerateRequest = _EMPTY_SHOPPING_COMMAND,
    ) -> ShoppingDetailResponse:
        del payload
        with _errors():
            service = service_provider()
            detail = service.regenerate(household_id, plan_id)
            return _detail_response(detail, service.get_current(household_id, plan_id))

    @router.get(
        "/meal-plans/{plan_id}/shopping-lists",
        response_model=ShoppingHistoryResponse,
    )
    def history(household_id: UUID, plan_id: UUID) -> ShoppingHistoryResponse:
        with _errors():
            service = service_provider()
            details = service.list_history(household_id, plan_id)
            if not details:
                return ShoppingHistoryResponse(shopping_lists=[])
            current = service.get_current(household_id, plan_id)
            return ShoppingHistoryResponse(
                shopping_lists=[_detail_response(detail, current) for detail in details]
            )

    return router
