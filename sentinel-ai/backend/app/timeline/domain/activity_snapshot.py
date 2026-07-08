from dataclasses import dataclass
from datetime import datetime
from app.timeline.domain.source import DataSource

@dataclass(frozen=True)
class ActivitySnapshot:
    external_id: str
    login_session_external_id: str
    data_source: DataSource
    start_time: datetime
    end_time: datetime | None
    duration_seconds: int
    activity_type_id: int
    source_id: int | None = None
    agent_external_id: str | None = None
    comment: str | None = None

    def overlaps(self, start: datetime, end: datetime) -> bool:
        if self.end_time is None:
            return False
        return self.start_time < end and self.end_time > start

    def overlap_seconds(self, start: datetime, end: datetime) -> int:
        if self.end_time is None or not self.overlaps(start, end):
            return 0
        return max(0, int((min(self.end_time, end) - max(self.start_time, start)).total_seconds()))
