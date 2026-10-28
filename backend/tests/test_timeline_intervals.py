from datetime import UTC, date, datetime, timedelta

from app.domain.data_sources import ActivityDataSource
from app.timeline.builder import _activity_interval_issues, _session_overlap_issues
from app.timeline.models import IntervalIssueType, TimelineActivity, TimelineSession

BASE = datetime(2026, 8, 26, 8, 0, tzinfo=UTC)


def activity(activity_id: str, start: int, end: int) -> TimelineActivity:
    return TimelineActivity(
        source_activity_id=activity_id,
        source_session_id="1001",
        agent_id="42",
        data_source_id=ActivityDataSource.SYSTEM,
        activity_type_id=1,
        start_at=BASE + timedelta(minutes=start),
        end_at=BASE + timedelta(minutes=end),
        duration_seconds=(end - start) * 60,
    )


def session(session_id: str, start: int, end: int) -> TimelineSession:
    return TimelineSession(
        source_session_id=session_id,
        agent_id="42",
        shift_date=date(2026, 8, 26),
        start_at=BASE + timedelta(minutes=start),
        end_at=BASE + timedelta(minutes=end),
        ready_for_payroll=True,
        payroll_adjusted=False,
        session_added_by=None,
        multiple_logins=0,
    )


def test_detects_gap_and_activity_overlap() -> None:
    gap = _activity_interval_issues(
        "1001", ActivityDataSource.SYSTEM, [activity("a", 0, 30), activity("b", 40, 60)]
    )
    overlap = _activity_interval_issues(
        "1001", ActivityDataSource.SYSTEM, [activity("a", 0, 40), activity("b", 30, 60)]
    )
    assert gap[0].issue_type == IntervalIssueType.GAP
    assert gap[0].duration_seconds == 600
    assert overlap[0].issue_type == IntervalIssueType.OVERLAP
    assert overlap[0].duration_seconds == 600


def test_detects_multiple_login_session_overlap() -> None:
    issues = _session_overlap_issues((session("1001", 0, 120), session("1002", 90, 180)))
    assert len(issues) == 1
    assert issues[0].issue_type == IntervalIssueType.SESSION_OVERLAP
    assert issues[0].duration_seconds == 1800
