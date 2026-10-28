from app.rules.models import RiskAssessment, RiskLevel, RuleFinding, RuleSeverity


_SEVERITY_BASE: dict[RuleSeverity, float] = {
    RuleSeverity.INFO: 0.0,
    RuleSeverity.LOW: 5.0,
    RuleSeverity.MEDIUM: 12.0,
    RuleSeverity.HIGH: 22.0,
    RuleSeverity.CRITICAL: 35.0,
}


def contribution(severity: RuleSeverity, confidence: float, magnitude: float = 1.0) -> float:
    bounded_magnitude = min(max(magnitude, 0.75), 1.75)
    return round(min(40.0, _SEVERITY_BASE[severity] * confidence * bounded_magnitude), 2)


def assess(findings: tuple[RuleFinding, ...], mitigating_notes: tuple[str, ...] = ()) -> RiskAssessment:
    # Findings intentionally sum transparently and cap at 100. Correlated-rule suppression can be
    # added later once production data establishes which combinations routinely co-trigger.
    score = round(min(100.0, sum(item.risk_contribution for item in findings)), 2)
    level = _level(score)
    return RiskAssessment(
        risk_score=score,
        risk_level=level,
        finding_count=len(findings),
        critical_count=sum(item.severity == RuleSeverity.CRITICAL for item in findings),
        high_count=sum(item.severity == RuleSeverity.HIGH for item in findings),
        findings=findings,
        mitigating_notes=mitigating_notes,
    )


def _level(score: float) -> RiskLevel:
    if score >= 81:
        return RiskLevel.CRITICAL
    if score >= 61:
        return RiskLevel.HIGH
    if score >= 41:
        return RiskLevel.SUSPICIOUS
    if score >= 21:
        return RiskLevel.REVIEW
    return RiskLevel.NORMAL
