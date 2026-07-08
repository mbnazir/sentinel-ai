from dataclasses import dataclass, field

from app.rules.domain.evidence import Evidence
from app.rules.domain.severity import Severity


@dataclass(frozen=True)
class RuleResult:
    rule_id: str
    rule_name: str
    severity: Severity
    score: int
    reason: str
    evidence: list[Evidence] = field(default_factory=list)
