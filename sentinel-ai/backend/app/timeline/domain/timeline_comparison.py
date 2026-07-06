from dataclasses import dataclass
from app.timeline.domain.source import DataSource

@dataclass(frozen=True)
class SourceDurationComparison:
    source: DataSource
    source_seconds: int
    baseline_seconds: int

    @property
    def delta_seconds(self) -> int:
        return self.source_seconds - self.baseline_seconds

    @property
    def delta_minutes(self) -> float:
        return round(self.delta_seconds / 60, 2)

@dataclass(frozen=True)
class TimelineComparison:
    login_session_external_id: str
    baseline_source: DataSource
    comparisons: list[SourceDurationComparison]
