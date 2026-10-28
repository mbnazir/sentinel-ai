from enum import StrEnum

from pydantic import BaseModel, ConfigDict

from app.domain.data_sources import ActivityDataSource
from app.timeline.models import TimelineActivity


class ActivityChangeType(StrEnum):
    UNCHANGED = "unchanged"
    INSERTED = "inserted"
    REMOVED = "removed"
    EXTENDED = "extended"
    SHORTENED = "shortened"
    SHIFTED = "shifted"
    TYPE_CHANGED = "type_changed"
    COMPOUND = "compound"


class ActivityMatch(BaseModel):
    model_config = ConfigDict(frozen=True)

    baseline_source: ActivityDataSource
    comparison_source: ActivityDataSource
    baseline_activity: TimelineActivity | None
    comparison_activity: TimelineActivity | None
    confidence: float
    overlap_seconds: int
    overlap_ratio: float
    start_delta_seconds: int | None
    end_delta_seconds: int | None
    duration_delta_seconds: int
    activity_type_changed: bool
    change_type: ActivityChangeType


class SourceComparison(BaseModel):
    model_config = ConfigDict(frozen=True)

    source_session_id: str
    baseline_source: ActivityDataSource
    comparison_source: ActivityDataSource
    matches: tuple[ActivityMatch, ...]
