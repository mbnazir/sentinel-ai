from datetime import datetime, timezone

from app.investigations.domain.case import InvestigationCase
from app.investigations.domain.priority import InvestigationPriority
from app.investigations.domain.status import InvestigationStatus
from app.platform.events.event_models import EventType
from app.platform.events.integration.investigation_event_factory import InvestigationEventFactory


def test_case_created_event() -> None:
    now = datetime.now(timezone.utc)
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
        evidence_links=[],
        comments=[],
    )

    event = InvestigationEventFactory().case_created(case)

    assert event.event_type == EventType.CASE_CREATED
    assert event.payload["case_id"] == "CASE1"
