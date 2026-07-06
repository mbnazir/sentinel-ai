from dataclasses import dataclass, field

from app.rules.domain.rule_result import RuleResult
from app.scoring.domain.risk_level import RiskLevel


@dataclass(frozen=True)
class RiskAssessment:
    entity_type: str
    entity_id: str
    risk_score: int
    risk_level: RiskLevel
    summary: str
    rule_results: list[RuleResult] = field(default_factory=list)
    top_reasons: list[str] = field(default_factory=list)
