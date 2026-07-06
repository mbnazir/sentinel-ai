from dataclasses import dataclass
from datetime import date, datetime
from typing import Any


@dataclass(frozen=True)
class QuartzAPIConfig:
    base_url: str
    api_key: str
    timeout_seconds: int = 30
    page_size: int = 500
    max_retries: int = 3


@dataclass(frozen=True)
class QuartzSessionDTO:
    id: str
    agent_id: str | None
    supervisor_id: str | None
    manager_id: str | None
    shift_date: date | None
    start_date: datetime
    end_date: datetime | None
    status_id: int | None
    raw: dict[str, Any]


@dataclass(frozen=True)
class QuartzActivityDTO:
    id: str
    login_session_id: str
    agent_id: str | None
    data_source_id: int
    activity_type_id: int
    source_id: int | None
    start_time: datetime
    end_time: datetime | None
    duration_seconds: int
    comment: str | None
    raw: dict[str, Any]


@dataclass(frozen=True)
class QuartzPage:
    items: list[dict[str, Any]]
    next_cursor: str | None
