import asyncio
import logging

from sqlalchemy.orm import Session

from app.platform.worker.due_schedule_runner import DueScheduleRunner
from app.platform.worker.queued_job_runner import QueuedJobRunner
from app.platform.worker.worker_settings import WorkerSettings

logger = logging.getLogger(__name__)


class WorkerService:
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
            enqueued = DueScheduleRunner(session).enqueue_due_jobs(
                limit=self.settings.max_jobs_per_tick
            )
            completed = await QueuedJobRunner(session).run_queued_jobs(
                limit=self.settings.max_jobs_per_tick
            )
            logger.info(
                "worker_tick_completed",
                extra={"enqueued_jobs": len(enqueued), "completed_jobs": len(completed)},
            )
            return {"enqueued": enqueued, "completed": completed}
        finally:
            session.close()
