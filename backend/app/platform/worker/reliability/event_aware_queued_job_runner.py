from app.platform.events.runtime.event_aware_job_service import EventAwareJobService
from app.platform.jobs.job_models import JobStatus
from app.platform.jobs.reliability.job_lease import InMemoryJobLeaseRepository
from app.platform.jobs.reliability.worker_heartbeat import InMemoryWorkerHeartbeatRepository


class EventAwareQueuedJobRunner:
    """Runs queued jobs with leases/heartbeat and emits domain events."""

    def __init__(
        self,
        job_service: EventAwareJobService,
        worker_id: str,
        lease_repository: InMemoryJobLeaseRepository | None = None,
        heartbeat_repository: InMemoryWorkerHeartbeatRepository | None = None,
        lease_ttl_seconds: int = 300,
    ) -> None:
        self.job_service = job_service
        self.worker_id = worker_id
        self.lease_repository = lease_repository or InMemoryJobLeaseRepository()
        self.heartbeat_repository = heartbeat_repository or InMemoryWorkerHeartbeatRepository()
        self.lease_ttl_seconds = lease_ttl_seconds

    async def run_queued_jobs(self, limit: int = 100) -> list[str]:
        queued_jobs = self.job_service.list(status=JobStatus.QUEUED)[:limit]
        attempted: list[str] = []

        for job in queued_jobs:
            lease = self.lease_repository.acquire(job.job_id, self.worker_id, self.lease_ttl_seconds)
            if lease is None:
                continue

            try:
                self.heartbeat_repository.beat(self.worker_id, active_job_id=job.job_id)
                await self.job_service.run_now(job.job_id)
                attempted.append(job.job_id)
            finally:
                self.heartbeat_repository.beat(self.worker_id, active_job_id=None)
                self.lease_repository.release(job.job_id, self.worker_id)

        return attempted
