from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ActivityChangeType(StrEnum):
    ADDED = "ADDED"
    REMOVED = "REMOVED"
    EXTENDED = "EXTENDED"
    SHORTENED = "SHORTENED"
    RECLASSIFIED = "RECLASSIFIED"
    UNCHANGED = "UNCHANGED"
    AMBIGUOUS = "AMBIGUOUS"


class ComparisonStatus(StrEnum):
    READY = "READY"
    PROVISIONAL = "PROVISIONAL"
    INCOMPLETE = "INCOMPLETE"


class ActivityInterval(BaseModel):
    model_config = ConfigDict(frozen=True)
    activity_id: str
    data_source_id: int
    activity_type_id: int
    start_at: datetime
    end_at: datetime | None
    duration_seconds: Decimal | None = None
    comment: str | None = None
    source_created_at: datetime | None = None
    source_updated_at: datetime | None = None
    source_system: str
    source_session_id: str
    ingestion_run_id: UUID


class ActivityVersion(BaseModel):
    model_config = ConfigDict(frozen=True)
    ingestion_run_id: UUID
    source_system: str
    source_session_id: str
    data_source_id: int
    activities: tuple[ActivityInterval, ...] = ()
    version_id: str
    evidence_confidence: Decimal | None = None


class ChangeEvidence(BaseModel):
    model_config = ConfigDict(frozen=True)
    original_activity_ids: tuple[str, ...] = ()
    revised_activity_ids: tuple[str, ...] = ()
    original_comments: tuple[str, ...] = ()
    revised_comments: tuple[str, ...] = ()
    original_created_at: tuple[datetime, ...] = ()
    revised_created_at: tuple[datetime, ...] = ()
    original_updated_at: tuple[datetime, ...] = ()
    revised_updated_at: tuple[datetime, ...] = ()
    editor_identity: str = "UNVERIFIED"
    editor_identity_verified: bool = False
    financial_impact: str = "UNVERIFIED"
    provenance: tuple[str, ...] = ()


class ActivityChange(BaseModel):
    model_config = ConfigDict(frozen=True)
    change_type: ActivityChangeType
    start_at: datetime | None
    end_at: datetime | None
    affected_seconds: Decimal | None
    net_covered_seconds: Decimal | None
    original_activity_ids: tuple[str, ...] = ()
    revised_activity_ids: tuple[str, ...] = ()
    original_activity_type_ids: tuple[int, ...] = ()
    revised_activity_type_ids: tuple[int, ...] = ()
    evidence: ChangeEvidence


class ComparisonReadiness(BaseModel):
    model_config = ConfigDict(frozen=True)
    status: ComparisonStatus
    reasons: tuple[str, ...] = ()
    missing_source_ids: tuple[int, ...] = ()
    malformed_activity_ids: tuple[str, ...] = ()
    conflicting_segments: int = 0
    duration_mismatch_activity_ids: tuple[str, ...] = ()


class VersionComparison(BaseModel):
    model_config = ConfigDict(frozen=True)
    ingestion_run_id: UUID
    source_system: str
    source_session_id: str
    original_version: ActivityVersion | None
    revised_version: ActivityVersion | None
    changes: tuple[ActivityChange, ...] = ()
    readiness: ComparisonReadiness
    net_covered_seconds: Decimal | None
    reclassified_seconds: Decimal
    evidence_confidence: Decimal | None = None
    finding: dict[str, object] | None = None


class ActivityComparisonResponse(BaseModel):
    model_config = ConfigDict(frozen=True)
    employee_id: str
    session_shift_date: str
    comparison: VersionComparison
