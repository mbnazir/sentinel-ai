from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.anomaly.persistence.anomaly_finding_repository import AnomalyFindingRepository
from app.core.database.session import get_db_session
from app.shared.api_response import ApiResponse

router = APIRouter()


@router.get("/findings", response_model=ApiResponse[list[dict]])
def list_anomaly_findings(
    organization_id: str,
    entity_type: str | None = None,
    limit: int = 100,
    session: Session = Depends(get_db_session),
) -> ApiResponse[list[dict]]:
    findings = AnomalyFindingRepository(session).list_active(
        organization_id=organization_id,
        entity_type=entity_type,
        limit=limit,
    )
    return ApiResponse(
        data=[
            {
                "entity_type": item.entity_type,
                "entity_id": item.entity_id,
                "score": item.score,
                "severity": item.severity.value,
                "summary": item.summary,
                "anomalies": [
                    {
                        "feature_name": anomaly.feature_name,
                        "value": anomaly.value,
                        "baseline": anomaly.baseline,
                        "deviation": anomaly.deviation,
                        "contribution": anomaly.contribution,
                        "reason": anomaly.reason,
                    }
                    for anomaly in item.anomalies
                ],
            }
            for item in findings
        ]
    )
