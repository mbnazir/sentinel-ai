from sqlalchemy.orm import Session

from app.platform.events.default_subscribers import build_default_event_bus
from app.platform.events.event_dispatcher import DomainEventDispatcher
from app.platform.events.event_repository import DomainEventRepository
from app.platform.events.integration.event_subscribers import (
    JobEnqueueingEventSubscriber,
    register_workflow_subscribers,
)
from app.platform.jobs.handlers.persistent_job_registry import build_persistent_job_registry
from app.platform.jobs.job_service import JobService
from app.platform.jobs.persistence.persistent_job_repository import PersistentJobRepository


def build_event_dispatcher(session: Session) -> DomainEventDispatcher:
    job_service = JobService(
        repository=PersistentJobRepository(session),
        registry=build_persistent_job_registry(session),
    )
    bus = build_default_event_bus()
    register_workflow_subscribers(bus, JobEnqueueingEventSubscriber(job_service))
    return DomainEventDispatcher(
        repository=DomainEventRepository(session),
        bus=bus,
    )
