from fastapi import APIRouter

from app.identity import APP_SLUG, PRODUCT_NAME
from app.schemas.health import HealthResponse
from app.version import resolve_effective_app_version

router = APIRouter(tags=["health"])


def health_payload() -> dict[str, str]:
    return {
        "status": "ok",
        "app": APP_SLUG,
        "product_name": PRODUCT_NAME,
        "mode": "local-first",
        "version": resolve_effective_app_version(),
    }


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(**health_payload())
