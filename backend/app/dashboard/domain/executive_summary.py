from dataclasses import dataclass, field


@dataclass(frozen=True)
class RiskDistribution:
    normal: int = 0
    review: int = 0
    suspicious: int = 0
    high_risk: int = 0
    critical: int = 0


@dataclass(frozen=True)
class TrendPoint:
    period: str
    case_count: int
    average_risk_score: float


@dataclass(frozen=True)
class TopRiskEntity:
    entity_type: str
    entity_id: str
    risk_score: int
    case_count: int


@dataclass(frozen=True)
class ExecutiveDashboardSummary:
    total_cases: int
    open_cases: int
    critical_cases: int
    high_risk_cases: int
    average_risk_score: float
    risk_distribution: RiskDistribution
    trend: list[TrendPoint] = field(default_factory=list)
    top_entities: list[TopRiskEntity] = field(default_factory=list)
