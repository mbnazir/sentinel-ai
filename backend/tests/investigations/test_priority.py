from app.investigations.domain.priority import InvestigationPriority, priority_from_risk_score


def test_priority_from_risk_score() -> None:
    assert priority_from_risk_score(10) == InvestigationPriority.LOW
    assert priority_from_risk_score(45) == InvestigationPriority.MEDIUM
    assert priority_from_risk_score(70) == InvestigationPriority.HIGH
    assert priority_from_risk_score(90) == InvestigationPriority.CRITICAL
