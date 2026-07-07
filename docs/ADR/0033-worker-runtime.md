# ADR-0033: Worker runtime for scheduled jobs

## Status

Accepted

## Context

Scheduled jobs require a runtime outside the HTTP API process.

## Decision

Add a worker service that enqueues due scheduled jobs and executes queued jobs.

## Consequences

- Jobs can run without user interaction.
- The worker can be deployed as a container or Kubernetes worker.
- Future retries and dead-letter handling can be added at the worker layer.
