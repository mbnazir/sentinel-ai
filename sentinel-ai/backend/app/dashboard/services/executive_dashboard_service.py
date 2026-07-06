from collections import defaultdict
from datetime import datetime

from app.dashboard.domain.executive_summary import (
    ExecutiveDashboardSummary,
    RiskDistribution,
    TopRiskEntity,
    TrendPoint,
)
from app.investigations.domain.case import InvestigationCase


class ExecutiveDashboardService:
    """Builds leadership-level analytics from investigation cases."""

    def summarize(self, cases: list[InvestigationCase]) -> ExecutiveDashboardSummary:
        total_cases = len(cases)
        open_cases = sum(1 for case in cases if case.status.value != "closed")
        critical_cases = sum(1 for case in cases if case.priority.value == "critical")
        high_risk_cases = sum(1 for case in cases if case.priority.value == "high")
        average_risk = round(sum(case.risk_score for case in cases) / total_cases, 2) if total_cases else 0.0

        return ExecutiveDashboardSummary(
            total_cases=total_cases,
            open_cases=open_cases,
            critical_cases=critical_cases,
            high_risk_cases=high_risk_cases,
            average_risk_score=average_risk,
            risk_distribution=self._risk_distribution(cases),
            trend=self._trend(cases),
            top_entities=self._top_entities(cases),
        )

    def _risk_distribution(self, cases: list[InvestigationCase]) -> RiskDistribution:
        return RiskDistribution(
            normal=sum(1 for case in cases if case.risk_score <= 20),
            review=sum(1 for case in cases if 21 <= case.risk_score <= 40),
            suspicious=sum(1 for case in cases if 41 <= case.risk_score <= 60),
            high_risk=sum(1 for case in cases if 61 <= case.risk_score <= 80),
            critical=sum(1 for case in cases if case.risk_score >= 81),
        )

    def _trend(self, cases: list[InvestigationCase]) -> list[TrendPoint]:
        buckets: dict[str, list[InvestigationCase]] = defaultdict(list)

        for case in cases:
            period = self._period(case.created_at)
            buckets[period].append(case)

        points = []
        for period in sorted(buckets):
            bucket = buckets[period]
            avg_risk = round(sum(case.risk_score for case in bucket) / len(bucket), 2)
            points.append(
                TrendPoint(
                    period=period,
                    case_count=len(bucket),
                    average_risk_score=avg_risk,
                )
            )
        return points

    def _top_entities(self, cases: list[InvestigationCase], limit: int = 10) -> list[TopRiskEntity]:
        grouped: dict[tuple[str, str], list[InvestigationCase]] = defaultdict(list)

        for case in cases:
            grouped[(case.entity_type, case.entity_id)].append(case)

        entities = []
        for (entity_type, entity_id), items in grouped.items():
            entities.append(
                TopRiskEntity(
                    entity_type=entity_type,
                    entity_id=entity_id,
                    risk_score=max(item.risk_score for item in items),
                    case_count=len(items),
                )
            )

        return sorted(entities, key=lambda item: (item.risk_score, item.case_count), reverse=True)[:limit]

    def _period(self, value: datetime) -> str:
        return f"{value.year}-{value.month:02d}"
