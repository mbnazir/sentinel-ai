from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any


@dataclass(frozen=True)
class LoginSession:
    external_id: str
    agent_external_id: str | None
    supervisor_external_id: str | None
    shift_date: date | None
    start_time: datetime
    end_time: datetime | None
    status: str | None = None
    raw_payload: dict[str, Any] = field(default_factory=dict)
