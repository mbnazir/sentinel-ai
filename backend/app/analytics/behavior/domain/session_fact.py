from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class SessionRiskFact:
    login_session_external_id: str
    agent_external_id: str | None
    supervisor_external_id: str | None
    manager_external_id: str | None
    campaign_external_id: str | None
    site_external_id: str | None
    shift_date: date
    risk_score: int
    inserted_activity_count: int = 0
    deleted_activity_count: int = 0
    extended_activity_count: int = 0
    payroll_adjustment_count: int = 0
    manual_added_seconds: int = 0
    rule_count: int = 0
