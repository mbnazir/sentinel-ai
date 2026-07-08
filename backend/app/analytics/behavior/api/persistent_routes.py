from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.analytics.behavior.persistence.behavior_repository import BehaviorRepository
from app.core.database.session import get_db_session
from app.shared.api_response import ApiResponse

router = APIRouter()


@router.get("/profiles/{entity_type}", response_model=ApiResponse[list[dict]])
def list_behavior_profiles(
    entity_type: str,
    organization_id: str,
    limit: int = 100,
    session: Session = Depends(get_db_session),
) -> ApiResponse[list[dict]]:
    profiles = BehaviorRepository(session).latest_profiles(
        organization_id=organization_id,
        entity_type=entity_type,
        limit=limit,
    )
    return ApiResponse(
        data=[
            {
                "entity_type": profile.entity_type,
                "entity_id": profile.entity_id,
                "window_days": profile.window_days,
                "date_to": profile.date_to.isoformat(),
                "behavior_score": profile.behavior_score,
                "behavior_level": profile.behavior_level.value,
                "summary": profile.summary,
                "metrics": [
                    {"name": metric.name, "value": metric.value, "unit": metric.unit}
                    for metric in profile.metrics
                ],
            }
            for profile in profiles
        ]
    )
