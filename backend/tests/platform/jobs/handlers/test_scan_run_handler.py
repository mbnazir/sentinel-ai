from app.platform.jobs.job_models import JobRecord, JobStatus, JobType
from datetime import datetime, timezone


def test_scan_run_job_payload_shape() -> None:
    job = JobRecord(
        job_id="JOB1",
        job_type=JobType.SCAN_RUN,
        organization_id="ORG1",
        status=JobStatus.QUEUED,
        payload={"shift_date_from": "2026-07-01", "shift_date_to": "2026-07-02"},
        requested_by="U1",
        created_at=datetime.now(timezone.utc),
    )

    assert job.payload["shift_date_from"] == "2026-07-01"
    assert job.job_type == JobType.SCAN_RUN
