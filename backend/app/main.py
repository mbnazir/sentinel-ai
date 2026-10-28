from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import database_healthcheck
from app.core.logging import configure_logging, logger
from app.core.middleware import CorrelationIdMiddleware
from app.core.redis import close_redis, redis_healthcheck



class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request:Request, call_next):
        response=await call_next(request)
        if settings.security_headers_enabled:
            response.headers["X-Content-Type-Options"]="nosniff"
            response.headers["X-Frame-Options"]="DENY"
            response.headers["Referrer-Policy"]="no-referrer"
            response.headers["Permissions-Policy"]="camera=(), microphone=(), geolocation=()"
            response.headers["Content-Security-Policy"]="default-src 'self'; frame-ancestors 'none'; object-src 'none'"
        return response

@asynccontextmanager
async def lifespan(_: FastAPI):
    configure_logging()
    logger.info("application_started", version=settings.app_version)
    yield
    await close_redis()
    logger.info("application_stopped")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    docs_url="/docs" if settings.docs_enabled else None,
    redoc_url=None,
    lifespan=lifespan,
)
app.add_middleware(CorrelationIdMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(CORSMiddleware, allow_origins=[x.strip() for x in settings.cors_origins.split(",") if x.strip()], allow_credentials=False, allow_methods=["GET","POST","PATCH"], allow_headers=["Authorization","Content-Type","X-Correlation-ID"])
app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/live", tags=["platform"])
async def live() -> dict[str, str]:
    return {"status": "alive"}


@app.get("/ready", tags=["platform"])
async def ready() -> dict[str, object]:
    database_ok = await database_healthcheck()
    redis_ok = await redis_healthcheck()
    status = "ready" if database_ok and redis_ok else "degraded"
    return {"status": status, "dependencies": {"postgres": database_ok, "redis": redis_ok}}
