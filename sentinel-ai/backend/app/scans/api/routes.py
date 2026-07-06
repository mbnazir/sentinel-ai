from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database.session import get_db_session
from app.scans.api.schemas import RunScanRequest, ScanSummaryResponse, SessionScanResultResponse
from app.scans.domain.scan_models import ScanRequest
from app.scans.services.normalized_scan_repository import NormalizedScanRepository
from app.scans.services.scan_pipeline_service import ScanPipelineService
from app.shared.api_response import ApiResponse

router = APIRouter()


@router.post("/run", response_model=ApiResponse[ScanSummaryResponse])
def run_scan(
    request: RunScanRequest,
    session: Session = Depends(get_db_session),
) -> ApiResponse[ScanSummaryResponse]:
    summary = ScanPipelineService(NormalizedScanRepository(session)).run(
        ScanRequest(
            organization_id=request.organization_id,
            shift_date_from=request.shift_date_from,
            shift_date_to=request.shift_date_to,
            create_cases=request.create_cases,
            minimum_case_score=request.minimum_case_score,
        )
    )

    return ApiResponse(
        data=ScanSummaryResponse(
            scan_id=summary.scan_id,
            organization_id=summary.organization_id,
            status=summary.status.value,
            started_at=summary.started_at,
            finished_at=summary.finished_at,
            sessions_scanned=summary.sessions_scanned,
            cases_created=summary.cases_created,
            results=[
                SessionScanResultResponse(
                    login_session_external_id=item.login_session_external_id,
                    risk_score=item.risk_score,
                    risk_level=item.risk_level,
                    rule_count=item.rule_count,
                    case_created=item.case_created,
                    case_id=item.case_id,
                )
                for item in summary.results
            ],
            error_message=summary.error_message,
        )
    )
