from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any


class JobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobType(StrEnum):
    QUARTZ_SYNC = "quartz_sync"
    SCAN_RUN = "scan_run"
    BEHAVIOR_REFRESH = "behavior_refresh"
    ANOMALY_SCORE = "anomaly_score"
    ANOMALY_CASE_ATTACHMENT = "anomaly_case_attachment"


@dataclass(frozen=True)
class JobRequest:
    job_type: JobType
    organization_id: str
    payload: dict[str, Any] = field(default_factory=dict)
    requested_by: str | None = None


@dataclass(frozen=True)
class JobRecord:
    job_id: str
    job_type: JobType
    organization_id: str
    status: JobStatus
    payload: dict[str, Any]
    requested_by: str | None
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error_message: str | None = None
