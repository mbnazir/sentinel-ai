from dataclasses import dataclass, field
from datetime import datetime
from app.timeline.domain.activity_snapshot import ActivitySnapshot
from app.timeline.domain.source import DataSource

@dataclass(frozen=True)
class TimelineSegment:
    start_time: datetime
    end_time: datetime
    activities_by_source: dict[DataSource, list[ActivitySnapshot]] = field(default_factory=dict)

    @property
    def duration_seconds(self) -> int:
        return int((self.end_time - self.start_time).total_seconds())

    def has_source(self, source: DataSource) -> bool:
        return bool(self.activities_by_source.get(source))

    def source_labels(self) -> list[str]:
        return [source.label for source in self.activities_by_source]
