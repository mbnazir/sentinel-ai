from collections import defaultdict
from multiprocessing import context

from app.domain.data_sources import ActivityDataSource
from app.evidence.models import EvidenceItem, EvidenceKind
from app.matcher.models import ActivityChangeType
from app.rules.context import RuleContext
from app.rules.models import FindingCategory, RuleFinding, RuleSeverity
from app.scoring.risk import contribution


def _manual_positive_change(evidence: EvidenceItem, source: ActivityDataSource) -> bool:
    return (
        evidence.evidence_kind == EvidenceKind.ACTIVITY_CHANGE
        and evidence.comparison_source == source
        and evidence.change_type in {
            ActivityChangeType.INSERTED,
            ActivityChangeType.EXTENDED,
            ActivityChangeType.COMPOUND,
        }
        and evidence.seconds_delta > 0
    )


def _confidence_with_capture(context: RuleContext, session_id: str, evidence_confidence: float) -> float:
    session = context.session(session_id)
    captured = context.captured_seconds(session)
    if 0 < captured < context.policy.captured_evidence_low_seconds:
        return round(evidence_confidence * 0.65, 4)
    return evidence_confidence


def _finding(
    *,
    rule_id: str,
    rule_name: str,
    category: FindingCategory,
    severity: RuleSeverity,
    confidence: float,
    reason: str,
    source_session_id: str | None = None,
    evidence: tuple[EvidenceItem, ...] = (),
    magnitude: float = 1.0,
    metadata: dict[str, object] | None = None,
) -> RuleFinding:
    return RuleFinding(
        rule_id=rule_id,
        rule_name=rule_name,
        category=category,
        severity=severity,
        source_session_id=source_session_id,
        confidence=confidence,
        risk_contribution=contribution(severity, confidence, magnitude),
        reason=reason,
        evidence=evidence,
        metadata=metadata or {},
    )


class AgentAddedTimeWithoutReviewRule:
    rule_id = "SA-R001"
    name = "Agent added time without downstream review"

    def evaluate(self, context: RuleContext) -> tuple[RuleFinding, ...]:
        findings: list[RuleFinding] = []
        by_session: dict[str, list[EvidenceItem]] = defaultdict(list)
        for item in context.analysis.evidence:
            if item.source_session_id and _manual_positive_change(item, ActivityDataSource.AGENT):
                by_session[item.source_session_id].append(item)
        for session_id, items in by_session.items():
            session = context.session(session_id)
            later_sources = {
                ActivityDataSource.SUPERVISOR,
                ActivityDataSource.MANAGER,
                ActivityDataSource.PAYROLL,
            }
            if any(activity.data_source_id in later_sources for activity in session.activities):
                continue
            if session.supervisor_action_at is not None or session.manager_action_at is not None:
                continue
            added = sum(max(0, item.seconds_delta) for item in items)
            confidence = min(_confidence_with_capture(context, session_id, max(i.confidence for i in items)), 0.95)
            findings.append(_finding(
                rule_id=self.rule_id,
                rule_name=self.name,
                category=FindingCategory.WORKFLOW,
                severity=RuleSeverity.HIGH,
                confidence=confidence,
                source_session_id=session_id,
                evidence=tuple(items),
                magnitude=1.0 + min(added / 7200, 0.75),
                reason=f"Agent-added time ({round(added / 60)} minutes) has no Supervisor, Manager, or Payroll activity version after it.",
                metadata={"added_seconds": added},
            ))
        return tuple(findings)


