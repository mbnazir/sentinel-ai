from datetime import datetime, timezone

from app.investigations.domain.case import (
    InvestigationCase,
    InvestigationComment,
    InvestigationEvidenceLink,
)
from app.investigations.domain.priority import InvestigationPriority
from app.investigations.domain.status import InvestigationStatus
from app.investigations.workspace.workspace_timeline_builder import WorkspaceTimelineBuilder


def test_timeline_builder_includes_case_evidence_and_notes() -> None:
    now = datetime(2026, 7, 1, tzinfo=timezone.utc)
    case = InvestigationCase(
        case_id="CASE1",
        organization_id="ORG1",
        title="Case",
        entity_type="agent",
        entity_id="A1",
        risk_score=90,
        priority=InvestigationPriority.CRITICAL,
        status=InvestigationStatus.NEW,
        assigned_to=None,
        created_at=now,
        updated_at=now,
        summary="summary",
        evidence_links=[
            InvestigationEvidenceLink("E1", "behavior_anomaly", "Anomaly Engine", "Anomaly found.")
        ],
        comments=[
            InvestigationComment("U1", "Review started.", now)
        ],
    )

    events = WorkspaceTimelineBuilder().build(case)

    assert [event.event_type for event in events] == [
        "case_created",
        "evidence_attached",
        "note_added",
    ]
