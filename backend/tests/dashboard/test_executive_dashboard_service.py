from datetime import datetime, timezone

from app.dashboard.services.executive_dashboard_service import ExecutiveDashboardService
from app.investigations.domain.case import InvestigationCase
from app.investigations.domain.priority import InvestigationPriority
from app.investigations.domain.status import InvestigationStatus


def case(case_id: str, entity_id: str, score: int, priority: InvestigationPriority, status: InvestigationStatus) -> InvestigationCase:
    now = datetime(2026, 7, 1, tzinfo=timezone.utc)
    return InvestigationCase(
        case_id=case_id,
        organization_id="ORG-1",
        title="Case",
        entity_type="agent",
        entity_id=entity_id,
        risk_score=score,
        priority=priority,
        status=status,
        assigned_to=None,
        created_at=now,
        updated_at=now,
        summary="summary",
        evidence_links=[],
        comments=[],
    )


def test_executive_dashboard_summary() -> None:
    cases = [
        case("C1", "A1", 90, InvestigationPriority.CRITICAL, InvestigationStatus.NEW),
        case("C2", "A1", 70, InvestigationPriority.HIGH, InvestigationStatus.ASSIGNED),
        case("C3", "A2", 35, InvestigationPriority.MEDIUM, InvestigationStatus.CLOSED),
    ]

    summary = ExecutiveDashboardService().summarize(cases)

    assert summary.total_cases == 3
    assert summary.open_cases == 2
    assert summary.critical_cases == 1
    assert summary.high_risk_cases == 1
    assert summary.risk_distribution.critical == 1
    assert summary.risk_distribution.high_risk == 1
    assert summary.top_entities[0].entity_id == "A1"
