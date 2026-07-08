from app.investigations.api.schemas import InvestigationCaseResponse, InvestigationCommentResponse, InvestigationEvidenceResponse
from app.investigations.domain.case import InvestigationCase

def investigation_case_to_response(case: InvestigationCase) -> InvestigationCaseResponse:
    return InvestigationCaseResponse(
        case_id=case.case_id, organization_id=case.organization_id, title=case.title,
        entity_type=case.entity_type, entity_id=case.entity_id, risk_score=case.risk_score,
        priority=case.priority.value, status=case.status.value, assigned_to=case.assigned_to,
        created_at=case.created_at, updated_at=case.updated_at, summary=case.summary,
        evidence_links=[InvestigationEvidenceResponse(evidence_id=l.evidence_id, evidence_type=l.evidence_type, source=l.source, summary=l.summary) for l in case.evidence_links],
        comments=[InvestigationCommentResponse(author_id=c.author_id, body=c.body, created_at=c.created_at) for c in case.comments],
    )
