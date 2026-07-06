from app.matcher.domain.match_result import MatchClassification
from app.rules.domain.evidence import Evidence
from app.rules.domain.rule_context import RuleContext
from app.rules.domain.rule_result import RuleResult
from app.rules.domain.severity import Severity
from app.rules.engine.base_rule import BaseRule
from app.timeline.domain.source import DataSource


class ExtendedManualActivityRule(BaseRule):
    def __init__(
        self,
        baseline_source: DataSource,
        comparison_source: DataSource,
        minimum_extension_seconds: int = 300,
    ) -> None:
        self.baseline_source = baseline_source
        self.comparison_source = comparison_source
        self.minimum_extension_seconds = minimum_extension_seconds
        self.rule_id = f"ACT_EXTENDED_{baseline_source.name}_{comparison_source.name}"
        self.name = f"Extended {comparison_source.label} activity"
        self.severity = Severity.CRITICAL if comparison_source in {DataSource.MANAGER, DataSource.PAYROLL} else Severity.HIGH
        self.score = self.severity.score_weight

    def evaluate(self, context: RuleContext) -> list[RuleResult]:
        results = []
        for match in context.matches(self.baseline_source, self.comparison_source):
            if match.classification != MatchClassification.EXTENDED:
                continue
            if match.delta_seconds < self.minimum_extension_seconds:
                continue
            results.append(
                RuleResult(
                    rule_id=self.rule_id,
                    rule_name=self.name,
                    severity=self.severity,
                    score=self.score,
                    reason=(
                        f"{self.comparison_source.label} extended a {self.baseline_source.label} activity "
                        f"by {round(match.delta_seconds / 60, 2)} minutes."
                    ),
                    evidence=[
                        Evidence(
                            evidence_type="extended_activity",
                            payload={
                                "baseline_activity_id": match.baseline_activity.external_id if match.baseline_activity else None,
                                "comparison_activity_id": match.comparison_activity.external_id if match.comparison_activity else None,
                                "baseline_source": self.baseline_source.label,
                                "comparison_source": self.comparison_source.label,
                                "delta_seconds": match.delta_seconds,
                                "confidence": match.confidence,
                            },
                        )
                    ],
                )
            )
        return results
