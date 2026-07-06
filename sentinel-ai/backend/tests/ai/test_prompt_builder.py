from datetime import datetime, timezone

from app.investigations.domain.case import InvestigationCase, InvestigationEvidenceLink
from app.investigations.domain.priority import InvestigationPriority
from app.investigations.domain.status import InvestigationStatus
from app.ai.services.prompt_builder import InvestigationPromptBuilder


def test_prompt_builder_includes_case_evidence() -> None:
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

    prompt = InvestigationPromptBuilder().build_case_prompt(case)

    assert "SEN-1" in prompt
    assert "Agent inserted 30 minutes." in prompt
    assert "Do not accuse" not in prompt
