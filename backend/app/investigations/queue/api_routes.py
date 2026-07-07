from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database.session import get_db_session
from app.infrastructure.persistence.repositories.investigation_repository import InvestigationRepository
from app.investigations.queue.investigation_queue_service import InvestigationQueueService
from app.shared.api_response import ApiResponse

router = APIRouter()


@router.get("", response_model=ApiResponse[dict])
def get_investigation_queue(
    organization_id: str,
    session: Session = Depends(get_db_session),
) -> ApiResponse[dict]:
    cases = InvestigationRepository(session).list(organization_id=organization_id, limit=1000)
    summary = InvestigationQueueService().build_queue(cases)

    return ApiResponse(
        data={
            "total_open": summary.total_open,
            "unassigned": summary.unassigned,
            "sla_breached": summary.sla_breached,
            "critical_open": summary.critical_open,
            "items": [
                {
                    "case_id": item.case_id,
                    "title": item.title,
                    "entity_type": item.entity_type,
                    "entity_id": item.entity_id,
                    "risk_score": item.risk_score,
                    "priority": item.priority,
                    "status": item.status,
                    "assigned_to": item.assigned_to,
                    "created_at": item.created_at.isoformat(),
                    "sla_due_at": item.sla_due_at.isoformat(),
                    "sla_breached": item.sla_breached,
                    "queue_score": item.queue_score,
                    "reason": item.reason,
                }
                for item in summary.items
            ],
        }
    )
