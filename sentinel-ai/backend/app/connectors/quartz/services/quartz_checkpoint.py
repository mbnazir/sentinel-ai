from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class QuartzSyncCheckpoint:
    connector_id: str
    last_shift_date_from: date | None = None
    last_shift_date_to: date | None = None
    last_cursor: str | None = None
    completed: bool = False
