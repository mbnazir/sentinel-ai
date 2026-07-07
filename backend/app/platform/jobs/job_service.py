from dataclasses import replace
from datetime import datetime, timezone
from uuid import uuid4

from app.platform.jobs.job_models import JobRecord, JobRequest, JobStatus
from app.platform.jobs.job_registry import JobHandlerRegistry, build_default_job_registry
from app.platform.jobs.job_repository import InMemoryJobRepository


class JobService:
    def __init__(
        self,
        repository: InMemoryJobRepository | None = None,
        registry: JobHandlerRegistry | None = None,
    ) -> None:
        self.repository = repository or InMemoryJobRepository()
        self.registry = registry or build_default_job_registry()

    def enqueue(self, request: JobRequest) -> JobRecord:
        now = datetime.now(timezone.utc)
        job = JobRecord(
            job_id=f"JOB-{uuid4().hex[:12].upper()}",
            job_type=request.job_type,
            organization_id=request.organization_id,
            status=JobStatus.QUEUED,
            payload=request.payload,
            requested_by=request.requested_by,
            created_at=now,
        )
        return self.repository.save(job)

    async def run_now(self, job_id: str) -> JobRecord:
        job = self.repository.get(job_id)
        if job is None:
            raise ValueError(f"Job {job_id} not found.")

        running = replace(job, status=JobStatus.RUNNING, started_at=datetime.now(timezone.utc))
        self.repository.save(running)

        try:
            handler = self.registry.get(running.job_type)
            result = await handler.handle(running)
            succeeded = replace(
                running,
                status=JobStatus.SUCCEEDED,
                finished_at=datetime.now(timezone.utc),
                payload={**running.payload, "_result": result},
            )
            return self.repository.save(succeeded)
        except Exception as exc:
            failed = replace(
                running,
                status=JobStatus.FAILED,
                finished_at=datetime.now(timezone.utc),
                error_message=str(exc),
            )
            self.repository.save(failed)
            raise

    def get(self, job_id: str) -> JobRecord | None:
        return self.repository.get(job_id)

    def list(self, organization_id: str | None = None, status: JobStatus | None = None) -> list[JobRecord]:
        return self.repository.list(organization_id=organization_id, status=status)
