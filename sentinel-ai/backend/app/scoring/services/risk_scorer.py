from collections import Counter

from app.rules.domain.rule_result import RuleResult
from app.rules.domain.severity import Severity
from app.scoring.domain.risk_assessment import RiskAssessment
from app.scoring.domain.risk_level import classify_risk_score


class RiskScorer:
    """Converts deterministic rule results into one normalized risk assessment.

    Scoring design:
    - base score comes from rule scores
    - duplicate rule ids are dampened to avoid one noisy rule dominating
    - critical/high rule combinations get a small escalation
    - final score is capped at 100
    """

    def score_session(
        self,
        login_session_external_id: str,
        rule_results: list[RuleResult],
    ) -> RiskAssessment:
        if not rule_results:
            return RiskAssessment(
                entity_type="login_session",
                entity_id=login_session_external_id,
                risk_score=0,
                risk_level=classify_risk_score(0),
                summary="No integrity risks detected.",
                rule_results=[],
                top_reasons=[],
            )

        score = self._calculate_weighted_score(rule_results)
        score = min(100, score)
        level = classify_risk_score(score)
        top_reasons = self._top_reasons(rule_results)

        return RiskAssessment(
            entity_type="login_session",
            entity_id=login_session_external_id,
            risk_score=score,
            risk_level=level,
            summary=self._build_summary(score, level.value, rule_results, top_reasons),
            rule_results=rule_results,
            top_reasons=top_reasons,
        )

    def _calculate_weighted_score(self, rule_results: list[RuleResult]) -> int:
        total = 0
        per_rule_count: Counter[str] = Counter()

        for result in sorted(rule_results, key=lambda item: item.score, reverse=True):
            per_rule_count[result.rule_id] += 1
            occurrence = per_rule_count[result.rule_id]

            if occurrence == 1:
                total += result.score
            elif occurrence <= 3:
                total += int(result.score * 0.35)
            else:
                total += int(result.score * 0.10)

        total += self._combination_bonus(rule_results)
        return int(total)

    def _combination_bonus(self, rule_results: list[RuleResult]) -> int:
        severities = [result.severity for result in rule_results]
        critical_count = severities.count(Severity.CRITICAL)
        high_count = severities.count(Severity.HIGH)

        bonus = 0

        if critical_count >= 1 and high_count >= 1:
            bonus += 10

        if critical_count >= 2:
            bonus += 15

        if len(rule_results) >= 5:
            bonus += 10

        return bonus

    def _top_reasons(self, rule_results: list[RuleResult], limit: int = 5) -> list[str]:
        ordered = sorted(rule_results, key=lambda item: item.score, reverse=True)
        return [result.reason for result in ordered[:limit]]

    def _build_summary(
        self,
        score: int,
        level: str,
        rule_results: list[RuleResult],
        top_reasons: list[str],
    ) -> str:
        return (
            f"Risk score {score}/100 classified as {level}. "
            f"{len(rule_results)} integrity rule(s) triggered. "
            f"Primary reason: {top_reasons[0] if top_reasons else 'None'}"
        )
