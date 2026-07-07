from fastapi import APIRouter

from app.platform.routing.router_registry import ROUTER_REGISTRY
from app.shared.api_response import ApiResponse

router = APIRouter()


@router.get("/routes", response_model=ApiResponse[list[dict[str, object]]])
def registered_routes() -> ApiResponse[list[dict[str, object]]]:
    return ApiResponse(
        data=[
            {
                "prefix": definition.prefix,
                "tags": definition.tags,
                "route_count": len(definition.router.routes),
            }
            for definition in ROUTER_REGISTRY
        ]
    )
