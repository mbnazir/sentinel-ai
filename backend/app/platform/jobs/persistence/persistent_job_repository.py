from sqlalchemy.orm import Session

from app.infrastructure.persistence.models_jobs import JobRunModel
from app.platform.jobs.job_models import JobRecord, JobStatus, JobType


class PersistentJobRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def save(self, job: JobRecord) -> JobRecord:
        model = self.session.query(JobRunModel).filter_by(job_id=job.job_id).one_or_none()
        if model is None:
            model = JobRunModel(job_id=job.job_id)
            self.session.add(model)

        model.job_type = job.job_type.value
        model.organization_id = job.organization_id
        model.status = job.status.value
        model.payload = job.payload
        model.requested_by = job.requested_by
        model.created_at = job.created_at
        model.started_at = job.started_at
        model.finished_at = job.finished_at
        model.error_message = job.error_message

        self.session.commit()
        return job

    def get(self, job_id: str) -> JobRecord | None:
        model = self.session.query(JobRunModel).filter_by(job_id=job_id).one_or_none()
        return self._to_domain(model) if model else None

    def list(self, organization_id: str | None = None, status: JobStatus | None = None) -> list[JobRecord]:
        query = self.session.query(JobRunModel)

        if organization_id:
            query = query.filter_by(organization_id=organization_id)

        if status:
            query = query.filter_by(status=status.value)

        rows = query.order_by(JobRunModel.created_at.desc()).limit(500).all()
        return [self._to_domain(row) for row in rows]

    def _to_domain(self, model: JobRunModel) -> JobRecord:
        return JobRecord(
            job_id=model.job_id,
            job_type=JobType(model.job_type),
            organization_id=model.organization_id,
            status=JobStatus(model.status),
            payload=model.payload or {},
            requested_by=model.requested_by,
            created_at=model.created_at,
            started_at=model.started_at,
            finished_at=model.finished_at,
            error_message=model.error_message,
        )
