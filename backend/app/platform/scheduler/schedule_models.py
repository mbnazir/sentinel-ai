from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any

from app.platform.jobs.job_models import JobType


class ScheduleStatus(StrEnum):
    ACTIVE = "active"
    PAUSED = "paused"
    DISABLED = "disabled"


class ScheduleFrequency(StrEnum):
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"


@dataclass(frozen=True)
class JobSchedule:
    schedule_id: str
    name: str
    organization_id: str
    job_type: JobType
    frequency: ScheduleFrequency
    payload: dict[str, Any] = field(default_factory=dict)
    status: ScheduleStatus = ScheduleStatus.ACTIVE
    created_by: str | None = None
    created_at: datetime | None = None
    last_run_at: datetime | None = None
    next_run_at: datetime | None = None
