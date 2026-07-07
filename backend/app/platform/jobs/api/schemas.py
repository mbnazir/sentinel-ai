from datetime import datetime
from typing import Any

from pydantic import BaseModel


class EnqueueJobRequest(BaseModel):
    job_type: str
    organization_id: str
    payload: dict[str, Any] = {}
    requested_by: str | None = None


class JobResponse(BaseModel):
    job_id: str
    job_type: str
    organization_id: str
    status: str
    payload: dict[str, Any]
    requested_by: str | None
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error_message: str | None = None
