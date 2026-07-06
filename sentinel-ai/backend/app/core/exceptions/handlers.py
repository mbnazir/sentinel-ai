from fastapi import FastAPI, Request
from fastapi.responses import ORJSONResponse

from app.core.exceptions.exceptions import SentinelError


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(SentinelError)
    async def sentinel_exception_handler(request: Request, exc: SentinelError) -> ORJSONResponse:
        return ORJSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "trace_id": request.headers.get("x-request-id"),
                },
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> ORJSONResponse:
        return ORJSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected error occurred.",
                    "trace_id": request.headers.get("x-request-id"),
                },
            },
        )
