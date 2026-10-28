from collections import defaultdict

from pydantic import BaseModel, ConfigDict

from app.domain.data_sources import ActivityDataSource
from app.evidence.models import EvidenceItem, EvidenceKind
from app.matcher.activity_matcher import compare_activity_versions
from app.matcher.models import ActivityChangeType, SourceComparison
from app.timeline.models import EmployeeDayTimeline, IntervalIssueType, TimelineActivity, TimelineSession


class SessionTimelineAnalysis(BaseModel):
    model_config = ConfigDict(frozen=True)

    source_session_id: str
    comparisons: tuple[SourceComparison, ...]


class EmployeeDayAnalysis(BaseModel):
    model_config = ConfigDict(frozen=True)

    timeline: EmployeeDayTimeline
    session_analyses: tuple[SessionTimelineAnalysis, ...]
    evidence: tuple[EvidenceItem, ...]


def analyze_employee_day(timeline: EmployeeDayTimeline) -> EmployeeDayAnalysis:
    session_analyses: list[SessionTimelineAnalysis] = []
    evidence: list[EvidenceItem] = _interval_evidence(timeline)
    for session in timeline.sessions:
        comparisons = _compare_session_chain(session)
        session_analyses.append(
            SessionTimelineAnalysis(
                source_session_id=session.source_session_id,
                comparisons=tuple(comparisons),
            )
        )
        for comparison in comparisons:
            evidence.extend(_comparison_evidence(comparison))

    evidence.sort(key=lambda item: (item.start_at, item.evidence_kind.value, item.description))
    return EmployeeDayAnalysis(
        timeline=timeline,
        session_analyses=tuple(session_analyses),
        evidence=tuple(evidence),
    )


def _compare_session_chain(session: TimelineSession) -> list[SourceComparison]:
    by_source: dict[ActivityDataSource, list[TimelineActivity]] = defaultdict(list)
    for activity in session.activities:
        by_source[activity.data_source_id].append(activity)
    for activities in by_source.values():
        activities.sort(key=lambda item: item.start_at)

    comparisons: list[SourceComparison] = []
    source_chain = (
        ActivityDataSource.AGENT,
        ActivityDataSource.SUPERVISOR,
        ActivityDataSource.MANAGER,
        ActivityDataSource.PAYROLL,
    )
    for target in source_chain:
        if not by_source[target]:
            continue
        baseline = _baseline_for(target, by_source)
        if baseline is None:
            comparisons.append(
                compare_activity_versions(
                    source_session_id=session.source_session_id,
                    baseline_source=ActivityDataSource.SYSTEM,
                    comparison_source=target,
                    baseline=[],
                    comparison=by_source[target],
                )
            )
            continue
        comparisons.append(
            compare_activity_versions(
                source_session_id=session.source_session_id,
                baseline_source=baseline,
                comparison_source=target,
                baseline=by_source[baseline],
                comparison=by_source[target],
            )
        )

    if by_source[ActivityDataSource.PHONE] and by_source[ActivityDataSource.SYSTEM]:
        comparisons.insert(
            0,
            compare_activity_versions(
                source_session_id=session.source_session_id,
                baseline_source=ActivityDataSource.PHONE,
                comparison_source=ActivityDataSource.SYSTEM,
                baseline=by_source[ActivityDataSource.PHONE],
                comparison=by_source[ActivityDataSource.SYSTEM],
            ),
        )
    return comparisons


def _baseline_for(
    target: ActivityDataSource,
    by_source: dict[ActivityDataSource, list[TimelineActivity]],
) -> ActivityDataSource | None:
    priority: dict[ActivityDataSource, tuple[ActivityDataSource, ...]] = {
        ActivityDataSource.AGENT: (ActivityDataSource.SYSTEM, ActivityDataSource.PHONE),
        ActivityDataSource.SUPERVISOR: (
            ActivityDataSource.AGENT,
            ActivityDataSource.SYSTEM,
            ActivityDataSource.PHONE,
        ),
        ActivityDataSource.MANAGER: (
            ActivityDataSource.SUPERVISOR,
            ActivityDataSource.AGENT,
            ActivityDataSource.SYSTEM,
            ActivityDataSource.PHONE,
        ),
        ActivityDataSource.PAYROLL: (
            ActivityDataSource.MANAGER,
            ActivityDataSource.SUPERVISOR,
            ActivityDataSource.AGENT,
            ActivityDataSource.SYSTEM,
            ActivityDataSource.PHONE,
        ),
    }
    return next((source for source in priority[target] if by_source[source]), None)