class RoleAddedTimeRule:
    def __init__(
        self,
        rule_id: str,
        name: str,
        source: ActivityDataSource,
        severity: RuleSeverity,
        category: FindingCategory,
    ) -> None:
        self.rule_id = rule_id
        self.name = name
        self.source = source
        self.severity = severity
        self.category = category

    def evaluate(self, context: RuleContext) -> tuple[RuleFinding, ...]:
        findings: list[RuleFinding] = []
        by_session: dict[str, list[EvidenceItem]] = defaultdict(list)
        for item in context.analysis.evidence:
            if item.source_session_id and _manual_positive_change(item, self.source):
                by_session[item.source_session_id].append(item)
        for session_id, items in by_session.items():
            added = sum(max(0, item.seconds_delta) for item in items)
            confidence = _confidence_with_capture(context, session_id, max(i.confidence for i in items))
            findings.append(_finding(
                rule_id=self.rule_id,
                rule_name=self.name,
                category=self.category,
                severity=self.severity,
                confidence=confidence,
                source_session_id=session_id,
                evidence=tuple(items),
                magnitude=1.0 + min(added / 7200, 0.75),
                reason=f"{self.source.label} increased matched/manual activity time by {round(added / 60)} minutes beyond the latest available prior version.",
                metadata={"added_seconds": added, "comparison_source": self.source.label},
            ))
        return tuple(findings)


class CapturedActivityRemovedRule:
    def __init__(self, baseline: ActivityDataSource, rule_id: str, name: str) -> None:
        self.baseline = baseline
        self.rule_id = rule_id
        self.name = name

    def evaluate(self, context: RuleContext) -> tuple[RuleFinding, ...]:
        findings: list[RuleFinding] = []
        for item in context.analysis.evidence:
            if (
                item.evidence_kind == EvidenceKind.ACTIVITY_CHANGE
                and item.change_type == ActivityChangeType.REMOVED
                and item.baseline_source == self.baseline
                and item.comparison_source is not None
                and item.comparison_source.is_manual
                and item.source_session_id
            ):
                seconds = abs(item.seconds_delta)
                # Open-ended activities cannot establish a reliable
                # removed-duration magnitude.
                if item.end_at is None:
                    continue

                # Avoid classifying negligible duration differences
                # as critical time-loss findings.
                if seconds < 60:
                    continue

                confidence = _confidence_with_capture(
                    context, item.source_session_id, item.confidence
                )
                findings.append(_finding(
                    rule_id=self.rule_id,
                    rule_name=self.name,
                    category=FindingCategory.INTEGRITY,
                    severity=RuleSeverity.CRITICAL,
                    confidence=confidence,
                    source_session_id=item.source_session_id,
                    evidence=(item,),
                    magnitude=1.0 + min(seconds / 3600, 0.75),
                    reason=f"A {self.baseline.label} activity covering {round(seconds / 60)} minutes is absent from the later {item.comparison_source.label} version.",
                    metadata={"removed_seconds": seconds},
                ))
        return tuple(findings)


class ManualActivityInsertedRule:
    rule_id = "SA-R007"
    name = "Manual activity inserted"

    def evaluate(self, context: RuleContext) -> tuple[RuleFinding, ...]:
        findings: list[RuleFinding] = []
        for item in context.analysis.evidence:
            if (
                item.evidence_kind == EvidenceKind.ACTIVITY_CHANGE
                and item.change_type == ActivityChangeType.INSERTED
                and item.comparison_source is not None
                and item.comparison_source.is_manual
                and item.source_session_id
            ):
                confidence = _confidence_with_capture(context, item.source_session_id, item.confidence)
                findings.append(_finding(
                    rule_id=self.rule_id,
                    rule_name=self.name,
                    category=FindingCategory.INTEGRITY,
                    severity=RuleSeverity.HIGH,
                    confidence=confidence,
                    source_session_id=item.source_session_id,
                    evidence=(item,),
                    magnitude=1.0 + min(item.seconds_delta / 7200, 0.75),
                    reason=f"{item.comparison_source.label} inserted an unmatched {round(item.seconds_delta / 60)}-minute activity.",
                    metadata={"inserted_seconds": item.seconds_delta},
                ))
        return tuple(findings)


