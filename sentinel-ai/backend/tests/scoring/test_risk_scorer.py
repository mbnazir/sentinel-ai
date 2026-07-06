from app.rules.domain.evidence import Evidence
from app.rules.domain.rule_result import RuleResult
from app.rules.domain.severity import Severity
from app.scoring.domain.risk_level import RiskLevel
from app.scoring.services.risk_scorer import RiskScorer


def result(rule_id: str, severity: Severity, score: int) -> RuleResult:
    return RuleResult(
        rule_id=rule_id,
        rule_name=rule_id,
        severity=severity,
        score=score,
        reason=f"{rule_id} reason",
        evidence=[Evidence("test", {"rule_id": rule_id})],
    )


def test_risk_scorer_returns_normal_when_no_rules_triggered() -> None:
    assessment = RiskScorer().score_session("LS-1", [])

    assert assessment.risk_score == 0
    assert assessment.risk_level == RiskLevel.NORMAL
    assert assessment.summary == "No integrity risks detected."


def test_risk_scorer_caps_score_at_100() -> None:
    rules = [
        result("R1", Severity.CRITICAL, 80),
        result("R2", Severity.CRITICAL, 80),
        result("R3", Severity.HIGH, 50),
    ]

    assessment = RiskScorer().score_session("LS-1", rules)

    assert assessment.risk_score == 100
    assert assessment.risk_level == RiskLevel.CRITICAL


def test_risk_scorer_dampens_duplicate_rules() -> None:
    rules = [
        result("R1", Severity.HIGH, 50),
        result("R1", Severity.HIGH, 50),
        result("R1", Severity.HIGH, 50),
    ]

    assessment = RiskScorer().score_session("LS-1", rules)

    assert assessment.risk_score == 85
    assert assessment.risk_level == RiskLevel.CRITICAL


def test_risk_scorer_builds_top_reasons() -> None:
    rules = [
        result("LOW", Severity.LOW, 10),
        result("HIGH", Severity.HIGH, 50),
    ]

    assessment = RiskScorer().score_session("LS-1", rules)

    assert assessment.top_reasons[0] == "HIGH reason"
