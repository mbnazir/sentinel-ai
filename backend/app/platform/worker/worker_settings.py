from dataclasses import dataclass
import os


@dataclass(frozen=True)
class WorkerSettings:
    poll_interval_seconds: int = 60
    run_once: bool = False
    max_jobs_per_tick: int = 100


def load_worker_settings() -> WorkerSettings:
    return WorkerSettings(
        poll_interval_seconds=int(os.getenv("SENTINEL_WORKER_POLL_INTERVAL_SECONDS", "60")),
        run_once=os.getenv("SENTINEL_WORKER_RUN_ONCE", "false").lower() == "true",
        max_jobs_per_tick=int(os.getenv("SENTINEL_WORKER_MAX_JOBS_PER_TICK", "100")),
    )
