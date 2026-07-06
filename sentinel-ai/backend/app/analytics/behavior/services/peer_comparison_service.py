import math

from app.analytics.behavior.domain.deviation import DeviationResult


class PeerComparisonService:
    """Compares one entity metric against a peer population."""

    def compare(
        self,
        entity_id: str,
        metric_name: str,
        entity_value: float,
        peer_values: list[float],
        z_threshold: float = 2.5,
    ) -> DeviationResult:
        if not peer_values:
            return DeviationResult(entity_id, metric_name, entity_value, 0.0, 0.0, 0.0, False)

        peer_average = sum(peer_values) / len(peer_values)
        variance = sum((value - peer_average) ** 2 for value in peer_values) / len(peer_values)
        stddev = math.sqrt(variance)

        if stddev == 0:
            z_score = 0.0
        else:
            z_score = (entity_value - peer_average) / stddev

        return DeviationResult(
            entity_id=entity_id,
            metric_name=metric_name,
            entity_value=entity_value,
            peer_average=round(peer_average, 4),
            peer_stddev=round(stddev, 4),
            z_score=round(z_score, 4),
            is_outlier=abs(z_score) >= z_threshold,
        )
