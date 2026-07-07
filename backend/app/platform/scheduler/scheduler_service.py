from dataclasses import replace
from datetime import datetime, timezone
from uuid import uuid4

from app.platform.jobs.job_models import JobRequest
from app.platform.jobs.job_service import JobService
from app.platform.scheduler.schedule_calculator import ScheduleCalculator
from app.platform.scheduler.schedule_models import JobSchedule, ScheduleFrequency, ScheduleStatus
from app.platform.scheduler.schedule_repository import JobScheduleRepository


class SchedulerService:
    def __init__(
        self,
        schedule_repository: JobScheduleRepository,
        job_service: JobService,
        calculator: ScheduleCalculator | None = None,
    ) -> None:
        self.schedule_repository = schedule_repository
        self.job_service = job_service
        self.calculator = calculator or ScheduleCalculator()

    def create_schedule(
        self,
        name: str,
        organization_id: str,
        job_type,
        frequency: ScheduleFrequency,
        payload: dict,
        created_by: str | None = None,
    ) -> JobSchedule:
        now = datetime.now(timezone.utc)
        schedule = JobSchedule(
            schedule_id=f"SCH-{uuid4().hex[:12].upper()}",
            name=name,
            organization_id=organization_id,
            job_type=job_type,
            frequency=frequency,
            payload=payload,
            status=ScheduleStatus.ACTIVE,
            created_by=created_by,
            created_at=now,
            next_run_at=self.calculator.next_run_after(now, frequency),
        )
        return self.schedule_repository.save(schedule)

    def run_due(self, now: datetime | None = None, limit: int = 100) -> list[str]:
        now = now or datetime.now(timezone.utc)
        due = self.schedule_repository.list_due(now, limit=limit)
        job_ids: list[str] = []

        for schedule in due:
            job = self.job_service.enqueue(
                JobRequest(
                    job_type=schedule.job_type,
                    organization_id=schedule.organization_id,
                    payload=schedule.payload,
                    requested_by=schedule.created_by,
                )
            )
            job_ids.append(job.job_id)

            updated = replace(
                schedule,
                last_run_at=now,
                next_run_at=self.calculator.next_run_after(now, schedule.frequency),
            )
            self.schedule_repository.save(updated)

        return job_ids
