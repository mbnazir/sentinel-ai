from datetime import date, datetime, timezone

from sqlalchemy.orm import Session

from app.anomaly.domain.anomaly_models import (
    AnomalyScore,
    AnomalySeverity,
    FeatureAnomaly,
)
from app.infrastructure.persistence.models_anomaly import AnomalyFindingModel


class AnomalyFindingRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def save(
        self,
        organization_id: str,
        anomaly_score: AnomalyScore,
        window_days: int,
        as_of_date: date,
    ) -> AnomalyScore:
        model = (
            self.session.query(AnomalyFindingModel)
            .filter_by(
                organization_id=organization_id,
                entity_type=anomaly_score.entity_type,
                entity_id=anomaly_score.entity_id,
                window_days=window_days,
                as_of_date=as_of_date,
            )
            .one_or_none()
        )

        if model is None:
            model = AnomalyFindingModel(
                organization_id=organization_id,
                entity_type=anomaly_score.entity_type,
                entity_id=anomaly_score.entity_id,
                window_days=window_days,
                as_of_date=as_of_date,
            )
            self.session.add(model)

        model.anomaly_score = anomaly_score.score
        model.severity = anomaly_score.severity.value
        model.summary = anomaly_score.summary
        model.anomaly_count = len(anomaly_score.anomalies)
        model.is_active = anomaly_score.severity != AnomalySeverity.NONE
        model.details = {
            "anomalies": [
                {
                    "feature_name": item.feature_name,
                    "value": item.value,
                    "baseline": item.baseline,
                    "deviation": item.deviation,
                    "contribution": item.contribution,
                    "reason": item.reason,
                }
                for item in anomaly_score.anomalies
            ]
        }
        model.updated_at = datetime.now(timezone.utc)

        self.session.commit()
        return anomaly_score

    def list_active(
        self,
        organization_id: str,
        entity_type: str | None = None,
        limit: int = 100,
    ) -> list[AnomalyScore]:
        query = self.session.query(AnomalyFindingModel).filter_by(
            organization_id=organization_id,
            is_active=True,
        )
        if entity_type:
            query = query.filter_by(entity_type=entity_type)

        rows = (
            query.order_by(AnomalyFindingModel.anomaly_score.desc(), AnomalyFindingModel.as_of_date.desc())
            .limit(limit)
            .all()
        )
        return [self._to_domain(row) for row in rows]

    def get_latest(
        self,
        organization_id: str,
        entity_type: str,
        entity_id: str,
    ) -> AnomalyScore | None:
        row = (
            self.session.query(AnomalyFindingModel)
            .filter_by(
                organization_id=organization_id,
                entity_type=entity_type,
                entity_id=entity_id,
            )
            .order_by(AnomalyFindingModel.as_of_date.desc())
            .first()
        )
        return self._to_domain(row) if row else None

    def _to_domain(self, row: AnomalyFindingModel) -> AnomalyScore:
        details = row.details or {}
        anomalies = [
            FeatureAnomaly(
                feature_name=item["feature_name"],
                value=float(item["value"]),
                baseline=float(item["baseline"]),
                deviation=float(item["deviation"]),
                contribution=float(item["contribution"]),
                reason=str(item["reason"]),
            )
            for item in details.get("anomalies", [])
        ]
        return AnomalyScore(
            entity_type=row.entity_type,
            entity_id=row.entity_id,
            score=row.anomaly_score,
            severity=AnomalySeverity(row.severity),
            anomalies=anomalies,
            summary=row.summary,
        )
