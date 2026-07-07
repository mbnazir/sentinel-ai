from app.platform.jobs.job_models import JobRecord, JobStatus


class InMemoryJobRepository:
    """Simple job repository for local/dev execution.

    Production should replace this with a persistent repository backed by Postgres.
    """

    def __init__(self) -> None:
        self._jobs: dict[str, JobRecord] = {}

    def save(self, job: JobRecord) -> JobRecord:
        self._jobs[job.job_id] = job
        return job

    def get(self, job_id: str) -> JobRecord | None:
        return self._jobs.get(job_id)

    def list(self, organization_id: str | None = None, status: JobStatus | None = None) -> list[JobRecord]:
        jobs = list(self._jobs.values())

        if organization_id is not None:
            jobs = [job for job in jobs if job.organization_id == organization_id]

        if status is not None:
            jobs = [job for job in jobs if job.status == status]

        return sorted(jobs, key=lambda item: item.created_at, reverse=True)
