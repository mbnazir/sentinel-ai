from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database.session import get_db_session
from app.shared.api_response import ApiResponse
from app.timeline.api.mapper import build_timeline_visualization_response
from app.timeline.repositories.timeline_activity_repository import TimelineActivityRepository

router = APIRouter()


@router.get("/{login_session_external_id}", response_model=ApiResponse[dict])
def get_timeline(
    login_session_external_id: str,
    session: Session = Depends(get_db_session),
) -> ApiResponse[dict]:
    activities = TimelineActivityRepository(session).list_by_login_session(login_session_external_id)
    return ApiResponse(
        data=build_timeline_visualization_response(login_session_external_id, activities)
    )
