from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database.session import get_db_session
from app.platform.jobs.api.schemas import EnqueueJobRequest, JobResponse
from app.platform.jobs.handlers.persistent_job_registry import build_persistent_job_registry
from app.platform.jobs.job_models import JobRequest, JobStatus, JobType
from app.platform.jobs.job_service import JobService
from app.platform.jobs.persistence.persistent_job_repository import PersistentJobRepository
from app.shared.api_response import ApiResponse

router = APIRouter()


def build_service(session: Session) -> JobService:
    return JobService(
        repository=PersistentJobRepository(session),
        registry=build_persistent_job_registry(session),
    )


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
def enqueue_job(request: EnqueueJobRequest, session: Session = Depends(get_db_session)) -> ApiResponse[JobResponse]:
    try:
        job = build_service(session).enqueue(
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
async def run_job(job_id: str, session: Session = Depends(get_db_session)) -> ApiResponse[JobResponse]:
    try:
        job = await build_service(session).run_now(job_id)
        return ApiResponse(data=to_response(job))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("", response_model=ApiResponse[list[JobResponse]])
def list_jobs(
    organization_id: str | None = None,
    status: str | None = None,
    session: Session = Depends(get_db_session),
) -> ApiResponse[list[JobResponse]]:
    parsed_status = JobStatus(status) if status else None
    return ApiResponse(
        data=[
            to_response(job)
            for job in build_service(session).list(organization_id=organization_id, status=parsed_status)
        ]
    )
