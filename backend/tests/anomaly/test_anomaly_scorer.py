from app.anomaly.domain.anomaly_models import AnomalySeverity, FeatureVector
from app.anomaly.services.anomaly_scorer import AnomalyScorer


def test_anomaly_scorer_scores_outlier_behavior() -> None:
    target = FeatureVector(
        entity_type="agent",
        entity_id="A1",
        features={
            "average_risk_score": 90,
            "manual_added_minutes": 300,
            "inserted_activity_count": 10,
            "deleted_activity_count": 5,
            "payroll_adjustment_count": 2,
            "high_risk_session_count": 8,
        },
    )
    peers = [
        FeatureVector("agent", "A2", {"average_risk_score": 20, "manual_added_minutes": 10, "inserted_activity_count": 1, "deleted_activity_count": 0, "payroll_adjustment_count": 0, "high_risk_session_count": 1}),
        FeatureVector("agent", "A3", {"average_risk_score": 22, "manual_added_minutes": 12, "inserted_activity_count": 1, "deleted_activity_count": 0, "payroll_adjustment_count": 0, "high_risk_session_count": 1}),
        FeatureVector("agent", "A4", {"average_risk_score": 18, "manual_added_minutes": 8, "inserted_activity_count": 0, "deleted_activity_count": 1, "payroll_adjustment_count": 0, "high_risk_session_count": 0}),
    ]

    result = AnomalyScorer().score(target, peers)

    assert result.score > 0
    assert result.severity != AnomalySeverity.NONE
    assert result.anomalies


def test_anomaly_scorer_returns_none_for_normal_behavior() -> None:
    target = FeatureVector("agent", "A1", {"average_risk_score": 21, "manual_added_minutes": 11})
    peers = [
        FeatureVector("agent", "A2", {"average_risk_score": 20, "manual_added_minutes": 10}),
        FeatureVector("agent", "A3", {"average_risk_score": 22, "manual_added_minutes": 12}),
    ]

    result = AnomalyScorer().score(target, peers)

    assert result.score == 0
    assert result.severity == AnomalySeverity.NONE