class ActivityTypeChangedRule:
    rule_id = "SA-R008"
    name = "Manual activity type changed"

    def evaluate(self, context: RuleContext) -> tuple[RuleFinding, ...]:
        return tuple(
            _finding(
                rule_id=self.rule_id,
                rule_name=self.name,
                category=FindingCategory.INTEGRITY,
                severity=RuleSeverity.HIGH,
                confidence=item.confidence,
                source_session_id=item.source_session_id,
                evidence=(item,),
                reason=f"{item.comparison_source.label} changed activity type {item.activity_type_before} to {item.activity_type_after}.",
                metadata={"activity_type_before": item.activity_type_before, "activity_type_after": item.activity_type_after},
            )
            for item in context.analysis.evidence
            if item.evidence_kind == EvidenceKind.ACTIVITY_CHANGE
            and item.change_type in {ActivityChangeType.TYPE_CHANGED, ActivityChangeType.COMPOUND}
            and item.activity_type_before != item.activity_type_after
            and item.comparison_source is not None
            and item.comparison_source.is_manual
            and item.source_session_id is not None
        )


class LargeAdditionRule:
    rule_id = "SA-R009"
    name = "Large contiguous manual addition"

    def evaluate(self, context: RuleContext) -> tuple[RuleFinding, ...]:
        findings: list[RuleFinding] = []
        for item in context.analysis.evidence:
            if (
                item.seconds_delta >= context.policy.large_addition_seconds
                and item.change_type in {ActivityChangeType.INSERTED, ActivityChangeType.EXTENDED, ActivityChangeType.COMPOUND}
                and item.comparison_source is not None
                and item.comparison_source.is_manual
                and item.source_session_id
            ):
                confidence = _confidence_with_capture(context, item.source_session_id, item.confidence)
                findings.append(_finding(
                    rule_id=self.rule_id,
                    rule_name=self.name,
                    category=FindingCategory.INTEGRITY,
                    severity=RuleSeverity.CRITICAL,
                    confidence=confidence,
                    source_session_id=item.source_session_id,
                    evidence=(item,),
                    magnitude=1.0 + min(item.seconds_delta / 14400, 0.75),
                    reason=f"A single {item.comparison_source.label} edit added {round(item.seconds_delta / 60)} minutes.",
                    metadata={"added_seconds": item.seconds_delta},
                ))
        return tuple(findings)


class RoundedAdditionRule:
    rule_id = "SA-R010"
    name = "Rounded manual time addition"

    def evaluate(self, context: RuleContext) -> tuple[RuleFinding, ...]:
        interval = context.policy.rounded_increment_seconds
        findings: list[RuleFinding] = []
        for item in context.analysis.evidence:
            if (
                item.seconds_delta >= context.policy.minimum_rounded_addition_seconds
                and item.seconds_delta % interval == 0
                and item.change_type in {ActivityChangeType.INSERTED, ActivityChangeType.EXTENDED, ActivityChangeType.COMPOUND}
                and item.comparison_source is not None
                and item.comparison_source.is_manual
                and item.source_session_id
            ):
                findings.append(_finding(
                    rule_id=self.rule_id,
                    rule_name=self.name,
                    category=FindingCategory.INTEGRITY,
                    severity=RuleSeverity.LOW,
                    confidence=item.confidence,
                    source_session_id=item.source_session_id,
                    evidence=(item,),
                    reason=f"Manual addition is exactly {round(item.seconds_delta / 60)} minutes, a configured round-time increment.",
                    metadata={"added_seconds": item.seconds_delta, "rounding_interval_seconds": interval},
                ))
        return tuple(findings)


