from fastapi import APIRouter
from app.scoring.domain.risk_level import RiskLevel
from app.shared.api_response import ApiResponse

router = APIRouter()

@router.get("/levels", response_model=ApiResponse[list[dict[str, str | int]]])
def risk_levels() -> ApiResponse[list[dict[str, str | int]]]:
    return ApiResponse(
        data=[
            {"level": RiskLevel.NORMAL.value, "min_score": 0, "max_score": 20},
            {"level": RiskLevel.REVIEW.value, "min_score": 21, "max_score": 40},
            {"level": RiskLevel.SUSPICIOUS.value, "min_score": 41, "max_score": 60},
            {"level": RiskLevel.HIGH_RISK.value, "min_score": 61, "max_score": 80},
            {"level": RiskLevel.CRITICAL.value, "min_score": 81, "max_score": 100},
        ]
    )
