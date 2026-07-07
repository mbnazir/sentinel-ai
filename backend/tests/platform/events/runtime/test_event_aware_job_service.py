from datetime import datetime, timezone

from app.platform.events.event_bus import DomainEventBus
from app.platform.events.event_dispatcher import DomainEventDispatcher
from app.platform.events.event_models import EventType
from app.platform.events.integration.job_event_mapper import JobEventMapper
from app.platform.events.runtime.event_aware_job_service import EventAwareJobService
from app.platform.jobs.job_handlers import JobHandler
from app.platform.jobs.job_models import JobRecord, JobStatus, JobType
from app.platform.jobs.job_registry import JobHandlerRegistry


class MemoryRepository:
    def __init__(self):
        self.jobs = {}
        self.events = []

    def save(self, item):
        if hasattr(item, "job_id"):
            self.jobs[item.job_id] = item
        else:
            self.events.append(item)
        return item

    def get(self, job_id):
        return self.jobs.get(job_id)

    def list(self, organization_id=None, status=None):
        jobs = list(self.jobs.values())
        if status:
            jobs = [job for job in jobs if job.status == status]
        return jobs


class PassingHandler(JobHandler):
    job_type = JobType.SCAN_RUN

    async def handle(self, job):
        return {"scan_id": "SCAN1"}


def test_job_event_mapper_still_maps_scan_completed() -> None:
    job = JobRecord(
        job_id="JOB1",
        job_type=JobType.SCAN_RUN,
        organization_id="ORG1",
        status=JobStatus.SUCCEEDED,
        payload={"_result": {"scan_id": "SCAN1"}},
        requested_by=None,
        created_at=datetime.now(timezone.utc),
    )

    event = JobEventMapper().to_completion_event(job)

    assert event.event_type == EventType.SCAN_COMPLETED


async def test_event_aware_job_service_persists_event() -> None:
    repo = MemoryRepository()
    job = JobRecord(
        job_id="JOB1",
        job_type=JobType.SCAN_RUN,
        organization_id="ORG1",
        status=JobStatus.QUEUED,
        payload={},
        requested_by=None,
        created_at=datetime.now(timezone.utc),
    )
    repo.save(job)

    registry = JobHandlerRegistry()
    registry.register(PassingHandler())
    dispatcher = DomainEventDispatcher(repo, DomainEventBus())

    result = await EventAwareJobService(repo, registry, dispatcher).run_now("JOB1")

    assert result.status == JobStatus.SUCCEEDED
    assert repo.events[0].event_type == EventType.SCAN_COMPLETED