class FinalExceedsCaptureRule:
    rule_id = "SA-R011"
    name = "Final manual duration exceeds captured evidence"

    def evaluate(self, context: RuleContext) -> tuple[RuleFinding, ...]:
        findings: list[RuleFinding] = []
        for session in context.analysis.timeline.sessions:
            captured = context.captured_seconds(session)
            final_source, final_seconds = context.latest_manual_seconds(session)
            if final_source is None or final_seconds <= captured + context.policy.final_vs_capture_tolerance_seconds:
                continue
            delta = final_seconds - captured
            confidence = 0.65 if 0 < captured < context.policy.captured_evidence_low_seconds else 0.95
            findings.append(_finding(
                rule_id=self.rule_id,
                rule_name=self.name,
                category=FindingCategory.PAYROLL,
                severity=RuleSeverity.HIGH,
                confidence=confidence,
                source_session_id=session.source_session_id,
                magnitude=1.0 + min(delta / 7200, 0.75),
                reason=f"Latest {final_source.label} version exceeds the strongest Phone/System captured duration by {round(delta / 60)} minutes.",
                metadata={"captured_seconds": captured, "final_seconds": final_seconds, "final_source": final_source.label},
            ))
        return tuple(findings)


class DirectWorkflowEditRule:
    def __init__(
        self,
        *,
        rule_id: str,
        name: str,
        source: ActivityDataSource,
        required_prior: tuple[ActivityDataSource, ...],
        severity: RuleSeverity,
    ) -> None:
        self.rule_id = rule_id
        self.name = name
        self.source = source
        self.required_prior = required_prior
        self.severity = severity

    def evaluate(self, context: RuleContext) -> tuple[RuleFinding, ...]:
        findings: list[RuleFinding] = []
        for session in context.analysis.timeline.sessions:
            if not context.source_activities(session, self.source):
                continue
            missing = [source for source in self.required_prior if not context.source_activities(session, source)]
            if len(missing) != len(self.required_prior):
                continue
            findings.append(_finding(
                rule_id=self.rule_id,
                rule_name=self.name,
                category=FindingCategory.WORKFLOW,
                severity=self.severity,
                confidence=0.9,
                source_session_id=session.source_session_id,
                reason=f"{self.source.label} activity version exists without any expected prior manual version ({', '.join(s.label for s in self.required_prior)}).",
                metadata={"missing_prior_sources": [source.label for source in missing]},
            ))
        return tuple(findings)


class PayrollAfterManagerApprovalRule:
    rule_id = "SA-R014"
    name = "Payroll modification after manager action"

    def evaluate(self, context: RuleContext) -> tuple[RuleFinding, ...]:
        findings: list[RuleFinding] = []
        for session in context.analysis.timeline.sessions:
            if not context.source_activities(session, ActivityDataSource.PAYROLL):
                continue
            if session.manager_action_at is None:
                continue
            if session.payroll_adjusted_at is not None and session.payroll_adjusted_at < session.manager_action_at:
                continue
            findings.append(_finding(
                rule_id=self.rule_id,
                rule_name=self.name,
                category=FindingCategory.PAYROLL,
                severity=RuleSeverity.HIGH,
                confidence=0.95,
                source_session_id=session.source_session_id,
                reason="Payroll activity exists after a recorded manager action; downstream adjustment requires independent validation.",
                metadata={
                    "manager_action_at": session.manager_action_at.isoformat(),
                    "payroll_adjusted_at": session.payroll_adjusted_at.isoformat() if session.payroll_adjusted_at else None,
                },
            ))
        return tuple(findings)


class SessionOverlapRule:
    rule_id = "SA-R015"
    name = "Overlapping login sessions"

    def evaluate(self, context: RuleContext) -> tuple[RuleFinding, ...]:
        return tuple(
            _finding(
                rule_id=self.rule_id,
                rule_name=self.name,
                category=FindingCategory.INTEGRITY,
                severity=RuleSeverity.HIGH,
                confidence=item.confidence,
                source_session_id=item.source_session_id,
                evidence=(item,),
                magnitude=1.0 + min(item.seconds_delta / 7200, 0.75),
                reason=item.description,
                metadata={"other_session_id": item.other_session_id, "overlap_seconds": item.seconds_delta},
            )
            for item in context.analysis.evidence
            if item.evidence_kind == EvidenceKind.SESSION_OVERLAP
        )


