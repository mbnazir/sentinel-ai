from dataclasses import dataclass, field
from datetime import datetime

from app.investigations.domain.priority import InvestigationPriority
from app.investigations.domain.status import InvestigationStatus


@dataclass(frozen=True)
class InvestigationEvidenceLink:
    evidence_id: str
    evidence_type: str
    source: str
    summary: str


@dataclass(frozen=True)
class InvestigationComment:
    author_id: str
    body: str
    created_at: datetime


@dataclass(frozen=True)
class InvestigationCase:
    case_id: str
    organization_id: str
    title: str
    entity_type: str
    entity_id: str
    risk_score: int
    priority: InvestigationPriority
    status: InvestigationStatus
    assigned_to: str | None
    created_at: datetime
    updated_at: datetime
    summary: str
    evidence_links: list[InvestigationEvidenceLink] = field(default_factory=list)
    comments: list[InvestigationComment] = field(default_factory=list)
