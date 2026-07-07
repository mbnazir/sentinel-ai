from dataclasses import dataclass


@dataclass(frozen=True)
class DeviationResult:
    entity_id: str
    metric_name: str
    entity_value: float
    peer_average: float
    peer_stddev: float
    z_score: float
    is_outlier: bool
