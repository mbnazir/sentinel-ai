from app.anomaly.domain.anomaly_models import AnomalyScore, AnomalySeverity
from app.rules.domain.evidence import Evidence
from app.rules.domain.rule_result import RuleResult
from app.rules.domain.severity import Severity


class AnomalyRuleAdapter:
    """Converts anomaly scores into deterministic rule results.

    This keeps the existing risk scorer as the single aggregation mechanism.
    """

    RULE_ID = "BEHAVIOR_ANOMALY_SCORE"
    RULE_NAME = "Behavior anomaly detected"

    def to_rule_result(self, anomaly_score: AnomalyScore) -> RuleResult | None:
        if anomaly_score.severity == AnomalySeverity.NONE:
            return None

        severity = self._map_severity(anomaly_score.severity)

        return RuleResult(
            rule_id=self.RULE_ID,
            rule_name=self.RULE_NAME,
            severity=severity,
            score=self._score_for_severity(severity, anomaly_score.score),
            reason=anomaly_score.summary,
            evidence=[
                Evidence(
                    evidence_type="behavior_anomaly",
                    payload={
                        "entity_type": anomaly_score.entity_type,
                        "entity_id": anomaly_score.entity_id,
                        "anomaly_score": anomaly_score.score,
                        "anomaly_severity": anomaly_score.severity.value,
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
                        ],
                    },
                )
            ],
        )

    def _map_severity(self, severity: AnomalySeverity) -> Severity:
        return {
            AnomalySeverity.LOW: Severity.LOW,
            AnomalySeverity.MEDIUM: Severity.MEDIUM,
            AnomalySeverity.HIGH: Severity.HIGH,
            AnomalySeverity.CRITICAL: Severity.CRITICAL,
        }.get(severity, Severity.LOW)

    def _score_for_severity(self, severity: Severity, anomaly_score: int) -> int:
        return min(100, max(severity.score_weight, anomaly_score))
