from app.analytics.behavior.domain.metric import BehaviorMetric, TrendDirection, TrendResult
from app.scoring.domain.risk_level import classify_risk_score


class BehaviorRiskScorer:
    """Scores longitudinal behavior from aggregated metrics and trends."""

    def score(self, metrics: list[BehaviorMetric], trends: list[TrendResult]) -> tuple[int, str]:
        metric_map = {metric.name: metric.value for metric in metrics}
        score = 0

        average_risk = metric_map.get("average_risk_score", 0)
        high_risk_sessions = metric_map.get("high_risk_session_count", 0)
        manual_added_minutes = metric_map.get("manual_added_minutes", 0)
        inserted_count = metric_map.get("inserted_activity_count", 0)
        deleted_count = metric_map.get("deleted_activity_count", 0)
        payroll_adjustments = metric_map.get("payroll_adjustment_count", 0)

        score += min(30, int(average_risk * 0.30))
        score += min(20, int(high_risk_sessions * 4))
        score += min(20, int(manual_added_minutes / 60) * 5)
        score += min(15, int(inserted_count * 3))
        score += min(15, int(deleted_count * 3))
        score += min(20, int(payroll_adjustments * 5))

        for trend in trends:
            if trend.direction == TrendDirection.INCREASING and trend.metric_name in {
                "average_risk_score",
                "manual_added_minutes",
                "high_risk_session_count",
            }:
                score += 10

        score = min(100, score)
        return score, classify_risk_score(score).value
