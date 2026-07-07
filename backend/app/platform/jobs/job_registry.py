from app.platform.jobs.job_handlers import JobHandler, NoOpJobHandler
from app.platform.jobs.job_models import JobType


class JobHandlerRegistry:
    def __init__(self) -> None:
        self._handlers: dict[JobType, JobHandler] = {}

    def register(self, handler: JobHandler) -> None:
        self._handlers[handler.job_type] = handler

    def get(self, job_type: JobType) -> JobHandler:
        if job_type not in self._handlers:
            raise KeyError(f"No job handler registered for {job_type.value}")
        return self._handlers[job_type]


def build_default_job_registry() -> JobHandlerRegistry:
    registry = JobHandlerRegistry()

    for job_type in JobType:
        registry.register(NoOpJobHandler(job_type))

    return registry
