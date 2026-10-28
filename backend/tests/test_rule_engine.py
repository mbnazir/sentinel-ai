from datetime import UTC, date, datetime, timedelta
from uuid import uuid4

from app.domain.data_sources import ActivityDataSource
from app.rules.engine import IntegrityRuleEngine
from app.rules.models import RiskLevel
from app.timeline.analysis import analyze_employee_day
from app.timeline.models import EmployeeDayTimeline, TimelineActivity, TimelineSession
import pytest

BASE = datetime(2026, 8, 26, 8, 0, tzinfo=UTC)


def activity(
    activity_id: str,
    session_id: str,
    source: ActivityDataSource,
    start_minute: int,
    end_minute: int,
    *,
    activity_type_id: int = 1,
    inactivity_seconds: int = 0,
    comment: str | None = "valid reason",
) -> TimelineActivity:
    return TimelineActivity(
        source_activity_id=activity_id,
        source_session_id=session_id,
        agent_id="42",
        data_source_id=source,
        activity_type_id=activity_type_id,
        start_at=BASE + timedelta(minutes=start_minute),
        end_at=BASE + timedelta(minutes=end_minute),
        duration_seconds=(end_minute - start_minute) * 60,
        inactivity_seconds=inactivity_seconds,
        comment=comment,
    )


def session(
    session_id: str,
    *activities: TimelineActivity,
    session_added_by: str | None = None,
    add_session_reason_id: int | None = None,
    manager_action_at: datetime | None = None,
    payroll_adjusted_at: datetime | None = None,
    multiple_logins: int = 0,
) -> TimelineSession:
    return TimelineSession(
        source_session_id=session_id,
        agent_id="42",
        shift_date=date(2026, 8, 26),
        start_at=min((a.start_at for a in activities), default=BASE),
        end_at=max((a.end_at for a in activities if a.end_at), default=BASE + timedelta(hours=8)),
        ready_for_payroll=True,
        payroll_adjusted=payroll_adjusted_at is not None,
        payroll_adjusted_at=payroll_adjusted_at,
        session_added_by=session_added_by,
        add_session_reason_id=add_session_reason_id,
        manager_action_at=manager_action_at,
        multiple_logins=multiple_logins,
        activities=activities,
    )


def assessment(*sessions: TimelineSession):
    timeline = EmployeeDayTimeline(
        ingestion_run_id=uuid4(),
        agent_id="42",
        shift_date=date(2026, 8, 26),
        sessions=sessions,
    )
    return IntegrityRuleEngine().evaluate(analyze_employee_day(timeline))


def finding_ids(result) -> set[str]:
    return {finding.rule_id for finding in result.findings}


def test_supervisor_addition_is_critical_and_explainable() -> None:
    result = assessment(
        session(
            "1001",
            activity("sys", "1001", ActivityDataSource.SYSTEM, 0, 480),
            activity("agent", "1001", ActivityDataSource.AGENT, 0, 480),
            activity("sup", "1001", ActivityDataSource.SUPERVISOR, 0, 570),
        )
    )
    assert "SA-R002" in finding_ids(result)
    hit = next(item for item in result.findings if item.rule_id == "SA-R002")
    assert hit.severity.value == "critical"
    assert hit.metadata["added_seconds"] == 5400
    assert hit.evidence


def test_agent_addition_without_review_is_flagged() -> None:
    result = assessment(
        session(
            "1001",
            activity("sys", "1001", ActivityDataSource.SYSTEM, 0, 420),
            activity("agent", "1001", ActivityDataSource.AGENT, 0, 480),
        )
    )
    assert "SA-R001" in finding_ids(result)


def test_low_capture_coverage_reduces_manual_addition_confidence() -> None:
    result = assessment(
        session(
            "1001",
            activity("sys", "1001", ActivityDataSource.SYSTEM, 0, 120),
            activity("agent", "1001", ActivityDataSource.AGENT, 0, 240),
        )
    )
    agent_hit = next(item for item in result.findings if item.rule_id == "SA-R001")
    assert agent_hit.confidence < 0.95
    assert "SA-R019" in finding_ids(result)
    assert result.mitigating_notes


def test_manual_session_without_capture_is_critical() -> None:
    result = assessment(
        session(
            "1001",
            activity("mgr", "1001", ActivityDataSource.MANAGER, 0, 480),
            session_added_by="9001",
            add_session_reason_id=5,
        )
    )
    assert "SA-R018" in finding_ids(result)
    hit = next(item for item in result.findings if item.rule_id == "SA-R018")
    assert hit.severity.value == "critical"


def test_repeated_modified_sessions_are_detected_at_employee_day_grain() -> None:
    result = assessment(
        session(
            "1001",
            activity("s1", "1001", ActivityDataSource.SYSTEM, 0, 120),
            activity("a1", "1001", ActivityDataSource.AGENT, 0, 150),
        ),
        session(
            "1002",
            activity("s2", "1002", ActivityDataSource.SYSTEM, 180, 300),
            activity("a2", "1002", ActivityDataSource.AGENT, 180, 330),
        ),
    )
    assert "SA-R016" in finding_ids(result)
    hit = next(item for item in result.findings if item.rule_id == "SA-R016")
    assert hit.metadata["modified_session_ids"] == ["1001", "1002"]


