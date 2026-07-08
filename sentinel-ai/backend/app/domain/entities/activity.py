from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class Activity:
    external_id: str
    login_session_external_id: str
    agent_external_id: str | None
    source: str
    activity_type: str
    start_time: datetime
    end_time: datetime | None
    duration_seconds: int
    source_code: int | None = None
    activity_type_external_id: str | None = None
    inactivity_seconds: int = 0
    comment: str | None = None
    raw_payload: dict[str, Any] = field(default_factory=dict)
