from datetime import datetime, timezone

from app.platform.events.event_models import EventType
from app.platform.events.integration.job_event_mapper import JobEventMapper
from app.platform.jobs.job_models import JobRecord, JobStatus, JobType


def make_job(status):
    return JobRecord(
        job_id="JOB1",
        job_type=JobType.SCAN_RUN,
        organization_id="ORG1",
        status=status,
        payload={"_result": {"scan_id": "SCAN1"}},
        requested_by="U1",
        created_at=datetime.now(timezone.utc),
        error_message="boom" if status == JobStatus.FAILED else None,
    )


def test_completion_event_for_scan_job() -> None:
    event = JobEventMapper().to_completion_event(make_job(JobStatus.SUCCEEDED))

    assert event.event_type == EventType.SCAN_COMPLETED
    assert event.payload["job_id"] == "JOB1"


def test_failure_event() -> None:
    event = JobEventMapper().to_failure_event(make_job(JobStatus.FAILED))

    assert event.event_type == EventType.JOB_FAILED
    assert event.payload["error_message"] == "boom"
