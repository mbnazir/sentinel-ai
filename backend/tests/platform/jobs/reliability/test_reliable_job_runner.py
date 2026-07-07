from datetime import datetime, timezone

from app.platform.jobs.job_handlers import JobHandler
from app.platform.jobs.job_models import JobRecord, JobStatus, JobType
from app.platform.jobs.job_registry import JobHandlerRegistry
from app.platform.jobs.reliability.reliable_job_runner import ReliableJobRunner
from app.platform.jobs.reliability.retry_policy import RetryPolicy


class MemoryRepository:
    def __init__(self):
        self.saved = []

    def save(self, job):
        self.saved.append(job)
        return job


class FailingHandler(JobHandler):
    job_type = JobType.SCAN_RUN

    async def handle(self, job):
        raise RuntimeError("boom")


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


async def test_reliable_runner_marks_success() -> None:
    repo = MemoryRepository()
    registry = JobHandlerRegistry()
    registry.register(PassingHandler())

    result = await ReliableJobRunner(repo, registry).run(make_job())

    assert result.status == JobStatus.SUCCEEDED
    assert result.payload["_result"]["ok"] is True


async def test_reliable_runner_requeues_when_retry_allowed() -> None:
    repo = MemoryRepository()
    registry = JobHandlerRegistry()
    registry.register(FailingHandler())

    result = await ReliableJobRunner(repo, registry, RetryPolicy(max_attempts=2)).run(make_job())

    assert result.status == JobStatus.QUEUED
    assert result.payload["_attempt_count"] == 1


async def test_reliable_runner_dead_letters_after_max_attempts() -> None:
    repo = MemoryRepository()
    registry = JobHandlerRegistry()
    registry.register(FailingHandler())
    job = make_job()
    job = job.__class__(**{**job.__dict__, "payload": {"_attempt_count": 1}})

    result = await ReliableJobRunner(repo, registry, RetryPolicy(max_attempts=2)).run(job)

    assert result.status == JobStatus.FAILED
