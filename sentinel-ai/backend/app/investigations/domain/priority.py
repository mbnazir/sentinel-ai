from enum import StrEnum


class InvestigationPriority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


def priority_from_risk_score(score: int) -> InvestigationPriority:
    if score >= 81:
        return InvestigationPriority.CRITICAL
    if score >= 61:
        return InvestigationPriority.HIGH
    if score >= 41:
        return InvestigationPriority.MEDIUM
    return InvestigationPriority.LOW
