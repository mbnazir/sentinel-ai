# Milestone 38 — Event-driven Job Runtime

## Purpose

Milestone 37 introduced event-emitting wrappers. Milestone 38 wires them into job execution and worker runtime.

## Added

- event runtime factory
- event-aware job service
- event-aware job factory
- event-aware queued job runner
- event-aware worker service
- event-aware worker CLI
- event-aware worker Dockerfile
- tests

## Run locally

```bash
cd backend
SENTINEL_WORKER_RUN_ONCE=true python -m scripts.event_aware_worker
```

## Docker

```bash
docker build -f backend/Dockerfile.event-aware-worker -t sentinel-event-aware-worker backend
```

## What this enables

- quartz_sync completion can enqueue scan_run
- scan_run completion can enqueue behavior_refresh
- job failures can emit job_failed events
- event history becomes the audit spine for workflow execution

## Next milestone

Investigation Workspace backend: richer case timeline, notes, actions, and evidence retrieval.
