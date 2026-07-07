from datetime import datetime
from pydantic import BaseModel


class WorkspaceTimelineEventResponse(BaseModel):
    event_id: str
    event_type: str
    title: str
    description: str
    occurred_at: datetime
    actor_id: str | None
    metadata: dict | None


class WorkspaceEvidenceItemResponse(BaseModel):
    evidence_id: str
    evidence_type: str
    source: str
    summary: str
    severity: str


class WorkspaceNoteResponse(BaseModel):
    author_id: str
    body: str
    created_at: datetime


class InvestigationWorkspaceResponse(BaseModel):
    case_id: str
    title: str
    entity_type: str
    entity_id: str
    risk_score: int
    priority: str
    status: str
    assigned_to: str | None
    summary: str
    evidence: list[WorkspaceEvidenceItemResponse]
    notes: list[WorkspaceNoteResponse]
    timeline: list[WorkspaceTimelineEventResponse]
