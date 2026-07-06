from fastapi import APIRouter
from app.shared.api_response import ApiResponse

router = APIRouter()

@router.get("/{login_session_external_id}", response_model=ApiResponse[dict[str, str]])
def get_timeline_placeholder(login_session_external_id: str) -> ApiResponse[dict[str, str]]:
    return ApiResponse(
        data={"login_session_external_id": login_session_external_id, "status": "timeline API scaffold created"},
        message="Repository-backed timeline retrieval will be wired after normalized activity repositories are finalized.",
    )
