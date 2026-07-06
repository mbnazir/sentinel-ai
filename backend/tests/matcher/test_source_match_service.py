from datetime import datetime
from app.matcher.domain.match_result import MatchClassification
from app.matcher.services.source_match_service import SourceMatchService
from app.timeline.domain.activity_snapshot import ActivitySnapshot
from app.timeline.domain.source import DataSource
from app.timeline.services.timeline_builder import TimelineBuilder

def dt(value: str) -> datetime:
    return datetime.fromisoformat(value)

def test_source_match_service_matches_from_timeline() -> None:
    activities = [
        ActivitySnapshot("sys-1", "LS-1", DataSource.SYSTEM, dt("2026-07-01T08:00:00"), dt("2026-07-01T09:00:00"), 3600, 1),
        ActivitySnapshot("sup-1", "LS-1", DataSource.SUPERVISOR, dt("2026-07-01T08:00:00"), dt("2026-07-01T09:45:00"), 6300, 1),
    ]
    timeline = TimelineBuilder().build("LS-1", activities)

    matches = SourceMatchService().match_timeline_sources(timeline, DataSource.SYSTEM, DataSource.SUPERVISOR)

    assert len(matches) == 1
    assert matches[0].classification == MatchClassification.EXTENDED
