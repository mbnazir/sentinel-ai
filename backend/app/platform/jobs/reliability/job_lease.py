from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


@dataclass(frozen=True)
class JobLease:
    job_id: str
    worker_id: str
    leased_until: datetime

    def is_expired(self, now: datetime | None = None) -> bool:
        now = now or datetime.now(timezone.utc)
        return now >= self.leased_until


class InMemoryJobLeaseRepository:
    def __init__(self) -> None:
        self.leases: dict[str, JobLease] = {}

    def acquire(self, job_id: str, worker_id: str, ttl_seconds: int = 300) -> JobLease | None:
        now = datetime.now(timezone.utc)
        existing = self.leases.get(job_id)

        if existing is not None and not existing.is_expired(now):
            return None

        lease = JobLease(
            job_id=job_id,
            worker_id=worker_id,
            leased_until=now + timedelta(seconds=ttl_seconds),
        )
        self.leases[job_id] = lease
        return lease

    def release(self, job_id: str, worker_id: str) -> bool:
        existing = self.leases.get(job_id)
        if existing is None or existing.worker_id != worker_id:
            return False

        del self.leases[job_id]
        return True
