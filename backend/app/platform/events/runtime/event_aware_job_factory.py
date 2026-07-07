from sqlalchemy.orm import Session

from app.platform.events.runtime.event_aware_job_service import EventAwareJobService
from app.platform.events.runtime.event_runtime_factory import build_event_dispatcher
from app.platform.jobs.handlers.persistent_job_registry import build_persistent_job_registry
from app.platform.jobs.persistence.persistent_job_repository import PersistentJobRepository


def build_event_aware_job_service(session: Session) -> EventAwareJobService:
    return EventAwareJobService(
        repository=PersistentJobRepository(session),
        registry=build_persistent_job_registry(session),
        dispatcher=build_event_dispatcher(session),
    )
