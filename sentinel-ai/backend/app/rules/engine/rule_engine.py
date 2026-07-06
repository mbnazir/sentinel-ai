from app.rules.domain.rule_context import RuleContext
from app.rules.domain.rule_result import RuleResult
from app.rules.engine.base_rule import BaseRule


class RuleEngine:
    def __init__(self, rules: list[BaseRule]) -> None:
        self.rules = rules

    def evaluate(self, context: RuleContext) -> list[RuleResult]:
        results: list[RuleResult] = []
        for rule in self.rules:
            results.extend(rule.evaluate(context))
        return results
