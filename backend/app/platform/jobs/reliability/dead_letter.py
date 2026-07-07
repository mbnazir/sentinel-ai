from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class DeadLetterJob:
    job_id: str
    job_type: str
    organization_id: str
    payload: dict[str, Any]
    error_message: str
    failed_at: datetime
    attempt_count: int


class InMemoryDeadLetterRepository:
    def __init__(self) -> None:
        self.items: list[DeadLetterJob] = []

    def add(self, item: DeadLetterJob) -> DeadLetterJob:
        self.items.append(item)
        return item

    def list(self, organization_id: str | None = None) -> list[DeadLetterJob]:
        if organization_id is None:
            return list(self.items)
        return [item for item in self.items if item.organization_id == organization_id]
