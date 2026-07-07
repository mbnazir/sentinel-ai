# ADR-0032: Scheduled jobs before worker runtime

## Status

Accepted

## Context

Jobs need recurrence before we decide exactly how workers will be deployed.

## Decision

Persist schedules and provide due-job enqueueing as a service/API.

## Consequences

- Scheduling semantics are testable.
- Cron, Kubernetes CronJob, Celery beat, or APScheduler can call the same service.
- Future worker runtime remains replaceable.
