from fastapi import APIRouter

from app.anomaly.api.schemas import (
    AnomalyScoreRequest,
    AnomalyScoreResponse,
    FeatureAnomalyResponse,
)
from app.anomaly.domain.anomaly_models import FeatureVector
from app.anomaly.services.anomaly_scorer import AnomalyScorer
from app.shared.api_response import ApiResponse

router = APIRouter()


@router.post("/score", response_model=ApiResponse[AnomalyScoreResponse])
def score_anomaly(request: AnomalyScoreRequest) -> ApiResponse[AnomalyScoreResponse]:
    target = FeatureVector(
        entity_type=request.target.entity_type,
        entity_id=request.target.entity_id,
        features={metric.name: metric.value for metric in request.target.metrics},
    )
    peers = [
        FeatureVector(
            entity_type=item.entity_type,
            entity_id=item.entity_id,
            features={metric.name: metric.value for metric in item.metrics},
        )
        for item in request.peers
    ]

    result = AnomalyScorer().score(target, peers)

    return ApiResponse(
        data=AnomalyScoreResponse(
            entity_type=result.entity_type,
            entity_id=result.entity_id,
            score=result.score,
            severity=result.severity.value,
            anomalies=[
                FeatureAnomalyResponse(
                    feature_name=item.feature_name,
                    value=item.value,
                    baseline=item.baseline,
                    deviation=item.deviation,
                    contribution=item.contribution,
                    reason=item.reason,
                )
                for item in result.anomalies
            ],
            summary=result.summary,
        )
    )
