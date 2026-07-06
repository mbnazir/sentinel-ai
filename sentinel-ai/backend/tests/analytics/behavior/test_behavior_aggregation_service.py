from datetime import date

from app.analytics.behavior.domain.session_fact import SessionRiskFact
from app.analytics.behavior.services.behavior_aggregation_service import BehaviorAggregationService


def test_build_agent_profile_aggregates_metrics() -> None:
    facts = [
        SessionRiskFact("LS-1", "A1", "S1", None, "C1", "SITE1", date(2026, 5, 1), 70, inserted_activity_count=2, manual_added_seconds=3600, rule_count=3),
        SessionRiskFact("LS-2", "A1", "S1", None, "C1", "SITE1", date(2026, 6, 1), 80, deleted_activity_count=1, manual_added_seconds=1800, rule_count=2),
        SessionRiskFact("LS-3", "A2", "S1", None, "C1", "SITE1", date(2026, 6, 1), 10),
    ]

    profile = BehaviorAggregationService().build_agent_profile("A1", facts, date(2026, 7, 1), 90)

    metric_map = {metric.name: metric.value for metric in profile.metrics}
    assert metric_map["session_count"] == 2
    assert metric_map["average_risk_score"] == 75
    assert metric_map["manual_added_minutes"] == 90
    assert profile.behavior_score > 0


def test_build_supervisor_profile_filters_supervisor_sessions() -> None:
    facts = [
        SessionRiskFact("LS-1", "A1", "S1", None, "C1", "SITE1", date(2026, 5, 1), 70),
        SessionRiskFact("LS-2", "A2", "S2", None, "C1", "SITE1", date(2026, 5, 1), 20),
    ]

    profile = BehaviorAggregationService().build_supervisor_profile("S1", facts, date(2026, 7, 1), 90)
    metric_map = {metric.name: metric.value for metric in profile.metrics}

    assert metric_map["session_count"] == 1
    assert profile.entity_type == "supervisor"
