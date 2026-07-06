from app.anomaly.domain.anomaly_models import AnomalyScore
from app.investigations.domain.case import InvestigationEvidenceLink


class AnomalyCaseEvidenceBuilder:
    """Converts anomaly findings into investigation evidence links."""

    def build_links(self, anomaly_score: AnomalyScore) -> list[InvestigationEvidenceLink]:
        if not anomaly_score.anomalies:
            return []

        links: list[InvestigationEvidenceLink] = []

        for index, anomaly in enumerate(anomaly_score.anomalies, start=1):
            links.append(
                InvestigationEvidenceLink(
                    evidence_id=f"ANOM-{anomaly_score.entity_type}-{anomaly_score.entity_id}-{index}",
                    evidence_type="behavior_anomaly",
                    source="Anomaly Detection Engine",
                    summary=(
                        f"{anomaly.feature_name} anomaly for {anomaly_score.entity_type} "
                        f"{anomaly_score.entity_id}: {anomaly.reason}"
                    ),
                )
            )

        return links