class RepeatedModifiedSessionsRule:
    rule_id = "SA-R016"
    name = "Repeated modified sessions on same employee-day"

    def evaluate(self, context: RuleContext) -> tuple[RuleFinding, ...]:
        modified: set[str] = set()
        for item in context.analysis.evidence:
            if (
                item.source_session_id
                and item.evidence_kind == EvidenceKind.ACTIVITY_CHANGE
                and item.comparison_source is not None
                and item.comparison_source.is_manual
                and item.change_type != ActivityChangeType.UNCHANGED
            ):
                modified.add(item.source_session_id)
        if len(modified) < context.policy.repeated_modified_sessions_threshold:
            return ()
        return (_finding(
            rule_id=self.rule_id,
            rule_name=self.name,
            category=FindingCategory.COLLUSION,
            severity=RuleSeverity.HIGH,
            confidence=0.9,
            reason=f"{len(modified)} separate login sessions for the same agent and shift date contain manual changes.",
            magnitude=1.0 + min((len(modified) - 1) * 0.15, 0.75),
            metadata={"modified_session_ids": sorted(modified)},
        ),)


class MultipleLoginsFlagRule:
    rule_id = "SA-R017"
    name = "Quartz multiple-login/abnormal-shutdown flag"

    def evaluate(self, context: RuleContext) -> tuple[RuleFinding, ...]:
        return tuple(
            _finding(
                rule_id=self.rule_id,
                rule_name=self.name,
                category=FindingCategory.DATA_QUALITY,
                severity=RuleSeverity.MEDIUM,
                confidence=1.0,
                source_session_id=session.source_session_id,
                reason=f"Quartz multiple_logins flag is {session.multiple_logins}; review system continuity before attributing manual time changes to misconduct.",
                metadata={"multiple_logins": session.multiple_logins},
            )
            for session in context.analysis.timeline.sessions
            if session.multiple_logins != 0
        )


class ManualSessionWithoutCaptureRule:
    rule_id = "SA-R018"
    name = "Manually added session without Phone/System corroboration"

    def evaluate(self, context: RuleContext) -> tuple[RuleFinding, ...]:
        findings: list[RuleFinding] = []
        for session in context.analysis.timeline.sessions:
            if session.session_added_by is None:
                continue
            if context.captured_seconds(session) > 0:
                continue
            _, manual_seconds = context.latest_manual_seconds(session)
            findings.append(_finding(
                rule_id=self.rule_id,
                rule_name=self.name,
                category=FindingCategory.INTEGRITY,
                severity=RuleSeverity.CRITICAL,
                confidence=0.95,
                source_session_id=session.source_session_id,
                magnitude=1.0 + min(manual_seconds / 14400, 0.75),
                reason="Session was manually added but contains no Phone or System activity evidence to corroborate worked time.",
                metadata={
                    "session_added_by": session.session_added_by,
                    "add_session_reason_id": session.add_session_reason_id,
                    "manual_seconds": manual_seconds,
                },
            ))
        return tuple(findings)


class LowCaptureCoverageRule:
    rule_id = "SA-R019"
    name = "Low captured evidence coverage"

    def evaluate(self, context: RuleContext) -> tuple[RuleFinding, ...]:
        findings: list[RuleFinding] = []
        for session in context.analysis.timeline.sessions:
            captured = context.captured_seconds(session)
            _, manual = context.latest_manual_seconds(session)
            if not (0 < captured < context.policy.captured_evidence_low_seconds and manual > captured):
                continue
            findings.append(_finding(
                rule_id=self.rule_id,
                rule_name=self.name,
                category=FindingCategory.DATA_QUALITY,
                severity=RuleSeverity.INFO,
                confidence=1.0,
                source_session_id=session.source_session_id,
                reason=f"Phone/System evidence covers only {round(captured / 60)} minutes. Positive manual-time findings for this session are confidence-reduced because a capture/system issue is plausible.",
                metadata={"captured_seconds": captured, "manual_seconds": manual},
            ))
        return tuple(findings)


