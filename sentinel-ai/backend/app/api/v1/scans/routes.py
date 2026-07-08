from fastapi import APIRouter

from app.shared.api_response import ApiResponse

router = APIRouter()


@router.get("", response_model=ApiResponse[list[dict[str, str]]])
def list_scans_placeholder() -> ApiResponse[list[dict[str, str]]]:
    return ApiResponse(data=[], message="Scan API scaffold created.")
