from app.analytics.behavior.domain.metric import BehaviorMetric, TrendDirection, TrendResult
from app.analytics.behavior.services.behavior_risk_scorer import BehaviorRiskScorer


def test_behavior_risk_scorer_scores_repeated_suspicious_metrics() -> None:
    metrics = [
        BehaviorMetric("average_risk_score", 80),
        BehaviorMetric("high_risk_session_count", 5),
        BehaviorMetric("manual_added_minutes", 180),
        BehaviorMetric("inserted_activity_count", 4),
        BehaviorMetric("deleted_activity_count", 2),
        BehaviorMetric("payroll_adjustment_count", 1),
    ]
    trends = [
        TrendResult("average_risk_score", TrendDirection.INCREASING, 5, 10, 80, 700),
    ]

    score, level = BehaviorRiskScorer().score(metrics, trends)

    assert score >= 61
    assert level in {"high_risk", "critical"}
