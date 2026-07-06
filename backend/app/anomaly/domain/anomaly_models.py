from dataclasses import dataclass, field
from enum import StrEnum


class AnomalySeverity(StrEnum):
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True)
class FeatureVector:
    entity_type: str
    entity_id: str
    features: dict[str, float]


@dataclass(frozen=True)
class FeatureAnomaly:
    feature_name: str
    value: float
    baseline: float
    deviation: float
    contribution: float
    reason: str


@dataclass(frozen=True)
class AnomalyScore:
    entity_type: str
    entity_id: str
    score: int
    severity: AnomalySeverity
    anomalies: list[FeatureAnomaly] = field(default_factory=list)
    summary: str = ""
