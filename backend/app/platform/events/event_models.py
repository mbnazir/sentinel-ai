from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import uuid4


class EventType(StrEnum):
    QUARTZ_SYNC_COMPLETED = "quartz_sync_completed"
    SCAN_COMPLETED = "scan_completed"
    BEHAVIOR_PROFILE_REFRESHED = "behavior_profile_refreshed"
    ANOMALY_DETECTED = "anomaly_detected"
    CASE_CREATED = "case_created"
    CASE_UPDATED = "case_updated"
    JOB_FAILED = "job_failed"


@dataclass(frozen=True)
class DomainEvent:
    event_id: str
    event_type: EventType
    organization_id: str
    payload: dict[str, Any] = field(default_factory=dict)
    correlation_id: str | None = None
    causation_id: str | None = None
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @staticmethod
    def create(
        event_type: EventType,
        organization_id: str,
        payload: dict[str, Any] | None = None,
        correlation_id: str | None = None,
        causation_id: str | None = None,
    ) -> "DomainEvent":
        return DomainEvent(
            event_id=f"EVT-{uuid4().hex[:12].upper()}",
            event_type=event_type,
            organization_id=organization_id,
            payload=payload or {},
            correlation_id=correlation_id,
            causation_id=causation_id,
        )
