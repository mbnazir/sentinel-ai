from datetime import datetime, timezone, timedelta

from app.investigations.domain.case import InvestigationCase
from app.investigations.domain.priority import InvestigationPriority
from app.investigations.domain.status import InvestigationStatus
from app.investigations.queue.investigation_queue_service import InvestigationQueueService


def make_case(case_id, priority, status, assigned_to=None, hours_old=1, risk_score=80):
    now = datetime(2026, 7, 1, 12, tzinfo=timezone.utc)
    created = now - timedelta(hours=hours_old)
    return InvestigationCase(
        case_id=case_id,
        organization_id="ORG1",
        title="Case",
        entity_type="agent",
        entity_id=case_id,
        risk_score=risk_score,
        priority=priority,
        status=status,
        assigned_to=assigned_to,
        created_at=created,
        updated_at=created,
        summary="summary",
        evidence_links=[],
        comments=[],
    )


def test_queue_orders_highest_operational_priority_first() -> None:
    now = datetime(2026, 7, 1, 12, tzinfo=timezone.utc)
    cases = [
        make_case("LOW", InvestigationPriority.LOW, InvestigationStatus.NEW, assigned_to="U1", risk_score=30),
        make_case("CRIT", InvestigationPriority.CRITICAL, InvestigationStatus.NEW, assigned_to=None, hours_old=10, risk_score=95),
    ]

    queue = InvestigationQueueService().build_queue(cases, now)

    assert queue.total_open == 2
    assert queue.items[0].case_id == "CRIT"
    assert queue.items[0].sla_breached is True
    assert queue.unassigned == 1


def test_queue_excludes_closed_cases() -> None:
    now = datetime(2026, 7, 1, 12, tzinfo=timezone.utc)
    cases = [
        make_case("OPEN", InvestigationPriority.HIGH, InvestigationStatus.NEW),
        make_case("CLOSED", InvestigationPriority.CRITICAL, InvestigationStatus.CLOSED),
    ]

    queue = InvestigationQueueService().build_queue(cases, now)

    assert queue.total_open == 1
    assert queue.items[0].case_id == "OPEN"
