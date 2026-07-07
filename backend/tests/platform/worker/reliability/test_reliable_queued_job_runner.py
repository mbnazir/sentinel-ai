from datetime import datetime, timezone

from app.platform.jobs.job_handlers import JobHandler
from app.platform.jobs.job_models import JobRecord, JobStatus, JobType
from app.platform.jobs.job_registry import JobHandlerRegistry
from app.platform.worker.reliability.reliable_queued_job_runner import ReliableQueuedJobRunner


class MemoryRepository:
    def __init__(self):
        self.jobs = {}

    def save(self, job):
        self.jobs[job.job_id] = job
        return job

    def list(self, organization_id=None, status=None):
        jobs = list(self.jobs.values())
        if status:
            jobs = [job for job in jobs if job.status == status]
        return jobs


class PassingHandler(JobHandler):
    job_type = JobType.SCAN_RUN

    async def handle(self, job):
        return {"ok": True}


def make_job():
    return JobRecord(
        job_id="JOB1",
        job_type=JobType.SCAN_RUN,
        organization_id="ORG1",
        status=JobStatus.QUEUED,
        payload={},
        requested_by=None,
        created_at=datetime.now(timezone.utc),
    )


async def test_reliable_queued_job_runner_runs_queued_job() -> None:
    repo = MemoryRepository()
    repo.save(make_job())

    registry = JobHandlerRegistry()
    registry.register(PassingHandler())

    attempted = await ReliableQueuedJobRunner(repo, registry, worker_id="W1").run_queued_jobs()

    assert attempted == ["JOB1"]
    assert repo.jobs["JOB1"].status == JobStatus.SUCCEEDED
