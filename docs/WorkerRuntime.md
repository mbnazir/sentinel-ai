# Milestone 33 — Worker Runtime

## Purpose

Milestone 32 added schedules, but schedules do nothing unless a worker process evaluates due schedules and runs queued jobs.

Milestone 33 adds a worker runtime.

## Added

- worker settings
- due schedule runner
- queued job runner
- worker service
- CLI entrypoint
- worker Dockerfile
- tests

## Run locally

```bash
cd backend
SENTINEL_WORKER_RUN_ONCE=true python -m scripts.worker
```

## Environment variables

```text
SENTINEL_WORKER_POLL_INTERVAL_SECONDS=60
SENTINEL_WORKER_RUN_ONCE=false
SENTINEL_WORKER_MAX_JOBS_PER_TICK=100
```

## Docker

```bash
docker build -f backend/Dockerfile.worker -t sentinel-worker backend
```

## Next milestone

Add worker observability: metrics, structured job events, failure reporting, retries, and dead-letter handling.
