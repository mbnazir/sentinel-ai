from app.matcher.domain.match_result import MatchClassification
from app.rules.domain.evidence import Evidence
from app.rules.domain.rule_context import RuleContext
from app.rules.domain.rule_result import RuleResult
from app.rules.domain.severity import Severity
from app.rules.engine.base_rule import BaseRule
from app.timeline.domain.source import DataSource


class TypeChangedActivityRule(BaseRule):
    def __init__(self, baseline_source: DataSource, comparison_source: DataSource) -> None:
        self.baseline_source = baseline_source
        self.comparison_source = comparison_source
        self.rule_id = f"ACT_TYPE_CHANGED_{baseline_source.name}_{comparison_source.name}"
        self.name = f"Changed activity type in {comparison_source.label}"
        self.severity = Severity.MEDIUM
        self.score = self.severity.score_weight

    def evaluate(self, context: RuleContext) -> list[RuleResult]:
        results = []
        for match in context.matches(self.baseline_source, self.comparison_source):
            if match.classification != MatchClassification.TYPE_CHANGED:
                continue
            results.append(
                RuleResult(
                    rule_id=self.rule_id,
                    rule_name=self.name,
                    severity=self.severity,
                    score=self.score,
                    reason=(
                        f"{self.comparison_source.label} changed activity type while overlapping "
                        f"{self.baseline_source.label} activity."
                    ),
                    evidence=[
                        Evidence(
                            evidence_type="activity_type_changed",
                            payload={
                                "baseline_activity_id": match.baseline_activity.external_id if match.baseline_activity else None,
                                "comparison_activity_id": match.comparison_activity.external_id if match.comparison_activity else None,
                                "baseline_activity_type_id": match.baseline_activity.activity_type_id if match.baseline_activity else None,
                                "comparison_activity_type_id": match.comparison_activity.activity_type_id if match.comparison_activity else None,
                                "confidence": match.confidence,
                            },
                        )
                    ],
                )
            )
        return results
