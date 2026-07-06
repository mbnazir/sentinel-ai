from app.anomaly.domain.anomaly_models import AnomalyScore, AnomalySeverity
from app.anomaly.integration.anomaly_risk_service import AnomalyRiskService


def test_anomaly_risk_service_scores_anomaly_without_existing_rules() -> None:
    anomaly = AnomalyScore(
        entity_type="agent",
        entity_id="A1",
        score=85,
        severity=AnomalySeverity.CRITICAL,
        summary="Critical anomaly.",
    )

    assessment = AnomalyRiskService().score_entity_with_anomaly("A1", [], anomaly)

    assert assessment.risk_score >= 80
    assert assessment.risk_level.value == "critical"
    assert assessment.rule_results[0].rule_id == "BEHAVIOR_ANOMALY_SCORE"
