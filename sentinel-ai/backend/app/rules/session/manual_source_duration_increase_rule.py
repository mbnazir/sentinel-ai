from app.rules.domain.evidence import Evidence
from app.rules.domain.rule_context import RuleContext
from app.rules.domain.rule_result import RuleResult
from app.rules.domain.severity import Severity
from app.rules.engine.base_rule import BaseRule
from app.timeline.domain.source import DataSource


class ManualSourceDurationIncreaseRule(BaseRule):
    def __init__(
        self,
        baseline_source: DataSource,
        comparison_source: DataSource,
        threshold_seconds: int,
    ) -> None:
        self.baseline_source = baseline_source
        self.comparison_source = comparison_source
        self.threshold_seconds = threshold_seconds
        self.rule_id = f"SESSION_DURATION_INCREASE_{baseline_source.name}_{comparison_source.name}"
        self.name = f"{comparison_source.label} duration exceeds {baseline_source.label}"
        self.severity = Severity.HIGH if comparison_source != DataSource.PAYROLL else Severity.CRITICAL
        self.score = self.severity.score_weight

    def evaluate(self, context: RuleContext) -> list[RuleResult]:
        totals = context.timeline.total_seconds_by_source()
        delta = totals[self.comparison_source] - totals[self.baseline_source]

        if delta < self.threshold_seconds:
            return []

        return [
            RuleResult(
                rule_id=self.rule_id,
                rule_name=self.name,
                severity=self.severity,
                score=self.score,
                reason=(
                    f"{self.comparison_source.label} total duration exceeds {self.baseline_source.label} "
                    f"by {round(delta / 60, 2)} minutes."
                ),
                evidence=[
                    Evidence(
                        evidence_type="source_duration_increase",
                        payload={
                            "baseline_source": self.baseline_source.label,
                            "comparison_source": self.comparison_source.label,
                            "baseline_seconds": totals[self.baseline_source],
                            "comparison_seconds": totals[self.comparison_source],
                            "delta_seconds": delta,
                            "threshold_seconds": self.threshold_seconds,
                        },
                    )
                ],
            )
        ]
