from app.matcher.domain.match_result import MatchClassification
from app.rules.domain.evidence import Evidence
from app.rules.domain.rule_context import RuleContext
from app.rules.domain.rule_result import RuleResult
from app.rules.domain.severity import Severity
from app.rules.engine.base_rule import BaseRule
from app.timeline.domain.source import DataSource


class InsertedManualActivityRule(BaseRule):
    def __init__(self, baseline_source: DataSource, comparison_source: DataSource) -> None:
        self.baseline_source = baseline_source
        self.comparison_source = comparison_source
        self.rule_id = f"ACT_INSERTED_{baseline_source.name}_{comparison_source.name}"
        self.name = f"Inserted {comparison_source.label} activity"
        self.severity = Severity.CRITICAL if comparison_source in {DataSource.MANAGER, DataSource.PAYROLL} else Severity.HIGH
        self.score = self.severity.score_weight

    def evaluate(self, context: RuleContext) -> list[RuleResult]:
        results = []
        for match in context.matches(self.baseline_source, self.comparison_source):
            if match.classification != MatchClassification.INSERTED or match.comparison_activity is None:
                continue
            activity = match.comparison_activity
            results.append(
                RuleResult(
                    rule_id=self.rule_id,
                    rule_name=self.name,
                    severity=self.severity,
                    score=self.score,
                    reason=(
                        f"{self.comparison_source.label} inserted an activity not present in "
                        f"{self.baseline_source.label}; added {round(activity.duration_seconds / 60, 2)} minutes."
                    ),
                    evidence=[
                        Evidence(
                            evidence_type="inserted_activity",
                            payload={
                                "activity_id": activity.external_id,
                                "source": self.comparison_source.label,
                                "start_time": activity.start_time.isoformat(),
                                "end_time": activity.end_time.isoformat() if activity.end_time else None,
                                "duration_seconds": activity.duration_seconds,
                                "activity_type_id": activity.activity_type_id,
                            },
                        )
                    ],
                )
            )
        return results
