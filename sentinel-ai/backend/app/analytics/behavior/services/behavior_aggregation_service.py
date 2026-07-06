from collections import defaultdict
from datetime import date, timedelta

from app.analytics.behavior.domain.metric import BehaviorMetric
from app.analytics.behavior.domain.profile import BehaviorProfile
from app.analytics.behavior.domain.session_fact import SessionRiskFact
from app.analytics.behavior.services.behavior_risk_scorer import BehaviorRiskScorer
from app.analytics.behavior.services.trend_detection_service import TrendDetectionService
from app.scoring.domain.risk_level import classify_risk_score


class BehaviorAggregationService:
    """Builds behavior profiles from session-level risk facts."""

    def __init__(
        self,
        trend_detector: TrendDetectionService | None = None,
        risk_scorer: BehaviorRiskScorer | None = None,
    ) -> None:
        self.trend_detector = trend_detector or TrendDetectionService()
        self.risk_scorer = risk_scorer or BehaviorRiskScorer()

    def build_agent_profile(
        self,
        agent_external_id: str,
        facts: list[SessionRiskFact],
        date_to: date,
        window_days: int = 90,
    ) -> BehaviorProfile:
        date_from = date_to - timedelta(days=window_days - 1)
        filtered = [
            fact
            for fact in facts
            if fact.agent_external_id == agent_external_id and date_from <= fact.shift_date <= date_to
        ]

        metrics = self._build_metrics(filtered)
        trends = self._build_monthly_trends(filtered)
        score, _level = self.risk_scorer.score(metrics, trends)
        level = classify_risk_score(score)

        return BehaviorProfile(
            entity_type="agent",
            entity_id=agent_external_id,
            window_days=window_days,
            date_from=date_from,
            date_to=date_to,
            metrics=metrics,
            trends=trends,
            behavior_score=score,
            behavior_level=level,
            summary=self._summary("agent", agent_external_id, score, len(filtered)),
        )

    def build_supervisor_profile(
        self,
        supervisor_external_id: str,
        facts: list[SessionRiskFact],
        date_to: date,
        window_days: int = 90,
    ) -> BehaviorProfile:
        date_from = date_to - timedelta(days=window_days - 1)
        filtered = [
            fact
            for fact in facts
            if fact.supervisor_external_id == supervisor_external_id and date_from <= fact.shift_date <= date_to
        ]

        metrics = self._build_metrics(filtered)
        trends = self._build_monthly_trends(filtered)
        score, _level = self.risk_scorer.score(metrics, trends)
        level = classify_risk_score(score)

        return BehaviorProfile(
            entity_type="supervisor",
            entity_id=supervisor_external_id,
            window_days=window_days,
            date_from=date_from,
            date_to=date_to,
            metrics=metrics,
            trends=trends,
            behavior_score=score,
            behavior_level=level,
            summary=self._summary("supervisor", supervisor_external_id, score, len(filtered)),
        )

    def _build_metrics(self, facts: list[SessionRiskFact]) -> list[BehaviorMetric]:
        session_count = len(facts)
        total_risk = sum(fact.risk_score for fact in facts)
        average_risk = round(total_risk / session_count, 2) if session_count else 0.0

        return [
            BehaviorMetric("session_count", session_count),
            BehaviorMetric("average_risk_score", average_risk),
            BehaviorMetric("max_risk_score", max((fact.risk_score for fact in facts), default=0)),
            BehaviorMetric("high_risk_session_count", sum(1 for fact in facts if fact.risk_score >= 61)),
            BehaviorMetric("inserted_activity_count", sum(fact.inserted_activity_count for fact in facts)),
            BehaviorMetric("deleted_activity_count", sum(fact.deleted_activity_count for fact in facts)),
            BehaviorMetric("extended_activity_count", sum(fact.extended_activity_count for fact in facts)),
            BehaviorMetric("payroll_adjustment_count", sum(fact.payroll_adjustment_count for fact in facts)),
            BehaviorMetric(
                "manual_added_minutes",
                round(sum(fact.manual_added_seconds for fact in facts) / 60, 2),
                "minutes",
            ),
            BehaviorMetric("rule_count", sum(fact.rule_count for fact in facts)),
        ]

    def _build_monthly_trends(self, facts: list[SessionRiskFact]):
        if not facts:
            return []

        buckets: dict[str, list[SessionRiskFact]] = defaultdict(list)
        for fact in facts:
            buckets[f"{fact.shift_date.year}-{fact.shift_date.month:02d}"].append(fact)

        ordered_keys = sorted(buckets)
        average_risk_values = []
        manual_added_values = []
        high_risk_values = []

        for key in ordered_keys:
            bucket = buckets[key]
            average_risk_values.append(sum(f.risk_score for f in bucket) / len(bucket))
            manual_added_values.append(sum(f.manual_added_seconds for f in bucket) / 60)
            high_risk_values.append(sum(1 for f in bucket if f.risk_score >= 61))

        return [
            self.trend_detector.detect("average_risk_score", average_risk_values),
            self.trend_detector.detect("manual_added_minutes", manual_added_values),
            self.trend_detector.detect("high_risk_session_count", high_risk_values),
        ]

    def _summary(self, entity_type: str, entity_id: str, score: int, session_count: int) -> str:
        return (
            f"{entity_type.title()} {entity_id} has behavior risk score {score}/100 "
            f"based on {session_count} analyzed session(s)."
        )
