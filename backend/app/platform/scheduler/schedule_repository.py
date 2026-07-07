from datetime import datetime

from sqlalchemy.orm import Session

from app.infrastructure.persistence.models_scheduler import JobScheduleModel
from app.platform.jobs.job_models import JobType
from app.platform.scheduler.schedule_models import JobSchedule, ScheduleFrequency, ScheduleStatus


class JobScheduleRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def save(self, schedule: JobSchedule) -> JobSchedule:
        model = self.session.query(JobScheduleModel).filter_by(schedule_id=schedule.schedule_id).one_or_none()

        if model is None:
            model = JobScheduleModel(schedule_id=schedule.schedule_id)
            self.session.add(model)

        model.name = schedule.name
        model.organization_id = schedule.organization_id
        model.job_type = schedule.job_type.value
        model.frequency = schedule.frequency.value
        model.payload = schedule.payload
        model.status = schedule.status.value
        model.created_by = schedule.created_by
        model.created_at = schedule.created_at
        model.last_run_at = schedule.last_run_at
        model.next_run_at = schedule.next_run_at

        self.session.commit()
        return schedule

    def get(self, schedule_id: str) -> JobSchedule | None:
        model = self.session.query(JobScheduleModel).filter_by(schedule_id=schedule_id).one_or_none()
        return self._to_domain(model) if model else None

    def list_due(self, now: datetime, limit: int = 100) -> list[JobSchedule]:
        rows = (
            self.session.query(JobScheduleModel)
            .filter(JobScheduleModel.status == ScheduleStatus.ACTIVE.value)
            .filter(JobScheduleModel.next_run_at <= now)
            .order_by(JobScheduleModel.next_run_at.asc())
            .limit(limit)
            .all()
        )
        return [self._to_domain(row) for row in rows]

    def list(self, organization_id: str | None = None, limit: int = 100) -> list[JobSchedule]:
        query = self.session.query(JobScheduleModel)
        if organization_id:
            query = query.filter_by(organization_id=organization_id)

        return [
            self._to_domain(row)
            for row in query.order_by(JobScheduleModel.created_at.desc()).limit(limit).all()
        ]

    def _to_domain(self, model: JobScheduleModel) -> JobSchedule:
        return JobSchedule(
            schedule_id=model.schedule_id,
            name=model.name,
            organization_id=model.organization_id,
            job_type=JobType(model.job_type),
            frequency=ScheduleFrequency(model.frequency),
            payload=model.payload or {},
            status=ScheduleStatus(model.status),
            created_by=model.created_by,
            created_at=model.created_at,
            last_run_at=model.last_run_at,
            next_run_at=model.next_run_at,
        )
