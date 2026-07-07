from app.platform.jobs.job_models import JobRecord, JobStatus, JobType
from datetime import datetime, timezone


def test_job_record_has_persistent_fields() -> None:
    job = JobRecord(
        job_id="JOB1",
        job_type=JobType.QUARTZ_SYNC,
        organization_id="ORG1",
        status=JobStatus.QUEUED,
        payload={},
        requested_by=None,
        created_at=datetime.now(timezone.utc),
    )

    assert job.job_id == "JOB1"
    assert job.status == JobStatus.QUEUED
