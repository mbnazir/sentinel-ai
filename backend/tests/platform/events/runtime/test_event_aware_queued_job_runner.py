from datetime import datetime, timezone

from app.platform.jobs.job_models import JobRecord, JobStatus, JobType
from app.platform.worker.reliability.event_aware_queued_job_runner import EventAwareQueuedJobRunner


class FakeJobService:
    def __init__(self):
        self.ran = []

    def list(self, status=None):
        return [
            JobRecord(
                job_id="JOB1",
                job_type=JobType.SCAN_RUN,
                organization_id="ORG1",
                status=JobStatus.QUEUED,
                payload={},
                requested_by=None,
                created_at=datetime.now(timezone.utc),
            )
        ]

    async def run_now(self, job_id):
        self.ran.append(job_id)


async def test_event_aware_queued_job_runner_runs_job() -> None:
    service = FakeJobService()

    attempted = await EventAwareQueuedJobRunner(service, "W1").run_queued_jobs()

    assert attempted == ["JOB1"]
    assert service.ran == ["JOB1"]
