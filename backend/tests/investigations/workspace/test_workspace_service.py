from datetime import datetime, timezone

from app.investigations.domain.case import InvestigationCase, InvestigationEvidenceLink
from app.investigations.domain.priority import InvestigationPriority
from app.investigations.domain.status import InvestigationStatus
from app.investigations.workspace.workspace_service import InvestigationWorkspaceService


class MemoryRepository:
    def __init__(self, case):
        self.case = case

    def get_by_case_id(self, case_id):
        return self.case if self.case.case_id == case_id else None


def test_workspace_service_builds_workspace() -> None:
    now = datetime(2026, 7, 1, tzinfo=timezone.utc)
    case = InvestigationCase(
        case_id="CASE1",
        organization_id="ORG1",
        title="Case",
        entity_type="agent",
        entity_id="A1",
        risk_score=80,
        priority=InvestigationPriority.HIGH,
        status=InvestigationStatus.NEW,
        assigned_to="U1",
        created_at=now,
        updated_at=now,
        summary="summary",
        evidence_links=[InvestigationEvidenceLink("E1", "behavior_anomaly", "Engine", "Finding")],
        comments=[],
    )

    workspace = InvestigationWorkspaceService(MemoryRepository(case)).get_workspace("CASE1")

    assert workspace.case_id == "CASE1"
    assert workspace.evidence[0].severity == "high"
    assert workspace.timeline
