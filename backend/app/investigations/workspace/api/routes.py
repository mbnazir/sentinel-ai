from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database.session import get_db_session
from app.infrastructure.persistence.repositories.investigation_repository import InvestigationRepository
from app.investigations.workspace.api.schemas import (
    InvestigationWorkspaceResponse,
    WorkspaceEvidenceItemResponse,
    WorkspaceNoteResponse,
    WorkspaceTimelineEventResponse,
)
from app.investigations.workspace.workspace_service import InvestigationWorkspaceService
from app.shared.api_response import ApiResponse

router = APIRouter()


@router.get("/{case_id}", response_model=ApiResponse[InvestigationWorkspaceResponse])
def get_workspace(
    case_id: str,
    session: Session = Depends(get_db_session),
) -> ApiResponse[InvestigationWorkspaceResponse]:
    try:
        workspace = InvestigationWorkspaceService(
            InvestigationRepository(session)
        ).get_workspace(case_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return ApiResponse(
        data=InvestigationWorkspaceResponse(
            case_id=workspace.case_id,
            title=workspace.title,
            entity_type=workspace.entity_type,
            entity_id=workspace.entity_id,
            risk_score=workspace.risk_score,
            priority=workspace.priority,
            status=workspace.status,
            assigned_to=workspace.assigned_to,
            summary=workspace.summary,
            evidence=[
                WorkspaceEvidenceItemResponse(
                    evidence_id=item.evidence_id,
                    evidence_type=item.evidence_type,
                    source=item.source,
                    summary=item.summary,
                    severity=item.severity,
                )
                for item in workspace.evidence
            ],
            notes=[
                WorkspaceNoteResponse(
                    author_id=item.author_id,
                    body=item.body,
                    created_at=item.created_at,
                )
                for item in workspace.notes
            ],
            timeline=[
                WorkspaceTimelineEventResponse(
                    event_id=item.event_id,
                    event_type=item.event_type,
                    title=item.title,
                    description=item.description,
                    occurred_at=item.occurred_at,
                    actor_id=item.actor_id,
                    metadata=item.metadata,
                )
                for item in workspace.timeline
            ],
        )
    )
