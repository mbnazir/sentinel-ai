from app.anomaly.domain.anomaly_models import (
    AnomalyScore,
    AnomalySeverity,
    FeatureAnomaly,
    FeatureVector,
)
from app.anomaly.services.robust_statistics import RobustStatistics


class AnomalyScorer:
    """Explainable anomaly scorer over behavior feature vectors."""

    DEFAULT_FEATURE_WEIGHTS: dict[str, float] = {
        "average_risk_score": 0.25,
        "manual_added_minutes": 0.25,
        "inserted_activity_count": 0.15,
        "deleted_activity_count": 0.15,
        "payroll_adjustment_count": 0.10,
        "high_risk_session_count": 0.10,
    }

    def __init__(
        self,
        statistics: RobustStatistics | None = None,
        feature_weights: dict[str, float] | None = None,
    ) -> None:
        self.statistics = statistics or RobustStatistics()
        self.feature_weights = feature_weights or self.DEFAULT_FEATURE_WEIGHTS

    def score(self, target: FeatureVector, peers: list[FeatureVector]) -> AnomalyScore:
        anomalies: list[FeatureAnomaly] = []
        raw_score = 0.0

        for feature_name, weight in self.feature_weights.items():
            value = float(target.features.get(feature_name, 0.0))
            peer_values = [
                float(peer.features.get(feature_name, 0.0))
                for peer in peers
                if peer.entity_id != target.entity_id
            ]

            if not peer_values:
                continue

            z_score = self.statistics.robust_z_score(value, peer_values)
            baseline = self.statistics.median(peer_values)

            if z_score <= 2.5:
                continue

            contribution = min(100.0, z_score * 15.0) * weight
            raw_score += contribution

            anomalies.append(
                FeatureAnomaly(
                    feature_name=feature_name,
                    value=value,
                    baseline=baseline,
                    deviation=z_score,
                    contribution=round(contribution, 2),
                    reason=(
                        f"{feature_name} is materially above peer baseline "
                        f"({value} vs median {baseline}; robust z={z_score})."
                    ),
                )
            )

        score = min(100, int(round(raw_score)))
        severity = self._severity(score)

        return AnomalyScore(
            entity_type=target.entity_type,
            entity_id=target.entity_id,
            score=score,
            severity=severity,
            anomalies=sorted(anomalies, key=lambda item: item.contribution, reverse=True),
            summary=self._summary(target, score, severity, anomalies),
        )

    def _severity(self, score: int) -> AnomalySeverity:
        if score >= 81:
            return AnomalySeverity.CRITICAL
        if score >= 61:
            return AnomalySeverity.HIGH
        if score >= 41:
            return AnomalySeverity.MEDIUM
        if score >= 21:
            return AnomalySeverity.LOW
        return AnomalySeverity.NONE

    def _summary(
        self,
        target: FeatureVector,
        score: int,
        severity: AnomalySeverity,
        anomalies: list[FeatureAnomaly],
    ) -> str:
        if not anomalies:
            return f"{target.entity_type} {target.entity_id} is within expected peer behavior."
        return (
            f"{target.entity_type} {target.entity_id} has anomaly score {score}/100 "
            f"({severity.value}) based on {len(anomalies)} anomalous feature(s)."
        )
