from datetime import datetime
from app.timeline.domain.activity_snapshot import ActivitySnapshot
from app.timeline.domain.source import DataSource
from app.timeline.services.timeline_builder import TimelineBuilder

def dt(value: str) -> datetime:
    return datetime.fromisoformat(value)

def test_timeline_builder_splits_overlapping_versions_into_atomic_segments() -> None:
    activities = [
        ActivitySnapshot("sys-1", "LS-1", DataSource.SYSTEM, dt("2026-07-01T08:00:00"), dt("2026-07-01T09:00:00"), 3600, 1),
        ActivitySnapshot("agent-1", "LS-1", DataSource.AGENT, dt("2026-07-01T08:00:00"), dt("2026-07-01T09:30:00"), 5400, 1),
    ]
    timeline = TimelineBuilder().build("LS-1", activities)
    assert timeline.total_segments == 2
    assert timeline.segments[0].has_source(DataSource.SYSTEM)
    assert timeline.segments[0].has_source(DataSource.AGENT)
    assert not timeline.segments[1].has_source(DataSource.SYSTEM)
    assert timeline.segments[1].has_source(DataSource.AGENT)

def test_timeline_builder_ignores_open_ended_activities_for_atomic_segments() -> None:
    activities = [ActivitySnapshot("open-1", "LS-1", DataSource.SYSTEM, dt("2026-07-01T08:00:00"), None, 0, 1)]
    timeline = TimelineBuilder().build("LS-1", activities)
    assert timeline.total_segments == 0
