from app.rules.base import IntegrityRule
from app.rules.builtin import BUILTIN_RULES
from app.rules.context import IntegrityPolicy, RuleContext
from app.rules.models import RiskAssessment, RuleFinding
from app.scoring.risk import assess
from app.timeline.analysis import EmployeeDayAnalysis


class IntegrityRuleEngine:
    def __init__(
        self,
        rules: tuple[IntegrityRule, ...] = BUILTIN_RULES,
        policy: IntegrityPolicy | None = None,
    ) -> None:
        self.rules = rules
        self.policy = policy or IntegrityPolicy()

    def evaluate(self, analysis: EmployeeDayAnalysis) -> RiskAssessment:
        context = RuleContext(analysis=analysis, policy=self.policy)
        findings: list[RuleFinding] = []
        for rule in self.rules:
            findings.extend(rule.evaluate(context))
        findings.sort(
            key=lambda item: (
                -item.risk_contribution,
                item.rule_id,
                item.source_session_id or "",
            )
        )
        mitigating_notes = tuple(
            finding.reason
            for finding in findings
            if finding.category.value == "data_quality" and finding.severity.value == "info"
        )
        return assess(tuple(findings), mitigating_notes)
