from fastapi import APIRouter

from app.api.v1.health.schemas import HealthResponse
from app.core.config.settings import settings
from app.shared.api_response import ApiResponse

router = APIRouter()


@router.get("", response_model=ApiResponse[HealthResponse])
def health() -> ApiResponse[HealthResponse]:
    return ApiResponse(
        data=HealthResponse(status="ok", service=settings.app_name, environment=settings.app_env)
    )


@router.get("/live", response_model=ApiResponse[HealthResponse])
def live() -> ApiResponse[HealthResponse]:
    return ApiResponse(
        data=HealthResponse(status="alive", service=settings.app_name, environment=settings.app_env)
    )


@router.get("/ready", response_model=ApiResponse[HealthResponse])
def ready() -> ApiResponse[HealthResponse]:
    return ApiResponse(
        data=HealthResponse(status="ready", service=settings.app_name, environment=settings.app_env)
    )
