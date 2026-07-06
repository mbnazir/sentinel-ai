from app.anomaly.domain.anomaly_models import AnomalyScore
from app.anomaly.integration.anomaly_rule_adapter import AnomalyRuleAdapter
from app.rules.domain.rule_result import RuleResult
from app.scoring.domain.risk_assessment import RiskAssessment
from app.scoring.services.risk_scorer import RiskScorer


class AnomalyRiskService:
    """Combines existing rule results with behavioral anomaly results."""

    def __init__(
        self,
        adapter: AnomalyRuleAdapter | None = None,
        risk_scorer: RiskScorer | None = None,
    ) -> None:
        self.adapter = adapter or AnomalyRuleAdapter()
        self.risk_scorer = risk_scorer or RiskScorer()

    def score_entity_with_anomaly(
        self,
        entity_id: str,
        existing_rule_results: list[RuleResult],
        anomaly_score: AnomalyScore | None,
    ) -> RiskAssessment:
        combined_rules = list(existing_rule_results)

        if anomaly_score is not None:
            anomaly_rule = self.adapter.to_rule_result(anomaly_score)
            if anomaly_rule is not None:
                combined_rules.append(anomaly_rule)

        return self.risk_scorer.score_session(entity_id, combined_rules)
