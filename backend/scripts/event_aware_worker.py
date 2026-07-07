import asyncio

from app.core.database.session import SessionLocal
from app.core.logging.logging_config import configure_logging
from app.platform.worker.event_aware_worker_service import EventAwareWorkerService
from app.platform.worker.worker_settings import load_worker_settings


async def main() -> None:
    configure_logging()
    worker = EventAwareWorkerService(
        session_factory=SessionLocal,
        settings=load_worker_settings(),
    )
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
