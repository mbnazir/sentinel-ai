from abc import ABC, abstractmethod

from app.platform.jobs.job_models import JobRecord, JobType


class JobHandler(ABC):
    job_type: JobType

    @abstractmethod
    async def handle(self, job: JobRecord) -> dict:
        raise NotImplementedError


class NoOpJobHandler(JobHandler):
    def __init__(self, job_type: JobType) -> None:
        self.job_type = job_type

    async def handle(self, job: JobRecord) -> dict:
        return {
            "message": f"No-op handler executed for {self.job_type.value}.",
            "job_id": job.job_id,
            "payload": job.payload,
        }
