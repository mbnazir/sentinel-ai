from datetime import date

from app.analytics.behavior.domain.metric import BehaviorMetric
from app.analytics.behavior.domain.profile import BehaviorProfile
from app.anomaly.integration.behavior_anomaly_pipeline import BehaviorAnomalyPipeline
from app.scoring.domain.risk_level import RiskLevel


def profile(entity_id: str, average_risk: float, manual_minutes: float) -> BehaviorProfile:
    return BehaviorProfile(
        entity_type="agent",
        entity_id=entity_id,
        window_days=90,
        date_from=date(2026, 4, 1),
        date_to=date(2026, 7, 1),
        metrics=[
            BehaviorMetric("average_risk_score", average_risk),
            BehaviorMetric("manual_added_minutes", manual_minutes),
        ],
        behavior_score=0,
        behavior_level=RiskLevel.NORMAL,
    )


def test_behavior_anomaly_pipeline_scores_profile_against_peers() -> None:
    target = profile("A1", 90, 300)
    peers = [
        profile("A2", 20, 10),
        profile("A3", 22, 11),
        profile("A4", 18, 9),
    ]

    result = BehaviorAnomalyPipeline().score_profile(target, peers)

    assert result.entity_id == "A1"
    assert result.score > 0
    assert result.anomalies
