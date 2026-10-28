from datetime import date, datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.data_sources import ActivityDataSource


class TimelineActivity(BaseModel):
    model_config = ConfigDict(frozen=True)

    source_activity_id: str
    source_session_id: str
    agent_id: str | None
    data_source_id: ActivityDataSource
    activity_type_id: int
    start_at: datetime
    end_at: datetime | None
    duration_seconds: int
    inactivity_seconds: int = 0
    comment: str | None = None


class TimelineSession(BaseModel):
    model_config = ConfigDict(frozen=True)

    source_session_id: str
    agent_id: str
    shift_date: date
    start_at: datetime
    end_at: datetime | None
    ready_for_payroll: bool
    payroll_adjusted: bool
    payroll_adjusted_at: datetime | None = None
    session_added_by: str | None
    add_session_reason_id: int | None = None
    agent_action_at: datetime | None = None
    supervisor_action_at: datetime | None = None
    manager_action_at: datetime | None = None
    multiple_logins: int
    activities: tuple[TimelineActivity, ...] = ()


class IntervalIssueType(StrEnum):
    GAP = "gap"
    OVERLAP = "overlap"
    SESSION_OVERLAP = "session_overlap"


class IntervalIssue(BaseModel):
    model_config = ConfigDict(frozen=True)

    issue_type: IntervalIssueType
    source_session_id: str | None = None
    other_session_id: str | None = None
    data_source_id: ActivityDataSource | None = None
    start_at: datetime
    end_at: datetime
    duration_seconds: int
    activity_ids: tuple[str, ...] = ()


class EmployeeDayTimeline(BaseModel):
    model_config = ConfigDict(frozen=True)

    ingestion_run_id: UUID
    agent_id: str
    shift_date: date
    sessions: tuple[TimelineSession, ...]
    interval_issues: tuple[IntervalIssue, ...] = ()

    @property
    def session_count(self) -> int:
        return len(self.sessions)

    def activities_for_source(self, source: ActivityDataSource) -> list[TimelineActivity]:
        return [
            activity
            for session in self.sessions
            for activity in session.activities
            if activity.data_source_id == source
        ]
