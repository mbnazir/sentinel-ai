from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class WorkspaceTimelineEvent:
    event_id: str
    event_type: str
    title: str
    description: str
    occurred_at: datetime
    actor_id: str | None = None
    metadata: dict | None = None


@dataclass(frozen=True)
class WorkspaceEvidenceItem:
    evidence_id: str
    evidence_type: str
    source: str
    summary: str
    severity: str = "info"


@dataclass(frozen=True)
class WorkspaceNote:
    author_id: str
    body: str
    created_at: datetime


@dataclass(frozen=True)
class InvestigationWorkspace:
    case_id: str
    title: str
    entity_type: str
    entity_id: str
    risk_score: int
    priority: str
    status: str
    assigned_to: str | None
    summary: str
    evidence: list[WorkspaceEvidenceItem]
    notes: list[WorkspaceNote]
    timeline: list[WorkspaceTimelineEvent]
