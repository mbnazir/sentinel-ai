from app.investigations.domain.case import InvestigationCase
from app.workflows.investigation_workflow_service import InvestigationWorkflowService
from app.scoring.domain.risk_assessment import RiskAssessment
from app.scoring.domain.risk_level import RiskLevel

class MemoryInvestigationRepository:
    def __init__(self) -> None:
        self.cases = {}
    def save(self, case: InvestigationCase) -> InvestigationCase:
        self.cases[case.case_id] = case
        return case
    def get_by_case_id(self, case_id: str):
        return self.cases.get(case_id)

class MemoryNarrativeRepository:
    def save(self, narrative):
        return narrative

def test_workflow_assigns_case() -> None:
    workflow = InvestigationWorkflowService(MemoryInvestigationRepository(), MemoryNarrativeRepository())
    assessment = RiskAssessment("login_session", "LS-1", 90, RiskLevel.CRITICAL, "Critical case.", [], [])
    case = workflow.create_case_from_assessment("ORG-1", assessment)
    assigned = workflow.assign_case(case.case_id, "U-1")
    assert assigned.assigned_to == "U-1"
    assert assigned.status.value == "assigned"
