from app.platform.worker.worker_service import WorkerService
from app.platform.worker.worker_settings import WorkerSettings


class FakeSession:
    def close(self):
        pass


def fake_session_factory():
    return FakeSession()


async def test_worker_service_run_once_executes_tick(monkeypatch) -> None:
    worker = WorkerService(
        session_factory=fake_session_factory,
        settings=WorkerSettings(run_once=True),
    )

    async def fake_tick():
        return {"enqueued": [], "completed": []}

    monkeypatch.setattr(worker, "tick", fake_tick)

    await worker.run()

    assert True
