from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.platform.jobs.handlers.persistent_job_registry import build_persistent_job_registry
from app.platform.jobs.job_service import JobService
from app.platform.jobs.persistence.persistent_job_repository import PersistentJobRepository
from app.platform.scheduler.schedule_repository import JobScheduleRepository
from app.platform.scheduler.scheduler_service import SchedulerService


class DueScheduleRunner:
    def __init__(self, session: Session) -> None:
        job_service = JobService(
            repository=PersistentJobRepository(session),
            registry=build_persistent_job_registry(session),
        )
        self.scheduler = SchedulerService(
            schedule_repository=JobScheduleRepository(session),
            job_service=job_service,
        )

    def enqueue_due_jobs(self, limit: int = 100) -> list[str]:
        return self.scheduler.run_due(now=datetime.now(timezone.utc), limit=limit)
