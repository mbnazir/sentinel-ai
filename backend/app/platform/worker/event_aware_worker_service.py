import asyncio
import logging

from sqlalchemy.orm import Session

from app.platform.events.runtime.event_aware_job_factory import build_event_aware_job_service
from app.platform.scheduler.schedule_repository import JobScheduleRepository
from app.platform.scheduler.scheduler_service import SchedulerService
from app.platform.worker.reliability.event_aware_queued_job_runner import EventAwareQueuedJobRunner
from app.platform.worker.reliability.worker_id import resolve_worker_id
from app.platform.worker.worker_settings import WorkerSettings

logger = logging.getLogger(__name__)


class EventAwareWorkerService:
    """Worker that enqueues due schedules, executes jobs, and emits domain events."""

    def __init__(self, session_factory, settings: WorkerSettings) -> None:
        self.session_factory = session_factory
        self.settings = settings
        self._stop_requested = False

    def request_stop(self) -> None:
        self._stop_requested = True

    async def run(self) -> None:
        while not self._stop_requested:
            await self.tick()

            if self.settings.run_once:
                break

            await asyncio.sleep(self.settings.poll_interval_seconds)

    async def tick(self) -> dict[str, list[str]]:
        session: Session = self.session_factory()
        try:
            job_service = build_event_aware_job_service(session)
            scheduler = SchedulerService(
                schedule_repository=JobScheduleRepository(session),
                job_service=job_service,
            )
            enqueued = scheduler.run_due(limit=self.settings.max_jobs_per_tick)
            attempted = await EventAwareQueuedJobRunner(
                job_service=job_service,
                worker_id=resolve_worker_id(),
            ).run_queued_jobs(limit=self.settings.max_jobs_per_tick)

            logger.info(
                "event_aware_worker_tick_completed",
                extra={"enqueued_jobs": len(enqueued), "attempted_jobs": len(attempted)},
            )
            return {"enqueued": enqueued, "attempted": attempted}
        finally:
            session.close()
