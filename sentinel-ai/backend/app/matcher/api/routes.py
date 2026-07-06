from fastapi import APIRouter
from app.shared.api_response import ApiResponse

router = APIRouter()

@router.get("/{login_session_external_id}", response_model=ApiResponse[dict[str, str]])
def get_activity_matches_placeholder(login_session_external_id: str) -> ApiResponse[dict[str, str]]:
    return ApiResponse(
        data={
            "login_session_external_id": login_session_external_id,
            "status": "activity matching API scaffold created",
        },
        message="Repository-backed source matching will be wired after timeline persistence is finalized.",
    )
