from sqlalchemy.orm import Session

from app.platform.jobs.handlers.persistent_job_registry import build_persistent_job_registry
from app.platform.jobs.job_models import JobStatus
from app.platform.jobs.job_service import JobService
from app.platform.jobs.persistence.persistent_job_repository import PersistentJobRepository


class QueuedJobRunner:
    def __init__(self, session: Session) -> None:
        self.service = JobService(
            repository=PersistentJobRepository(session),
            registry=build_persistent_job_registry(session),
        )

    async def run_queued_jobs(self, limit: int = 100) -> list[str]:
        queued_jobs = self.service.list(status=JobStatus.QUEUED)[:limit]
        completed_job_ids: list[str] = []

        for job in queued_jobs:
            await self.service.run_now(job.job_id)
            completed_job_ids.append(job.job_id)

        return completed_job_ids
