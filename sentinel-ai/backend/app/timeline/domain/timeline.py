from dataclasses import dataclass, field
from app.timeline.domain.activity_snapshot import ActivitySnapshot
from app.timeline.domain.source import DataSource
from app.timeline.domain.timeline_segment import TimelineSegment

@dataclass(frozen=True)
class Timeline:
    login_session_external_id: str
    segments: list[TimelineSegment] = field(default_factory=list)

    @property
    def total_segments(self) -> int:
        return len(self.segments)

    def total_seconds_by_source(self) -> dict[DataSource, int]:
        totals = {source: 0 for source in DataSource}
        for segment in self.segments:
            for source in segment.activities_by_source:
                totals[source] += segment.duration_seconds
        return totals

    def get_source_activities(self, source: DataSource) -> list[ActivitySnapshot]:
        activities = {}
        for segment in self.segments:
            for activity in segment.activities_by_source.get(source, []):
                activities[activity.external_id] = activity
        return list(activities.values())
