from sqlalchemy.orm import Session

from app.platform.jobs.handlers.persistent_job_registry import build_persistent_job_registry
from app.platform.jobs.persistence.persistent_job_repository import PersistentJobRepository
from app.platform.worker.reliability.reliable_queued_job_runner import ReliableQueuedJobRunner
from app.platform.worker.reliability.worker_id import resolve_worker_id


def build_reliable_queued_job_runner(session: Session) -> ReliableQueuedJobRunner:
    return ReliableQueuedJobRunner(
        repository=PersistentJobRepository(session),
        registry=build_persistent_job_registry(session),
        worker_id=resolve_worker_id(),
    )
