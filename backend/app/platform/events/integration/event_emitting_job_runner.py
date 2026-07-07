from app.platform.events.event_dispatcher import DomainEventDispatcher
from app.platform.events.integration.job_event_mapper import JobEventMapper
from app.platform.jobs.job_models import JobRecord
from app.platform.jobs.job_registry import JobHandlerRegistry
from app.platform.jobs.reliability.reliable_job_runner import ReliableJobRunner
from app.platform.jobs.reliability.retry_policy import RetryPolicy


class EventEmittingJobRunner:
    """Runs a job reliably and emits domain events after terminal outcomes."""

    def __init__(
        self,
        repository,
        registry: JobHandlerRegistry,
        dispatcher: DomainEventDispatcher,
        retry_policy: RetryPolicy | None = None,
        event_mapper: JobEventMapper | None = None,
    ) -> None:
        self.runner = ReliableJobRunner(repository, registry, retry_policy=retry_policy)
        self.dispatcher = dispatcher
        self.event_mapper = event_mapper or JobEventMapper()

    async def run(self, job: JobRecord) -> JobRecord:
        result = await self.runner.run(job)

        for event in [
            self.event_mapper.to_completion_event(result),
            self.event_mapper.to_failure_event(result),
        ]:
            if event is not None:
                await self.dispatcher.dispatch(event)

        return result
