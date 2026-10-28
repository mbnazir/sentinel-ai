from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.domain.data_sources import ActivityDataSource


class NormalizedLoginSession(BaseModel):
    model_config = ConfigDict(frozen=True)

    source_system: str
    source_session_id: str
    agent_id: str
    supervisor_id: str | None = None
    manager_id: str | None = None
    site_id: str | None = None
    site_name: str | None = None
    team_id: str | None = None
    shift_date: date
    start_at: datetime
    end_at: datetime | None = None
    status_id: int | None = None
    dispute_reason_id: int | None = None
    dispute_state: int | None = None
    supervisor_status_id: int | None = None
    ready_for_payroll: bool = False
    payroll_adjusted: bool = False
    payroll_adjusted_at: datetime | None = None
    session_added_by: str | None = None
    add_session_reason_id: int | None = None
    manager_action_at: datetime | None = None
    supervisor_action_at: datetime | None = None
    agent_action_at: datetime | None = None
    multiple_logins: int = 0
    agent_ip: str | None = None
    machine_hostname: str | None = None
    primary_campaign_id: str | None = None
    primary_campaign_name: str | None = None
    primary_client_id: int | None = None
    primary_client_name: str | None = None
    metadata: dict[str, object] = Field(default_factory=dict)


class NormalizedActivity(BaseModel):
    model_config = ConfigDict(frozen=True)

    source_system: str
    source_activity_id: str
    source_session_id: str
    agent_id: str | None = None
    data_source_id: ActivityDataSource
    activity_type_id: int
    source_id: int | None = None
    start_at: datetime
    end_at: datetime | None
    duration_seconds: int | None
    inactivity_seconds: int = 0
    campaign_id: str | None = None
    campaign_name: str | None = None
    client_id: int | None = None
    comment: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    metadata: dict[str, object] = Field(default_factory=dict)

    @field_validator("duration_seconds")
    @classmethod
    def duration_must_be_non_negative(cls, value: int | None) -> int | None:
        if value is not None and value < 0:
            raise ValueError("duration_seconds cannot be negative")
        return value