def test_payroll_after_manager_action_is_flagged() -> None:
    manager_time = BASE + timedelta(hours=9)
    payroll_time = BASE + timedelta(hours=10)
    result = assessment(
        session(
            "1001",
            activity("m1", "1001", ActivityDataSource.MANAGER, 0, 480),
            activity("p1", "1001", ActivityDataSource.PAYROLL, 0, 500),
            manager_action_at=manager_time,
            payroll_adjusted_at=payroll_time,
        )
    )
    assert "SA-R014" in finding_ids(result)


def test_score_is_bounded_and_classified() -> None:
    result = assessment(
        session(
            "1001",
            activity("sys", "1001", ActivityDataSource.SYSTEM, 0, 120),
            activity("sup", "1001", ActivityDataSource.SUPERVISOR, 0, 600, comment=None),
            session_added_by="9001",
            multiple_logins=2,
        )
    )
    assert 0 <= result.risk_score <= 100
    assert result.risk_level in set(RiskLevel)


def test_agent_addition_with_supervisor_action_is_not_marked_unreviewed() -> None:
    reviewed = session(
        "1001",
        activity("sys", "1001", ActivityDataSource.SYSTEM, 0, 420),
        activity("agent", "1001", ActivityDataSource.AGENT, 0, 480),
    ).model_copy(update={"supervisor_action_at": BASE + timedelta(hours=9)})
    result = assessment(reviewed)
    assert "SA-R001" not in finding_ids(result)


def test_phone_system_mismatch_is_data_quality_finding() -> None:
    result = assessment(
        session(
            "1001",
            activity("phone", "1001", ActivityDataSource.PHONE, 0, 480),
            activity("system", "1001", ActivityDataSource.SYSTEM, 0, 300),
        )
    )
    assert "SA-R023" in finding_ids(result)
    hit = next(item for item in result.findings if item.rule_id == "SA-R023")
    assert hit.category.value == "data_quality"
def test_zero_duration_system_removal_is_not_critical():
    result = assessment(
        session(
            "zero-removal",
            activity(
                "sys",
                "zero-removal",
                ActivityDataSource.SYSTEM,
                0,
                0,
            ),
            activity(
                "agent",
                "zero-removal",
                ActivityDataSource.AGENT,
                60,
                120,
            ),
        )
    )
    assert not any(
        finding.rule_id == "SA-R005"
        for finding in result.findings
    )


def test_meaningful_system_removal_is_still_detected():
    result = assessment(
        session(
            "meaningful-removal",
            activity(
                "sys",
                "meaningful-removal",
                ActivityDataSource.SYSTEM,
                0,
                120,
            ),
            activity(
                "agent",
                "meaningful-removal",
                ActivityDataSource.AGENT,
                180,
                240,
            ),
        )
    )
    assert any(
        finding.rule_id == "SA-R005"
        for finding in result.findings
    )
    



@pytest.mark.parametrize(
    "duration_seconds,expected",
    [
        (0, False),
        (1, False),
        (19, False),
        (59, False),
        (60, True),
        (120, True),
        (7200, True),
    ],
)
def test_sa_r005_removed_duration_boundary(
    duration_seconds: int,
    expected: bool,
) -> None:
    source_activity = activity(
        "system-boundary",
        "boundary-session",
        ActivityDataSource.SYSTEM,
        0,
        1,
    ).model_copy(
        update={
            "end_at": BASE + timedelta(seconds=duration_seconds),
            "duration_seconds": duration_seconds,
        }
    )

    manual_activity = activity(
        "agent-boundary",
        "boundary-session",
        ActivityDataSource.AGENT,
        180,
        240,
    )

    result = assessment(
        session(
            "boundary-session",
            source_activity,
            manual_activity,
        )
    )

    matches = [
        finding
        for finding in result.findings
        if finding.rule_id == "SA-R005"
    ]

    assert bool(matches) is expected

    if expected:
        assert matches[0].severity.value == "critical"
        assert matches[0].metadata["removed_seconds"] == duration_seconds


def test_sa_r005_open_ended_activity_is_not_critical() -> None:
    source_activity = activity(
        "system-open",
        "open-session",
        ActivityDataSource.SYSTEM,
        0,
        1,
    ).model_copy(
        update={
            "end_at": None,
            "duration_seconds": 0,
        }
    )

    manual_activity = activity(
        "agent-open",
        "open-session",
        ActivityDataSource.AGENT,
        180,
        240,
    )

    result = assessment(
        session(
            "open-session",
            source_activity,
            manual_activity,
        )
    )

    assert not any(
        finding.rule_id == "SA-R005"
        for finding in result.findings
    )