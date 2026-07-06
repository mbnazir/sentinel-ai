from fastapi import APIRouter

from app.shared.api_response import ApiResponse

router = APIRouter()


@router.post("/investigations/{case_id}/narrative", response_model=ApiResponse[dict[str, str]])
async def generate_investigation_narrative_placeholder(case_id: str) -> ApiResponse[dict[str, str]]:
    return ApiResponse(
        data={"case_id": case_id, "status": "AI narrative API scaffold created"},
        message="Persistence-backed narrative generation will be wired after case repositories are implemented.",
    )
