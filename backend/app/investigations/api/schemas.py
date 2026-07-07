from datetime import datetime

from pydantic import BaseModel


class InvestigationEvidenceResponse(BaseModel):
    evidence_id: str
    evidence_type: str
    source: str
    summary: str


class InvestigationCommentResponse(BaseModel):
    author_id: str
    body: str
    created_at: datetime


class InvestigationCaseResponse(BaseModel):
    case_id: str
    organization_id: str
    title: str
    entity_type: str
    entity_id: str
    risk_score: int
    priority: str
    status: str
    assigned_to: str | None
    created_at: datetime
    updated_at: datetime
    summary: str
    evidence_links: list[InvestigationEvidenceResponse]
    comments: list[InvestigationCommentResponse]


class AssignInvestigationRequest(BaseModel):
    assignee_id: str


class TransitionInvestigationRequest(BaseModel):
    target_status: str


class AddInvestigationCommentRequest(BaseModel):
    author_id: str
    body: str
