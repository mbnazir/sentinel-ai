from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class InvestigationQueueItem:
    case_id: str
    title: str
    entity_type: str
    entity_id: str
    risk_score: int
    priority: str
    status: str
    assigned_to: str | None
    created_at: datetime
    sla_due_at: datetime
    sla_breached: bool
    queue_score: int
    reason: str


@dataclass(frozen=True)
class InvestigationQueueSummary:
    total_open: int
    unassigned: int
    sla_breached: int
    critical_open: int
    items: list[InvestigationQueueItem]
