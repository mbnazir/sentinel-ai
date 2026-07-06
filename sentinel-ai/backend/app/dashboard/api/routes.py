from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database.session import get_db_session
from app.dashboard.services.executive_dashboard_service import ExecutiveDashboardService
from app.infrastructure.persistence.repositories.investigation_repository import InvestigationRepository
from app.shared.api_response import ApiResponse

router = APIRouter()


@router.get("/executive", response_model=ApiResponse[dict])
def executive_dashboard(
    organization_id: str | None = None,
    session: Session = Depends(get_db_session),
) -> ApiResponse[dict]:
    cases = InvestigationRepository(session).list(organization_id=organization_id, limit=1000)
    summary = ExecutiveDashboardService().summarize(cases)

    return ApiResponse(
        data={
            "total_cases": summary.total_cases,
            "open_cases": summary.open_cases,
            "critical_cases": summary.critical_cases,
            "high_risk_cases": summary.high_risk_cases,
            "average_risk_score": summary.average_risk_score,
            "risk_distribution": {
                "normal": summary.risk_distribution.normal,
                "review": summary.risk_distribution.review,
                "suspicious": summary.risk_distribution.suspicious,
                "high_risk": summary.risk_distribution.high_risk,
                "critical": summary.risk_distribution.critical,
            },
            "trend": [
                {
                    "period": point.period,
                    "case_count": point.case_count,
                    "average_risk_score": point.average_risk_score,
                }
                for point in summary.trend
            ],
            "top_entities": [
                {
                    "entity_type": item.entity_type,
                    "entity_id": item.entity_id,
                    "risk_score": item.risk_score,
                    "case_count": item.case_count,
                }
                for item in summary.top_entities
            ],
        }
    )
