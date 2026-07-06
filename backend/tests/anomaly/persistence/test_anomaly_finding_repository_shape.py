from app.anomaly.domain.anomaly_models import (
    AnomalyScore,
    AnomalySeverity,
    FeatureAnomaly,
)


def test_anomaly_score_shape_for_persistence() -> None:
    score = AnomalyScore(
        entity_type="agent",
        entity_id="A1",
        score=80,
        severity=AnomalySeverity.HIGH,
        anomalies=[
            FeatureAnomaly(
                feature_name="manual_added_minutes",
                value=300,
                baseline=10,
                deviation=8.5,
                contribution=25,
                reason="Outlier.",
            )
        ],
        summary="High anomaly.",
    )

    assert score.entity_id == "A1"
    assert score.anomalies[0].feature_name == "manual_added_minutes"
