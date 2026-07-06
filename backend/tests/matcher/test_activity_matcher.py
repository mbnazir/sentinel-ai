from datetime import datetime
from app.matcher.domain.match_result import MatchClassification
from app.matcher.services.activity_matcher import ActivityMatcher
from app.timeline.domain.activity_snapshot import ActivitySnapshot
from app.timeline.domain.source import DataSource

def dt(value: str) -> datetime:
    return datetime.fromisoformat(value)

def activity(external_id: str, source: DataSource, start: str, end: str, duration: int, activity_type_id: int = 1) -> ActivitySnapshot:
    return ActivitySnapshot(
        external_id=external_id,
        login_session_external_id="LS-1",
        data_source=source,
        start_time=dt(start),
        end_time=dt(end),
        duration_seconds=duration,
        activity_type_id=activity_type_id,
    )

def test_matcher_classifies_extended_activity() -> None:
    baseline = [activity("sys-1", DataSource.SYSTEM, "2026-07-01T08:00:00", "2026-07-01T09:00:00", 3600)]
    comparison = [activity("agent-1", DataSource.AGENT, "2026-07-01T08:00:00", "2026-07-01T09:30:00", 5400)]

    matches = ActivityMatcher().match_sources(baseline, comparison, DataSource.SYSTEM, DataSource.AGENT)

    assert len(matches) == 1
    assert matches[0].classification == MatchClassification.EXTENDED
    assert matches[0].delta_seconds == 1800

def test_matcher_classifies_inserted_activity() -> None:
    baseline = []
    comparison = [activity("agent-1", DataSource.AGENT, "2026-07-01T09:00:00", "2026-07-01T09:30:00", 1800)]

    matches = ActivityMatcher().match_sources(baseline, comparison, DataSource.SYSTEM, DataSource.AGENT)

    assert len(matches) == 1
    assert matches[0].classification == MatchClassification.INSERTED
    assert matches[0].delta_seconds == 1800

def test_matcher_classifies_deleted_activity() -> None:
    baseline = [activity("sys-1", DataSource.SYSTEM, "2026-07-01T09:00:00", "2026-07-01T09:30:00", 1800)]
    comparison = []

    matches = ActivityMatcher().match_sources(baseline, comparison, DataSource.SYSTEM, DataSource.AGENT)

    assert len(matches) == 1
    assert matches[0].classification == MatchClassification.DELETED
    assert matches[0].delta_seconds == -1800

def test_matcher_classifies_type_changed_activity() -> None:
    baseline = [activity("sys-1", DataSource.SYSTEM, "2026-07-01T09:00:00", "2026-07-01T09:30:00", 1800, activity_type_id=1)]
    comparison = [activity("agent-1", DataSource.AGENT, "2026-07-01T09:00:00", "2026-07-01T09:30:00", 1800, activity_type_id=2)]

    matches = ActivityMatcher().match_sources(baseline, comparison, DataSource.SYSTEM, DataSource.AGENT)

    assert len(matches) == 1
    assert matches[0].classification == MatchClassification.TYPE_CHANGED
