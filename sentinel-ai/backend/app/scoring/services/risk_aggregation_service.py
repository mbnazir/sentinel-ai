from app.rules.domain.rule_result import RuleResult
from app.scoring.domain.risk_assessment import RiskAssessment
from app.scoring.services.risk_scorer import RiskScorer


class RiskAggregationService:
    """Application service for building session-level risk assessments."""

    def __init__(self, scorer: RiskScorer | None = None) -> None:
        self.scorer = scorer or RiskScorer()

    def assess_login_session(
        self,
        login_session_external_id: str,
        rule_results: list[RuleResult],
    ) -> RiskAssessment:
        return self.scorer.score_session(login_session_external_id, rule_results)
