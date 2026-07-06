from sqlalchemy.orm import Session
from app.investigations.domain.case import InvestigationCase, InvestigationComment, InvestigationEvidenceLink
from app.investigations.domain.priority import InvestigationPriority
from app.investigations.domain.status import InvestigationStatus
from app.infrastructure.persistence.models_investigations import InvestigationCaseModel, InvestigationCommentModel, InvestigationEvidenceLinkModel

class InvestigationRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def save(self, case: InvestigationCase) -> InvestigationCase:
        model = self.session.query(InvestigationCaseModel).filter_by(case_id=case.case_id).one_or_none()
        if model is None:
            model = InvestigationCaseModel(case_id=case.case_id)
            self.session.add(model)
        model.organization_id = case.organization_id
        model.title = case.title
        model.entity_type = case.entity_type
        model.entity_id = case.entity_id
        model.risk_score = case.risk_score
        model.priority = case.priority.value
        model.status = case.status.value
        model.assigned_to = case.assigned_to
        model.summary = case.summary
        model.created_at = case.created_at
        model.updated_at = case.updated_at
        self.session.query(InvestigationEvidenceLinkModel).filter_by(case_id=case.case_id).delete()
        self.session.query(InvestigationCommentModel).filter_by(case_id=case.case_id).delete()
        for link in case.evidence_links:
            self.session.add(InvestigationEvidenceLinkModel(case_id=case.case_id, evidence_id=link.evidence_id, evidence_type=link.evidence_type, source=link.source, summary=link.summary))
        for comment in case.comments:
            self.session.add(InvestigationCommentModel(case_id=case.case_id, author_id=comment.author_id, body=comment.body, created_at=comment.created_at))
        self.session.commit()
        return case

    def get_by_case_id(self, case_id: str) -> InvestigationCase | None:
        model = self.session.query(InvestigationCaseModel).filter_by(case_id=case_id).one_or_none()
        if model is None:
            return None
        links = self.session.query(InvestigationEvidenceLinkModel).filter_by(case_id=case_id).all()
        comments = self.session.query(InvestigationCommentModel).filter_by(case_id=case_id).all()
        return InvestigationCase(
            case_id=model.case_id, organization_id=model.organization_id, title=model.title,
            entity_type=model.entity_type, entity_id=model.entity_id, risk_score=model.risk_score,
            priority=InvestigationPriority(model.priority), status=InvestigationStatus(model.status),
            assigned_to=model.assigned_to, created_at=model.created_at, updated_at=model.updated_at,
            summary=model.summary,
            evidence_links=[InvestigationEvidenceLink(l.evidence_id, l.evidence_type, l.source, l.summary) for l in links],
            comments=[InvestigationComment(c.author_id, c.body, c.created_at) for c in comments],
        )

    def list(self, organization_id: str | None = None, limit: int = 100) -> list[InvestigationCase]:
        query = self.session.query(InvestigationCaseModel)
        if organization_id:
            query = query.filter_by(organization_id=organization_id)
        rows = query.order_by(InvestigationCaseModel.created_at.desc()).limit(limit).all()
        return [case for row in rows if (case := self.get_by_case_id(row.case_id)) is not None]
