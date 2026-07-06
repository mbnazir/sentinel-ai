from app.ai.domain.investigation_narrative import InvestigationNarrative
from app.audit.services.audit_log_service import AuditEvent, AuditLogService
from app.ai.services.investigation_narrative_service import InvestigationNarrativeService
from app.infrastructure.persistence.repositories.investigation_repository import InvestigationRepository
from app.infrastructure.persistence.repositories.narrative_repository import NarrativeRepository
from app.investigations.domain.case import InvestigationCase
from app.investigations.domain.status import InvestigationStatus
from app.investigations.services.investigation_case_service import InvestigationCaseService
from app.scoring.domain.risk_assessment import RiskAssessment

class InvestigationWorkflowService:
    def __init__(self, investigation_repository: InvestigationRepository, narrative_repository: NarrativeRepository, audit_log_service: AuditLogService | None = None) -> None:
        self.investigation_repository = investigation_repository
        self.narrative_repository = narrative_repository
        self.case_service = InvestigationCaseService()
        self.narrative_service = InvestigationNarrativeService()
        self.audit_log_service = audit_log_service or AuditLogService()

    def create_case_from_assessment(self, organization_id: str, assessment: RiskAssessment) -> InvestigationCase:
        case = self.investigation_repository.save(self.case_service.create_from_risk_assessment(organization_id, assessment))
        self._audit("investigation.case_created", organization_id, None, {"case_id": case.case_id, "entity_id": case.entity_id, "risk_score": case.risk_score})
        return case

    def assign_case(self, case_id: str, assignee_id: str) -> InvestigationCase:
        case = self._require_case(case_id)
        updated = self.investigation_repository.save(self.case_service.assign(case, assignee_id))
        self._audit("investigation.case_assigned", updated.organization_id, assignee_id, {"case_id": case_id, "assignee_id": assignee_id})
        return updated

    def transition_case(self, case_id: str, target_status: InvestigationStatus) -> InvestigationCase:
        case = self._require_case(case_id)
        updated = self.investigation_repository.save(self.case_service.transition(case, target_status))
        self._audit("investigation.case_transitioned", updated.organization_id, None, {"case_id": case_id, "from_status": case.status.value, "to_status": target_status.value})
        return updated

    def add_comment(self, case_id: str, author_id: str, body: str) -> InvestigationCase:
        case = self._require_case(case_id)
        updated = self.investigation_repository.save(self.case_service.add_comment(case, author_id, body))
        self._audit("investigation.comment_added", updated.organization_id, author_id, {"case_id": case_id})
        return updated

    async def generate_narrative(self, case_id: str) -> InvestigationNarrative:
        narrative = await self.narrative_service.generate_for_case(self._require_case(case_id))
        saved = self.narrative_repository.save(narrative)
        case = self._require_case(case_id)
        self._audit("investigation.narrative_generated", case.organization_id, None, {"case_id": case_id})
        return saved

    def _require_case(self, case_id: str) -> InvestigationCase:
        case = self.investigation_repository.get_by_case_id(case_id)
        if case is None:
            raise ValueError(f"Investigation case {case_id} not found.")
        return case


    def _audit(self, event_type: str, organization_id: str | None, user_id: str | None, payload: dict) -> None:
        self.audit_log_service.record(
            AuditEvent(
                event_type=event_type,
                organization_id=organization_id,
                user_id=user_id,
                payload=payload,
            )
        )
