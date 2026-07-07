import asyncio

from app.core.database.session import SessionLocal
from app.core.logging.logging_config import configure_logging
from app.platform.worker.worker_service import WorkerService
from app.platform.worker.worker_settings import load_worker_settings


async def main() -> None:
    configure_logging()
    worker = WorkerService(
        session_factory=SessionLocal,
        settings=load_worker_settings(),
    )
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
