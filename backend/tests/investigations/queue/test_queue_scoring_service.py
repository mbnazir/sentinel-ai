from datetime import datetime, timezone, timedelta

from app.investigations.domain.case import InvestigationCase
from app.investigations.domain.priority import InvestigationPriority
from app.investigations.domain.status import InvestigationStatus
from app.investigations.queue.queue_scoring_service import InvestigationQueueScoringService


def test_scoring_adds_sla_breach_and_unassigned_weight() -> None:
    now = datetime(2026, 7, 1, 12, tzinfo=timezone.utc)
    case = InvestigationCase(
        case_id="C1",
        organization_id="ORG1",
        title="Case",
        entity_type="agent",
        entity_id="A1",
        risk_score=80,
        priority=InvestigationPriority.HIGH,
        status=InvestigationStatus.NEW,
        assigned_to=None,
        created_at=now - timedelta(days=2),
        updated_at=now,
        summary="summary",
        evidence_links=[],
        comments=[],
    )

    score, reason = InvestigationQueueScoringService().score(case, now - timedelta(hours=1), now)

    assert score > 80
    assert "SLA breached" in reason
    assert "unassigned" in reason
