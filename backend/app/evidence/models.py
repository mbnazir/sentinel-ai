from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from app.domain.data_sources import ActivityDataSource
from app.matcher.models import ActivityChangeType


class EvidenceKind(StrEnum):
    ACTIVITY_CHANGE = "activity_change"
    ACTIVITY_GAP = "activity_gap"
    ACTIVITY_OVERLAP = "activity_overlap"
    SESSION_OVERLAP = "session_overlap"


class EvidenceItem(BaseModel):
    model_config = ConfigDict(frozen=True)

    evidence_kind: EvidenceKind
    source_session_id: str | None = None
    other_session_id: str | None = None
    baseline_source: ActivityDataSource | None = None
    comparison_source: ActivityDataSource | None = None
    change_type: ActivityChangeType | None = None
    baseline_activity_id: str | None = None
    comparison_activity_id: str | None = None
    start_at: datetime
    end_at: datetime | None = None
    seconds_delta: int = 0
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    activity_type_before: int | None = None
    activity_type_after: int | None = None
    description: str
