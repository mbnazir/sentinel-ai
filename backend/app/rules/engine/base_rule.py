from abc import ABC, abstractmethod

from app.rules.domain.rule_context import RuleContext
from app.rules.domain.rule_result import RuleResult
from app.rules.domain.severity import Severity


class BaseRule(ABC):
    rule_id: str
    name: str
    severity: Severity
    score: int

    @abstractmethod
    def evaluate(self, context: RuleContext) -> list[RuleResult]:
        raise NotImplementedError
