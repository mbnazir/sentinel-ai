from fastapi import APIRouter

from app.shared.api_response import ApiResponse

router = APIRouter()


@router.post("/login", response_model=ApiResponse[dict[str, str]])
def login_placeholder() -> ApiResponse[dict[str, str]]:
    return ApiResponse(data={"status": "authentication scaffold created"})
