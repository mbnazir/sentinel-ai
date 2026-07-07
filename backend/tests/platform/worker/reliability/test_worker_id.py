from app.platform.worker.reliability.worker_id import resolve_worker_id


def test_resolve_worker_id_returns_value(monkeypatch) -> None:
    monkeypatch.setenv("SENTINEL_WORKER_ID", "worker-1")

    assert resolve_worker_id() == "worker-1"
