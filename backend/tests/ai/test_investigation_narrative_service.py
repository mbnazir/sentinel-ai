from datetime import datetime, timezone

import pytest

from app.ai.services.investigation_narrative_service import InvestigationNarrativeService
from app.investigations.domain.case import InvestigationCase, InvestigationEvidenceLink
from app.investigations.domain.priority import InvestigationPriority
from app.investigations.domain.status import InvestigationStatus


@pytest.mark.asyncio
async def test_investigation_narrative_service_generates_mock_summary() -> None:
    now = datetime.now(timezone.utc)
    case = InvestigationCase(
        case_id="SEN-1",
        organization_id="ORG-1",
        title="Case",
        entity_type="login_session",
        entity_id="LS-1",
        risk_score=90,
        priority=InvestigationPriority.CRITICAL,
        status=InvestigationStatus.NEW,
        assigned_to=None,
        created_at=now,
        updated_at=now,
        summary="Critical case.",
        evidence_links=[
            InvestigationEvidenceLink(
                evidence_id="E1",
                evidence_type="inserted_activity",
                source="Inserted Activity Rule",
                summary="Agent inserted 30 minutes.",
            )
        ],
        comments=[],
    )

    narrative = await InvestigationNarrativeService().generate_for_case(case)

    assert narrative.case_id == "SEN-1"
    assert "integrity risk" in narrative.executive_summary.lower()
    assert narrative.key_findings
    assert narrative.limitations
