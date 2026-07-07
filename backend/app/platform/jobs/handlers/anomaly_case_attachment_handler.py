from app.anomaly.cases.anomaly_case_attachment_service import AnomalyCaseAttachmentService
from app.anomaly.persistence.anomaly_finding_repository import AnomalyFindingRepository
from app.infrastructure.persistence.repositories.investigation_repository import InvestigationRepository
from app.platform.jobs.job_handlers import JobHandler
from app.platform.jobs.job_models import JobRecord, JobType


class AnomalyCaseAttachmentJobHandler(JobHandler):
    job_type = JobType.ANOMALY_CASE_ATTACHMENT

    def __init__(self, session) -> None:
        self.session = session

    async def handle(self, job: JobRecord) -> dict:
        entity_type = job.payload["entity_type"]
        entity_id = job.payload["entity_id"]
        minimum_score = int(job.payload.get("minimum_score", 61))

        anomaly_score = AnomalyFindingRepository(self.session).get_latest(
            organization_id=job.organization_id,
            entity_type=entity_type,
            entity_id=entity_id,
        )
        if anomaly_score is None:
            return {"case_created": False, "reason": "No anomaly finding found."}

        case = AnomalyCaseAttachmentService(
            InvestigationRepository(self.session)
        ).attach_or_create_case(
            organization_id=job.organization_id,
            anomaly_score=anomaly_score,
            minimum_score=minimum_score,
        )

        return {
            "case_created": case is not None,
            "case_id": case.case_id if case else None,
        }
