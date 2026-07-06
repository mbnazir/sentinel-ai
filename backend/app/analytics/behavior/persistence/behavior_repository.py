from datetime import date, datetime, timezone

from sqlalchemy.orm import Session

from app.analytics.behavior.domain.metric import BehaviorMetric
from app.analytics.behavior.domain.profile import BehaviorProfile
from app.analytics.behavior.domain.deviation import DeviationResult
from app.infrastructure.persistence.models_behavior import (
    BehaviorFeatureSnapshotModel,
    BehaviorPeerDeviationModel,
)
from app.scoring.domain.risk_level import RiskLevel


class BehaviorRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def save_profile(
        self,
        organization_id: str,
        profile: BehaviorProfile,
    ) -> BehaviorProfile:
        model = (
            self.session.query(BehaviorFeatureSnapshotModel)
            .filter_by(
                organization_id=organization_id,
                entity_type=profile.entity_type,
                entity_id=profile.entity_id,
                window_days=profile.window_days,
                as_of_date=profile.date_to,
            )
            .one_or_none()
        )
        if model is None:
            model = BehaviorFeatureSnapshotModel(
                organization_id=organization_id,
                entity_type=profile.entity_type,
                entity_id=profile.entity_id,
                window_days=profile.window_days,
                as_of_date=profile.date_to,
            )
            self.session.add(model)

        metric_map = {metric.name: metric.value for metric in profile.metrics}
        model.session_count = int(metric_map.get("session_count", 0))
        model.average_risk_score = float(metric_map.get("average_risk_score", 0))
        model.max_risk_score = int(metric_map.get("max_risk_score", 0))
        model.high_risk_session_count = int(metric_map.get("high_risk_session_count", 0))
        model.inserted_activity_count = int(metric_map.get("inserted_activity_count", 0))
        model.deleted_activity_count = int(metric_map.get("deleted_activity_count", 0))
        model.extended_activity_count = int(metric_map.get("extended_activity_count", 0))
        model.payroll_adjustment_count = int(metric_map.get("payroll_adjustment_count", 0))
        model.manual_added_seconds = int(float(metric_map.get("manual_added_minutes", 0)) * 60)
        model.rule_count = int(metric_map.get("rule_count", 0))
        model.behavior_score = profile.behavior_score
        model.behavior_level = profile.behavior_level.value
        model.summary = profile.summary
        model.metadata_json = {
            "trends": [
                {
                    "metric_name": trend.metric_name,
                    "direction": trend.direction.value,
                    "slope": trend.slope,
                    "first_value": trend.first_value,
                    "last_value": trend.last_value,
                    "change_percent": trend.change_percent,
                }
                for trend in profile.trends
            ]
        }
        model.updated_at = datetime.now(timezone.utc)

        self.session.commit()
        return profile

    def save_deviation(
        self,
        organization_id: str,
        entity_type: str,
        window_days: int,
        as_of_date: date,
        deviation: DeviationResult,
    ) -> DeviationResult:
        model = (
            self.session.query(BehaviorPeerDeviationModel)
            .filter_by(
                organization_id=organization_id,
                entity_type=entity_type,
                entity_id=deviation.entity_id,
                metric_name=deviation.metric_name,
                window_days=window_days,
                as_of_date=as_of_date,
            )
            .one_or_none()
        )
        if model is None:
            model = BehaviorPeerDeviationModel(
                organization_id=organization_id,
                entity_type=entity_type,
                entity_id=deviation.entity_id,
                metric_name=deviation.metric_name,
                window_days=window_days,
                as_of_date=as_of_date,
            )
            self.session.add(model)

        model.entity_value = deviation.entity_value
        model.peer_average = deviation.peer_average
        model.peer_stddev = deviation.peer_stddev
        model.z_score = deviation.z_score
        model.is_outlier = deviation.is_outlier

        self.session.commit()
        return deviation

    def latest_profiles(
        self,
        organization_id: str,
        entity_type: str,
        limit: int = 100,
    ) -> list[BehaviorProfile]:
        rows = (
            self.session.query(BehaviorFeatureSnapshotModel)
            .filter_by(organization_id=organization_id, entity_type=entity_type)
            .order_by(BehaviorFeatureSnapshotModel.as_of_date.desc(), BehaviorFeatureSnapshotModel.behavior_score.desc())
            .limit(limit)
            .all()
        )
        return [self._to_profile(row) for row in rows]

    def _to_profile(self, row: BehaviorFeatureSnapshotModel) -> BehaviorProfile:
        metrics = [
            BehaviorMetric("session_count", row.session_count),
            BehaviorMetric("average_risk_score", row.average_risk_score),
            BehaviorMetric("max_risk_score", row.max_risk_score),
            BehaviorMetric("high_risk_session_count", row.high_risk_session_count),
            BehaviorMetric("inserted_activity_count", row.inserted_activity_count),
            BehaviorMetric("deleted_activity_count", row.deleted_activity_count),
            BehaviorMetric("extended_activity_count", row.extended_activity_count),
            BehaviorMetric("payroll_adjustment_count", row.payroll_adjustment_count),
            BehaviorMetric("manual_added_minutes", round(row.manual_added_seconds / 60, 2), "minutes"),
            BehaviorMetric("rule_count", row.rule_count),
        ]
        return BehaviorProfile(
            entity_type=row.entity_type,
            entity_id=row.entity_id,
            window_days=row.window_days,
            date_from=row.as_of_date,
            date_to=row.as_of_date,
            metrics=metrics,
            trends=[],
            behavior_score=row.behavior_score,
            behavior_level=RiskLevel(row.behavior_level),
            summary=row.summary,
        )
