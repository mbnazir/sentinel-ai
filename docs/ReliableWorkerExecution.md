# Milestone 35 — Reliable Worker Execution

## Purpose

Milestone 34 added reliability primitives. Milestone 35 wires them into actual worker execution.

## Added

- ReliableQueuedJobRunner
- worker ID resolver
- reliable worker factory
- ReliableWorkerService
- reliable worker CLI entrypoint
- reliable worker Dockerfile
- tests

## Run locally

```bash
cd backend
SENTINEL_WORKER_RUN_ONCE=true python -m scripts.reliable_worker
```

## Docker

```bash
docker build -f backend/Dockerfile.reliable-worker -t sentinel-reliable-worker backend
```

## What changed

Queued jobs are now executed with:

- lease acquisition
- heartbeat updates
- retry handling
- dead-letter fallback

## Next milestone

Add event bus so job completion can trigger downstream workflows cleanly.
