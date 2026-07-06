from dataclasses import dataclass
from enum import StrEnum

from app.timeline.domain.activity_snapshot import ActivitySnapshot
from app.timeline.domain.source import DataSource


class MatchClassification(StrEnum):
    EXACT = "exact"
    EXTENDED = "extended"
    SHORTENED = "shortened"
    SHIFTED = "shifted"
    TYPE_CHANGED = "type_changed"
    PARTIAL_OVERLAP = "partial_overlap"
    INSERTED = "inserted"
    DELETED = "deleted"
    NO_MATCH = "no_match"


@dataclass(frozen=True)
class ActivityMatchScore:
    overlap_score: float
    start_proximity_score: float
    end_proximity_score: float
    duration_similarity_score: float
    activity_type_score: float

    @property
    def total(self) -> float:
        return round(
            (
                self.overlap_score * 0.45
                + self.start_proximity_score * 0.15
                + self.end_proximity_score * 0.15
                + self.duration_similarity_score * 0.15
                + self.activity_type_score * 0.10
            ),
            4,
        )


@dataclass(frozen=True)
class ActivityMatch:
    baseline_activity: ActivitySnapshot | None
    comparison_activity: ActivitySnapshot | None
    baseline_source: DataSource
    comparison_source: DataSource
    classification: MatchClassification
    score: ActivityMatchScore | None
    confidence: float
    delta_seconds: int
    reason: str
