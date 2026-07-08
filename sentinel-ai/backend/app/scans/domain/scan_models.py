from dataclasses import dataclass, field
from datetime import date, datetime
from enum import StrEnum


class ScanStatus(StrEnum):
    REQUESTED = "requested"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True)
class ScanRequest:
    organization_id: str
    shift_date_from: date
    shift_date_to: date
    create_cases: bool = True
    minimum_case_score: int = 61


@dataclass(frozen=True)
class SessionScanResult:
    login_session_external_id: str
    risk_score: int
    risk_level: str
    rule_count: int
    case_created: bool = False
    case_id: str | None = None


@dataclass(frozen=True)
class ScanSummary:
    scan_id: str
    organization_id: str
    status: ScanStatus
    started_at: datetime
    finished_at: datetime | None
    sessions_scanned: int
    cases_created: int
    results: list[SessionScanResult] = field(default_factory=list)
    error_message: str | None = None
