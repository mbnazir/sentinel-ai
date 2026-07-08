from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.anomaly.cases.anomaly_case_attachment_service import AnomalyCaseAttachmentService
from app.anomaly.persistence.anomaly_finding_repository import AnomalyFindingRepository
from app.core.database.session import get_db_session
from app.infrastructure.persistence.repositories.investigation_repository import InvestigationRepository
from app.investigations.api.mapper import investigation_case_to_response
from app.investigations.api.schemas import InvestigationCaseResponse
from app.shared.api_response import ApiResponse

router = APIRouter()


class AttachAnomalyCaseRequest(BaseModel):
    organization_id: str
    entity_type: str
    entity_id: str
    minimum_score: int = 61


@router.post("/attach-case", response_model=ApiResponse[InvestigationCaseResponse | None])
def attach_anomaly_to_case(
    request: AttachAnomalyCaseRequest,
    session: Session = Depends(get_db_session),
) -> ApiResponse[InvestigationCaseResponse | None]:
    anomaly_score = AnomalyFindingRepository(session).get_latest(
        organization_id=request.organization_id,
        entity_type=request.entity_type,
        entity_id=request.entity_id,
    )

    if anomaly_score is None:
        return ApiResponse(data=None, message="No anomaly finding found for entity.")

    case = AnomalyCaseAttachmentService(
        repository=InvestigationRepository(session),
    ).attach_or_create_case(
        organization_id=request.organization_id,
        anomaly_score=anomaly_score,
        minimum_score=request.minimum_score,
    )

    return ApiResponse(
        data=investigation_case_to_response(case) if case else None,
        message="Anomaly did not meet case creation threshold." if case is None else None,
    )
