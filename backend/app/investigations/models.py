from datetime import date, datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ScanStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ComparisonEligibilityMode(StrEnum):
    STRICT_RECONCILED = "STRICT_RECONCILED"
    OBSERVED_RECORDS_ONLY = "OBSERVED_RECORDS_ONLY"


class CaseStatus(StrEnum):
    OPEN = "open"
    IN_REVIEW = "in_review"
    AWAITING_INFO = "awaiting_info"
    RESOLVED = "resolved"
    CLOSED = "closed"


class CaseDisposition(StrEnum):
    UNDETERMINED = "undetermined"
    FALSE_POSITIVE = "false_positive"
    VALID_ADJUSTMENT = "valid_adjustment"
    POLICY_VIOLATION = "policy_violation"
    PAYROLL_CORRECTION = "payroll_correction"
    ESCALATED = "escalated"


class ScanCreate(BaseModel):
    ingestion_run_id: UUID
    baseline_ingestion_run_id: UUID | None = None
    date_from: date
    date_to: date
    requested_by: str
    scope: str = "employee_day"
    eligibility_mode: ComparisonEligibilityMode = ComparisonEligibilityMode.STRICT_RECONCILED
    eligibility_override_reason: str | None = None


class ScanRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    ingestion_run_id: UUID
    baseline_ingestion_run_id: UUID | None = None
    eligibility_mode: ComparisonEligibilityMode = ComparisonEligibilityMode.STRICT_RECONCILED
    eligibility_override_reason: str | None = None
    eligibility_override_role: str | None = None
    date_from: date
    date_to: date
    requested_by: str
    scope: str
    status: ScanStatus
    started_at: datetime | None = None
    completed_at: datetime | None = None
    employee_days_processed: int = 0
    finding_count: int = 0


class DurableFinding(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    scan_id: UUID
    finding_key: str
    agent_id: str | None = None
    shift_date: date | None = None
    source_session_id: str | None = None
    rule_id: str
    severity: str
    confidence: float = Field(ge=0, le=1)
    risk_contribution: float = Field(ge=0, le=100)
    reason: str
    evidence_json: dict[str, object]
    immutable_hash: str


class CaseCreate(BaseModel):
    title: str
    finding_ids: tuple[UUID, ...] = ()
    assigned_to: str | None = None
    created_by: str


class CaseUpdate(BaseModel):
    status: CaseStatus | None = None
    disposition: CaseDisposition | None = None
    assigned_to: str | None = None
    note: str | None = None
    # HTTP routes always use the authenticated principal; retained for internal callers.
    actor: str = ""


class InvestigationCase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    case_number: str
    title: str
    status: CaseStatus
    disposition: CaseDisposition
    assigned_to: str | None = None
    created_by: str
    created_at: datetime
    updated_at: datetime


class AuditEvent(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    case_id: UUID | None = None
    scan_id: UUID | None = None
    actor: str
    event_type: str
    event_json: dict[str, object]
    created_at: datetime
