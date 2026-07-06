from enum import StrEnum


class RiskLevel(StrEnum):
    NORMAL = "normal"
    REVIEW = "review"
    SUSPICIOUS = "suspicious"
    HIGH_RISK = "high_risk"
    CRITICAL = "critical"


def classify_risk_score(score: int) -> RiskLevel:
    if score >= 81:
        return RiskLevel.CRITICAL
    if score >= 61:
        return RiskLevel.HIGH_RISK
    if score >= 41:
        return RiskLevel.SUSPICIOUS
    if score >= 21:
        return RiskLevel.REVIEW
    return RiskLevel.NORMAL