def _comparison_evidence(comparison: SourceComparison) -> list[EvidenceItem]:
    evidence: list[EvidenceItem] = []
    for match in comparison.matches:
        if match.change_type == ActivityChangeType.UNCHANGED:
            continue
        before = match.baseline_activity
        after = match.comparison_activity
        activity = after or before
        assert activity is not None
        evidence.append(
            EvidenceItem(
                evidence_kind=EvidenceKind.ACTIVITY_CHANGE,
                source_session_id=comparison.source_session_id,
                baseline_source=comparison.baseline_source,
                comparison_source=comparison.comparison_source,
                change_type=match.change_type,
                baseline_activity_id=before.source_activity_id if before else None,
                comparison_activity_id=after.source_activity_id if after else None,
                start_at=activity.start_at,
                end_at=activity.end_at,
                seconds_delta=match.duration_delta_seconds,
                confidence=match.confidence,
                activity_type_before=before.activity_type_id if before else None,
                activity_type_after=after.activity_type_id if after else None,
                description=_change_description(comparison, match.change_type, match.duration_delta_seconds),
            )
        )
    return evidence


def _change_description(
    comparison: SourceComparison, change_type: ActivityChangeType, seconds_delta: int
) -> str:
    left = comparison.baseline_source.label
    right = comparison.comparison_source.label
    if change_type == ActivityChangeType.INSERTED:
        return f"{right} contains an activity not matched to {left}."
    if change_type == ActivityChangeType.REMOVED:
        return f"An activity present in {left} is not matched in {right}."
    if change_type == ActivityChangeType.TYPE_CHANGED:
        return f"Activity type changed between {left} and {right}."
    if change_type == ActivityChangeType.EXTENDED:
        return f"{right} extends matched activity time by {seconds_delta} seconds."
    if change_type == ActivityChangeType.SHORTENED:
        return f"{right} shortens matched activity time by {abs(seconds_delta)} seconds."
    if change_type == ActivityChangeType.SHIFTED:
        return f"Matched activity boundaries shifted between {left} and {right}."
    return f"Matched activity changed between {left} and {right}."


def _interval_evidence(timeline: EmployeeDayTimeline) -> list[EvidenceItem]:
    result: list[EvidenceItem] = []
    for issue in timeline.interval_issues:
        if issue.issue_type == IntervalIssueType.SESSION_OVERLAP:
            kind = EvidenceKind.SESSION_OVERLAP
            description = (
                f"Login sessions {issue.source_session_id} and {issue.other_session_id} overlap "
                f"for {issue.duration_seconds} seconds."
            )
        elif issue.issue_type == IntervalIssueType.OVERLAP:
            kind = EvidenceKind.ACTIVITY_OVERLAP
            description = (
                f"{issue.data_source_id.label if issue.data_source_id is not None else 'Source'} "
                f"activities overlap for {issue.duration_seconds} seconds."
            )
        else:
            kind = EvidenceKind.ACTIVITY_GAP
            description = (
                f"{issue.data_source_id.label if issue.data_source_id is not None else 'Source'} "
                f"timeline contains a {issue.duration_seconds}-second gap."
            )
        result.append(
            EvidenceItem(
                evidence_kind=kind,
                source_session_id=issue.source_session_id,
                other_session_id=issue.other_session_id,
                baseline_source=issue.data_source_id,
                start_at=issue.start_at,
                end_at=issue.end_at,
                seconds_delta=issue.duration_seconds,
                description=description,
            )
        )
    return result
