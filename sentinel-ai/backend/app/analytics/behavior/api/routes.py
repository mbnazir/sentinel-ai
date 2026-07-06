from fastapi import APIRouter
from app.shared.api_response import ApiResponse

router = APIRouter()

@router.get("/agent/{agent_external_id}", response_model=ApiResponse[dict[str, str]])
def get_agent_behavior_placeholder(agent_external_id: str) -> ApiResponse[dict[str, str]]:
    return ApiResponse(
        data={"agent_external_id": agent_external_id, "status": "behavior analytics API scaffold created"},
        message="Repository-backed behavior analytics will be wired after risk fact persistence is finalized.",
    )

@router.get("/supervisor/{supervisor_external_id}", response_model=ApiResponse[dict[str, str]])
def get_supervisor_behavior_placeholder(supervisor_external_id: str) -> ApiResponse[dict[str, str]]:
    return ApiResponse(
        data={"supervisor_external_id": supervisor_external_id, "status": "behavior analytics API scaffold created"},
        message="Repository-backed behavior analytics will be wired after risk fact persistence is finalized.",
    )
