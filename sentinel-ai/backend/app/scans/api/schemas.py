from datetime import date, datetime

from pydantic import BaseModel


class RunScanRequest(BaseModel):
    organization_id: str
    shift_date_from: date
    shift_date_to: date
    create_cases: bool = True
    minimum_case_score: int = 61


class SessionScanResultResponse(BaseModel):
    login_session_external_id: str
    risk_score: int
    risk_level: str
    rule_count: int
    case_created: bool
    case_id: str | None


class ScanSummaryResponse(BaseModel):
    scan_id: str
    organization_id: str
    status: str
    started_at: datetime
    finished_at: datetime | None
    sessions_scanned: int
    cases_created: int
    results: list[SessionScanResultResponse]
    error_message: str | None = None
