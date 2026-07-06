from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.ai.api.schemas import InvestigationNarrativeResponse
from app.core.database.session import get_db_session
from app.infrastructure.persistence.repositories.investigation_repository import InvestigationRepository
from app.infrastructure.persistence.repositories.narrative_repository import NarrativeRepository
from app.investigations.api.mapper import investigation_case_to_response
from app.investigations.api.schemas import AddInvestigationCommentRequest, AssignInvestigationRequest, InvestigationCaseResponse, TransitionInvestigationRequest
from app.investigations.domain.status import InvestigationStatus
from app.shared.api_response import ApiResponse
from app.workflows.investigation_workflow_service import InvestigationWorkflowService

router = APIRouter()

def get_workflow(session: Session = Depends(get_db_session)) -> InvestigationWorkflowService:
    return InvestigationWorkflowService(InvestigationRepository(session), NarrativeRepository(session))

@router.get("/investigations", response_model=ApiResponse[list[InvestigationCaseResponse]])
def list_cases(organization_id: str | None = None, session: Session = Depends(get_db_session)) -> ApiResponse[list[InvestigationCaseResponse]]:
    cases = InvestigationRepository(session).list(organization_id=organization_id)
    return ApiResponse(data=[investigation_case_to_response(case) for case in cases])

@router.post("/investigations/{case_id}/assign", response_model=ApiResponse[InvestigationCaseResponse])
def assign_case(case_id: str, request: AssignInvestigationRequest, workflow: InvestigationWorkflowService = Depends(get_workflow)) -> ApiResponse[InvestigationCaseResponse]:
    return ApiResponse(data=investigation_case_to_response(workflow.assign_case(case_id, request.assignee_id)))

@router.post("/investigations/{case_id}/transition", response_model=ApiResponse[InvestigationCaseResponse])
def transition_case(case_id: str, request: TransitionInvestigationRequest, workflow: InvestigationWorkflowService = Depends(get_workflow)) -> ApiResponse[InvestigationCaseResponse]:
    return ApiResponse(data=investigation_case_to_response(workflow.transition_case(case_id, InvestigationStatus(request.target_status))))

@router.post("/investigations/{case_id}/comments", response_model=ApiResponse[InvestigationCaseResponse])
def add_comment(case_id: str, request: AddInvestigationCommentRequest, workflow: InvestigationWorkflowService = Depends(get_workflow)) -> ApiResponse[InvestigationCaseResponse]:
    return ApiResponse(data=investigation_case_to_response(workflow.add_comment(case_id, request.author_id, request.body)))

@router.post("/investigations/{case_id}/narrative", response_model=ApiResponse[InvestigationNarrativeResponse])
async def generate_narrative(case_id: str, workflow: InvestigationWorkflowService = Depends(get_workflow)) -> ApiResponse[InvestigationNarrativeResponse]:
    narrative = await workflow.generate_narrative(case_id)
    return ApiResponse(data=InvestigationNarrativeResponse(case_id=narrative.case_id, executive_summary=narrative.executive_summary, key_findings=narrative.key_findings, evidence_summary=narrative.evidence_summary, recommended_next_steps=narrative.recommended_next_steps, limitations=narrative.limitations))
