from collections import defaultdict
from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.data_sources import ActivityDataSource
from app.infrastructure.models import ActivitySnapshotModel, SessionSnapshotModel
from app.timeline.models import (
    EmployeeDayTimeline,
    IntervalIssue,
    IntervalIssueType,
    TimelineActivity,
    TimelineSession,
)

MIN_GAP_SECONDS = 60


async def load_employee_day_timeline(
    db: AsyncSession,
    *,
    ingestion_run_id: UUID,
    agent_id: str,
    shift_date: date,
) -> EmployeeDayTimeline | None:
    session_result = await db.execute(
        select(SessionSnapshotModel)
        .where(
            SessionSnapshotModel.ingestion_run_id == ingestion_run_id,
            SessionSnapshotModel.agent_id == agent_id,
            SessionSnapshotModel.shift_date == shift_date,
        )
        .order_by(SessionSnapshotModel.start_at, SessionSnapshotModel.source_session_id)
    )
    session_rows = list(session_result.scalars())
    if not session_rows:
        return None

    session_ids = [row.source_session_id for row in session_rows]
    activity_result = await db.execute(
        select(ActivitySnapshotModel)
        .where(
            ActivitySnapshotModel.ingestion_run_id == ingestion_run_id,
            ActivitySnapshotModel.source_session_id.in_(session_ids),
        )
        .order_by(
            ActivitySnapshotModel.source_session_id,
            ActivitySnapshotModel.data_source_id,
            ActivitySnapshotModel.start_at,
        )
    )
    activities_by_session: dict[str, list[TimelineActivity]] = defaultdict(list)
    for row in activity_result.scalars():
        activities_by_session[row.source_session_id].append(
            TimelineActivity(
                source_activity_id=row.source_activity_id,
                source_session_id=row.source_session_id,
                agent_id=row.agent_id,
                data_source_id=ActivityDataSource(row.data_source_id),
                activity_type_id=row.activity_type_id,
                start_at=row.start_at,
                end_at=row.end_at,
                duration_seconds=_duration_seconds(row),
                inactivity_seconds=row.inactivity_seconds,
                comment=row.comment,
            )
        )

    sessions = tuple(
        TimelineSession(
            source_session_id=row.source_session_id,
            agent_id=row.agent_id,
            shift_date=row.shift_date,
            start_at=row.start_at,
            end_at=row.end_at,
            ready_for_payroll=row.ready_for_payroll,
            payroll_adjusted=row.payroll_adjusted,
            payroll_adjusted_at=row.payroll_adjusted_at,
            session_added_by=row.session_added_by,
            add_session_reason_id=row.add_session_reason_id,
            agent_action_at=row.agent_action_at,
            supervisor_action_at=row.supervisor_action_at,
            manager_action_at=row.manager_action_at,
            multiple_logins=row.multiple_logins,
            activities=tuple(activities_by_session[row.source_session_id]),
        )
        for row in session_rows
    )
    return EmployeeDayTimeline(
        ingestion_run_id=ingestion_run_id,
        agent_id=agent_id,
        shift_date=shift_date,
        sessions=sessions,
        interval_issues=tuple(_interval_issues(sessions)),
    )


def _duration_seconds(row: ActivitySnapshotModel) -> int:
    if row.duration_seconds is not None:
        return max(0, int(row.duration_seconds))
    if row.end_at is None:
        return 0
    return max(0, int((row.end_at - row.start_at).total_seconds()))


def _interval_issues(sessions: tuple[TimelineSession, ...]) -> list[IntervalIssue]:
    issues = _session_overlap_issues(sessions)
    for session in sessions:
        by_source: dict[ActivityDataSource, list[TimelineActivity]] = defaultdict(list)
        for activity in session.activities:
            by_source[activity.data_source_id].append(activity)
        for source, activities in by_source.items():
            issues.extend(_activity_interval_issues(session.source_session_id, source, activities))
    return sorted(issues, key=lambda item: (item.start_at, item.issue_type.value))


def _activity_interval_issues(
    source_session_id: str,
    source: ActivityDataSource,
    activities: list[TimelineActivity],
) -> list[IntervalIssue]:
    ordered = sorted(activities, key=lambda item: (item.start_at, item.end_at or item.start_at))
    issues: list[IntervalIssue] = []
    for left, right in zip(ordered, ordered[1:], strict=False):
        if left.end_at is None:
            continue
        delta = int((right.start_at - left.end_at).total_seconds())
        if delta >= MIN_GAP_SECONDS:
            issues.append(
                IntervalIssue(
                    issue_type=IntervalIssueType.GAP,
                    source_session_id=source_session_id,
                    data_source_id=source,
                    start_at=left.end_at,
                    end_at=right.start_at,
                    duration_seconds=delta,
                    activity_ids=(left.source_activity_id, right.source_activity_id),
                )
            )
        elif delta < 0:
            issues.append(
                IntervalIssue(
                    issue_type=IntervalIssueType.OVERLAP,
                    source_session_id=source_session_id,
                    data_source_id=source,
                    start_at=right.start_at,
                    end_at=min(left.end_at, right.end_at or left.end_at),
                    duration_seconds=max(0, int((min(left.end_at, right.end_at or left.end_at) - right.start_at).total_seconds())),
                    activity_ids=(left.source_activity_id, right.source_activity_id),
                )
            )
    return issues


def _session_overlap_issues(sessions: tuple[TimelineSession, ...]) -> list[IntervalIssue]:
    issues: list[IntervalIssue] = []
    ordered = sorted(sessions, key=lambda item: item.start_at)
    for index, left in enumerate(ordered):
        if left.end_at is None:
            continue
        for right in ordered[index + 1 :]:
            if right.start_at >= left.end_at:
                break
            if right.end_at is None:
                overlap_end = left.end_at
            else:
                overlap_end = min(left.end_at, right.end_at)
            seconds = max(0, int((overlap_end - right.start_at).total_seconds()))
            if seconds > 0:
                issues.append(
                    IntervalIssue(
                        issue_type=IntervalIssueType.SESSION_OVERLAP,
                        source_session_id=left.source_session_id,
                        other_session_id=right.source_session_id,
                        start_at=right.start_at,
                        end_at=overlap_end,
                        duration_seconds=seconds,
                    )
                )
    return issues
