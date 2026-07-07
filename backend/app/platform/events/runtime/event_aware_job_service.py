from app.platform.events.integration.event_emitting_job_runner import EventEmittingJobRunner
from app.platform.jobs.job_models import JobRecord
from app.platform.jobs.job_service import JobService


class EventAwareJobService(JobService):
    """JobService variant that emits domain events when jobs complete or fail."""

    def __init__(self, repository, registry, dispatcher) -> None:
        super().__init__(repository=repository, registry=registry)
        self.dispatcher = dispatcher

    async def run_now(self, job_id: str) -> JobRecord:
        job = self.repository.get(job_id)
        if job is None:
            raise ValueError(f"Job {job_id} not found.")

        return await EventEmittingJobRunner(
            repository=self.repository,
            registry=self.registry,
            dispatcher=self.dispatcher,
        ).run(job)
