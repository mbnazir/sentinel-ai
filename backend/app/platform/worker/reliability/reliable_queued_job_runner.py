from app.platform.jobs.job_models import JobStatus
from app.platform.jobs.job_registry import JobHandlerRegistry
from app.platform.jobs.persistence.persistent_job_repository import PersistentJobRepository
from app.platform.jobs.reliability.job_lease import InMemoryJobLeaseRepository
from app.platform.jobs.reliability.reliable_job_runner import ReliableJobRunner
from app.platform.jobs.reliability.worker_heartbeat import InMemoryWorkerHeartbeatRepository


class ReliableQueuedJobRunner:
    """Runs queued jobs with lease + heartbeat + retry/DLQ semantics."""

    def __init__(
        self,
        repository: PersistentJobRepository,
        registry: JobHandlerRegistry,
        worker_id: str,
        lease_repository: InMemoryJobLeaseRepository | None = None,
        heartbeat_repository: InMemoryWorkerHeartbeatRepository | None = None,
        lease_ttl_seconds: int = 300,
    ) -> None:
        self.repository = repository
        self.registry = registry
        self.worker_id = worker_id
        self.lease_repository = lease_repository or InMemoryJobLeaseRepository()
        self.heartbeat_repository = heartbeat_repository or InMemoryWorkerHeartbeatRepository()
        self.lease_ttl_seconds = lease_ttl_seconds

    async def run_queued_jobs(self, limit: int = 100) -> list[str]:
        queued_jobs = self.repository.list(status=JobStatus.QUEUED)[:limit]
        completed_or_attempted: list[str] = []

        for job in queued_jobs:
            lease = self.lease_repository.acquire(
                job_id=job.job_id,
                worker_id=self.worker_id,
                ttl_seconds=self.lease_ttl_seconds,
            )
            if lease is None:
                continue

            try:
                self.heartbeat_repository.beat(self.worker_id, active_job_id=job.job_id)
                await ReliableJobRunner(
                    repository=self.repository,
                    registry=self.registry,
                ).run(job)
                completed_or_attempted.append(job.job_id)
            finally:
                self.heartbeat_repository.beat(self.worker_id, active_job_id=None)
                self.lease_repository.release(job.job_id, self.worker_id)

        return completed_or_attempted
