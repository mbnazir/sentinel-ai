from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database.session import get_db_session
from app.platform.jobs.handlers.persistent_job_registry import build_persistent_job_registry
from app.platform.jobs.job_models import JobType
from app.platform.jobs.job_service import JobService
from app.platform.jobs.persistence.persistent_job_repository import PersistentJobRepository
from app.platform.scheduler.api.schemas import CreateScheduleRequest, RunDueResponse, ScheduleResponse
from app.platform.scheduler.schedule_models import ScheduleFrequency
from app.platform.scheduler.schedule_repository import JobScheduleRepository
from app.platform.scheduler.scheduler_service import SchedulerService
from app.shared.api_response import ApiResponse

router = APIRouter()


def build_scheduler(session: Session) -> SchedulerService:
    job_service = JobService(
        repository=PersistentJobRepository(session),
        registry=build_persistent_job_registry(session),
    )
    return SchedulerService(JobScheduleRepository(session), job_service)


def to_response(schedule) -> ScheduleResponse:
    return ScheduleResponse(
        schedule_id=schedule.schedule_id,
        name=schedule.name,
        organization_id=schedule.organization_id,
        job_type=schedule.job_type.value,
        frequency=schedule.frequency.value,
        payload=schedule.payload,
        status=schedule.status.value,
        created_by=schedule.created_by,
        created_at=schedule.created_at,
        last_run_at=schedule.last_run_at,
        next_run_at=schedule.next_run_at,
    )


@router.post("", response_model=ApiResponse[ScheduleResponse])
def create_schedule(
    request: CreateScheduleRequest,
    session: Session = Depends(get_db_session),
) -> ApiResponse[ScheduleResponse]:
    schedule = build_scheduler(session).create_schedule(
        name=request.name,
        organization_id=request.organization_id,
        job_type=JobType(request.job_type),
        frequency=ScheduleFrequency(request.frequency),
        payload=request.payload,
        created_by=request.created_by,
    )
    return ApiResponse(data=to_response(schedule))


@router.get("", response_model=ApiResponse[list[ScheduleResponse]])
def list_schedules(
    organization_id: str | None = None,
    session: Session = Depends(get_db_session),
) -> ApiResponse[list[ScheduleResponse]]:
    schedules = JobScheduleRepository(session).list(organization_id=organization_id)
    return ApiResponse(data=[to_response(schedule) for schedule in schedules])


@router.post("/run-due", response_model=ApiResponse[RunDueResponse])
def run_due(session: Session = Depends(get_db_session)) -> ApiResponse[RunDueResponse]:
    job_ids = build_scheduler(session).run_due()
    return ApiResponse(data=RunDueResponse(enqueued_job_ids=job_ids))
