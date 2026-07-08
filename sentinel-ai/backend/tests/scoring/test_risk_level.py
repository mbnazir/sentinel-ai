from app.scoring.domain.risk_level import RiskLevel, classify_risk_score


def test_risk_level_boundaries() -> None:
    assert classify_risk_score(0) == RiskLevel.NORMAL
    assert classify_risk_score(20) == RiskLevel.NORMAL
    assert classify_risk_score(21) == RiskLevel.REVIEW
    assert classify_risk_score(41) == RiskLevel.SUSPICIOUS
    assert classify_risk_score(61) == RiskLevel.HIGH_RISK
    assert classify_risk_score(81) == RiskLevel.CRITICAL
    assert classify_risk_score(100) == RiskLevel.CRITICAL
