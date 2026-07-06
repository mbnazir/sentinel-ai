from fastapi import APIRouter

from app.shared.api_response import ApiResponse

router = APIRouter()


@router.get("", response_model=ApiResponse[list[dict[str, str]]])
def list_investigations_placeholder() -> ApiResponse[list[dict[str, str]]]:
    return ApiResponse(
        data=[],
        message="Investigation case API scaffold created. Persistence-backed case listing comes next.",
    )


@router.get("/{case_id}", response_model=ApiResponse[dict[str, str]])
def get_investigation_placeholder(case_id: str) -> ApiResponse[dict[str, str]]:
    return ApiResponse(
        data={"case_id": case_id, "status": "investigation API scaffold created"},
        message="Persistence-backed case retrieval comes next.",
    )
