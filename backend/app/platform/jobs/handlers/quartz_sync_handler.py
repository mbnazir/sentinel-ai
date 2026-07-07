from datetime import date

from app.connectors.quartz.api.routes import build_ingestion_service
from app.platform.jobs.job_handlers import JobHandler
from app.platform.jobs.job_models import JobRecord, JobType


class QuartzSyncJobHandler(JobHandler):
    job_type = JobType.QUARTZ_SYNC

    def __init__(self, session) -> None:
        self.session = session

    async def handle(self, job: JobRecord) -> dict:
        result = await build_ingestion_service(self.session).ingest_and_persist(
            organization_id=job.organization_id,
            shift_date_from=date.fromisoformat(job.payload["shift_date_from"]),
            shift_date_to=date.fromisoformat(job.payload["shift_date_to"]),
        )
        return {
            "fetched_sessions": result.fetched_sessions,
            "fetched_activities": result.fetched_activities,
            "persisted_sessions": result.persisted_sessions,
            "persisted_activities": result.persisted_activities,
        }
