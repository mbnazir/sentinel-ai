from app.weekly.models import ResolutionStatus, WeeklyImpactAssessment
from app.weekly.activity_models import ActivityChangeType, ComparisonStatus, VersionComparison


def evaluate_weekly_rules(assessment: WeeklyImpactAssessment) -> tuple[dict[str, object], ...]:
    week, summary = assessment.payroll_week, assessment.summary
    findings: list[dict[str, object]] = []
    complete = week.completeness.value == "COMPLETE"
    if assessment.adjustments:
        findings.append({"rule_id": "WF-001", "classification": "investigative_lead",
                         "actor_evidence": "available", "adjustment_ids": [a.adjustment_id for a in assessment.adjustments]})
    valid_impact = complete and summary.status == ResolutionStatus.VERIFIED
    if valid_impact and summary.incremental_overtime_seconds and summary.incremental_overtime_seconds > 0:
        findings.append({"rule_id": "WF-002", "classification": "confirmed_mathematical_impact",
                         "incremental_overtime_seconds": str(summary.incremental_overtime_seconds)})
        overtime_date = assessment.provenance.get("overtime_reached_on")
        earlier = [a for a in assessment.adjustments
                   if overtime_date and a.shift_date.isoformat() < str(overtime_date)]
        if earlier:
            findings.append({"rule_id": "WF-003", "classification": "earlier_adjustment_later_overtime",
                             "adjustment_ids": [a.adjustment_id for a in earlier]})
    if not complete:
        findings.append({"classification": "incomplete_payroll_week"})
    if any(a.actor_id == "ACTOR_UNVERIFIED" for a in assessment.adjustments):
        findings.append({"classification": "missing_attribution_evidence"})
    return tuple(findings)


def repeated_actor_employee_patterns(assessments, *, minimum_weeks: int = 2,
                                    comparison_population_reliable: bool = False
                                    ) -> tuple[dict[str, object], ...]:
    """Only report repeated patterns from complete, verified weeks and explicitly verified actors."""
    if not comparison_population_reliable:
        return ()
    grouped: dict[tuple[str, str], set[str]] = {}
    for item in assessments:
        if item.payroll_week.completeness.value != "COMPLETE" or item.summary.status != ResolutionStatus.VERIFIED:
            continue
        for adjustment in item.adjustments:
            if adjustment.actor_status.value != "VERIFIED":
                continue
            grouped.setdefault((adjustment.actor_id, adjustment.employee_id), set()).add(
                item.payroll_week.start_date.isoformat())
    return tuple({"rule_id": "WF-004", "actor_id": actor, "employee_id": employee,
                  "complete_weeks": sorted(weeks), "classification": "investigative_lead"}
                 for (actor, employee), weeks in sorted(grouped.items()) if len(weeks) >= minimum_weeks)


def evaluate_wf005(comparison: VersionComparison) -> dict[str, object] | None:
    """Create a provisional review signal only for defensible interval reclassification."""
    if (comparison.readiness.status == ComparisonStatus.INCOMPLETE
            or comparison.readiness.malformed_activity_ids
            or comparison.original_version is None or comparison.revised_version is None
            or comparison.original_version.data_source_id == comparison.revised_version.data_source_id):
        return None
    if not any(change.change_type == ActivityChangeType.RECLASSIFIED for change in comparison.changes):
        return None
    return {
        "code": "WF-005",
        "classification": "provisional_review_signal",
        "observation": "Activity classification differs between available source timelines",
        "interpretation": "Interval-level reclassification observed",
        "suspected_risk": "Requires review; no fraud conclusion",
        "verified_fact": "Captured activity classifications and intervals differ",
        "editor_identity": "UNVERIFIED",
        "financial_impact": "UNVERIFIED",
    }
