from datetime import datetime
from typing import Any

from pydantic import BaseModel


class CreateScheduleRequest(BaseModel):
    name: str
    organization_id: str
    job_type: str
    frequency: str
    payload: dict[str, Any] = {}
    created_by: str | None = None


class ScheduleResponse(BaseModel):
    schedule_id: str
    name: str
    organization_id: str
    job_type: str
    frequency: str
    payload: dict[str, Any]
    status: str
    created_by: str | None
    created_at: datetime | None
    last_run_at: datetime | None
    next_run_at: datetime | None


class RunDueResponse(BaseModel):
    enqueued_job_ids: list[str]