class ExcessiveFinalDayRule:
    rule_id = "SA-R020"
    name = "Excessive final payable duration"

    def evaluate(self, context: RuleContext) -> tuple[RuleFinding, ...]:
        total = 0
        source_breakdown: dict[str, int] = {}
        for session in context.analysis.timeline.sessions:
            source, seconds = context.latest_manual_seconds(session)
            if source is None:
                seconds = context.captured_seconds(session)
                source_name = "Captured"
            else:
                source_name = source.label
            total += seconds
            source_breakdown[session.source_session_id] = seconds
        if total <= context.policy.excessive_day_seconds:
            return ()
        return (_finding(
            rule_id=self.rule_id,
            rule_name=self.name,
            category=FindingCategory.PAYROLL,
            severity=RuleSeverity.HIGH,
            confidence=0.9,
            reason=f"Combined final duration across all sessions on the shift date is {round(total / 3600, 2)} hours, exceeding the configured {round(context.policy.excessive_day_seconds / 3600, 2)}-hour threshold.",
            magnitude=1.0 + min((total - context.policy.excessive_day_seconds) / 14400, 0.75),
            metadata={"total_seconds": total, "session_seconds": source_breakdown},
        ),)


class InactivityReducedRule:
    rule_id = "SA-R021"
    name = "Manual version reduced recorded inactivity"

    def evaluate(self, context: RuleContext) -> tuple[RuleFinding, ...]:
        findings: list[RuleFinding] = []
        for session_analysis in context.analysis.session_analyses:
            for comparison in session_analysis.comparisons:
                if not comparison.comparison_source.is_manual:
                    continue
                for match in comparison.matches:
                    before = match.baseline_activity
                    after = match.comparison_activity
                    if before is None or after is None:
                        continue
                    reduction = before.inactivity_seconds - after.inactivity_seconds
                    if reduction <= 0:
                        continue
                    findings.append(_finding(
                        rule_id=self.rule_id,
                        rule_name=self.name,
                        category=FindingCategory.INTEGRITY,
                        severity=RuleSeverity.HIGH,
                        confidence=match.confidence,
                        source_session_id=session_analysis.source_session_id,
                        reason=f"{comparison.comparison_source.label} reduced recorded inactivity by {round(reduction / 60)} minutes on a matched activity.",
                        metadata={"inactivity_reduced_seconds": reduction},
                    ))
        return tuple(findings)


class MissingCommentOnAdditionRule:
    rule_id = "SA-R022"
    name = "Manual time addition lacks activity comment"

    def evaluate(self, context: RuleContext) -> tuple[RuleFinding, ...]:
        findings: list[RuleFinding] = []
        for session_analysis in context.analysis.session_analyses:
            for comparison in session_analysis.comparisons:
                if not comparison.comparison_source.is_manual:
                    continue
                for match in comparison.matches:
                    if match.duration_delta_seconds <= 0 or match.comparison_activity is None:
                        continue
                    if match.comparison_activity.comment and match.comparison_activity.comment.strip():
                        continue
                    findings.append(_finding(
                        rule_id=self.rule_id,
                        rule_name=self.name,
                        category=FindingCategory.WORKFLOW,
                        severity=RuleSeverity.LOW,
                        confidence=match.confidence,
                        source_session_id=session_analysis.source_session_id,
                        reason=f"{comparison.comparison_source.label} added {round(match.duration_delta_seconds / 60)} minutes without an activity-level comment.",
                        metadata={"added_seconds": match.duration_delta_seconds},
                    ))
        return tuple(findings)


