from fastapi import APIRouter

from app.core.config import settings

router = APIRouter(tags=["platform"])


@router.get("/health")
async def health() -> dict[str, str]:
    return {
        "status": "healthy",
        "service": "sentinel-api",
        "version": settings.app_version,
        "environment": settings.environment,
    }
