from app.ai.domain.investigation_narrative import InvestigationNarrative
from app.ai.services.investigation_narrative_service import InvestigationNarrativeService
from app.infrastructure.persistence.repositories.investigation_repository import InvestigationRepository
from app.infrastructure.persistence.repositories.narrative_repository import NarrativeRepository
from app.investigations.domain.case import InvestigationCase
from app.investigations.domain.status import InvestigationStatus
from app.investigations.services.investigation_case_service import InvestigationCaseService
from app.scoring.domain.risk_assessment import RiskAssessment

class InvestigationWorkflowService:
    def __init__(self, investigation_repository: InvestigationRepository, narrative_repository: NarrativeRepository) -> None:
        self.investigation_repository = investigation_repository
        self.narrative_repository = narrative_repository
        self.case_service = InvestigationCaseService()
        self.narrative_service = InvestigationNarrativeService()

    def create_case_from_assessment(self, organization_id: str, assessment: RiskAssessment) -> InvestigationCase:
        return self.investigation_repository.save(self.case_service.create_from_risk_assessment(organization_id, assessment))

    def assign_case(self, case_id: str, assignee_id: str) -> InvestigationCase:
        case = self._require_case(case_id)
        return self.investigation_repository.save(self.case_service.assign(case, assignee_id))

    def transition_case(self, case_id: str, target_status: InvestigationStatus) -> InvestigationCase:
        case = self._require_case(case_id)
        return self.investigation_repository.save(self.case_service.transition(case, target_status))

    def add_comment(self, case_id: str, author_id: str, body: str) -> InvestigationCase:
        case = self._require_case(case_id)
        return self.investigation_repository.save(self.case_service.add_comment(case, author_id, body))

    async def generate_narrative(self, case_id: str) -> InvestigationNarrative:
        narrative = await self.narrative_service.generate_for_case(self._require_case(case_id))
        return self.narrative_repository.save(narrative)

    def _require_case(self, case_id: str) -> InvestigationCase:
        case = self.investigation_repository.get_by_case_id(case_id)
        if case is None:
            raise ValueError(f"Investigation case {case_id} not found.")
        return case
