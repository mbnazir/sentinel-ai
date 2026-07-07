from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class WorkerHeartbeat:
    worker_id: str
    last_seen_at: datetime
    active_job_id: str | None = None


class InMemoryWorkerHeartbeatRepository:
    def __init__(self) -> None:
        self.items: dict[str, WorkerHeartbeat] = {}

    def beat(self, worker_id: str, active_job_id: str | None = None) -> WorkerHeartbeat:
        heartbeat = WorkerHeartbeat(
            worker_id=worker_id,
            active_job_id=active_job_id,
            last_seen_at=datetime.now(timezone.utc),
        )
        self.items[worker_id] = heartbeat
        return heartbeat

    def get(self, worker_id: str) -> WorkerHeartbeat | None:
        return self.items.get(worker_id)
