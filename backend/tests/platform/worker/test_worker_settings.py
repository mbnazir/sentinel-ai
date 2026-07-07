from app.platform.worker.worker_settings import WorkerSettings


def test_worker_settings_defaults() -> None:
    settings = WorkerSettings()

    assert settings.poll_interval_seconds == 60
    assert settings.run_once is False
    assert settings.max_jobs_per_tick == 100
