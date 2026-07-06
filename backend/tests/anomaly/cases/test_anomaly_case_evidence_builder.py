from app.anomaly.cases.anomaly_case_evidence_builder import AnomalyCaseEvidenceBuilder
from app.anomaly.domain.anomaly_models import AnomalyScore, AnomalySeverity, FeatureAnomaly


def test_builder_creates_evidence_links() -> None:
    score = AnomalyScore(
        entity_type="agent",
        entity_id="A1",
        score=80,
        severity=AnomalySeverity.HIGH,
        anomalies=[
            FeatureAnomaly("manual_added_minutes", 300, 10, 8.5, 25, "Outlier manual added minutes."),
        ],
        summary="High anomaly.",
    )

    links = AnomalyCaseEvidenceBuilder().build_links(score)

    assert len(links) == 1
    assert links[0].evidence_type == "behavior_anomaly"
    assert "manual_added_minutes" in links[0].summary
