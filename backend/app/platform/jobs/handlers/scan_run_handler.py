from datetime import date

from app.platform.jobs.job_handlers import JobHandler
from app.platform.jobs.job_models import JobRecord, JobType
from app.scans.domain.scan_models import ScanRequest
from app.scans.services.normalized_scan_repository import NormalizedScanRepository
from app.scans.services.scan_pipeline_service import ScanPipelineService


class ScanRunJobHandler(JobHandler):
    job_type = JobType.SCAN_RUN

    def __init__(self, session) -> None:
        self.session = session

    async def handle(self, job: JobRecord) -> dict:
        summary = ScanPipelineService(NormalizedScanRepository(self.session)).run(
            ScanRequest(
                organization_id=job.organization_id,
                shift_date_from=date.fromisoformat(job.payload["shift_date_from"]),
                shift_date_to=date.fromisoformat(job.payload["shift_date_to"]),
                create_cases=bool(job.payload.get("create_cases", True)),
                minimum_case_score=int(job.payload.get("minimum_case_score", 61)),
            )
        )
        return {
            "scan_id": summary.scan_id,
            "sessions_scanned": summary.sessions_scanned,
            "cases_created": summary.cases_created,
            "status": summary.status.value,
        }
