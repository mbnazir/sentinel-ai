from typing import Any
from app.timeline.domain.source import DataSource
from app.timeline.domain.timeline import Timeline
from app.timeline.domain.timeline_comparison import TimelineComparison
from app.timeline.services.activity_snapshot_mapper import ActivitySnapshotMapper
from app.timeline.services.timeline_builder import TimelineBuilder
from app.timeline.services.timeline_comparator import TimelineComparator

class TimelineQueryService:
    def __init__(self) -> None:
        self.builder = TimelineBuilder()
        self.comparator = TimelineComparator()
        self.mapper = ActivitySnapshotMapper()

    def build_from_activity_rows(self, login_session_external_id: str, rows: list[dict[str, Any]]) -> Timeline:
        return self.builder.build(login_session_external_id, [self.mapper.from_mapping(row) for row in rows])

    def compare(self, timeline: Timeline, baseline_source: DataSource = DataSource.SYSTEM) -> TimelineComparison:
        totals = timeline.total_seconds_by_source()
        if totals[baseline_source] == 0 and totals[DataSource.PHONE] > 0:
            baseline_source = DataSource.PHONE
        return self.comparator.compare_against_baseline(timeline, baseline_source)
