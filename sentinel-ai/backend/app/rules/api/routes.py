from fastapi import APIRouter
from app.rules.engine.default_rules import build_default_rules
from app.shared.api_response import ApiResponse

router = APIRouter()

@router.get("", response_model=ApiResponse[list[dict[str, str | int]]])
def list_rules() -> ApiResponse[list[dict[str, str | int]]]:
    rules = build_default_rules()
    return ApiResponse(
        data=[
            {
                "rule_id": rule.rule_id,
                "name": rule.name,
                "severity": rule.severity.value,
                "score": rule.score,
            }
            for rule in rules
        ]
    )
