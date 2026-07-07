from fastapi import APIRouter, HTTPException

from app.platform.jobs.api.schemas import EnqueueJobRequest, JobResponse
from app.platform.jobs.job_models import JobRequest, JobStatus, JobType
from app.platform.jobs.job_service import JobService
from app.shared.api_response import ApiResponse

router = APIRouter()
job_service = JobService()


def to_response(job) -> JobResponse:
    return JobResponse(
        job_id=job.job_id,
        job_type=job.job_type.value,
        organization_id=job.organization_id,
        status=job.status.value,
        payload=job.payload,
        requested_by=job.requested_by,
        created_at=job.created_at,
        started_at=job.started_at,
        finished_at=job.finished_at,
        error_message=job.error_message,
    )


@router.post("", response_model=ApiResponse[JobResponse])
def enqueue_job(request: EnqueueJobRequest) -> ApiResponse[JobResponse]:
    try:
        job = job_service.enqueue(
            JobRequest(
                job_type=JobType(request.job_type),
                organization_id=request.organization_id,
                payload=request.payload,
                requested_by=request.requested_by,
            )
        )
        return ApiResponse(data=to_response(job))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{job_id}/run", response_model=ApiResponse[JobResponse])
async def run_job(job_id: str) -> ApiResponse[JobResponse]:
    try:
        job = await job_service.run_now(job_id)
        return ApiResponse(data=to_response(job))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("", response_model=ApiResponse[list[JobResponse]])
def list_jobs(
    organization_id: str | None = None,
    status: str | None = None,
) -> ApiResponse[list[JobResponse]]:
    parsed_status = JobStatus(status) if status else None
    return ApiResponse(
        data=[
            to_response(job)
            for job in job_service.list(organization_id=organization_id, status=parsed_status)
        ]
    )
