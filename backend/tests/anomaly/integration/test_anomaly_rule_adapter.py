from app.anomaly.domain.anomaly_models import (
    AnomalyScore,
    AnomalySeverity,
    FeatureAnomaly,
)
from app.anomaly.integration.anomaly_rule_adapter import AnomalyRuleAdapter


def test_adapter_converts_anomaly_to_rule_result() -> None:
    anomaly = AnomalyScore(
        entity_type="agent",
        entity_id="A1",
        score=75,
        severity=AnomalySeverity.HIGH,
        anomalies=[
            FeatureAnomaly(
                feature_name="manual_added_minutes",
                value=300,
                baseline=10,
                deviation=8.5,
                contribution=25,
                reason="Manual added minutes above peer baseline.",
            )
        ],
        summary="Agent A1 has high behavioral anomaly.",
    )

    result = AnomalyRuleAdapter().to_rule_result(anomaly)

    assert result is not None
    assert result.rule_id == "BEHAVIOR_ANOMALY_SCORE"
    assert result.severity.value == "high"
    assert result.evidence[0].payload["entity_id"] == "A1"


def test_adapter_ignores_none_severity() -> None:
    anomaly = AnomalyScore(
        entity_type="agent",
        entity_id="A1",
        score=0,
        severity=AnomalySeverity.NONE,
    )

    assert AnomalyRuleAdapter().to_rule_result(anomaly) is None
