from dataclasses import dataclass, field
from datetime import date

from app.analytics.behavior.domain.metric import BehaviorMetric, TrendResult
from app.scoring.domain.risk_level import RiskLevel


@dataclass(frozen=True)
class BehaviorProfile:
    entity_type: str
    entity_id: str
    window_days: int
    date_from: date
    date_to: date
    metrics: list[BehaviorMetric] = field(default_factory=list)
    trends: list[TrendResult] = field(default_factory=list)
    behavior_score: int = 0
    behavior_level: RiskLevel = RiskLevel.NORMAL
    summary: str = ""
