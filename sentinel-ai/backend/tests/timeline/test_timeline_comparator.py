from datetime import datetime
from app.timeline.domain.activity_snapshot import ActivitySnapshot
from app.timeline.domain.source import DataSource
from app.timeline.services.timeline_builder import TimelineBuilder
from app.timeline.services.timeline_comparator import TimelineComparator

def dt(value: str) -> datetime:
    return datetime.fromisoformat(value)

def test_timeline_comparator_calculates_delta_against_system() -> None:
    activities = [
        ActivitySnapshot("sys-1", "LS-1", DataSource.SYSTEM, dt("2026-07-01T08:00:00"), dt("2026-07-01T09:00:00"), 3600, 1),
        ActivitySnapshot("sup-1", "LS-1", DataSource.SUPERVISOR, dt("2026-07-01T08:00:00"), dt("2026-07-01T09:45:00"), 6300, 1),
    ]
    timeline = TimelineBuilder().build("LS-1", activities)
    comparison = TimelineComparator().compare_against_baseline(timeline, DataSource.SYSTEM)
    supervisor = [item for item in comparison.comparisons if item.source == DataSource.SUPERVISOR][0]
    assert supervisor.delta_seconds == 2700
    assert supervisor.delta_minutes == 45
