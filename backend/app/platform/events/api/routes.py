from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database.session import get_db_session
from app.platform.events.event_models import EventType
from app.platform.events.event_repository import DomainEventRepository
from app.shared.api_response import ApiResponse

router = APIRouter()


@router.get("", response_model=ApiResponse[list[dict]])
def list_events(
    organization_id: str | None = None,
    event_type: str | None = None,
    limit: int = 100,
    session: Session = Depends(get_db_session),
) -> ApiResponse[list[dict]]:
    parsed_type = EventType(event_type) if event_type else None
    events = DomainEventRepository(session).list(
        organization_id=organization_id,
        event_type=parsed_type,
        limit=limit,
    )
    return ApiResponse(
        data=[
            {
                "event_id": event.event_id,
                "event_type": event.event_type.value,
                "organization_id": event.organization_id,
                "payload": event.payload,
                "correlation_id": event.correlation_id,
                "causation_id": event.causation_id,
                "occurred_at": event.occurred_at.isoformat(),
            }
            for event in events
        ]
    )
