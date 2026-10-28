from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ResolutionStatus(StrEnum):
    VERIFIED = "VERIFIED"
    PROVISIONAL = "PROVISIONAL"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


class ActorStatus(StrEnum):
    VERIFIED = "VERIFIED"
    ACTOR_UNVERIFIED = "ACTOR_UNVERIFIED"
    CONFLICTING = "CONFLICTING"


class WeeklyEvidenceQuality(StrEnum):
    COMPLETE = "COMPLETE"
    INCOMPLETE = "INCOMPLETE"
    UNVERIFIED = "UNVERIFIED"
    UNKNOWN = "UNVERIFIED"  # backwards-compatible alias


class PayrollWeek(BaseModel):
    model_config = ConfigDict(frozen=True)
    employee_id: str
    start_date: date
    end_date: date
    ingestion_run_id: UUID
    completeness: WeeklyEvidenceQuality = WeeklyEvidenceQuality.UNKNOWN
    missing_dates: tuple[date, ...] = ()
    source_record_count: int | None = None
    received_record_count: int | None = None
    source_count_reconciled: bool = False
    provenance: dict[str, object] = Field(default_factory=dict)


class SessionPayable(BaseModel):
    model_config = ConfigDict(frozen=True)
    regular_seconds: Decimal | None = None
    overtime_seconds: Decimal | None = None
    total_seconds: Decimal | None = None
    status: ResolutionStatus
    raw_regular_hour: object = None
    raw_overtime: object = None
    provenance: tuple[str, ...] = ()


class WeeklySession(BaseModel):
    model_config = ConfigDict(frozen=True)
    source_session_id: str
    employee_id: str
    shift_date: date
    start_at: datetime
    end_at: datetime | None = None
    ingestion_run_id: UUID
    supervisor_id: str | None = None
    manager_id: str | None = None
    metadata: dict[str, object] = Field(default_factory=dict)
    payable: SessionPayable | None = None


class WeeklyAdjustment(BaseModel):
    model_config = ConfigDict(frozen=True)
    adjustment_id: str
    employee_id: str
    source_session_id: str
    source_activity_id: str | None = None
    shift_date: date
    delta_seconds: Decimal
    actor_id: str = "ACTOR_UNVERIFIED"
    actor_status: ActorStatus = ActorStatus.ACTOR_UNVERIFIED
    before_seconds: Decimal | None = None
    after_seconds: Decimal | None = None
    action_at: datetime | None = None
    data_source_id: int | None = None
    provenance: tuple[str, ...] = ()


class WeeklyPayableSummary(BaseModel):
    model_config = ConfigDict(frozen=True)
    employee_id: str
    week_start: date
    week_end: date
    baseline_eligible_seconds: Decimal | None = None
    final_eligible_seconds: Decimal | None = None
    baseline_overtime_seconds: Decimal | None = None
    final_overtime_seconds: Decimal | None = None
    incremental_overtime_seconds: Decimal | None = None
    additional_regular_seconds: Decimal | None = None
    status: ResolutionStatus
    adjustments: tuple[WeeklyAdjustment, ...] = ()
    provenance: dict[str, object] = Field(default_factory=dict)


class WeeklyImpactAssessment(BaseModel):
    model_config = ConfigDict(frozen=True)
    payroll_week: PayrollWeek
    sessions: tuple[WeeklySession, ...]
    adjustments: tuple[WeeklyAdjustment, ...] = ()
    summary: WeeklyPayableSummary
    findings: tuple[dict[str, object], ...] = ()
    confidence: float = Field(default=0, ge=0, le=1)
    provenance: dict[str, object] = Field(default_factory=dict)
