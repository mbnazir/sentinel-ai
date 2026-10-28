from datetime import UTC, date, datetime, timedelta
from uuid import uuid4

from app.domain.data_sources import ActivityDataSource
from app.evidence.models import EvidenceKind
from app.matcher.models import ActivityChangeType
from app.timeline.analysis import analyze_employee_day
from app.timeline.models import EmployeeDayTimeline, TimelineActivity, TimelineSession

BASE = datetime(2026, 8, 26, 8, 0, tzinfo=UTC)


def item(activity_id: str, source: ActivityDataSource, start: int, end: int) -> TimelineActivity:
    return TimelineActivity(
        source_activity_id=activity_id,
        source_session_id="1001",
        agent_id="42",
        data_source_id=source,
        activity_type_id=1,
        start_at=BASE + timedelta(minutes=start),
        end_at=BASE + timedelta(minutes=end),
        duration_seconds=(end - start) * 60,
    )


def timeline(*activities: TimelineActivity) -> EmployeeDayTimeline:
    session = TimelineSession(
        source_session_id="1001",
        agent_id="42",
        shift_date=date(2026, 8, 26),
        start_at=BASE,
        end_at=BASE + timedelta(hours=9),
        ready_for_payroll=True,
        payroll_adjusted=False,
        session_added_by=None,
        multiple_logins=0,
        activities=activities,
    )
    return EmployeeDayTimeline(
        ingestion_run_id=uuid4(),
        agent_id="42",
        shift_date=date(2026, 8, 26),
        sessions=(session,),
    )


def test_supervisor_compares_to_agent_when_agent_version_exists() -> None:
    result = analyze_employee_day(
        timeline(
            item("sys", ActivityDataSource.SYSTEM, 0, 60),
            item("agent", ActivityDataSource.AGENT, 0, 60),
            item("supervisor", ActivityDataSource.SUPERVISOR, 0, 90),
        )
    )
    supervisor_comparison = next(
        comparison
        for comparison in result.session_analyses[0].comparisons
        if comparison.comparison_source == ActivityDataSource.SUPERVISOR
    )
    assert supervisor_comparison.baseline_source == ActivityDataSource.AGENT
    assert supervisor_comparison.matches[0].change_type == ActivityChangeType.EXTENDED


def test_supervisor_falls_back_to_system_without_agent_version() -> None:
    result = analyze_employee_day(
        timeline(
            item("sys", ActivityDataSource.SYSTEM, 0, 60),
            item("supervisor", ActivityDataSource.SUPERVISOR, 0, 90),
        )
    )
    comparison = result.session_analyses[0].comparisons[0]
    assert comparison.baseline_source == ActivityDataSource.SYSTEM
    assert comparison.comparison_source == ActivityDataSource.SUPERVISOR


def test_activity_change_is_emitted_as_neutral_evidence() -> None:
    result = analyze_employee_day(
        timeline(
            item("sys", ActivityDataSource.SYSTEM, 0, 60),
            item("agent", ActivityDataSource.AGENT, 0, 90),
        )
    )
    evidence = next(e for e in result.evidence if e.evidence_kind == EvidenceKind.ACTIVITY_CHANGE)
    assert evidence.change_type == ActivityChangeType.EXTENDED
    assert evidence.seconds_delta == 1800
    assert "Agent extends" in evidence.description