class PhoneSystemMismatchRule:
    rule_id = "SA-R023"
    name = "Phone/System captured-time mismatch"

    def evaluate(self, context: RuleContext) -> tuple[RuleFinding, ...]:
        findings: list[RuleFinding] = []
        for session in context.analysis.timeline.sessions:
            phone = context.source_seconds(session, ActivityDataSource.PHONE)
            system = context.source_seconds(session, ActivityDataSource.SYSTEM)
            if phone == 0 or system == 0:
                continue
            delta = abs(phone - system)
            if delta <= context.policy.phone_system_mismatch_seconds:
                continue
            findings.append(_finding(
                rule_id=self.rule_id,
                rule_name=self.name,
                category=FindingCategory.DATA_QUALITY,
                severity=RuleSeverity.MEDIUM,
                confidence=1.0,
                source_session_id=session.source_session_id,
                reason=f"Phone and System captured durations differ by {round(delta / 60)} minutes; manual adjustments require additional corroboration.",
                metadata={"phone_seconds": phone, "system_seconds": system, "difference_seconds": delta},
            ))
        return tuple(findings)


class MultiStageManualRevisionRule:
    rule_id = "SA-R024"
    name = "Multiple manual workflow stages modified session"

    def evaluate(self, context: RuleContext) -> tuple[RuleFinding, ...]:
        findings: list[RuleFinding] = []
        for session in context.analysis.timeline.sessions:
            sources = [
                source
                for source in (ActivityDataSource.AGENT, ActivityDataSource.SUPERVISOR, ActivityDataSource.MANAGER, ActivityDataSource.PAYROLL)
                if context.source_activities(session, source)
            ]
            if len(sources) < 3:
                continue
            findings.append(_finding(
                rule_id=self.rule_id,
                rule_name=self.name,
                category=FindingCategory.WORKFLOW,
                severity=RuleSeverity.MEDIUM,
                confidence=0.9,
                source_session_id=session.source_session_id,
                reason=f"Session contains manual versions from {len(sources)} workflow stages: {', '.join(source.label for source in sources)}.",
                magnitude=1.0 + ((len(sources) - 3) * 0.25),
                metadata={"manual_sources": [source.label for source in sources]},
            ))
        return tuple(findings)


BUILTIN_RULES = (
    AgentAddedTimeWithoutReviewRule(),
    RoleAddedTimeRule("SA-R002", "Supervisor added time beyond prior version", ActivityDataSource.SUPERVISOR, RuleSeverity.CRITICAL, FindingCategory.COLLUSION),
    RoleAddedTimeRule("SA-R003", "Manager added time beyond prior version", ActivityDataSource.MANAGER, RuleSeverity.CRITICAL, FindingCategory.COLLUSION),
    RoleAddedTimeRule("SA-R004", "Payroll added time beyond prior version", ActivityDataSource.PAYROLL, RuleSeverity.CRITICAL, FindingCategory.PAYROLL),
    CapturedActivityRemovedRule(ActivityDataSource.SYSTEM, "SA-R005", "System activity removed from manual version"),
    CapturedActivityRemovedRule(ActivityDataSource.PHONE, "SA-R006", "Phone activity removed from manual version"),
    ManualActivityInsertedRule(),
    ActivityTypeChangedRule(),
    LargeAdditionRule(),
    RoundedAdditionRule(),
    FinalExceedsCaptureRule(),
    DirectWorkflowEditRule(rule_id="SA-R012", name="Supervisor edited without Agent version", source=ActivityDataSource.SUPERVISOR, required_prior=(ActivityDataSource.AGENT,), severity=RuleSeverity.HIGH),
    DirectWorkflowEditRule(rule_id="SA-R013", name="Manager edited without Agent/Supervisor version", source=ActivityDataSource.MANAGER, required_prior=(ActivityDataSource.AGENT, ActivityDataSource.SUPERVISOR), severity=RuleSeverity.HIGH),
    PayrollAfterManagerApprovalRule(),
    SessionOverlapRule(),
    RepeatedModifiedSessionsRule(),
    MultipleLoginsFlagRule(),
    ManualSessionWithoutCaptureRule(),
    LowCaptureCoverageRule(),
    ExcessiveFinalDayRule(),
    InactivityReducedRule(),
    MissingCommentOnAdditionRule(),
    PhoneSystemMismatchRule(),
    MultiStageManualRevisionRule(),
)
