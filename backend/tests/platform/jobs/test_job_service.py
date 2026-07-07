from app.platform.jobs.job_models import JobRequest, JobStatus, JobType
from app.platform.jobs.job_service import JobService


async def test_job_service_enqueue_and_run() -> None:
    service = JobService()

    job = service.enqueue(
        JobRequest(
            job_type=JobType.SCAN_RUN,
            organization_id="ORG1",
            payload={"shift_date_from": "2026-07-01"},
            requested_by="U1",
        )
    )

    assert job.status == JobStatus.QUEUED

    completed = await service.run_now(job.job_id)

    assert completed.status == JobStatus.SUCCEEDED
    assert "_result" in completed.payload


def test_job_service_lists_jobs() -> None:
    service = JobService()
    service.enqueue(JobRequest(JobType.QUARTZ_SYNC, "ORG1"))
    service.enqueue(JobRequest(JobType.SCAN_RUN, "ORG2"))

    org1_jobs = service.list(organization_id="ORG1")

    assert len(org1_jobs) == 1
    assert org1_jobs[0].organization_id == "ORG1"
